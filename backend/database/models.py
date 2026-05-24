"""
NutriSense Database Models
SQLAlchemy ORM models for all database tables.
Implements the DATA LAYER of the Data vs Logic separation architecture.
All raw nutritional data lives here; Prolog handles only rules/logic.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    """
    User profile table.
    Stores demographic info used by ICMR RDA lookup and Bayesian Network.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # male/female/other
    weight_kg = db.Column(db.Float, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    budget_monthly_inr = db.Column(db.Float, nullable=True, default=3000.0)
    diet_type = db.Column(db.String(20), nullable=True, default='veg')  # veg/nonveg/eggetarian/vegan
    allergies = db.Column(db.Text, nullable=True, default='[]')  # JSON array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy=True)
    meal_plans = db.relationship('MealPlan', backref='user', lazy=True)

    def get_allergies(self):
        """Return allergies as Python list."""
        try:
            return json.loads(self.allergies or '[]')
        except Exception:
            return []

    def get_bmi(self):
        """Calculate BMI from weight and height."""
        if self.weight_kg and self.height_cm and self.height_cm > 0:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'weight_kg': self.weight_kg,
            'height_cm': self.height_cm,
            'bmi': self.get_bmi(),
            'budget_monthly_inr': self.budget_monthly_inr,
            'diet_type': self.diet_type,
            'allergies': self.get_allergies(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Food(db.Model):
    """
    Foods table — loaded from IFCT 2017 (Indian Food Composition Tables).
    This is the DATA LAYER. Prolog will query this via Python and assert facts dynamically.
    All nutritional values are per 100g of food.
    Source: National Institute of Nutrition, India (NIN) — IFCT 2017.
    """
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_hindi = db.Column(db.String(100), nullable=True)
    food_group = db.Column(db.String(50), nullable=True)   # cereals, pulses, vegetables, etc.
    region = db.Column(db.String(50), nullable=True)        # north/south/east/west/pan-india
    diet_type = db.Column(db.String(20), nullable=True)     # veg/nonveg/eggetarian/vegan

    # Nutritional values per 100g (IFCT 2017)
    calories = db.Column(db.Float, nullable=True, default=0)
    protein = db.Column(db.Float, nullable=True, default=0)       # grams
    iron = db.Column(db.Float, nullable=True, default=0)          # mg
    calcium = db.Column(db.Float, nullable=True, default=0)       # mg
    vitaminC = db.Column(db.Float, nullable=True, default=0)      # mg
    vitaminD = db.Column(db.Float, nullable=True, default=0)      # mcg
    vitaminB12 = db.Column(db.Float, nullable=True, default=0)    # mcg
    carbs = db.Column(db.Float, nullable=True, default=0)         # grams
    fat = db.Column(db.Float, nullable=True, default=0)           # grams
    fibre = db.Column(db.Float, nullable=True, default=0)         # grams
    sugar = db.Column(db.Float, nullable=True, default=0)         # grams
    sodium = db.Column(db.Float, nullable=True, default=0)        # mg (for salt/BP risk)

    price_per_100g_inr = db.Column(db.Float, nullable=True, default=5.0)  # 2024 Indian market price
    source = db.Column(db.String(50), nullable=True, default='IFCT2017')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_hindi': self.name_hindi,
            'food_group': self.food_group,
            'region': self.region,
            'diet_type': self.diet_type,
            'calories': self.calories,
            'protein': self.protein,
            'iron': self.iron,
            'calcium': self.calcium,
            'vitaminC': self.vitaminC,
            'vitaminD': self.vitaminD,
            'vitaminB12': self.vitaminB12,
            'carbs': self.carbs,
            'fat': self.fat,
            'fibre': self.fibre,
            'sugar': self.sugar,
            'sodium': self.sodium,
            'price_per_100g_inr': self.price_per_100g_inr,
            'source': self.source
        }


class RDAValue(db.Model):
    """
    ICMR Recommended Daily Allowance values.
    Source: ICMR-NIN 2020 Dietary Guidelines for Indians.
    Different values for different demographic groups.
    Used by Forward Chaining and Prolog deficiency detection rules.
    """
    __tablename__ = 'rda_values'

    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(20), nullable=False)   # male/female/pregnant/lactating/child/elderly
    age_min = db.Column(db.Integer, nullable=False)
    age_max = db.Column(db.Integer, nullable=False)

    # ICMR RDA values per day
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)        # grams
    iron = db.Column(db.Float, nullable=True)           # mg
    calcium = db.Column(db.Float, nullable=True)        # mg
    vitaminC = db.Column(db.Float, nullable=True)       # mg
    vitaminD = db.Column(db.Float, nullable=True)       # mcg
    vitaminB12 = db.Column(db.Float, nullable=True)     # mcg
    fibre = db.Column(db.Float, nullable=True)          # grams
    carbs = db.Column(db.Float, nullable=True)          # grams
    fat = db.Column(db.Float, nullable=True)            # grams

    def to_dict(self):
        return {
            'id': self.id,
            'gender': self.gender,
            'age_min': self.age_min,
            'age_max': self.age_max,
            'calories': self.calories,
            'protein': self.protein,
            'iron': self.iron,
            'calcium': self.calcium,
            'vitaminC': self.vitaminC,
            'vitaminD': self.vitaminD,
            'vitaminB12': self.vitaminB12,
            'fibre': self.fibre,
            'carbs': self.carbs,
            'fat': self.fat
        }


