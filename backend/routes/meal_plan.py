"""Meal plan route — generate a 7-day structured Indian meal plan."""

import json
import random
from collections import Counter
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from database.models import db, Food, MealPlan, RDAValue
from routes.auth import token_required

meal_plan_bp = Blueprint('meal_plan', __name__)

# ---------------------------------------------------------------------------
# FOOD TAXONOMY
# Maps lowercase food name substrings → classification metadata.
# ---------------------------------------------------------------------------
FOOD_TAXONOMY = {
    # ── Cereal-base: South Indian ──────────────────────────────────────────
    'idli':      {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'dinner'],                          'region': 'south-indian'},
    'dosa':      {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'dinner'],                          'region': 'south-indian'},
    'uttapam':   {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'dinner'],                          'region': 'south-indian'},
    'appam':     {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'dinner'],                          'region': 'south-indian'},
    # ── Cereal-base: snack-breakfast ──────────────────────────────────────
    'poha':      {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'morning_snack'],                   'region': 'west-indian'},
    'upma':      {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'morning_snack'],                   'region': 'south-indian'},
    # ── Cereal-base: flatbreads ────────────────────────────────────────────
    'paratha':   {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'lunch', 'dinner'],                 'region': 'north-indian'},
    'thepla':    {'role': 'cereal-base', 'eligible_meals': ['breakfast', 'lunch', 'dinner'],                 'region': 'west-indian'},
    'roti':      {'role': 'cereal-base', 'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'chapati':   {'role': 'cereal-base', 'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    # ── Cereal-base: rice & grains ─────────────────────────────────────────
    'rice':      {'role': 'cereal-base', 'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'khichdi':   {'role': 'cereal-base', 'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'oats':      {'role': 'cereal-base', 'eligible_meals': ['breakfast'],                                    'region': 'pan-indian'},
    # ── Dal / Pulse ────────────────────────────────────────────────────────
    'dal':       {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'sambar':    {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'south-indian'},
    'rasam':     {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'south-indian'},
    'rajma':     {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'north-indian'},
    'chana':     {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'chole':     {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'north-indian'},
    'moong':     {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'masoor':    {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'toor':      {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    'urad':      {'role': 'dal-pulse',   'eligible_meals': ['lunch', 'dinner'],                              'region': 'pan-indian'},
    # ── Sabzi / Vegetables ─────────────────────────────────────────────────
    'spinach':       {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'potato':        {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'tomato':        {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'carrot':        {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'brinjal':       {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'cauliflower':   {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'peas':          {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'bottle gourd':  {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'pumpkin':       {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'beetroot':      {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'capsicum':      {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'onion':         {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'drumstick':     {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'south-indian'},
    'bitter gourd':  {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'cabbage':       {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    'beans':         {'role': 'sabzi', 'eligible_meals': ['lunch', 'dinner'], 'region': 'pan-indian'},
    # ── Protein dishes ─────────────────────────────────────────────────────
    'paneer':    {'role': 'protein-dish', 'eligible_meals': ['breakfast', 'lunch', 'dinner'],                'region': 'north-indian'},
    'egg':       {'role': 'protein-dish', 'eligible_meals': ['breakfast', 'lunch', 'dinner'],                'region': 'pan-indian'},
    'chicken':   {'role': 'protein-dish', 'eligible_meals': ['lunch', 'dinner'],                             'region': 'pan-indian'},
    'fish':      {'role': 'protein-dish', 'eligible_meals': ['lunch', 'dinner'],                             'region': 'pan-indian'},
    'mutton':    {'role': 'protein-dish', 'eligible_meals': ['lunch', 'dinner'],                             'region': 'pan-indian'},
    # ── Dairy ──────────────────────────────────────────────────────────────
    'milk':        {'role': 'dairy', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],      'region': 'pan-indian'},
    'curd':        {'role': 'dairy', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],      'region': 'pan-indian'},
    'yogurt':      {'role': 'dairy', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],      'region': 'pan-indian'},
    'lassi':       {'role': 'dairy', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],      'region': 'north-indian'},
    'buttermilk':  {'role': 'dairy', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],      'region': 'pan-indian'},
    # ── Fruits ─────────────────────────────────────────────────────────────
    'banana':       {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'apple':        {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'orange':       {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'mango':        {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'papaya':       {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'guava':        {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'pineapple':    {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'watermelon':   {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'grapes':       {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    'pomegranate':  {'role': 'fruit', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],     'region': 'pan-indian'},
    # ── Dry snacks & sweets ────────────────────────────────────────────────
    'chivda':         {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'west-indian'},
    'murukku':        {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'south-indian'},
    'chakli':         {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'west-indian'},
    'makhana':        {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'roasted chana':  {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'peanuts':        {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'almonds':        {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'cashews':        {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'chikki':         {'role': 'dry-snack', 'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'ladoo':          {'role': 'sweet',     'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    'barfi':          {'role': 'sweet',     'eligible_meals': ['morning_snack', 'evening_snack'],            'region': 'pan-indian'},
    # ── Beverages ──────────────────────────────────────────────────────────
    'chai':   {'role': 'beverage', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],        'region': 'pan-indian'},
    'tea':    {'role': 'beverage', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],        'region': 'pan-indian'},
    'coffee': {'role': 'beverage', 'eligible_meals': ['breakfast', 'morning_snack', 'evening_snack'],        'region': 'pan-indian'},
    # ── Ingredients (never served as meal items) ───────────────────────────
    'ghee':             {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'oil':              {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'butter':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'salt':             {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'sugar':            {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'jaggery':          {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'turmeric':         {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'cumin':            {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'mustard':          {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'coriander seeds':  {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'ginger':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'garlic':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'pepper':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'cardamom':         {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'cloves':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'cinnamon':         {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'asafoetida':       {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'baking':           {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'yeast':            {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'vinegar':          {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'corn starch':      {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'wheat flour':      {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'besan':            {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'corn flour':       {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
    'maize flour':      {'role': 'ingredient', 'eligible_meals': [], 'region': 'pan-indian'},
}

# ---------------------------------------------------------------------------
# MEAL SLOT STRUCTURE
# ---------------------------------------------------------------------------
MEAL_SLOTS = {
    'breakfast': {
        'required': [
            {'role': 'cereal-base', 'eligible_meal': 'breakfast', 'grams': 200, 'name': 'main'},
        ],
        'optional': [
            {'role': 'dairy',  'eligible_meal': 'breakfast', 'grams': 150, 'name': 'drink'},
            {'role': 'fruit',  'eligible_meal': 'breakfast', 'grams': 100, 'name': 'fruit'},
        ],
    },
    'lunch': {
        'required': [
            {'role': 'cereal-base', 'eligible_meal': 'lunch', 'grams': 250, 'name': 'base'},
            {'role': 'dal-pulse',   'eligible_meal': 'lunch', 'grams': 150, 'name': 'dal'},
            {'role': 'sabzi',       'eligible_meal': 'lunch', 'grams': 100, 'name': 'sabzi'},
        ],
        'optional': [
            {'role': 'dairy', 'eligible_meal': 'lunch', 'grams': 100, 'name': 'curd'},
        ],
    },
    'dinner': {
        'required': [
            {'role': 'cereal-base', 'eligible_meal': 'dinner', 'grams': 180, 'name': 'base'},
            {'role': 'dal-pulse',   'eligible_meal': 'dinner', 'grams': 150, 'name': 'dal'},
            {'role': 'sabzi',       'eligible_meal': 'dinner', 'grams': 100, 'name': 'sabzi'},
        ],
        'optional': [],
    },
    'snack': {
        'required': [
            {'role': 'fruit|dry-snack|dairy', 'eligible_meal': 'evening_snack', 'grams': 100, 'name': 'snack'},
        ],
        'optional': [],
    },
}

# Non-vegetarian food name fragments
_NONVEG_FRAGMENTS = ('chicken', 'fish', 'mutton', 'prawn', 'shrimp', 'lamb', 'pork', 'beef', 'meat')


# ---------------------------------------------------------------------------
# TAXONOMY HELPERS
# ---------------------------------------------------------------------------

def _get_food_role(food_name: str) -> str:
    """Return the taxonomy role for a food name, defaulting to 'ingredient'."""
    lower = food_name.lower()
    for fragment, meta in FOOD_TAXONOMY.items():
        if fragment in lower:
            return meta['role']
    return 'ingredient'


def _get_food_eligible_meals(food_name: str) -> list:
    """Return eligible meal slots for a food name, defaulting to []."""
    lower = food_name.lower()
    for fragment, meta in FOOD_TAXONOMY.items():
        if fragment in lower:
            return meta['eligible_meals']
    return []


def _is_nonveg(food_name: str) -> bool:
    lower = food_name.lower()
    return any(frag in lower for frag in _NONVEG_FRAGMENTS)


# ---------------------------------------------------------------------------
# FOOD LOOKUP
# ---------------------------------------------------------------------------

def _get_food_for_slot(slot: dict, foods_by_group: dict, diet_type: str,
                       used_this_week: Counter, used_today: set):
    """
    Pick a Food object for the given slot.

    slot keys: role (may be pipe-separated), eligible_meal, grams, name
    Returns a Food ORM object or None.
    """
    roles = [r.strip() for r in slot['role'].split('|')]
    eligible_meal = slot['eligible_meal']

    # Collect all Food objects whose taxonomy role matches and eligible_meal is correct
    candidates = []
    for food_list in foods_by_group.values():
        for food in food_list:
            role = _get_food_role(food.name)
            if role not in roles:
                continue
            eligible = _get_food_eligible_meals(food.name)
            if eligible_meal not in eligible:
                continue
            candidates.append(food)

    # Diet filter
    if diet_type == 'veg':
        candidates = [f for f in candidates if not _is_nonveg(f.name)]
    elif diet_type == 'vegan':
        candidates = [f for f in candidates
                      if not _is_nonveg(f.name) and _get_food_role(f.name) != 'dairy']

    # Exclude foods already used today
    candidates = [f for f in candidates if f.id not in used_today]

    if not candidates:
        return None

    # Repetition penalty: split into preferred (≤2 uses this week) and deprioritised
    preferred = [f for f in candidates if used_this_week.get(f.id, 0) <= 2]
    pool = preferred if preferred else candidates

    return random.choice(pool)


# ---------------------------------------------------------------------------
# DAY GENERATION
# ---------------------------------------------------------------------------

def _build_item(food, grams: int) -> dict:
    """Build a meal item dict from a Food ORM object and serving grams."""
    factor = grams / 100.0
    return {
        'food_id':        food.id,
        'food_name':      food.name,
        'food_group':     food.food_group,
        'quantity_grams': grams,
        'cost_inr':       round((food.price_per_100g_inr or 0) * factor, 2),
        'nutrition': {
            'calories':  round((food.calories  or 0) * factor, 1),
            'protein':   round((food.protein   or 0) * factor, 1),
            'iron':      round((food.iron      or 0) * factor, 2),
            'calcium':   round((food.calcium   or 0) * factor, 2),
            'vitaminC':  round((food.vitaminC  or 0) * factor, 2),
            'vitaminD':  round((food.vitaminD  or 0) * factor, 2),
            'vitaminB12':round((food.vitaminB12 or 0) * factor, 2),
            'carbs':     round((food.carbs     or 0) * factor, 1),
            'fat':       round((food.fat       or 0) * factor, 1),
            'fibre':     round((food.fibre     or 0) * factor, 1),
        },
    }


def _fill_meal_slots(meal_type: str, foods_by_group: dict, diet_type: str,
                     used_this_week: Counter, used_today: set) -> list:
    """Fill required then optional slots for a meal type. Returns list of items."""
    slot_def = MEAL_SLOTS[meal_type]
    items = []

    for slot in slot_def['required']:
        food = _get_food_for_slot(slot, foods_by_group, diet_type, used_this_week, used_today)
        if food:
            items.append(_build_item(food, slot['grams']))
            used_today.add(food.id)

    for slot in slot_def['optional']:
        food = _get_food_for_slot(slot, foods_by_group, diet_type, used_this_week, used_today)
        if food:
            items.append(_build_item(food, slot['grams']))
            used_today.add(food.id)

    return items


def _generate_day(foods_by_group: dict, diet_type: str,
                  used_this_week: Counter, rda: dict) -> dict:
    """Generate one full day of meals."""
    used_today: set = set()
    day_plan = {}

    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
        day_plan[meal_type] = _fill_meal_slots(
            meal_type, foods_by_group, diet_type, used_this_week, used_today
        )

    # Compute day totals
    day_nutrition = {k: 0.0 for k in ['calories', 'protein', 'iron', 'calcium',
                                        'vitaminC', 'vitaminD', 'vitaminB12',
                                        'fibre', 'carbs', 'fat']}
    day_cost = 0.0
    for items in day_plan.values():
        for item in items:
            day_cost += item['cost_inr']
            for key in day_nutrition:
                day_nutrition[key] += item['nutrition'].get(key, 0)

    return {
        'meals': day_plan,
        'cost_inr': round(day_cost, 2),
        'nutrition': {k: round(v, 2) for k, v in day_nutrition.items()},
    }


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def _snack_calories(items: list) -> float:
    return sum(i['nutrition'].get('calories', 0) for i in items)


def _validate_meal(meal_type: str, items: list) -> list:
    """
    Returns a list of violation strings (empty list = pass).
    Checks:
      1. No ingredient-role food in any meal
      2. Breakfast has no roti/rice/dal as main
      3. Lunch/dinner has cereal-base + dal-pulse
      4. Snack calorie total < 300 kcal
      5. No two cereal-bases in same meal
      6. Dal not alone without cereal-base
    """
    violations = []

    roles_present = [_get_food_role(i['food_name']) for i in items]

    # 1. No ingredient-role food
    for item in items:
        if _get_food_role(item['food_name']) == 'ingredient':
            violations.append(
                f"{meal_type}: ingredient '{item['food_name']}' should not appear in a meal"
            )

    # 2. Breakfast: no roti/rice/dal as main
    if meal_type == 'breakfast':
        for item in items:
            name_lower = item['food_name'].lower()
            if any(bad in name_lower for bad in ('roti', 'chapati', 'rice')):
                violations.append(
                    f"breakfast: '{item['food_name']}' is not appropriate for breakfast"
                )
            if _get_food_role(item['food_name']) == 'dal-pulse':
                violations.append(
                    f"breakfast: dal/pulse '{item['food_name']}' should not be main breakfast item"
                )

    # 3. Lunch/dinner must have cereal-base + dal-pulse
    if meal_type in ('lunch', 'dinner'):
        if 'cereal-base' not in roles_present:
            violations.append(f"{meal_type}: missing cereal-base")
        if 'dal-pulse' not in roles_present:
            violations.append(f"{meal_type}: missing dal-pulse")

    # 4. Snack calorie total < 300 kcal
    if meal_type == 'snack':
        cal = _snack_calories(items)
        if cal >= 300:
            violations.append(f"snack: calorie total {cal:.0f} kcal exceeds 300 kcal limit")

    # 5. No two cereal-bases in same meal
    cereal_count = roles_present.count('cereal-base')
    if cereal_count > 1:
        violations.append(f"{meal_type}: {cereal_count} cereal-base items in same meal")

    # 6. Dal not alone without cereal-base
    if 'dal-pulse' in roles_present and 'cereal-base' not in roles_present:
        if meal_type in ('lunch', 'dinner'):
            violations.append(f"{meal_type}: dal without cereal-base")

    return violations


def _validate_and_fix(day_plan: dict, foods_by_group: dict, diet_type: str,
                      used_this_week: Counter, rda: dict) -> tuple:
    """
    Validate each meal in day_plan and attempt to regenerate violating meals.
    Returns (fixed_plan, quality_report).
    """
    fixed_plan = dict(day_plan)
    all_violations = []
    regenerated = 0
    passed = 0

    for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
        items = fixed_plan['meals'][meal_type]
        violations = _validate_meal(meal_type, items)

        if not violations:
            passed += 1
            continue

        # Attempt up to 3 regenerations
        fixed = False
        for _ in range(3):
            used_today_regen: set = set()
            new_items = _fill_meal_slots(
                meal_type, foods_by_group, diet_type, used_this_week, used_today_regen
            )
            new_violations = _validate_meal(meal_type, new_items)
            if not new_violations:
                fixed_plan['meals'][meal_type] = new_items
                regenerated += 1
                passed += 1
                fixed = True
                break

        if not fixed:
            all_violations.extend(violations)

    quality_report = {
        'total_meals': 4,
        'passed': passed,
        'regenerated': regenerated,
        'violations': all_violations,
    }
    return fixed_plan, quality_report


# ---------------------------------------------------------------------------
# WEEKLY PLAN
# ---------------------------------------------------------------------------

def _generate_week(foods_by_group: dict, diet_type: str, rda: dict) -> tuple:
    """
    Generate a 7-day meal plan with validation and weekly variety enforcement.
    Returns (plan_dict, weekly_quality_report).
    """
    used_this_week: Counter = Counter()
    plan = {}
    weekly_violations = []
    total_passed = 0
    total_regenerated = 0

    # Track per-day sabzi to prevent consecutive repeats
    prev_day_sabzis: set = set()
    # Track breakfast dish counts and dal counts for weekly caps
    breakfast_counts: Counter = Counter()
    dal_counts: Counter = Counter()

    for day_idx in range(7):
        day_key = f'day_{day_idx + 1}'

        # Generate raw day
        raw_day = _generate_day(foods_by_group, diet_type, used_this_week, rda)

        # Enforce weekly variety rules before validation
        # Rule: same breakfast dish max 2x per week
        bf_items = raw_day['meals'].get('breakfast', [])
        for item in bf_items:
            if _get_food_role(item['food_name']) == 'cereal-base':
                if breakfast_counts[item['food_name']] >= 2:
                    # Regenerate breakfast
                    used_today_tmp: set = set()
                    new_bf = _fill_meal_slots(
                        'breakfast', foods_by_group, diet_type, used_this_week, used_today_tmp
                    )
                    raw_day['meals']['breakfast'] = new_bf
                    bf_items = new_bf
                    break

        # Rule: same dal max 3x per week
        for meal_type in ('lunch', 'dinner'):
            for item in raw_day['meals'].get(meal_type, []):
                if _get_food_role(item['food_name']) == 'dal-pulse':
                    if dal_counts[item['food_name']] >= 3:
                        used_today_tmp2: set = set()
                        new_meal = _fill_meal_slots(
                            meal_type, foods_by_group, diet_type, used_this_week, used_today_tmp2
                        )
                        raw_day['meals'][meal_type] = new_meal
                        break

        # Rule: same sabzi not on consecutive days
        today_sabzis: set = set()
        for meal_type in ('lunch', 'dinner'):
            for item in raw_day['meals'].get(meal_type, []):
                if _get_food_role(item['food_name']) == 'sabzi':
                    today_sabzis.add(item['food_name'])

        repeated_sabzis = today_sabzis & prev_day_sabzis
        if repeated_sabzis:
            for meal_type in ('lunch', 'dinner'):
                for item in list(raw_day['meals'].get(meal_type, [])):
                    if item['food_name'] in repeated_sabzis:
                        used_today_tmp3: set = set()
                        new_meal = _fill_meal_slots(
                            meal_type, foods_by_group, diet_type, used_this_week, used_today_tmp3
                        )
                        raw_day['meals'][meal_type] = new_meal
                        break

        # Validate and fix
        fixed_day, day_report = _validate_and_fix(
            raw_day, foods_by_group, diet_type, used_this_week, rda
        )

        total_passed += day_report['passed']
        total_regenerated += day_report['regenerated']
        weekly_violations.extend(
            [f"Day {day_idx + 1} {v}" for v in day_report['violations']]
        )

        # Update counters
        for meal_type, items in fixed_day['meals'].items():
            for item in items:
                used_this_week[item['food_id']] += 1
                role = _get_food_role(item['food_name'])
                if role == 'cereal-base' and meal_type == 'breakfast':
                    breakfast_counts[item['food_name']] += 1
                if role == 'dal-pulse':
                    dal_counts[item['food_name']] += 1

        # Refresh sabzi tracking
        prev_day_sabzis = set()
        for meal_type in ('lunch', 'dinner'):
            for item in fixed_day['meals'].get(meal_type, []):
                if _get_food_role(item['food_name']) == 'sabzi':
                    prev_day_sabzis.add(item['food_name'])

        plan[day_key] = fixed_day

    weekly_quality_report = {
        'total_meals': 28,
        'passed': total_passed,
        'regenerated': total_regenerated,
        'violations': weekly_violations,
    }
    return plan, weekly_quality_report


# ---------------------------------------------------------------------------
# UNCHANGED HELPERS
# ---------------------------------------------------------------------------

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


def _compute_coverage(plan_nutrition: dict, rda: dict) -> dict:
    nutrient_map = {
        'calories': 'calories', 'protein': 'protein', 'iron': 'iron',
        'calcium': 'calcium', 'vitaminC': 'vitaminC', 'vitaminD': 'vitaminD',
        'vitaminB12': 'vitaminB12', 'fibre': 'fibre',
    }
    coverage = {}
    for key, rda_key in nutrient_map.items():
        rda_val = rda.get(rda_key, 1)
        intake = plan_nutrition.get(key, 0)
        coverage[key] = round(min((intake / rda_val) * 100, 200), 1) if rda_val else 0
    return coverage


def _build_foods_by_group(foods_pool: list) -> dict:
    """Index foods by food_group for fast lookup."""
    index = {}
    for food in foods_pool:
        group = (food.food_group or 'other').lower()
        index.setdefault(group, []).append(food)
    return index


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@meal_plan_bp.route('/generate', methods=['POST'])
@token_required
def generate_meal_plan(current_user):
    data = request.get_json() or {}
    week_start   = date.fromisoformat(data.get('week_start', date.today().isoformat()))
    diet_type    = current_user.diet_type or 'veg'
    daily_budget = (current_user.budget_monthly_inr or 3000.0) / 30.0
    rda          = _get_rda(current_user)

    foods_pool = Food.query.all()
    if not foods_pool:
        return jsonify({'error': 'No foods in database'}), 500

    foods_by_group = _build_foods_by_group(foods_pool)

    plan, quality_report = _generate_week(foods_by_group, diet_type, rda)

    # Build date-keyed plan and aggregate nutrition
    dated_plan = {}
    total_cost = 0.0
    avg_nutrition = {k: 0.0 for k in ['calories', 'protein', 'iron', 'calcium',
                                        'vitaminC', 'vitaminD', 'vitaminB12', 'fibre']}

    for day_idx, (day_key, day_data) in enumerate(plan.items()):
        day_date = week_start + timedelta(days=day_idx)
        dated_plan[day_date.isoformat()] = day_data
        total_cost += day_data.get('cost_inr', 0)
        for key in avg_nutrition:
            avg_nutrition[key] += day_data.get('nutrition', {}).get(key, 0)

    for key in avg_nutrition:
        avg_nutrition[key] = round(avg_nutrition[key] / 7, 2)

    coverage = _compute_coverage(avg_nutrition, rda)

    mp = MealPlan(
        user_id=current_user.id,
        week_start_date=week_start,
        plan_json=json.dumps(dated_plan),
        total_cost=round(total_cost, 2),
        nutritional_coverage_json=json.dumps(coverage),
    )
    db.session.add(mp)
    db.session.commit()

    return jsonify({
        'id':                          mp.id,
        'week_start':                  week_start.isoformat(),
        'plan':                        dated_plan,
        'total_cost_inr':              round(total_cost, 2),
        'daily_budget_inr':            round(daily_budget, 2),
        'avg_daily_nutrition':         avg_nutrition,
        'nutritional_coverage_percent': coverage,
        'quality_report':              quality_report,
    })


@meal_plan_bp.route('/latest', methods=['GET'])
@token_required
def get_latest_plan(current_user):
    mp = MealPlan.query.filter_by(user_id=current_user.id) \
                       .order_by(MealPlan.created_at.desc()).first()
    if not mp:
        return jsonify(None)
    return jsonify(mp.to_dict())
