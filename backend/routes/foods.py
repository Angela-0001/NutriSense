"""Foods routes — search, list, get by ID, AI-generate missing foods."""

import os, json, re, logging, requests
from flask import Blueprint, request, jsonify
from database.models import db, Food
from routes.auth import token_required

foods_bp = Blueprint('foods', __name__)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'


@foods_bp.route('/', methods=['GET'])
@token_required
def list_foods(current_user):
    """List foods with optional filters: group, diet_type, search query."""
    query = Food.query

    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(Food.name.ilike(f'%{search}%'))

    group = request.args.get('group', '').strip()
    if group:
        query = query.filter(Food.food_group == group)

    diet = request.args.get('diet_type', '').strip()
    if diet:
        query = query.filter(Food.diet_type == diet)

    limit = min(int(request.args.get('limit', 50)), 200)
    foods = query.limit(limit).all()
    return jsonify([f.to_dict() for f in foods])


@foods_bp.route('/<int:food_id>', methods=['GET'])
@token_required
def get_food(current_user, food_id):
    food = Food.query.get_or_404(food_id)
    return jsonify(food.to_dict())


@foods_bp.route('/groups', methods=['GET'])
@token_required
def get_groups(current_user):
    """Return distinct food groups."""
    groups = db_distinct_groups()
    return jsonify(groups)


def db_distinct_groups():
    rows = db.session.query(Food.food_group).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@foods_bp.route('/generate-missing', methods=['POST'])
@token_required
def generate_missing_food(current_user):
    """
    Called when a food is not found in the DB.
    Uses Groq to generate nutritional data, saves it, and returns the food.
    Body: { "food_name": "Pav bhaji" }
    """
    data = request.get_json() or {}
    food_name = data.get('food_name', '').strip()
    if not food_name:
        return jsonify({'error': 'food_name required'}), 400

    # Check if it already exists
    existing = Food.query.filter(Food.name.ilike(food_name)).first()
    if existing:
        return jsonify(existing.to_dict())

    if not GROQ_API_KEY or GROQ_API_KEY == 'paste_your_groq_key_here':
        return jsonify({'error': 'GROQ_API_KEY not configured'}), 503

    prompt = f"""Estimate nutritional values per 100g for this Indian food: {food_name}

Return ONLY a single JSON object, no other text:
{{"name":"{food_name}","food_group":"dishes","diet_type":"veg","region":"pan-india","calories":0,"protein":0,"carbs":0,"fat":0,"fibre":0,"iron":0,"calcium":0,"vitaminC":0,"vitaminD":0,"vitaminB12":0,"sugar":0,"sodium":0,"price_per_100g_inr":5}}"""

    try:
        r = requests.post(GROQ_URL,
            headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={'model': 'llama-3.3-70b-versatile',
                  'messages': [{'role': 'user', 'content': prompt}],
                  'temperature': 0.1, 'max_tokens': 512},
            timeout=20)
        r.raise_for_status()
        text = r.json()['choices'][0]['message']['content'].strip()
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`')
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            return jsonify({'error': 'Could not generate nutrition data'}), 502
        item = json.loads(match.group(0))

        food = Food(
            name=str(item.get('name', food_name)),
            food_group=str(item.get('food_group', 'dishes')),
            diet_type=str(item.get('diet_type', 'veg')),
            region=str(item.get('region', 'pan-india')),
            calories=max(0, float(item.get('calories', 0))),
            protein=max(0, float(item.get('protein', 0))),
            carbs=max(0, float(item.get('carbs', 0))),
            fat=max(0, float(item.get('fat', 0))),
            fibre=max(0, float(item.get('fibre', 0))),
            iron=max(0, float(item.get('iron', 0))),
            calcium=max(0, float(item.get('calcium', 0))),
            vitaminC=max(0, float(item.get('vitaminC', 0))),
            vitaminD=max(0, float(item.get('vitaminD', 0))),
            vitaminB12=max(0, float(item.get('vitaminB12', 0))),
            sugar=max(0, float(item.get('sugar', 0))),
            sodium=max(0, float(item.get('sodium', 0))),
            price_per_100g_inr=max(0, float(item.get('price_per_100g_inr', 5))),
            source='Groq-LLaMA3-estimated'
        )
        db.session.add(food)
        db.session.commit()
        logger.info(f'AI-generated food saved: {food.name}')
        return jsonify(food.to_dict()), 201

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        return jsonify({'error': f'Groq API error {status}'}), 502
    except Exception as e:
        logger.error(f'generate_missing_food error: {e}')
        return jsonify({'error': str(e)}), 500
