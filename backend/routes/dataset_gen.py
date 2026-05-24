"""
Dataset Generator route — uses Groq LLM to estimate nutritional values
for Indian foods not in the IFCT dataset, then optionally saves to DB.

POST /api/dataset/generate   — generate nutrition for a list of food names
POST /api/dataset/save       — save approved entries to the foods table
GET  /api/dataset/export     — export all generated entries as CSV
"""

import os
import json
import logging
import csv
import io
import requests
from flask import Blueprint, request, jsonify, Response
from routes.auth import token_required
from database.models import db, Food

dataset_bp = Blueprint('dataset', __name__)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'

SYSTEM_PROMPT = """You are a nutrition expert specializing in Indian cuisine.
Given a list of Indian food/snack names, return ONLY a valid JSON array with
nutritional estimates per 100g. Use standard Indian recipes and cooking methods.
Be accurate based on typical ingredients and preparation."""

USER_PROMPT_TEMPLATE = """Estimate nutritional values per 100g for these Indian foods:
{food_list}

Return ONLY a JSON array, no other text. Each object must have exactly these fields:
{{
  "name": "food name",
  "food_group": "one of: cereals/pulses/vegetables/fruits/milk and milk products/meat, poultry and fish/nuts and oilseeds/fats and oils/sugar and jaggery/snacks and sweets/beverages/spices and condiments",
  "diet_type": "veg or nonveg",
  "region": "north-india/south-india/east-india/west-india/pan-india",
  "calories": 0,
  "protein": 0,
  "carbs": 0,
  "fat": 0,
  "fibre": 0,
  "iron": 0,
  "calcium": 0,
  "vitaminC": 0,
  "vitaminD": 0,
  "vitaminB12": 0,
  "sugar": 0,
  "sodium": 0,
  "price_per_100g_inr": 0
}}

All numeric values are per 100g. price_per_100g_inr is approximate 2024 Indian market price."""


@dataset_bp.route('/generate', methods=['POST'])
@token_required
def generate_nutrition(current_user):
    """
    Generate nutritional data for a list of food names using Groq.
    Body: { "foods": ["samosa", "bhel puri", "vada pav"] }
    """
    if not GROQ_API_KEY or GROQ_API_KEY == 'paste_your_groq_key_here':
        return jsonify({'error': 'GROQ_API_KEY not configured. Add it to .env file.'}), 503

    data = request.get_json() or {}
    food_names = data.get('foods', [])

    if not food_names:
        return jsonify({'error': 'Provide a list of food names in "foods" field'}), 400
    if len(food_names) > 20:
        return jsonify({'error': 'Max 20 foods per request'}), 400

    # Clean and deduplicate
    food_names = list(dict.fromkeys([f.strip() for f in food_names if f.strip()]))
    food_list = '\n'.join(f'- {name}' for name in food_names)

    payload = {
        'model': GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user',   'content': USER_PROMPT_TEMPLATE.format(food_list=food_list)}
        ],
        'temperature': 0.1,
        'max_tokens': 4096,
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        text = response.json()['choices'][0]['message']['content'].strip()
        logger.info(f'Groq raw response (first 300): {text[:300]}')

        # Extract JSON array
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if not match:
            return jsonify({'error': f'Could not parse Groq response: {text[:300]}'}), 502

        results = json.loads(match.group(0))

        # Validate and clamp values, cross-check against category averages
        cleaned = []
        for item in results:
            food_group = str(item.get('food_group', 'snacks and sweets'))

            # Cross-check against category average from IFCT foods
            category_foods = Food.query.filter_by(food_group=food_group).limit(20).all()
            flags = []
            if category_foods:
                for macro in ['calories', 'protein', 'carbs', 'fat']:
                    vals = [getattr(f, macro) for f in category_foods if getattr(f, macro, 0) > 0]
                    if vals:
                        avg = sum(vals) / len(vals)
                        ai_val = float(item.get(macro, 0))
                        if avg > 0 and abs(ai_val - avg) / avg > 0.40:
                            flags.append({
                                'macro': macro,
                                'ai_value': round(ai_val, 1),
                                'category_avg': round(avg, 1),
                                'deviation_pct': round(abs(ai_val - avg) / avg * 100, 1)
                            })

            cleaned.append({
                'name':              str(item.get('name', '')),
                'food_group':        food_group,
                'diet_type':         str(item.get('diet_type', 'veg')),
                'region':            str(item.get('region', 'pan-india')),
                'calories':          max(0, float(item.get('calories', 0))),
                'protein':           max(0, float(item.get('protein', 0))),
                'carbs':             max(0, float(item.get('carbs', 0))),
                'fat':               max(0, float(item.get('fat', 0))),
                'fibre':             max(0, float(item.get('fibre', 0))),
                'iron':              max(0, float(item.get('iron', 0))),
                'calcium':           max(0, float(item.get('calcium', 0))),
                'vitaminC':          max(0, float(item.get('vitaminC', 0))),
                'vitaminD':          max(0, float(item.get('vitaminD', 0))),
                'vitaminB12':        max(0, float(item.get('vitaminB12', 0))),
                'sugar':             max(0, float(item.get('sugar', 0))),
                'sodium':            max(0, float(item.get('sodium', 0))),
                'price_per_100g_inr':max(0, float(item.get('price_per_100g_inr', 5))),
                'source':            'Groq-LLaMA3-estimated',
                'already_in_db':     Food.query.filter(
                                         Food.name.ilike(f"%{item.get('name','')}%")
                                     ).first() is not None,
                'flagged':           len(flags) > 0,
                'flags':             flags,
            })

        return jsonify({'results': cleaned, 'count': len(cleaned)})

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        body = e.response.text[:300] if e.response else ''
        logger.error(f'Groq HTTP error {status}: {body}')
        if status == 401:
            return jsonify({'error': 'Invalid Groq API key'}), 401
        if status == 429:
            return jsonify({'error': 'Groq rate limit hit. Wait a moment.'}), 429
        return jsonify({'error': f'Groq API error {status}: {body}'}), 502

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f'Parse error: {e}')
        return jsonify({'error': f'Failed to parse Groq response: {str(e)}'}), 502

    except Exception as e:
        logger.error(f'Dataset gen error: {e}')
        return jsonify({'error': str(e)}), 500


