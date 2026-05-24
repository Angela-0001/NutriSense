"""
NutriSense Forward Chaining Engine
forward_chaining.py

Experiment 2: Forward Chaining (Data-Driven Reasoning)

Built completely from scratch — no AI libraries used.
Implements the classic forward chaining algorithm:
  1. Start with known facts (user's nutrition data)
  2. Match facts against rule conditions (antecedents)
  3. Fire matching rules to derive new facts (consequents)
  4. Repeat until no new facts can be derived (fixed point)

This is used to detect nutritional deficiencies and disease risks
from the user's daily food log data.
"""


class ForwardChainer:
    """
    Forward Chaining inference engine for nutritional deficiency detection.

    Algorithm: Data-Driven / Bottom-Up reasoning
    - Start with observed facts (nutrition intake values)
    - Apply rules to derive conclusions (deficiencies, risks)
    - Continue until no new conclusions can be drawn

    Each rule has the form:
        IF condition1 AND condition2 AND ... THEN conclusion
    """

    def __init__(self, facts: dict, rules: list):
        """
        Initialize the forward chainer.

        Args:
            facts: dict of known facts, e.g. {'iron_intake': 8.5, 'gender': 'female'}
            rules: list of rule dicts, each with:
                   - 'id': unique rule identifier
                   - 'conditions': list of condition functions or dicts
                   - 'conclusion': str key to add to facts
                   - 'conclusion_value': value to set for conclusion
                   - 'explanation': human-readable explanation of the rule
                   - 'nutrient': which nutrient this rule relates to
        """
        self.facts = dict(facts)  # Working memory — copy to avoid mutating input
        self.rules = rules
        self.reasoning_chain = []  # Audit trail of all rule firings
        self.fired_rules = set()   # Track which rules have already fired

    def _evaluate_condition(self, condition: dict) -> bool:
        """
        Evaluate a single condition against current facts.

        Condition format:
            {'fact': 'iron_intake', 'op': '<', 'value': 17}
            {'fact': 'gender', 'op': '==', 'value': 'female'}
            {'fact': 'iron_deficiency', 'op': '==', 'value': True}

        Args:
            condition: dict describing the condition to check

        Returns:
            bool: True if condition is satisfied
        """
        fact_key = condition.get('fact')
        op = condition.get('op')
        threshold = condition.get('value')

        # Get current value from working memory
        current_value = self.facts.get(fact_key)

        if current_value is None:
            return False  # Fact not known → condition fails

        try:
            if op == '<':
                return float(current_value) < float(threshold)
            elif op == '>':
                return float(current_value) > float(threshold)
            elif op == '<=':
                return float(current_value) <= float(threshold)
            elif op == '>=':
                return float(current_value) >= float(threshold)
            elif op == '==':
                return current_value == threshold
            elif op == '!=':
                return current_value != threshold
            else:
                return False
        except (TypeError, ValueError):
            return False

    def _check_rule(self, rule: dict) -> bool:
        """
        Check if ALL conditions of a rule are satisfied (AND logic).

        Args:
            rule: rule dict with 'conditions' list

        Returns:
            bool: True if all conditions are met
        """
        conditions = rule.get('conditions', [])
        if not conditions:
            return False

        for condition in conditions:
            if not self._evaluate_condition(condition):
                return False  # Short-circuit: one false → rule fails

        return True  # All conditions satisfied

    def run(self) -> dict:
        """
        Execute the forward chaining algorithm until fixed point.

        Fixed point = no new facts can be derived in a full pass.
        This is the classic forward chaining loop.

        Returns:
            dict with:
                - 'derived_facts': all facts after inference
                - 'reasoning_chain': list of rule firing events
                - 'deficiencies': list of detected deficiencies
                - 'risks': list of detected disease risks
        """
        iteration = 0
        max_iterations = 50  # Safety limit to prevent infinite loops

        while iteration < max_iterations:
            new_fact_derived = False
            iteration += 1

            for rule in self.rules:
                rule_id = rule.get('id')

                # Skip already-fired rules (each rule fires at most once)
                if rule_id in self.fired_rules:
                    continue

                # Check if all conditions are satisfied
                if self._check_rule(rule):
                    # FIRE the rule — add conclusion to working memory
                    conclusion_key = rule.get('conclusion')
                    conclusion_value = rule.get('conclusion_value', True)

                    # Only count as new if fact wasn't already known
                    if self.facts.get(conclusion_key) != conclusion_value:
                        self.facts[conclusion_key] = conclusion_value
                        new_fact_derived = True

                    self.fired_rules.add(rule_id)

                    # Record this rule firing in the reasoning chain
                    firing_record = {
                        'step': len(self.reasoning_chain) + 1,
                        'rule_id': rule_id,
                        'rule_name': rule.get('name', rule_id),
                        'conditions_matched': [
                            {
                                'fact': c['fact'],
                                'op': c['op'],
                                'threshold': c['value'],
                                'actual_value': self.facts.get(c['fact'])
                            }
                            for c in rule.get('conditions', [])
                        ],
                        'conclusion': conclusion_key,
                        'conclusion_value': conclusion_value,
                        'explanation': rule.get('explanation', ''),
                        'nutrient': rule.get('nutrient', ''),
                        'severity': rule.get('severity', 'moderate'),
                        'iteration': iteration
                    }
                    self.reasoning_chain.append(firing_record)

            # Fixed point reached — no new facts derived in this pass
            if not new_fact_derived:
                break

        # Collect deficiencies and risks from derived facts
        deficiencies = self._extract_deficiencies()
        risks = self._extract_risks()

        return {
            'derived_facts': self.facts,
            'reasoning_chain': self.reasoning_chain,
            'deficiencies': deficiencies,
            'risks': risks,
            'iterations': iteration,
            'rules_fired': len(self.fired_rules)
        }

    def _extract_deficiencies(self) -> list:
        """Extract deficiency conclusions from derived facts."""
        deficiency_keys = {
            'iron_deficiency': {
                'name': 'Iron Deficiency',
                'nutrient': 'iron',
                'health_impact': 'Can lead to anaemia, fatigue, and impaired immune function.',
                'foods': ['Spinach', 'Methi', 'Masoor dal', 'Bajra', 'Til (sesame seeds)', 'Drumstick leaves (moringa)']
            },
            'protein_deficiency': {
                'name': 'Protein Deficiency',
                'nutrient': 'protein',
                'health_impact': 'Can cause muscle loss, poor immunity, and slow wound healing.',
                'foods': ['Moong dal', 'Soyabean', 'Paneer', 'Groundnuts (peanuts)', 'Rajma (kidney beans)', 'Chana dal']
            },
            'calcium_deficiency': {
                'name': 'Calcium Deficiency',
                'nutrient': 'calcium',
                'health_impact': 'Weakens bones and teeth, increases osteoporosis risk.',
                'foods': ['Milk (cow full fat)', 'Paneer', 'Curd (yogurt)', 'Ragi (finger millet)', 'Til (sesame seeds)', 'Drumstick leaves (moringa)']
            },
            'vitD_deficiency': {
                'name': 'Vitamin D Deficiency',
                'nutrient': 'vitaminD',
                'health_impact': 'Impairs calcium absorption, weakens bones, affects mood.',
                'foods': ['Egg (whole)', 'Sardines (canned)', 'Mackerel', 'Milk (cow full fat)', 'Mushrooms']
            },
            'vitB12_deficiency': {
                'name': 'Vitamin B12 Deficiency',
                'nutrient': 'vitaminB12',
                'health_impact': 'Causes neurological damage, megaloblastic anaemia, fatigue.',
                'foods': ['Egg (whole)', 'Milk (cow full fat)', 'Curd (yogurt)', 'Paneer', 'Fish Rohu', 'Sardines (canned)']
            },
            'fibre_deficiency': {
                'name': 'Dietary Fibre Deficiency',
                'nutrient': 'fibre',
                'health_impact': 'Increases constipation risk, poor gut health, higher diabetes risk.',
                'foods': ['Rajma (kidney beans)', 'Oats', 'Flaxseeds', 'Moong sprouts', 'Broccoli', 'Guava']
            }
        }

        result = []
        for key, info in deficiency_keys.items():
            if self.facts.get(key):
                severity = self.facts.get(f'{key}_severity', 'moderate')
                result.append({
                    'type': key,
                    'name': info['name'],
                    'nutrient': info['nutrient'],
                    'severity': severity,
                    'health_impact': info['health_impact'],
                    'recommended_foods': info['foods'],
                    'current_value': self.facts.get(f"{info['nutrient']}_intake", 0),
                    'rda_value': self.facts.get(f"rda_{info['nutrient']}", 0)
                })
        return result

    def _extract_risks(self) -> list:
        """Extract disease risk conclusions from derived facts."""
        risk_keys = {
            'diabetes_risk': {
                'name': 'Type 2 Diabetes',
                'description': 'High sugar intake combined with low fibre increases insulin resistance risk.',
                'dietary_changes': ['Reduce refined carbs and sugar', 'Increase fibre intake', 'Add bitter gourd to diet']
            },
            'bp_risk': {
                'name': 'Hypertension (High BP)',
                'description': 'High salt and fat intake strains the cardiovascular system.',
                'dietary_changes': ['Reduce salt intake', 'Limit fried foods', 'Increase potassium-rich foods']
            },
            'anaemia_risk': {
                'name': 'Anaemia',
                'description': 'Combined iron and B12 deficiency leads to reduced red blood cell production.',
                'dietary_changes': ['Eat iron-rich foods with vitamin C', 'Include dairy or eggs for B12']
            },
            'osteoporosis_risk': {
                'name': 'Osteoporosis',
                'description': 'Low calcium and vitamin D weakens bone density over time.',
                'dietary_changes': ['Increase dairy intake', 'Get morning sunlight', 'Add ragi to diet']
            }
        }

        result = []
        for key, info in risk_keys.items():
            if self.facts.get(key):
                result.append({
                    'type': key,
                    'name': info['name'],
                    'level': self.facts.get(f'{key}_level', 'elevated'),
                    'description': info['description'],
                    'dietary_changes': info['dietary_changes']
                })
        return result


