"""Meal plan route — generate a 7-day budget-aware meal plan."""

import json
import random
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from database.models import db, Food, MealPlan, RDAValue
from routes.auth import token_required

meal_plan_bp = Blueprint('meal_plan', __name__)

MEAL_TYPES = ['breakfast', 'lunch', 'dinner', 'snack']

# Rough calorie targets per meal as fraction of daily total
MEAL_FRACTIONS = {'breakfast': 0.25, 'lunch': 0.35, 'dinner': 0.30, 'snack': 0.10}


def _get_rda(user) -> dict:
    gender = user.gender or 'male'
    age = user.age or 30
    rda = RDAValue.query.filter(
        RDAValue.gender == gender,
        RDAValue.age_min <= age,
        RDAValue.age_max >= age
    ).first()
    if not rda:
        rda = RDAValue.query.filter_by(gender='male').first()
    return rda.to_dict() if rda else {'calories': 2000, 'protein': 55}


def _generate_day_plan(foods_pool: list, diet_type: str, daily_budget: float,
                        rda: dict) -> dict:
    """
    Generate a single day's meal plan from the food pool.
    Simple greedy approach: pick foods that fit calorie targets and budget.
    """
    day = {}
    day_cost = 0.0
    day_nutrition = {k: 0.0 for k in ['calories', 'protein', 'iron', 'calcium',
                                        'vitaminC', 'vitaminD', 'vitaminB12',
                                        'fibre', 'carbs', 'fat']}

    # Filter by diet type
    allowed = [f for f in foods_pool if f.diet_type in ('veg', diet_type) or diet_type == 'nonveg']
    if not allowed:
        allowed = foods_pool

    for meal_type in MEAL_TYPES:
        target_cal = rda.get('calories', 2000) * MEAL_FRACTIONS[meal_type]
        meal_budget = daily_budget * MEAL_FRACTIONS[meal_type]
        meal_items = []
        meal_cost = 0.0
        meal_cal = 0.0

        # Pick 2-3 foods per meal
        candidates = random.sample(allowed, min(len(allowed), 20))
        for food in candidates:
            if meal_cal >= target_cal * 0.9:
                break
            if meal_cost + food.price_per_100g_inr > meal_budget:
                continue

            # Estimate serving size to hit ~30% of meal calorie target
            if food.calories and food.calories > 0:
                grams = min(300, max(50, (target_cal * 0.4 / food.calories) * 100))
            else:
                grams = 100

            factor = grams / 100.0
            item_cost = food.price_per_100g_inr * factor
            item_cal = (food.calories or 0) * factor

            meal_items.append({
                'food_id': food.id,
                'food_name': food.name,
                'food_group': food.food_group,
                'quantity_grams': round(grams),
                'cost_inr': round(item_cost, 2),
                'nutrition': {
                    'calories': round(item_cal, 1),
                    'protein': round((food.protein or 0) * factor, 1),
                    'iron': round((food.iron or 0) * factor, 2),
                }
            })

            meal_cost += item_cost
            meal_cal += item_cal
            for key in day_nutrition:
                day_nutrition[key] += getattr(food, key, 0) * factor

            if len(meal_items) >= 3:
                break

        day[meal_type] = meal_items
        day_cost += meal_cost

    return {'meals': day, 'cost_inr': round(day_cost, 2), 'nutrition': {
        k: round(v, 2) for k, v in day_nutrition.items()
    }}


def _compute_coverage(plan_nutrition: dict, rda: dict) -> dict:
    """Compute % RDA coverage for each nutrient."""
    coverage = {}
    nutrient_map = {
        'calories': 'calories', 'protein': 'protein', 'iron': 'iron',
        'calcium': 'calcium', 'vitaminC': 'vitaminC', 'vitaminD': 'vitaminD',
        'vitaminB12': 'vitaminB12', 'fibre': 'fibre',
    }
    for key, rda_key in nutrient_map.items():
        rda_val = rda.get(rda_key, 1)
        intake = plan_nutrition.get(key, 0)
        coverage[key] = round(min((intake / rda_val) * 100, 200), 1) if rda_val else 0
    return coverage


@meal_plan_bp.route('/generate', methods=['POST'])
@token_required
def generate_meal_plan(current_user):
    """Generate a 7-day meal plan respecting budget and diet type."""
    data = request.get_json() or {}
    week_start = date.fromisoformat(data.get('week_start', date.today().isoformat()))
    budget_monthly = current_user.budget_monthly_inr or 3000.0
    daily_budget = budget_monthly / 30.0
    diet_type = current_user.diet_type or 'veg'
    rda = _get_rda(current_user)

    foods_pool = Food.query.all()
    if not foods_pool:
        return jsonify({'error': 'No foods in database'}), 500

    plan = {}
    total_cost = 0.0
    avg_nutrition = {k: 0.0 for k in ['calories', 'protein', 'iron', 'calcium',
                                        'vitaminC', 'vitaminD', 'vitaminB12', 'fibre']}

    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_plan = _generate_day_plan(foods_pool, diet_type, daily_budget, rda)
        plan[day_date.isoformat()] = day_plan
        total_cost += day_plan['cost_inr']
        for key in avg_nutrition:
            avg_nutrition[key] += day_plan['nutrition'].get(key, 0)

    for key in avg_nutrition:
        avg_nutrition[key] = round(avg_nutrition[key] / 7, 2)

    coverage = _compute_coverage(avg_nutrition, rda)

    # Persist
    mp = MealPlan(
        user_id=current_user.id,
        week_start_date=week_start,
        plan_json=json.dumps(plan),
        total_cost=round(total_cost, 2),
        nutritional_coverage_json=json.dumps(coverage)
    )
    db.session.add(mp)
    db.session.commit()

    return jsonify({
        'id': mp.id,
        'week_start': week_start.isoformat(),
        'plan': plan,
        'total_cost_inr': round(total_cost, 2),
        'daily_budget_inr': round(daily_budget, 2),
        'avg_daily_nutrition': avg_nutrition,
        'nutritional_coverage_percent': coverage,
    })


@meal_plan_bp.route('/latest', methods=['GET'])
@token_required
def get_latest_plan(current_user):
    """Get the most recently generated meal plan."""
    mp = MealPlan.query.filter_by(user_id=current_user.id)\
                       .order_by(MealPlan.created_at.desc()).first()
    if not mp:
        return jsonify(None)
    return jsonify(mp.to_dict())
