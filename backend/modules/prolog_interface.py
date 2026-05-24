"""
NutriSense Prolog Interface
prolog_interface.py

Bridge between Python (SQLite data) and SWI-Prolog (logic rules).
Uses pyswip to:
  1. Load nutrition_kb.pl (rules only — no hardcoded data)
  2. Assert food facts dynamically from SQLite
  3. Assert user daily intake and RDA facts
  4. Query Prolog rules and return results to Python

This implements the DATA vs LOGIC separation:
  DATA  → SQLite (IFCT 2017 dataset, user logs)
  LOGIC → Prolog (nutrition_kb.pl inference rules)
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from pyswip import Prolog
    # Quick sanity test before marking as available
    _test = Prolog()
    PYSWIP_AVAILABLE = True
    del _test
except Exception:
    PYSWIP_AVAILABLE = False
    logger.warning("pyswip/SWI-Prolog not available or incompatible version. Using Python fallback.")


KB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nutrition_kb.pl')


class PrologInterface:
    """
    Interface to SWI-Prolog knowledge base.
    Dynamically asserts facts from SQLite and queries rules.
    """

    def __init__(self):
        self.prolog = None
        self._loaded = False
        if PYSWIP_AVAILABLE:
            try:
                self._init_prolog()
            except Exception as e:
                logger.warning(f"Prolog init skipped: {e}")
                self._loaded = False

    def _init_prolog(self):
        """Load the Prolog knowledge base file."""
        try:
            self.prolog = Prolog()
            kb_path_escaped = KB_PATH.replace('\\', '/')
            self.prolog.consult(kb_path_escaped)
            self._loaded = True
            logger.info(f"Prolog KB loaded from {KB_PATH}")
        except Exception as e:
            logger.warning(f"Prolog initialization failed (assertion crash or missing SWI-Prolog): {e}. "
                           f"Prolog queries will use fallback Python logic.")
            self._loaded = False
            self.prolog = None

    def _safe_atom(self, name: str) -> str:
        """Convert food name to a safe Prolog atom (lowercase, underscores)."""
        return name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace("'", '').replace('-', '_')

    def assert_food_facts(self, foods: list):
        """
        Assert all food nutritional facts into Prolog working memory.
        Called once per session with all foods from SQLite.

        Args:
            foods: list of Food model instances or dicts
        """
        if not self._loaded:
            return

        try:
            # Retract all existing food facts first
            for pred in ['protein', 'iron', 'calcium', 'vitaminC', 'vitaminD',
                         'vitaminB12', 'carbs', 'fat', 'fibre', 'sugar', 'price', 'food_group', 'diet_type_food']:
                try:
                    list(self.prolog.query(f'retractall({pred}(_, _))'))
                except Exception:
                    pass

            for food in foods:
                if isinstance(food, dict):
                    f = food
                else:
                    f = food.to_dict()

                atom = self._safe_atom(f['name'])

                assertions = [
                    f"assertz(protein('{atom}', {f.get('protein', 0)}))",
                    f"assertz(iron('{atom}', {f.get('iron', 0)}))",
                    f"assertz(calcium('{atom}', {f.get('calcium', 0)}))",
                    f"assertz(vitaminC('{atom}', {f.get('vitaminC', 0)}))",
                    f"assertz(vitaminD('{atom}', {f.get('vitaminD', 0)}))",
                    f"assertz(vitaminB12('{atom}', {f.get('vitaminB12', 0)}))",
                    f"assertz(carbs('{atom}', {f.get('carbs', 0)}))",
                    f"assertz(fat('{atom}', {f.get('fat', 0)}))",
                    f"assertz(fibre('{atom}', {f.get('fibre', 0)}))",
                    f"assertz(sugar('{atom}', {f.get('sugar', 0)}))",
                    f"assertz(price('{atom}', {f.get('price_per_100g_inr', 5)}))",
                    f"assertz(food_group('{atom}', '{f.get('food_group', 'other')}'))",
                    f"assertz(diet_type_food('{atom}', '{f.get('diet_type', 'veg')}'))",
                ]

                for assertion in assertions:
                    list(self.prolog.query(assertion))

            # Assert same_food_group facts
            self._assert_same_food_group(foods)
            logger.info(f"Asserted facts for {len(foods)} foods into Prolog.")

        except Exception as e:
            logger.error(f"Error asserting food facts: {e}")

    def _assert_same_food_group(self, foods: list):
        """Assert same_food_group/2 facts for all food pairs in the same group."""
        try:
            list(self.prolog.query('retractall(same_food_group(_, _))'))
            group_map = {}
            for food in foods:
                f = food if isinstance(food, dict) else food.to_dict()
                group = f.get('food_group', 'other')
                atom = self._safe_atom(f['name'])
                group_map.setdefault(group, []).append(atom)

            for group, atoms in group_map.items():
                for i, a1 in enumerate(atoms):
                    for a2 in atoms[i + 1:]:
                        list(self.prolog.query(f"assertz(same_food_group('{a1}', '{a2}'))"))
                        list(self.prolog.query(f"assertz(same_food_group('{a2}', '{a1}'))"))
        except Exception as e:
            logger.error(f"Error asserting same_food_group: {e}")

    def assert_user_facts(self, user_id: int, daily_nutrition: dict, rda: dict, diet_type: str):
        """
        Assert user-specific daily intake and RDA facts for deficiency detection.

        Args:
            user_id: integer user ID (used as Prolog atom)
            daily_nutrition: dict of daily totals
            rda: dict of ICMR RDA values for this user
            diet_type: 'veg'/'nonveg'/'vegan'/'eggetarian'
        """
        if not self._loaded:
            return

        user_atom = f'user_{user_id}'

        try:
            # Retract existing user facts
            for pred in ['daily_iron', 'daily_protein', 'daily_calcium', 'daily_vitD',
                         'daily_vitB12', 'daily_vitC', 'daily_sugar', 'daily_fibre',
                         'daily_fat', 'daily_salt', 'rda_iron', 'rda_protein',
                         'rda_calcium', 'rda_vitD', 'rda_vitB12', 'rda_vitC',
                         'diet_type']:
                try:
                    list(self.prolog.query(f"retractall({pred}('{user_atom}', _))"))
                except Exception:
                    pass

            # Assert daily intake facts
            intake_assertions = [
                f"assertz(daily_iron('{user_atom}', {daily_nutrition.get('iron', 0)}))",
                f"assertz(daily_protein('{user_atom}', {daily_nutrition.get('protein', 0)}))",
                f"assertz(daily_calcium('{user_atom}', {daily_nutrition.get('calcium', 0)}))",
                f"assertz(daily_vitD('{user_atom}', {daily_nutrition.get('vitaminD', 0)}))",
                f"assertz(daily_vitB12('{user_atom}', {daily_nutrition.get('vitaminB12', 0)}))",
                f"assertz(daily_vitC('{user_atom}', {daily_nutrition.get('vitaminC', 0)}))",
                f"assertz(daily_sugar('{user_atom}', {daily_nutrition.get('sugar', 0)}))",
                f"assertz(daily_fibre('{user_atom}', {daily_nutrition.get('fibre', 0)}))",
                f"assertz(daily_fat('{user_atom}', {daily_nutrition.get('fat', 0)}))",
                f"assertz(daily_salt('{user_atom}', {daily_nutrition.get('salt', 0)}))",
            ]

            # Assert RDA facts
            rda_assertions = [
                f"assertz(rda_iron('{user_atom}', {rda.get('iron', 21)}))",
                f"assertz(rda_protein('{user_atom}', {rda.get('protein', 55)}))",
                f"assertz(rda_calcium('{user_atom}', {rda.get('calcium', 600)}))",
                f"assertz(rda_vitD('{user_atom}', {rda.get('vitaminD', 10)}))",
                f"assertz(rda_vitB12('{user_atom}', {rda.get('vitaminB12', 1.0)}))",
                f"assertz(rda_vitC('{user_atom}', {rda.get('vitaminC', 40)}))",
            ]

            # Map diet_type to Prolog atom
            diet_map = {'veg': 'vegetarian', 'nonveg': 'nonvegetarian',
                        'vegan': 'vegan', 'eggetarian': 'eggetarian'}
            prolog_diet = diet_map.get(diet_type, 'vegetarian')
            diet_assertion = [f"assertz(diet_type('{user_atom}', {prolog_diet}))"]

            for a in intake_assertions + rda_assertions + diet_assertion:
                list(self.prolog.query(a))

        except Exception as e:
            logger.error(f"Error asserting user facts: {e}")

    def query_deficiencies(self, user_id: int) -> dict:
        """
        Query all deficiency and disease risk rules for a user.

        Returns:
            dict with deficiencies and risks lists
        """
        if not self._loaded:
            return self._fallback_deficiencies()

        user_atom = f'user_{user_id}'
        deficiencies = []
        risks = []

        deficiency_queries = [
            ('iron_deficient', 'Iron Deficiency', 'iron'),
            ('protein_deficient', 'Protein Deficiency', 'protein'),
            ('calcium_deficient', 'Calcium Deficiency', 'calcium'),
            ('vitD_deficient', 'Vitamin D Deficiency', 'vitaminD'),
            ('vitB12_deficient', 'Vitamin B12 Deficiency', 'vitaminB12'),
            ('vitC_deficient', 'Vitamin C Deficiency', 'vitaminC'),
        ]

        risk_queries = [
            ('diabetes_risk_high', 'Type 2 Diabetes Risk'),
            ('bp_risk_high', 'Hypertension Risk'),
            ('anaemia_risk_high', 'Anaemia Risk'),
            ('osteoporosis_risk', 'Osteoporosis Risk'),
            ('metabolic_syndrome_risk', 'Metabolic Syndrome Risk'),
        ]

        try:
            for predicate, name, nutrient in deficiency_queries:
                results = list(self.prolog.query(f"{predicate}('{user_atom}')"))
                if results:
                    deficiencies.append({'type': predicate, 'name': name, 'nutrient': nutrient})

            for predicate, name in risk_queries:
                results = list(self.prolog.query(f"{predicate}('{user_atom}')"))
                if results:
                    risks.append({'type': predicate, 'name': name})

        except Exception as e:
            logger.error(f"Prolog query error: {e}")

        return {'deficiencies': deficiencies, 'risks': risks}

    def query_food_recommendations(self, deficiency_type: str, max_price: float = 20.0) -> list:
        """
        Query Prolog for food recommendations to fix a deficiency.

        Args:
            deficiency_type: e.g. 'iron', 'protein', 'calcium'
            max_price: maximum price per 100g in INR

        Returns:
            list of food atom strings
        """
        if not self._loaded:
            return []

        predicate_map = {
            'iron': 'recommend_for_iron',
            'protein': 'recommend_for_protein',
            'calcium': 'recommend_for_calcium',
            'vitaminC': 'recommend_for_vitC',
            'vitaminB12': 'recommend_for_vitB12',
            'vitaminD': 'recommend_for_vitD',
        }

        predicate = predicate_map.get(deficiency_type)
        if not predicate:
            return []

        try:
            results = list(self.prolog.query(f"{predicate}(Food), budget_friendly(Food, {max_price})"))
            return [r['Food'] for r in results[:10]]
        except Exception as e:
            logger.error(f"Prolog recommendation query error: {e}")
            return []

    def query_affordable_alternatives(self, food_name: str) -> list:
        """
        Query Prolog for affordable alternatives to a given food.

        Args:
            food_name: food name string

        Returns:
            list of alternative food atom strings
        """
        if not self._loaded:
            return []

        atom = self._safe_atom(food_name)
        try:
            results = list(self.prolog.query(f"affordable_alternative('{atom}', Alt)"))
            return [r['Alt'] for r in results[:5]]
        except Exception as e:
            logger.error(f"Prolog alternative query error: {e}")
            return []

    def _fallback_deficiencies(self) -> dict:
        """Return empty result when Prolog is unavailable."""
        return {'deficiencies': [], 'risks': []}
