"""
NutriSense Seed Data Script
Populates the SQLite database with:
1. IFCT 2017 food data from ifct_foods.csv
2. ICMR RDA values for different demographic groups
3. A demo user with 7 days of realistic Indian food log data

Run this script once before starting the Flask app:
    python database/seed_data.py
"""

import sys
import os
import csv
import json
from datetime import date, timedelta, datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash


def seed_database(app, db):
    """
    Main seeding function. Called from app.py on first run.
    Seeds foods, RDA values, and demo user data.
    """
    with app.app_context():
        from database.models import User, Food, RDAValue, FoodLog, NutritionDaily

        # Only seed if tables are empty
        if Food.query.count() > 0:
            print("[Seed] Database already seeded. Skipping.")
            return

        print("[Seed] Starting database seeding...")

        _seed_foods(db, Food)
        _seed_rda_values(db, RDAValue)
        _seed_demo_user(db, User, Food, FoodLog, NutritionDaily)

        print("[Seed] Database seeding complete!")


def _seed_foods(db, Food):
    """
    Load IFCT 2017 food data from ifct_foods.csv into the foods table.
    IFCT = Indian Food Composition Tables, published by NIN (National Institute of Nutrition), India.
    """
    csv_path = os.path.join(os.path.dirname(__file__), 'ifct_foods.csv')

    if not os.path.exists(csv_path):
        print(f"[Seed] ERROR: {csv_path} not found!")
        return

    count = 0
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            food = Food(
                name=row['name'].strip(),
                name_hindi=row.get('name_hindi', '').strip(),
                food_group=row.get('food_group', '').strip(),
                region=row.get('region', 'pan-india').strip(),
                diet_type=row.get('diet_type', 'veg').strip(),
                calories=float(row.get('calories', 0) or 0),
                protein=float(row.get('protein', 0) or 0),
                iron=float(row.get('iron', 0) or 0),
                calcium=float(row.get('calcium', 0) or 0),
                vitaminC=float(row.get('vitaminC', 0) or 0),
                vitaminD=float(row.get('vitaminD', 0) or 0),
                vitaminB12=float(row.get('vitaminB12', 0) or 0),
                carbs=float(row.get('carbs', 0) or 0),
                fat=float(row.get('fat', 0) or 0),
                fibre=float(row.get('fibre', 0) or 0),
                sugar=float(row.get('sugar', 0) or 0),
                sodium=float(row.get('sodium', 0) or 0),
                price_per_100g_inr=float(row.get('price_per_100g_inr', 5) or 5),
                source=row.get('source', 'IFCT2017').strip()
            )
            db.session.add(food)
            count += 1

    db.session.commit()
    print(f"[Seed] Loaded {count} foods from IFCT 2017 dataset.")


