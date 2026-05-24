"""
Analysis routes — forward chaining, backward chaining,
Bayesian network, resolution engine, Prolog queries.
"""

from datetime import date
from flask import Blueprint, request, jsonify
from database.models import db, Food, FoodLog, NutritionDaily, RDAValue, DeficiencyReport, DiseaseRisk
from routes.auth import token_required
from modules.forward_chaining import ForwardChainer, build_nutrition_rules
from modules.backward_chaining import BackwardChainer, build_bc_knowledge_base
from modules.bayesian_network import BayesianRiskPredictor
from modules.resolution_engine import ResolutionEngine, AVAILABLE_CLAIMS
from modules.prolog_interface import PrologInterface
from modules.meal_context import enrich_recommendations_with_context
import json

analysis_bp = Blueprint('analysis', __name__)

# Singletons — initialized once
_bayesian = BayesianRiskPredictor()
_prolog = PrologInterface()
_prolog_seeded = False


def _get_rda(user) -> dict:
    """Fetch ICMR RDA for a user based on age and gender."""
    gender = user.gender or 'male'
    age = user.age or 30
    rda = RDAValue.query.filter(
        RDAValue.gender == gender,
        RDAValue.age_min <= age,
        RDAValue.age_max >= age
    ).first()
    if not rda:
        rda = RDAValue.query.filter_by(gender='male').first()
    return rda.to_dict() if rda else {
        'protein': 60, 'iron': 17, 'calcium': 600, 'vitaminD': 10,
        'vitaminB12': 1.0, 'vitaminC': 40, 'fibre': 40, 'carbs': 390,
        'fat': 30, 'calories': 2320
    }


def _get_daily_nutrition(user_id: int, target_date: date) -> dict:
    """Get daily nutrition totals for a user on a given date."""
    nd = NutritionDaily.query.filter_by(user_id=user_id, date=target_date).first()
    if not nd:
        return {}
    return {
        'calories': nd.total_calories, 'protein': nd.total_protein,
        'iron': nd.total_iron, 'calcium': nd.total_calcium,
        'vitaminC': nd.total_vitC, 'vitaminD': nd.total_vitD,
        'vitaminB12': nd.total_vitB12, 'fibre': nd.total_fibre,
        'carbs': nd.total_carbs, 'fat': nd.total_fat,
        'sugar': nd.total_sugar, 'salt': nd.total_salt,
    }


def _seed_prolog_if_needed():
    """Seed Prolog with food facts once per app lifetime."""
    global _prolog_seeded
    if not _prolog_seeded:
        foods = Food.query.all()
        _prolog.assert_food_facts(foods)
        _prolog_seeded = True


def _get_confidence_discount(user_id: int, target_date: date) -> tuple:
    """
    Check if any food logged today has AI-estimated nutritional values.
    Returns (discount_factor, has_ai_foods, has_user_confirmed).
    - IFCT2017 source → 0% discount
    - Groq-LLaMA3-estimated → 15% discount
    - user-confirmed → 5% discount
    """
    logs = FoodLog.query.filter_by(user_id=user_id, date=target_date).all()
    has_ai = False
    has_confirmed = False
    for log in logs:
        if log.food and log.food.source:
            src = log.food.source
            if 'Groq' in src or 'estimated' in src.lower():
                if 'user-confirmed' in src.lower():
                    has_confirmed = True
                else:
                    has_ai = True
    if has_ai:
        return 0.15, True, has_confirmed
    if has_confirmed:
        return 0.05, False, True
    return 0.0, False, False


def _enrich_deficiencies_with_context(deficiencies: list, meal_type: str = 'lunch') -> list:
    """Add meal-context-aware prepared food recommendations to each deficiency."""
    for d in deficiencies:
        raw_foods = d.get('recommended_foods', [])
        d['recommended_foods_context'] = enrich_recommendations_with_context(raw_foods, meal_type)
    return deficiencies


# ── FORWARD CHAINING ───────────────────────────────────────────────────────────

