"""
One-time script to seed common Indian snacks and dishes into the database.
Run: python seed_snacks.py
"""
import os, sys, requests, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

GROQ_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'

SNACKS = [
    'Samosa', 'Bhel puri', 'Vada pav', 'Pani puri', 'Chakli',
    'Murukku', 'Sev', 'Chivda', 'Kachori', 'Dhokla',
    'Khakhra', 'Thepla', 'Misal pav', 'Dabeli', 'Pav bhaji',
    'Aloo tikki', 'Jalebi', 'Gulab jamun', 'Ladoo', 'Barfi',
    'Chole bhature', 'Dal makhani', 'Paneer tikka', 'Butter chicken',
    'Biryani (veg)', 'Pulao', 'Khichdi', 'Halwa', 'Kheer', 'Rasgulla',
    'Mathri', 'Namak para', 'Papdi', 'Golgappa', 'Dahi vada',
    'Aloo paratha', 'Gobi paratha', 'Paneer paratha', 'Methi paratha',
    'Masala dosa', 'Rava dosa', 'Pesarattu', 'Appam', 'Puttu',
]

FOOD_GROUP_MAP = {
    'Samosa': 'snacks and sweets', 'Bhel puri': 'snacks and sweets',
    'Vada pav': 'snacks and sweets', 'Pani puri': 'snacks and sweets',
    'Chakli': 'snacks and sweets', 'Murukku': 'snacks and sweets',
    'Sev': 'snacks and sweets', 'Chivda': 'snacks and sweets',
    'Kachori': 'snacks and sweets', 'Dhokla': 'snacks and sweets',
    'Khakhra': 'snacks and sweets', 'Jalebi': 'snacks and sweets',
    'Gulab jamun': 'snacks and sweets', 'Ladoo': 'snacks and sweets',
    'Barfi': 'snacks and sweets', 'Halwa': 'snacks and sweets',
    'Kheer': 'snacks and sweets', 'Rasgulla': 'snacks and sweets',
    'Mathri': 'snacks and sweets', 'Namak para': 'snacks and sweets',
    'Papdi': 'snacks and sweets', 'Golgappa': 'snacks and sweets',
    'Aloo tikki': 'snacks and sweets',
}

DIET_MAP = {
    'Butter chicken': 'nonveg',
    'Biryani (veg)': 'veg',
}

def fetch_nutrition(food_list):
    food_str = '\n'.join(f'- {f}' for f in food_list)
    prompt = f"""Estimate nutritional values per 100g for these Indian foods:
{food_str}

Return ONLY a valid JSON array. Each object must have exactly these fields:
name, food_group, diet_type, region, calories, protein, carbs, fat, fibre,
iron, calcium, vitaminC, vitaminD, vitaminB12, sugar, sodium, price_per_100g_inr

food_group must be one of: cereals, pulses, vegetables, fruits, milk and milk products,
meat poultry and fish, nuts and oilseeds, fats and oils, sugar and jaggery,
snacks and sweets, beverages, spices and condiments, dishes

All numeric values per 100g. price_per_100g_inr is 2024 Indian market price."""

    r = requests.post(GROQ_URL,
        headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': 'llama-3.3-70b-versatile',
            'messages': [
                {'role': 'system', 'content': 'You are a nutrition expert. Return only valid JSON array, no other text.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.1,
            'max_tokens': 8192,
        },
        timeout=60
    )
    r.raise_for_status()
    text = r.json()['choices'][0]['message']['content'].strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError(f'No JSON array in response: {text[:200]}')
    return json.loads(match.group(0))


def main():
    from app import create_app
    app = create_app()

    with app.app_context():
        from database.models import Food, db

        # Check which snacks are already in DB
        to_add = []
        for name in SNACKS:
            if Food.query.filter(Food.name.ilike(name)).first():
                print(f'  exists: {name}')
            else:
                to_add.append(name)

        if not to_add:
            print('All snacks already in database.')
            return

        print(f'\nFetching nutrition for {len(to_add)} foods from Groq...')

        # Process in batches of 20
        batch_size = 20
        total_saved = 0

        for i in range(0, len(to_add), batch_size):
            batch = to_add[i:i + batch_size]
            print(f'  Batch {i//batch_size + 1}: {batch}')

            try:
                items = fetch_nutrition(batch)
            except Exception as e:
                print(f'  ERROR: {e}')
                continue

            for item in items:
                name = str(item.get('name', '')).strip()
                if not name:
                    continue
                if Food.query.filter(Food.name.ilike(name)).first():
                    continue

                food_group = FOOD_GROUP_MAP.get(name, str(item.get('food_group', 'dishes')))
                diet_type  = DIET_MAP.get(name, str(item.get('diet_type', 'veg')))

                food = Food(
                    name=name,
                    food_group=food_group,
                    diet_type=diet_type,
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
                total_saved += 1
                print(f'    + {name}')

            db.session.commit()

        print(f'\nDone. Added {total_saved} foods to database.')
        print('Total foods in DB:', Food.query.count())


if __name__ == '__main__':
    main()
