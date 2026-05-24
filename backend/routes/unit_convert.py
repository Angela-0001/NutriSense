"""
Unit conversion route — converts natural language quantity to grams using Gemini.
POST /api/unit/convert
Body: { "food_name": "Samosa", "quantity_text": "1 samosa" }
Returns: { "grams": 85, "explanation": "1 medium samosa weighs ~85g" }
"""

import os, json, re, logging, requests
from flask import Blueprint, request, jsonify
from routes.auth import token_required

unit_bp = Blueprint('unit', __name__)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = (
    'https://generativelanguage.googleapis.com/v1beta/models/'
    'gemini-2.5-flash:generateContent?key={key}'
)

PROMPT = """Convert this food quantity to grams for Indian cooking context.

Food: "{food_name}"
Quantity: "{quantity_text}"

Examples:
- "1 samosa" → 85g (1 medium samosa)
- "2 rotis" → 70g (2 medium wheat rotis at 35g each)
- "1 katori dal" → 150g
- "1 glass milk" → 200g
- "1 handful peanuts" → 20g
- "1 plate rice" → 300g
- "half cup" → 80g

Reply ONLY with JSON: {{"grams": 85, "explanation": "1 medium samosa weighs about 85g"}}"""


@unit_bp.route('/convert', methods=['POST'])
@token_required
def convert_unit(current_user):
    data = request.get_json() or {}
    food_name = data.get('food_name', '').strip()
    quantity_text = data.get('quantity_text', '').strip()

    if not food_name or not quantity_text:
        return jsonify({'error': 'food_name and quantity_text required'}), 400

    # Fast path: if it's already a number + g/ml, just parse it
    direct = re.match(r'^(\d+(?:\.\d+)?)\s*(?:g|grams?|ml)$', quantity_text.lower())
    if direct:
        return jsonify({'grams': float(direct.group(1)), 'explanation': f'{quantity_text} (direct)'})

    if not GEMINI_API_KEY:
        return jsonify({'error': 'GEMINI_API_KEY not configured'}), 503

    payload = {
        'contents': [{'parts': [{'text': PROMPT.format(
            food_name=food_name, quantity_text=quantity_text
        )}]}],
        'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 64}
    }

    try:
        r = requests.post(GEMINI_URL.format(key=GEMINI_API_KEY), json=payload, timeout=15)
        r.raise_for_status()
        text = r.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        text = re.sub(r'```(?:json)?\s*', '', text).strip().rstrip('`')

        # Extract grams
        grams = None
        try:
            result = json.loads(re.search(r'\{.*\}', text, re.DOTALL).group(0))
            grams = float(result.get('grams', 100))
            explanation = result.get('explanation', '')
        except Exception:
            m = re.search(r'"grams"\s*:\s*(\d+(?:\.\d+)?)', text)
            grams = float(m.group(1)) if m else 100
            explanation = text[:80]

        grams = max(1, min(grams, 5000))
        return jsonify({'grams': grams, 'explanation': explanation})

    except Exception as e:
        logger.error(f'Unit convert error: {e}')
        return jsonify({'error': str(e)}), 500