def _seed_rda_values(db, RDAValue):
    """
    Seed ICMR Recommended Daily Allowance values.
    Source: ICMR-NIN 2020 'Dietary Guidelines for Indians' and
    ICMR 2010 'Nutrient Requirements and Recommended Dietary Allowances for Indians'.
    Values are specific to Indian body types and lifestyle.
    """
    rda_data = [
        # Adult males (18-59 years) — sedentary/moderate activity
        {'gender': 'male', 'age_min': 18, 'age_max': 59,
         'calories': 2320, 'protein': 60, 'iron': 17, 'calcium': 600,
         'vitaminC': 40, 'vitaminD': 10, 'vitaminB12': 1.0, 'fibre': 40,
         'carbs': 390, 'fat': 30},

        # Adult females (18-59 years)
        {'gender': 'female', 'age_min': 18, 'age_max': 59,
         'calories': 1900, 'protein': 55, 'iron': 21, 'calcium': 600,
         'vitaminC': 40, 'vitaminD': 10, 'vitaminB12': 1.0, 'fibre': 35,
         'carbs': 310, 'fat': 25},

        # Pregnant women
        {'gender': 'pregnant', 'age_min': 18, 'age_max': 45,
         'calories': 2200, 'protein': 78, 'iron': 35, 'calcium': 1200,
         'vitaminC': 60, 'vitaminD': 10, 'vitaminB12': 1.2, 'fibre': 40,
         'carbs': 350, 'fat': 30},

        # Lactating women
        {'gender': 'lactating', 'age_min': 18, 'age_max': 45,
         'calories': 2425, 'protein': 74, 'iron': 21, 'calcium': 1200,
         'vitaminC': 80, 'vitaminD': 10, 'vitaminB12': 1.5, 'fibre': 45,
         'carbs': 390, 'fat': 35},

        # Children (5-12 years)
        {'gender': 'child', 'age_min': 5, 'age_max': 12,
         'calories': 1690, 'protein': 40, 'iron': 26, 'calcium': 600,
         'vitaminC': 40, 'vitaminD': 10, 'vitaminB12': 0.9, 'fibre': 25,
         'carbs': 280, 'fat': 25},

        # Adolescent males (13-17 years)
        {'gender': 'male', 'age_min': 13, 'age_max': 17,
         'calories': 2450, 'protein': 70, 'iron': 32, 'calcium': 800,
         'vitaminC': 40, 'vitaminD': 10, 'vitaminB12': 1.0, 'fibre': 38,
         'carbs': 400, 'fat': 35},

        # Adolescent females (13-17 years)
        {'gender': 'female', 'age_min': 13, 'age_max': 17,
         'calories': 2060, 'protein': 65, 'iron': 27, 'calcium': 800,
         'vitaminC': 40, 'vitaminD': 10, 'vitaminB12': 1.0, 'fibre': 35,
         'carbs': 335, 'fat': 30},

        # Elderly males (60+ years)
        {'gender': 'male', 'age_min': 60, 'age_max': 100,
         'calories': 1900, 'protein': 60, 'iron': 17, 'calcium': 800,
         'vitaminC': 40, 'vitaminD': 15, 'vitaminB12': 1.5, 'fibre': 30,
         'carbs': 310, 'fat': 25},

        # Elderly females (60+ years)
        {'gender': 'female', 'age_min': 60, 'age_max': 100,
         'calories': 1600, 'protein': 55, 'iron': 17, 'calcium': 800,
         'vitaminC': 40, 'vitaminD': 15, 'vitaminB12': 1.5, 'fibre': 25,
         'carbs': 260, 'fat': 20},
    ]

    for rda in rda_data:
        r = RDAValue(**rda)
        db.session.add(r)

    db.session.commit()
    print(f"[Seed] Loaded {len(rda_data)} ICMR RDA value sets.")