class FoodLog(db.Model):
    """
    Daily food log entries. Each row = one food item logged at one meal.
    Used to compute daily nutrition totals for deficiency detection.
    """
    __tablename__ = 'food_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast/lunch/dinner/snack
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    quantity_grams = db.Column(db.Float, nullable=False, default=100.0)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

    food = db.relationship('Food', backref='logs')

    def get_nutrition(self):
        """Calculate actual nutrition based on quantity logged."""
        if not self.food:
            return {}
        factor = self.quantity_grams / 100.0
        return {
            'calories': round((self.food.calories or 0) * factor, 2),
            'protein': round((self.food.protein or 0) * factor, 2),
            'iron': round((self.food.iron or 0) * factor, 2),
            'calcium': round((self.food.calcium or 0) * factor, 2),
            'vitaminC': round((self.food.vitaminC or 0) * factor, 2),
            'vitaminD': round((self.food.vitaminD or 0) * factor, 2),
            'vitaminB12': round((self.food.vitaminB12 or 0) * factor, 2),
            'carbs': round((self.food.carbs or 0) * factor, 2),
            'fat': round((self.food.fat or 0) * factor, 2),
            'fibre': round((self.food.fibre or 0) * factor, 2),
            'sugar': round((self.food.sugar or 0) * factor, 2),
            'sodium': round((self.food.sodium or 0) * factor, 2),
        }

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'meal_type': self.meal_type,
            'food_id': self.food_id,
            'food_name': self.food.name if self.food else None,
            'food_source': self.food.source if self.food else None,
            'quantity_grams': self.quantity_grams,
            'nutrition': self.get_nutrition(),
            'logged_at': self.logged_at.isoformat() if self.logged_at else None
        }


class NutritionDaily(db.Model):
    """
    Aggregated daily nutrition totals per user.
    Computed from food_logs and cached here for fast retrieval.
    Used as input to Forward Chaining and Bayesian Network.
    """
    __tablename__ = 'nutrition_daily'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    total_calories = db.Column(db.Float, default=0)
    total_protein = db.Column(db.Float, default=0)
    total_iron = db.Column(db.Float, default=0)
    total_calcium = db.Column(db.Float, default=0)
    total_vitC = db.Column(db.Float, default=0)
    total_vitD = db.Column(db.Float, default=0)
    total_vitB12 = db.Column(db.Float, default=0)
    total_fibre = db.Column(db.Float, default=0)
    total_carbs = db.Column(db.Float, default=0)
    total_fat = db.Column(db.Float, default=0)
    total_sugar = db.Column(db.Float, default=0)
    total_salt = db.Column(db.Float, default=0)   # sodium in mg

    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'calories': self.total_calories,
            'protein': self.total_protein,
            'iron': self.total_iron,
            'calcium': self.total_calcium,
            'vitaminC': self.total_vitC,
            'vitaminD': self.total_vitD,
            'vitaminB12': self.total_vitB12,
            'fibre': self.total_fibre,
            'carbs': self.total_carbs,
            'fat': self.total_fat,
            'sugar': self.total_sugar,
            'salt': self.total_salt
        }


class DeficiencyReport(db.Model):
    """
    Stores deficiency analysis results including FC reasoning chain and BC proof tree.
    The reasoning_chain and proof_tree are stored as JSON for frontend display.
    """
    __tablename__ = 'deficiency_reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    deficiency_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # critical/moderate/mild
    fc_reasoning_chain = db.Column(db.Text, nullable=True)   # JSON
    bc_proof_tree = db.Column(db.Text, nullable=True)        # JSON

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'deficiency_type': self.deficiency_type,
            'severity': self.severity,
            'fc_reasoning_chain': json.loads(self.fc_reasoning_chain or '[]'),
            'bc_proof_tree': json.loads(self.bc_proof_tree or '{}')
        }


class DiseaseRisk(db.Model):
    """
    Stores Bayesian Network disease risk predictions.
    bayesian_evidence stores the evidence variables used for inference.
    """
    __tablename__ = 'disease_risks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    diabetes_prob = db.Column(db.Float, default=0)
    bp_prob = db.Column(db.Float, default=0)
    anaemia_prob = db.Column(db.Float, default=0)
    osteoporosis_prob = db.Column(db.Float, default=0)
    vitD_prob = db.Column(db.Float, default=0)
    bayesian_evidence = db.Column(db.Text, nullable=True)  # JSON

    def to_dict(self):
        return {
            'date': self.date.isoformat() if self.date else None,
            'diabetes_prob': self.diabetes_prob,
            'bp_prob': self.bp_prob,
            'anaemia_prob': self.anaemia_prob,
            'osteoporosis_prob': self.osteoporosis_prob,
            'vitD_prob': self.vitD_prob,
            'bayesian_evidence': json.loads(self.bayesian_evidence or '{}')
        }


class MealPlan(db.Model):
    """
    Stores generated 7-day meal plans.
    plan_json contains the full structured meal plan.
    nutritional_coverage_json stores % coverage per nutrient.
    """
    __tablename__ = 'meal_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week_start_date = db.Column(db.Date, nullable=False)
    plan_json = db.Column(db.Text, nullable=True)
    total_cost = db.Column(db.Float, default=0)
    nutritional_coverage_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'week_start_date': self.week_start_date.isoformat() if self.week_start_date else None,
            'plan': json.loads(self.plan_json or '{}'),
            'total_cost': self.total_cost,
            'nutritional_coverage': json.loads(self.nutritional_coverage_json or '{}'),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