@analysis_bp.route('/forward-chain', methods=['GET'])
@token_required
def forward_chain(current_user):
    """Run forward chaining deficiency detection for the current user."""
    target_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    meal_type   = request.args.get('meal_type', 'lunch')
    nutrition   = _get_daily_nutrition(current_user.id, target_date)
    rda         = _get_rda(current_user)

    if not nutrition:
        return jsonify({'error': 'No food log data for this date'}), 404

    # Compute confidence discount based on data sources in today's log
    discount, has_ai_foods, has_user_confirmed = _get_confidence_discount(current_user.id, target_date)

    facts = {
        'iron_intake':    nutrition.get('iron', 0),
        'protein_intake': nutrition.get('protein', 0),
        'calcium_intake': nutrition.get('calcium', 0),
        'vitD_intake':    nutrition.get('vitaminD', 0),
        'vitB12_intake':  nutrition.get('vitaminB12', 0),
        'vitC_intake':    nutrition.get('vitaminC', 0),
        'fibre_intake':   nutrition.get('fibre', 0),
        'sugar_intake':   nutrition.get('sugar', 0),
        'fat_intake':     nutrition.get('fat', 0),
        'salt_intake':    nutrition.get('salt', 0),
        'gender':         current_user.gender or 'female',
        'age':            current_user.age or 30,
        'diet_type':      current_user.diet_type or 'veg',
    }

    rules = build_nutrition_rules(rda, confidence_discount=discount)
    fc = ForwardChainer(facts, rules)
    result = fc.run()

    # Enrich deficiencies with meal-context recommendations
    deficiencies = _enrich_deficiencies_with_context(result.get('deficiencies', []), meal_type)

    # Add confidence metadata to each deficiency
    for d in deficiencies:
        d['data_confidence'] = {
            'has_ai_estimated_foods': has_ai_foods,
            'has_user_confirmed_foods': has_user_confirmed,
            'discount_applied': discount,
            'accuracy_note': (
                'This result includes foods with AI-estimated values — accuracy may vary.'
                if has_ai_foods else
                'Values confirmed by user — higher accuracy.' if has_user_confirmed else
                'All values from verified IFCT 2017 dataset.'
            )
        }

    # Persist deficiency reports
    for deficiency in deficiencies:
        report = DeficiencyReport(
            user_id=current_user.id,
            date=target_date,
            deficiency_type=deficiency['type'],
            severity=deficiency.get('severity', 'moderate'),
            fc_reasoning_chain=json.dumps(result['reasoning_chain'])
        )
        db.session.add(report)
    db.session.commit()

    return jsonify({
        'date': target_date.isoformat(),
        'deficiencies': deficiencies,
        'risks': result['risks'],
        'reasoning_chain': result['reasoning_chain'],
        'rules_fired': result['rules_fired'],
        'iterations': result['iterations'],
        'nutrition': nutrition,
        'rda': rda,
        'data_confidence': {
            'has_ai_estimated_foods': has_ai_foods,
            'discount_applied': discount,
        }
    })


# ── BACKWARD CHAINING ──────────────────────────────────────────────────────────

@analysis_bp.route('/backward-chain', methods=['POST'])
@token_required
def backward_chain(current_user):
    """
    Run backward chaining to explain a specific goal.
    Body: { "goal": "anaemia_risk", "date": "2024-01-01" }
    """
    data = request.get_json() or {}
    goal = data.get('goal', 'anaemia_risk')
    target_date = date.fromisoformat(data.get('date', date.today().isoformat()))

    nutrition = _get_daily_nutrition(current_user.id, target_date)
    rda = _get_rda(current_user)

    facts = {
        'iron_intake':    nutrition.get('iron', 0),
        'protein_intake': nutrition.get('protein', 0),
        'calcium_intake': nutrition.get('calcium', 0),
        'vitD_intake':    nutrition.get('vitaminD', 0),
        'vitB12_intake':  nutrition.get('vitaminB12', 0),
        'vitC_intake':    nutrition.get('vitaminC', 0),
        'fibre_intake':   nutrition.get('fibre', 0),
        'sugar_intake':   nutrition.get('sugar', 0),
        'fat_intake':     nutrition.get('fat', 0),
        'salt_intake':    nutrition.get('salt', 0),
        'gender':         current_user.gender or 'female',
        'age':            current_user.age or 30,
        'diet_type':      current_user.diet_type or 'veg',
    }

    rules = build_nutrition_rules(rda)
    kb = build_bc_knowledge_base(facts, rules)
    bc = BackwardChainer(kb)
    result = bc.solve(goal)

    # Persist proof tree to existing deficiency report if present
    report = DeficiencyReport.query.filter_by(
        user_id=current_user.id, date=target_date, deficiency_type=goal
    ).first()
    if report:
        report.bc_proof_tree = json.dumps(result['proof_tree'])
        db.session.commit()

    return jsonify(result)


# ── BAYESIAN NETWORK ───────────────────────────────────────────────────────────

@analysis_bp.route('/bayesian', methods=['GET'])
@token_required
def bayesian_risk(current_user):
    """Run Bayesian Network disease risk prediction."""
    target_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    nutrition = _get_daily_nutrition(current_user.id, target_date)

    if not nutrition:
        return jsonify({'error': 'No food log data for this date'}), 404

    user_profile = {
        'age': current_user.age or 30,
        'gender': current_user.gender or 'male',
        'bmi': current_user.get_bmi() or 22,
        'sunlight_hours': 1,  # default — no sunlight tracking yet
    }

    risks = _bayesian.predict(nutrition, user_profile)

    # Persist
    dr = DiseaseRisk.query.filter_by(user_id=current_user.id, date=target_date).first()
    if not dr:
        dr = DiseaseRisk(user_id=current_user.id, date=target_date)
        db.session.add(dr)

    risk_map = {r['disease']: r['risk_probability'] for r in risks}
    dr.diabetes_prob      = risk_map.get('Type 2 Diabetes', 0)
    dr.bp_prob            = risk_map.get('Hypertension (High BP)', 0)
    dr.anaemia_prob       = risk_map.get('Anaemia', 0)
    dr.osteoporosis_prob  = risk_map.get('Osteoporosis', 0)
    dr.vitD_prob          = risk_map.get('Vitamin D Deficiency', 0)
    dr.bayesian_evidence  = json.dumps(risks)
    db.session.commit()

    return jsonify({'date': target_date.isoformat(), 'risks': risks})