def _seed_demo_user(db, User, Food, FoodLog, NutritionDaily):
    """
    Create a demo user with 7 days of realistic Indian food log data.
    The diet is intentionally heavy in carbs and low in protein/iron
    to demonstrate deficiency detection and disease risk features.
    Demo credentials: demo@nutrisense.in / demo123
    """
    # Check if demo user already exists
    if User.query.filter_by(email='demo@nutrisense.in').first():
        print("[Seed] Demo user already exists.")
        return

    demo_user = User(
        email='demo@nutrisense.in',
        password_hash=generate_password_hash('demo123'),
        name='Priya Sharma',
        age=28,
        gender='female',
        weight_kg=58.0,
        height_cm=162.0,
        budget_monthly_inr=3500.0,
        diet_type='veg',
        allergies=json.dumps([]),
        created_at=datetime.utcnow()
    )
    db.session.add(demo_user)
    db.session.flush()  # Get the user ID

    # Get food IDs for common Indian foods
    food_map = {}
    for food in Food.query.all():
        food_map[food.name] = food

    # 7-day typical Indian vegetarian diet (carb-heavy, low protein/iron)
    # This will trigger deficiency alerts for demo purposes
    weekly_meals = [
        # Day 1 - Monday
        {
            'breakfast': [('Poha (cooked)', 200), ('Milk (cow full fat)', 200)],
            'lunch': [('Rice (cooked)', 300), ('Dal tadka', 150), ('Tomato', 50)],
            'dinner': [('Roti (wheat)', 120), ('Dal tadka', 100), ('Bottle gourd', 100)],
            'snack': [('Banana', 100), ('Tea', 0)]
        },
        # Day 2 - Tuesday
        {
            'breakfast': [('Idli', 200), ('Sambar', 100)],
            'lunch': [('Rice (cooked)', 300), ('Toor dal (pigeon pea)', 100), ('Carrot', 50)],
            'dinner': [('Roti (wheat)', 120), ('Potato', 150), ('Onion', 30)],
            'snack': [('Apple', 150)]
        },
        # Day 3 - Wednesday
        {
            'breakfast': [('Aloo paratha', 150), ('Curd (yogurt)', 100)],
            'lunch': [('Rice (cooked)', 300), ('Rajma (kidney beans)', 100), ('Tomato', 50)],
            'dinner': [('Roti (wheat)', 120), ('Brinjal (eggplant)', 100), ('Onion', 30)],
            'snack': [('Banana', 100), ('Groundnuts (peanuts)', 30)]
        },
        # Day 4 - Thursday
        {
            'breakfast': [('Upma (semolina)', 200), ('Milk (cow full fat)', 150)],
            'lunch': [('Rice (cooked)', 300), ('Moong dal (green gram)', 100), ('Bottle gourd', 100)],
            'dinner': [('Roti (wheat)', 120), ('Potato', 100), ('Peas (green)', 50)],
            'snack': [('Orange', 150)]
        },
        # Day 5 - Friday
        {
            'breakfast': [('Dosa', 150), ('Sambar', 100), ('Curd (yogurt)', 50)],
            'lunch': [('Rice (cooked)', 300), ('Toor dal (pigeon pea)', 100), ('Tomato', 50)],
            'dinner': [('Roti (wheat)', 120), ('Cauliflower', 100), ('Onion', 30)],
            'snack': [('Banana', 100)]
        },
        # Day 6 - Saturday
        {
            'breakfast': [('Poha (cooked)', 200), ('Milk (cow full fat)', 200)],
            'lunch': [('Chole bhature', 250), ('Onion', 50)],
            'dinner': [('Roti (wheat)', 120), ('Dal tadka', 100), ('Carrot', 50)],
            'snack': [('Groundnuts (peanuts)', 50), ('Jaggery', 20)]
        },
        # Day 7 - Sunday
        {
            'breakfast': [('Idli', 200), ('Sambar', 150), ('Curd (yogurt)', 100)],
            'lunch': [('Rice (cooked)', 300), ('Rajma (kidney beans)', 150), ('Tomato', 50)],
            'dinner': [('Roti (wheat)', 120), ('Palak paneer', 100)],
            'snack': [('Apple', 150), ('Milk (cow full fat)', 150)]
        }
    ]

    today = date.today()
    meal_type_map = {'breakfast': 'breakfast', 'lunch': 'lunch', 'dinner': 'dinner', 'snack': 'snack'}

    for day_offset, day_meals in enumerate(weekly_meals):
        log_date = today - timedelta(days=6 - day_offset)
        daily_nutrition = {k: 0 for k in ['calories', 'protein', 'iron', 'calcium',
                                            'vitC', 'vitD', 'vitB12', 'fibre',
                                            'carbs', 'fat', 'sugar', 'salt']}

        for meal_type, items in day_meals.items():
            for food_name, quantity in items:
                food = food_map.get(food_name)
                if not food or quantity == 0:
                    continue

                log = FoodLog(
                    user_id=demo_user.id,
                    date=log_date,
                    meal_type=meal_type_map[meal_type],
                    food_id=food.id,
                    quantity_grams=float(quantity),
                    logged_at=datetime.utcnow()
                )
                db.session.add(log)

                # Accumulate daily nutrition
                factor = quantity / 100.0
                daily_nutrition['calories'] += (food.calories or 0) * factor
                daily_nutrition['protein'] += (food.protein or 0) * factor
                daily_nutrition['iron'] += (food.iron or 0) * factor
                daily_nutrition['calcium'] += (food.calcium or 0) * factor
                daily_nutrition['vitC'] += (food.vitaminC or 0) * factor
                daily_nutrition['vitD'] += (food.vitaminD or 0) * factor
                daily_nutrition['vitB12'] += (food.vitaminB12 or 0) * factor
                daily_nutrition['fibre'] += (food.fibre or 0) * factor
                daily_nutrition['carbs'] += (food.carbs or 0) * factor
                daily_nutrition['fat'] += (food.fat or 0) * factor
                daily_nutrition['sugar'] += (food.sugar or 0) * factor
                daily_nutrition['salt'] += (food.sodium or 0) * factor

        # Save daily nutrition summary
        nd = NutritionDaily(
            user_id=demo_user.id,
            date=log_date,
            total_calories=round(daily_nutrition['calories'], 2),
            total_protein=round(daily_nutrition['protein'], 2),
            total_iron=round(daily_nutrition['iron'], 2),
            total_calcium=round(daily_nutrition['calcium'], 2),
            total_vitC=round(daily_nutrition['vitC'], 2),
            total_vitD=round(daily_nutrition['vitD'], 2),
            total_vitB12=round(daily_nutrition['vitB12'], 2),
            total_fibre=round(daily_nutrition['fibre'], 2),
            total_carbs=round(daily_nutrition['carbs'], 2),
            total_fat=round(daily_nutrition['fat'], 2),
            total_sugar=round(daily_nutrition['sugar'], 2),
            total_salt=round(daily_nutrition['salt'], 2)
        )
        db.session.add(nd)

    db.session.commit()
    print(f"[Seed] Demo user created: demo@nutrisense.in / demo123")
    print(f"[Seed] 7 days of food log data added for demo user.")
