"""
Vision route — portion estimation from food photo using Gemini Vision.
POST /api/vision/estimate-portion
"""

import os
import base64
import json
import logging
import re
import requests
from flask import Blueprint, request, jsonify
from routes.auth import token_required

vision_bp = Blueprint('vision', __name__)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_URL = (
    'https://generativelanguage.googleapis.com/v1beta/models/'
    'gemini-2.5-flash:generateContent?key={key}'
)

PROMPT_TEMPLATE = """You are a nutrition assistant. Estimate grams of "{food_name}" visible in this image.

Reply with ONLY this JSON, nothing else:
{{"estimated_grams":150,"confidence":"medium","reasoning":"standard katori bowl","range_min":120,"range_max":180}}"""


@vision_bp.route('/estimate-portion', methods=['POST'])
@token_required
def estimate_portion(current_user):
    if not GEMINI_API_KEY:
        return jsonify({'error': 'GEMINI_API_KEY not configured on server'}), 503

    food_name = request.form.get('food_name', '').strip()
    if not food_name:
        return jsonify({'error': 'food_name is required'}), 400

    image_file = request.files.get('image')
    if not image_file:
        return jsonify({'error': 'image file is required'}), 400

    allowed = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
    mime_type = image_file.mimetype or 'image/jpeg'
    if mime_type not in allowed:
        return jsonify({'error': f'Unsupported image type: {mime_type}'}), 400

    image_bytes = image_file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        return jsonify({'error': 'Image too large. Max 10MB.'}), 400

    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    payload = {
        'contents': [{
            'parts': [
                {'inline_data': {'mime_type': mime_type, 'data': image_b64}},
                {'text': PROMPT_TEMPLATE.format(food_name=food_name)}
            ]
        }],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 128,
        }
    }

    try:
        response = requests.post(
            GEMINI_URL.format(key=GEMINI_API_KEY),
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        text = data['candidates'][0]['content']['parts'][0]['text'].strip()
        logger.info(f'Gemini raw response: {text}')

        text = re.sub(r'```(?:json)?\s*', '', text).strip()
        text = re.sub(r'```', '', text).strip()

        # Extract JSON — handle truncated responses by pulling known fields directly
        grams = 100
        confidence = 'medium'
        reasoning = ''
        range_min = 70
        range_max = 130

        # Try full JSON parse first
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                grams = int(result.get('estimated_grams', 100))
                confidence = result.get('confidence', 'medium')
                reasoning = result.get('reasoning', '')
                range_min = int(result.get('range_min', max(5, grams - 30)))
                range_max = int(result.get('range_max', grams + 30))
        except (json.JSONDecodeError, ValueError):
            # Fallback: extract estimated_grams with regex even from truncated JSON
            m = re.search(r'"estimated_grams"\s*:\s*(\d+)', text)
            if m:
                grams = int(m.group(1))
                range_min = max(5, grams - 30)
                range_max = grams + 30
            m2 = re.search(r'"confidence"\s*:\s*"(\w+)"', text)
            if m2:
                confidence = m2.group(1)
            m3 = re.search(r'"reasoning"\s*:\s*"([^"]+)"', text)
            if m3:
                reasoning = m3.group(1)

        grams = max(5, min(grams, 2000))

        return jsonify({
            'food_name': food_name,
            'estimated_grams': grams,
            'range_min': range_min,
            'range_max': range_max,
            'confidence': confidence,
            'reasoning': reasoning,
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Gemini API timed out. Try again.'}), 504

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        try:
            body = e.response.json()
        except Exception:
            body = e.response.text if e.response else ''
        logger.error(f'Gemini HTTP error {status}: {body}')
        if status == 403:
            return jsonify({'error': 'API key invalid or Gemini API not enabled.'}), 403
        if status == 429:
            return jsonify({'error': 'Rate limit hit. Wait a moment and try again.'}), 429
        return jsonify({'error': f'Gemini API error {status}: {body}'}), 502

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raw = text if 'text' in dir() else 'no response'
        logger.error(f'Parse error: {e} — raw: {raw}')
        return jsonify({'error': f'Could not parse Gemini response: {raw[:200]}'}), 502
    except Exception as e:
        logger.error(f'Vision estimate error: {e}')
        return jsonify({'error': str(e)}), 500