# ── RESOLUTION ENGINE ──────────────────────────────────────────────────────────

@analysis_bp.route('/claims', methods=['GET'])
@token_required
def list_claims(current_user):
    """Return all available claims that can be validated."""
    return jsonify(AVAILABLE_CLAIMS)


@analysis_bp.route('/validate-claim', methods=['POST'])
@token_required
def validate_claim(current_user):
    """
    Validate a dietary claim using resolution refutation.
    Body: { "claim": "iron_adequate", "date": "2024-01-01" }
    """
    data = request.get_json() or {}
    claim = data.get('claim', 'iron_adequate')
    target_date = date.fromisoformat(data.get('date', date.today().isoformat()))

    nutrition = _get_daily_nutrition(current_user.id, target_date)
    rda = _get_rda(current_user)

    facts = {
        'iron_intake':    nutrition.get('iron', 0),
        'protein_intake': nutrition.get('protein', 0),
        'calcium_intake': nutrition.get('calcium', 0),
        'vitD_intake':    nutrition.get('vitaminD', 0),
        'vitB12_intake':  nutrition.get('vitaminB12', 0),
        'vitC_intake':    nutrition.get('vitaminC', 0),
        'fibre_intake':   nutrition.get('fibre', 0),
        'sugar_intake':   nutrition.get('sugar', 0),
        'fat_intake':     nutrition.get('fat', 0),
        'salt_intake':    nutrition.get('salt', 0),
    }

    engine = ResolutionEngine()
    result = engine.validate_claim(claim, facts, rda)
    return jsonify(result)


# ── PROLOG QUERIES ─────────────────────────────────────────────────────────────

@analysis_bp.route('/prolog/deficiencies', methods=['GET'])
@token_required
def prolog_deficiencies(current_user):
    """Query Prolog KB for deficiencies and risks."""
    target_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    nutrition = _get_daily_nutrition(current_user.id, target_date)
    rda = _get_rda(current_user)

    _seed_prolog_if_needed()
    _prolog.assert_user_facts(
        current_user.id, nutrition, rda, current_user.diet_type or 'veg'
    )
    result = _prolog.query_deficiencies(current_user.id)
    return jsonify(result)


@analysis_bp.route('/prolog/recommendations', methods=['GET'])
@token_required
def prolog_recommendations(current_user):
    """Query Prolog KB for food recommendations for a deficiency."""
    deficiency = request.args.get('deficiency', 'iron')
    max_price = float(request.args.get('max_price', 20))

    _seed_prolog_if_needed()
    food_atoms = _prolog.query_food_recommendations(deficiency, max_price)

    # Resolve atoms back to Food records
    foods = []
    for atom in food_atoms:
        name_guess = atom.replace('_', ' ').title()
        food = Food.query.filter(Food.name.ilike(f'%{name_guess}%')).first()
        if food:
            foods.append(food.to_dict())

    return jsonify({'deficiency': deficiency, 'recommendations': foods})


# ── FULL ANALYSIS (all engines combined) ──────────────────────────────────────

@analysis_bp.route('/full', methods=['GET'])
@token_required
def full_analysis(current_user):
    """Run all analysis engines and return combined results."""
    target_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    nutrition = _get_daily_nutrition(current_user.id, target_date)
    rda = _get_rda(current_user)

    if not nutrition:
        return jsonify({'error': 'No food log data for this date'}), 404

    facts = {
        'iron_intake':    nutrition.get('iron', 0),
        'protein_intake': nutrition.get('protein', 0),
        'calcium_intake': nutrition.get('calcium', 0),
        'vitD_intake':    nutrition.get('vitaminD', 0),
        'vitB12_intake':  nutrition.get('vitaminB12', 0),
        'vitC_intake':    nutrition.get('vitaminC', 0),
        'fibre_intake':   nutrition.get('fibre', 0),
        'sugar_intake':   nutrition.get('sugar', 0),
        'fat_intake':     nutrition.get('fat', 0),
        'salt_intake':    nutrition.get('salt', 0),
        'gender':         current_user.gender or 'female',
        'age':            current_user.age or 30,
        'diet_type':      current_user.diet_type or 'veg',
    }

    # Forward chaining
    rules = build_nutrition_rules(rda)
    fc_result = ForwardChainer(facts, rules).run()

    # Bayesian
    user_profile = {
        'age': current_user.age or 30,
        'gender': current_user.gender or 'male',
        'bmi': current_user.get_bmi() or 22,
        'sunlight_hours': 1,
    }
    bayesian_risks = _bayesian.predict(nutrition, user_profile)

    return jsonify({
        'date': target_date.isoformat(),
        'nutrition': nutrition,
        'rda': rda,
        'deficiencies': fc_result['deficiencies'],
        'risks': fc_result['risks'],
        'reasoning_chain': fc_result['reasoning_chain'],
        'bayesian_risks': bayesian_risks,
    })