def build_nutrition_rules(rda: dict, confidence_discount: float = 0.0) -> list:
    """
    Build the complete set of forward chaining rules for nutritional analysis.
    Rules are based on ICMR guidelines and established medical research.

    Args:
        rda: dict of ICMR RDA values for the user's demographic
        confidence_discount: float 0.0-1.0 — applied when AI-estimated foods are in the log.
                             0.15 = thresholds relaxed by 15% to avoid false positives.

    Returns:
        list of rule dicts for ForwardChainer
    """
    # Apply confidence discount — relax thresholds so AI-estimated foods
    # don't trigger false deficiency alerts
    discount = max(0.0, min(confidence_discount, 0.5))

    iron_rda    = rda.get('iron', 21)    * (1 - discount)
    protein_rda = rda.get('protein', 55) * (1 - discount)
    calcium_rda = rda.get('calcium', 600)* (1 - discount)
    vitD_rda    = rda.get('vitaminD', 10)* (1 - discount)
    vitB12_rda  = rda.get('vitaminB12', 1.0) * (1 - discount)
    vitC_rda    = rda.get('vitaminC', 40)* (1 - discount)
    fibre_rda   = rda.get('fibre', 35)   * (1 - discount)

    rules = [
        # ── IRON DEFICIENCY RULES ──────────────────────────────────────
        {
            'id': 'R01',
            'name': 'Iron Deficiency (Female)',
            'conditions': [
                {'fact': 'iron_intake', 'op': '<', 'value': iron_rda},
                {'fact': 'gender', 'op': '==', 'value': 'female'}
            ],
            'conclusion': 'iron_deficiency',
            'conclusion_value': True,
            'explanation': f'Iron intake is below ICMR RDA of {iron_rda}mg/day for females. '
                           'Women need more iron due to menstrual losses.',
            'nutrient': 'iron',
            'severity': 'high'
        },
        {
            'id': 'R01b',
            'name': 'Iron Deficiency (Male)',
            'conditions': [
                {'fact': 'iron_intake', 'op': '<', 'value': iron_rda},
                {'fact': 'gender', 'op': '==', 'value': 'male'}
            ],
            'conclusion': 'iron_deficiency',
            'conclusion_value': True,
            'explanation': f'Iron intake is below ICMR RDA of {iron_rda}mg/day.',
            'nutrient': 'iron',
            'severity': 'moderate'
        },
        {
            'id': 'R01c',
            'name': 'Iron Deficiency Severity',
            'conditions': [
                {'fact': 'iron_intake', 'op': '<', 'value': iron_rda * 0.5}
            ],
            'conclusion': 'iron_deficiency_severity',
            'conclusion_value': 'critical',
            'explanation': f'Iron intake is less than 50% of ICMR RDA ({iron_rda}mg). Critical deficiency.',
            'nutrient': 'iron',
            'severity': 'critical'
        },

        # ── VITAMIN D DEFICIENCY ───────────────────────────────────────
        {
            'id': 'R02',
            'name': 'Vitamin D Deficiency',
            'conditions': [
                {'fact': 'vitD_intake', 'op': '<', 'value': vitD_rda}
            ],
            'conclusion': 'vitD_deficiency',
            'conclusion_value': True,
            'explanation': f'Vitamin D intake is below ICMR RDA of {vitD_rda}mcg/day. '
                           'Most Indians are deficient due to indoor lifestyle.',
            'nutrient': 'vitaminD',
            'severity': 'moderate'
        },

        # ── PROTEIN DEFICIENCY ─────────────────────────────────────────
        {
            'id': 'R03',
            'name': 'Protein Deficiency (Vegetarian)',
            'conditions': [
                {'fact': 'protein_intake', 'op': '<', 'value': protein_rda},
                {'fact': 'diet_type', 'op': '==', 'value': 'veg'}
            ],
            'conclusion': 'protein_deficiency',
            'conclusion_value': True,
            'explanation': f'Protein intake is below ICMR RDA of {protein_rda}g/day. '
                           'Vegetarian diets often lack complete proteins — combine cereals with pulses.',
            'nutrient': 'protein',
            'severity': 'critical'
        },
        {
            'id': 'R03b',
            'name': 'Protein Deficiency (General)',
            'conditions': [
                {'fact': 'protein_intake', 'op': '<', 'value': protein_rda}
            ],
            'conclusion': 'protein_deficiency',
            'conclusion_value': True,
            'explanation': f'Protein intake is below ICMR RDA of {protein_rda}g/day.',
            'nutrient': 'protein',
            'severity': 'moderate'
        },

        # ── CALCIUM DEFICIENCY ─────────────────────────────────────────
        {
            'id': 'R04',
            'name': 'Calcium Deficiency',
            'conditions': [
                {'fact': 'calcium_intake', 'op': '<', 'value': calcium_rda}
            ],
            'conclusion': 'calcium_deficiency',
            'conclusion_value': True,
            'explanation': f'Calcium intake is below ICMR RDA of {calcium_rda}mg/day.',
            'nutrient': 'calcium',
            'severity': 'moderate'
        },

        # ── VITAMIN B12 DEFICIENCY ─────────────────────────────────────
        {
            'id': 'R05',
            'name': 'Vitamin B12 Deficiency',
            'conditions': [
                {'fact': 'vitB12_intake', 'op': '<', 'value': vitB12_rda}
            ],
            'conclusion': 'vitB12_deficiency',
            'conclusion_value': True,
            'explanation': f'Vitamin B12 intake is below ICMR RDA of {vitB12_rda}mcg/day. '
                           'B12 is found almost exclusively in animal products.',
            'nutrient': 'vitaminB12',
            'severity': 'high'
        },

        # ── FIBRE DEFICIENCY ───────────────────────────────────────────
        {
            'id': 'R06',
            'name': 'Dietary Fibre Deficiency',
            'conditions': [
                {'fact': 'fibre_intake', 'op': '<', 'value': fibre_rda}
            ],
            'conclusion': 'fibre_deficiency',
            'conclusion_value': True,
            'explanation': f'Dietary fibre intake is below ICMR recommendation of {fibre_rda}g/day.',
            'nutrient': 'fibre',
            'severity': 'moderate'
        },

        # ── DISEASE RISK RULES ─────────────────────────────────────────
        {
            'id': 'R07',
            'name': 'Diabetes Risk (High Sugar + Low Fibre)',
            'conditions': [
                {'fact': 'sugar_intake', 'op': '>', 'value': 50},
                {'fact': 'fibre_intake', 'op': '<', 'value': 15}
            ],
            'conclusion': 'diabetes_risk',
            'conclusion_value': True,
            'explanation': 'High sugar intake (>50g) combined with low fibre (<15g) significantly '
                           'increases insulin resistance and Type 2 Diabetes risk.',
            'nutrient': 'sugar',
            'severity': 'high'
        },
        {
            'id': 'R08',
            'name': 'Blood Pressure Risk (High Salt + High Fat)',
            'conditions': [
                {'fact': 'salt_intake', 'op': '>', 'value': 5000},  # sodium in mg
                {'fact': 'fat_intake', 'op': '>', 'value': 70}
            ],
            'conclusion': 'bp_risk',
            'conclusion_value': True,
            'explanation': 'High sodium intake (>5000mg) combined with high fat (>70g) '
                           'elevates blood pressure risk.',
            'nutrient': 'sodium',
            'severity': 'high'
        },
        {
            'id': 'R09',
            'name': 'Anaemia Risk (Iron + B12 Deficiency)',
            'conditions': [
                {'fact': 'iron_deficiency', 'op': '==', 'value': True},
                {'fact': 'vitB12_deficiency', 'op': '==', 'value': True}
            ],
            'conclusion': 'anaemia_risk',
            'conclusion_value': True,
            'explanation': 'Combined iron and vitamin B12 deficiency leads to both '
                           'iron-deficiency anaemia and megaloblastic anaemia.',
            'nutrient': 'iron',
            'severity': 'critical'
        },
        {
            'id': 'R10',
            'name': 'Osteoporosis Risk (Calcium + Age)',
            'conditions': [
                {'fact': 'calcium_intake', 'op': '<', 'value': calcium_rda},
                {'fact': 'age', 'op': '>', 'value': 40}
            ],
            'conclusion': 'osteoporosis_risk',
            'conclusion_value': True,
            'explanation': 'Low calcium intake in adults over 40 significantly increases '
                           'osteoporosis risk as bone density naturally decreases with age.',
            'nutrient': 'calcium',
            'severity': 'high'
        },

        # ── ABSORPTION ENHANCEMENT RULES ──────────────────────────────
        {
            'id': 'R11',
            'name': 'Iron Absorption Enhanced by Vitamin C',
            'conditions': [
                {'fact': 'vitC_intake', 'op': '>', 'value': 40},
                {'fact': 'iron_deficiency', 'op': '==', 'value': True}
            ],
            'conclusion': 'iron_absorption_enhanced',
            'conclusion_value': True,
            'explanation': 'Adequate vitamin C (>40mg) enhances non-heme iron absorption '
                           'by up to 3x. This partially mitigates iron deficiency severity.',
            'nutrient': 'vitaminC',
            'severity': 'positive'
        },
        {
            'id': 'R12',
            'name': 'Calcium Absorption Enhanced by Vitamin D',
            'conditions': [
                {'fact': 'vitD_intake', 'op': '>', 'value': 5},
                {'fact': 'calcium_deficiency', 'op': '==', 'value': True}
            ],
            'conclusion': 'calcium_absorption_enhanced',
            'conclusion_value': True,
            'explanation': 'Adequate vitamin D (>5mcg) enhances calcium absorption in the gut.',
            'nutrient': 'vitaminD',
            'severity': 'positive'
        },
    ]

    return rules