@dataset_bp.route('/save', methods=['POST'])
@token_required
def save_foods(current_user):
    """
    Save approved generated food entries to the foods table.
    Body: { "foods": [ ...array of food objects from /generate... ] }
    """
    data = request.get_json() or {}
    foods = data.get('foods', [])
    if not foods:
        return jsonify({'error': 'No foods provided'}), 400

    saved, skipped = [], []
    for item in foods:
        name = item.get('name', '').strip()
        if not name:
            continue
        # Skip if already exists
        if Food.query.filter(Food.name.ilike(name)).first():
            skipped.append(name)
            continue

        food = Food(
            name=name,
            food_group=item.get('food_group', 'snacks and sweets'),
            diet_type=item.get('diet_type', 'veg'),
            region=item.get('region', 'pan-india'),
            calories=item.get('calories', 0),
            protein=item.get('protein', 0),
            carbs=item.get('carbs', 0),
            fat=item.get('fat', 0),
            fibre=item.get('fibre', 0),
            iron=item.get('iron', 0),
            calcium=item.get('calcium', 0),
            vitaminC=item.get('vitaminC', 0),
            vitaminD=item.get('vitaminD', 0),
            vitaminB12=item.get('vitaminB12', 0),
            sugar=item.get('sugar', 0),
            sodium=item.get('sodium', 0),
            price_per_100g_inr=item.get('price_per_100g_inr', 5),
            source='Groq-LLaMA3-estimated'
        )
        db.session.add(food)
        saved.append(name)

    db.session.commit()
    return jsonify({'saved': saved, 'skipped': skipped,
                    'saved_count': len(saved), 'skipped_count': len(skipped)})


@dataset_bp.route('/export', methods=['GET'])
@token_required
def export_csv(current_user):
    """Export all Groq-generated foods as CSV."""
    foods = Food.query.filter_by(source='Groq-LLaMA3-estimated').all()

    output = io.StringIO()
    fields = ['name', 'food_group', 'diet_type', 'region', 'calories', 'protein',
              'carbs', 'fat', 'fibre', 'iron', 'calcium', 'vitaminC', 'vitaminD',
              'vitaminB12', 'sugar', 'sodium', 'price_per_100g_inr', 'source']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for f in foods:
        writer.writerow({field: getattr(f, field, '') for field in fields})

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=nutrisense_generated_foods.csv'}
    )
