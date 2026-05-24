"""
Meal Context Mapping
meal_context.py

Maps raw IFCT food ingredients to culturally appropriate prepared forms
based on meal time (breakfast/lunch/dinner/snack).

Structure per food:
  {
    'breakfast': ('Palak Paratha', 'add to paratha dough'),
    'lunch':     ('Palak Sabzi', 'cook as sabzi with onion and spices'),
    'dinner':    ('Palak Dal', 'add to dal while cooking'),
    'snack':     ('Palak Chaat', 'blanch and toss with chaat masala'),
  }

If a meal slot is None, a generic cooking suggestion is returned instead.
"""

# ── MEAL CONTEXT MAP ──────────────────────────────────────────────────────────
# Keys are lowercase food name substrings (matched with 'in' check)
# Values are dicts with breakfast/lunch/dinner/snack prepared forms

MEAL_CONTEXT_MAP = {
    # ── LEAFY GREENS ──────────────────────────────────────────────────────────
    'spinach': {
        'breakfast': ('Palak Paratha', 'spinach stuffed flatbread'),
        'lunch':     ('Palak Sabzi', 'spinach cooked with onion and spices'),
        'dinner':    ('Palak Dal', 'spinach added to lentil curry'),
        'snack':     ('Palak Pakoda', 'spinach fritters'),
    },
    'palak': {
        'breakfast': ('Palak Paratha', 'spinach stuffed flatbread'),
        'lunch':     ('Palak Paneer', 'spinach and cottage cheese curry'),
        'dinner':    ('Palak Dal', 'spinach lentil curry'),
        'snack':     ('Palak Pakoda', 'spinach fritters'),
    },
    'methi': {
        'breakfast': ('Methi Paratha', 'fenugreek flatbread'),
        'lunch':     ('Methi Sabzi', 'fenugreek leaves stir-fry'),
        'dinner':    ('Methi Dal', 'fenugreek lentil curry'),
        'snack':     ('Methi Mathri', 'fenugreek crackers'),
    },
    'drumstick': {
        'breakfast': None,
        'lunch':     ('Drumstick Sambar', 'drumstick in lentil soup'),
        'dinner':    ('Drumstick Curry', 'drumstick in coconut curry'),
        'snack':     None,
    },
    'moringa': {
        'breakfast': ('Moringa Paratha', 'moringa leaf flatbread'),
        'lunch':     ('Moringa Dal', 'moringa leaves in dal'),
        'dinner':    ('Moringa Sabzi', 'moringa stir-fry'),
        'snack':     ('Moringa Tea', 'moringa leaf tea'),
    },
    # ── SEEDS & NUTS ──────────────────────────────────────────────────────────
    'sesame': {
        'breakfast': ('Til Ladoo', 'sesame seed sweet balls'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Til Chikki', 'sesame jaggery brittle'),
    },
    'til': {
        'breakfast': ('Til Paratha', 'sesame flatbread'),
        'lunch':     ('Til Chutney', 'sesame seed chutney'),
        'dinner':    None,
        'snack':     ('Til Chikki', 'sesame jaggery brittle'),
    },
    'flax': {
        'breakfast': ('Flaxseed Paratha', 'flaxseed flatbread'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Roasted Flaxseeds', 'dry roasted flaxseeds with salt'),
    },
    'groundnut': {
        'breakfast': ('Peanut Poha', 'flattened rice with peanuts'),
        'lunch':     ('Peanut Chutney', 'groundnut chutney with rice'),
        'dinner':    None,
        'snack':     ('Roasted Peanuts', 'dry roasted salted peanuts'),
    },
    'peanut': {
        'breakfast': ('Peanut Poha', 'flattened rice with peanuts'),
        'lunch':     ('Peanut Chutney', 'groundnut chutney'),
        'dinner':    None,
        'snack':     ('Roasted Peanuts', 'dry roasted salted peanuts'),
    },
    'almond': {
        'breakfast': ('Soaked Almonds', '4-5 soaked almonds with milk'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Roasted Almonds', 'dry roasted almonds'),
    },
    # ── PULSES & LEGUMES ──────────────────────────────────────────────────────
    'moong': {
        'breakfast': ('Moong Dal Chilla', 'moong dal savoury pancake'),
        'lunch':     ('Moong Dal', 'yellow lentil curry'),
        'dinner':    ('Moong Dal Khichdi', 'rice and lentil porridge'),
        'snack':     ('Moong Sprouts Chaat', 'sprouted moong chaat'),
    },
    'masoor': {
        'breakfast': ('Masoor Dal Paratha', 'red lentil stuffed flatbread'),
        'lunch':     ('Masoor Dal', 'red lentil curry'),
        'dinner':    ('Masoor Dal Soup', 'red lentil soup'),
        'snack':     None,
    },
    'chana': {
        'breakfast': ('Chana Poha', 'flattened rice with chickpeas'),
        'lunch':     ('Chana Masala', 'spiced chickpea curry'),
        'dinner':    ('Chana Dal', 'split chickpea curry'),
        'snack':     ('Roasted Chana', 'dry roasted spiced chickpeas'),
    },
    'rajma': {
        'breakfast': None,
        'lunch':     ('Rajma Chawal', 'kidney beans with rice'),
        'dinner':    ('Rajma Curry', 'kidney bean curry'),
        'snack':     None,
    },
    'soyabean': {
        'breakfast': ('Soya Paratha', 'soya stuffed flatbread'),
        'lunch':     ('Soya Chunks Curry', 'textured soya protein curry'),
        'dinner':    ('Soya Pulao', 'soya chunks rice'),
        'snack':     ('Roasted Soya', 'roasted soya nuts'),
    },
    # ── DAIRY ─────────────────────────────────────────────────────────────────
    'paneer': {
        'breakfast': ('Paneer Paratha', 'cottage cheese stuffed flatbread'),
        'lunch':     ('Paneer Sabzi', 'cottage cheese curry'),
        'dinner':    ('Palak Paneer', 'spinach cottage cheese curry'),
        'snack':     ('Paneer Tikka', 'grilled spiced cottage cheese'),
    },
    'milk': {
        'breakfast': ('Milk with Turmeric', 'warm turmeric milk (haldi doodh)'),
        'lunch':     None,
        'dinner':    ('Warm Milk', 'warm milk before bed'),
        'snack':     ('Lassi', 'yogurt-based drink'),
    },
    'curd': {
        'breakfast': ('Curd with Poha', 'yogurt served with flattened rice'),
        'lunch':     ('Raita', 'spiced yogurt with vegetables'),
        'dinner':    ('Plain Curd', 'plain yogurt as side'),
        'snack':     ('Lassi', 'blended yogurt drink'),
    },
    # ── CEREALS ───────────────────────────────────────────────────────────────
    'bajra': {
        'breakfast': ('Bajra Roti', 'pearl millet flatbread'),
        'lunch':     ('Bajra Khichdi', 'pearl millet porridge'),
        'dinner':    ('Bajra Roti', 'pearl millet flatbread with ghee'),
        'snack':     ('Bajra Ladoo', 'pearl millet sweet balls'),
    },
    'ragi': {
        'breakfast': ('Ragi Dosa', 'finger millet crepe'),
        'lunch':     ('Ragi Mudde', 'finger millet balls with sambar'),
        'dinner':    ('Ragi Roti', 'finger millet flatbread'),
        'snack':     ('Ragi Ladoo', 'finger millet sweet balls'),
    },
    'oats': {
        'breakfast': ('Oats Upma', 'savoury oats with vegetables'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Oats Chikki', 'oats jaggery brittle'),
    },
    # ── VEGETABLES ────────────────────────────────────────────────────────────
    'carrot': {
        'breakfast': ('Gajar Paratha', 'carrot stuffed flatbread'),
        'lunch':     ('Gajar Sabzi', 'carrot stir-fry'),
        'dinner':    ('Gajar Halwa', 'carrot pudding'),
        'snack':     ('Carrot Sticks with Chutney', 'raw carrot with green chutney'),
    },
    'tomato': {
        'breakfast': ('Tomato Chutney', 'tomato chutney with idli/dosa'),
        'lunch':     ('Tomato Dal', 'tomato lentil curry'),
        'dinner':    ('Tomato Sabzi', 'tomato curry'),
        'snack':     None,
    },
    'bitter gourd': {
        'breakfast': None,
        'lunch':     ('Karela Sabzi', 'bitter gourd stir-fry'),
        'dinner':    ('Karela Masala', 'spiced bitter gourd'),
        'snack':     ('Karela Chips', 'crispy bitter gourd chips'),
    },
    'amla': {
        'breakfast': ('Amla Juice', 'fresh amla juice'),
        'lunch':     ('Amla Chutney', 'amla green chutney'),
        'dinner':    None,
        'snack':     ('Amla Murabba', 'amla in sugar syrup'),
    },
    'guava': {
        'breakfast': ('Guava with Salt', 'fresh guava with rock salt'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Guava Chaat', 'guava with chaat masala'),
    },
    # ── FISH & EGGS ───────────────────────────────────────────────────────────
    'egg': {
        'breakfast': ('Egg Bhurji', 'scrambled spiced eggs'),
        'lunch':     ('Egg Curry', 'boiled egg curry'),
        'dinner':    ('Egg Masala', 'spiced egg curry'),
        'snack':     ('Boiled Egg', 'hard boiled egg with salt and pepper'),
    },
    'sardine': {
        'breakfast': None,
        'lunch':     ('Sardine Curry', 'sardine fish curry'),
        'dinner':    ('Sardine Masala', 'spiced sardine fry'),
        'snack':     None,
    },
    'mackerel': {
        'breakfast': None,
        'lunch':     ('Bangda Curry', 'mackerel fish curry'),
        'dinner':    ('Bangda Fry', 'spiced mackerel fry'),
        'snack':     None,
    },
    'rohu': {
        'breakfast': None,
        'lunch':     ('Rohu Curry', 'rohu fish curry'),
        'dinner':    ('Rohu Fry', 'spiced rohu fish fry'),
        'snack':     None,
    },
    # ── JAGGERY & SWEETS ──────────────────────────────────────────────────────
    'jaggery': {
        'breakfast': ('Jaggery with Roti', 'roti with jaggery and ghee'),
        'lunch':     None,
        'dinner':    None,
        'snack':     ('Jaggery Chikki', 'jaggery peanut brittle'),
    },
}

# Generic cooking suggestions when no specific form is defined
GENERIC_SUGGESTIONS = {
    'breakfast': 'add to your paratha dough or morning upma',
    'lunch':     'add to your sabzi or dal',
    'dinner':    'mix into your roti dough or add to dal',
    'snack':     'roast lightly and eat as a snack with salt',
}


def get_meal_context_recommendation(food_name: str, meal_type: str) -> dict:
    """
    Given a raw food name and meal type, return the culturally appropriate
    prepared form for that meal context.

    Args:
        food_name: raw food name from IFCT (e.g. 'Spinach', 'Til (sesame seeds)')
        meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack'

    Returns:
        dict with:
            - prepared_name: the dish name to show prominently
            - raw_ingredient: the original food name (shown as subtitle)
            - cooking_note: description of how it's prepared
            - has_specific_form: bool — True if a specific form was found
    """
    meal_type = meal_type.lower() if meal_type else 'lunch'
    if meal_type not in ('breakfast', 'lunch', 'dinner', 'snack'):
        meal_type = 'lunch'

    food_lower = food_name.lower()

    # Find matching entry in context map
    matched_entry = None
    for key, forms in MEAL_CONTEXT_MAP.items():
        if key in food_lower:
            matched_entry = forms
            break

    if matched_entry:
        form = matched_entry.get(meal_type)
        if form:
            return {
                'prepared_name': form[0],
                'raw_ingredient': food_name,
                'cooking_note': form[1],
                'has_specific_form': True,
            }

    # No specific form — return generic suggestion
    generic = GENERIC_SUGGESTIONS.get(meal_type, 'add to your meal')
    return {
        'prepared_name': food_name,
        'raw_ingredient': food_name,
        'cooking_note': generic,
        'has_specific_form': False,
    }


def enrich_recommendations_with_context(recommendations: list, meal_type: str) -> list:
    """
    Enrich a list of food recommendation strings with meal context.

    Args:
        recommendations: list of food name strings
        meal_type: meal context

    Returns:
        list of enriched recommendation dicts
    """
    return [
        get_meal_context_recommendation(food, meal_type)
        for food in recommendations
    ]
