"""
NutriSense Backward Chaining Engine
backward_chaining.py

Experiment 6: Backward Chaining (Goal-Driven Reasoning)

Built completely from scratch — no AI libraries used.
Implements the classic backward chaining algorithm:
  1. Start with a GOAL (e.g., "why does user have anaemia risk?")
  2. Find rules whose CONCLUSION matches the goal
  3. Recursively try to prove each CONDITION of that rule
  4. Continue until base facts are reached or goal is disproved

This is used to:
  - Explain WHY a user has a deficiency (trace back to missing foods)
  - Explain WHAT to eat to fix a deficiency (goal-directed recommendations)
"""


class BackwardChainer:
    """
    Backward Chaining inference engine for nutritional explanation.

    Algorithm: Goal-Driven / Top-Down reasoning
    - Start with a hypothesis/goal
    - Work backwards to find supporting evidence
    - Returns a proof tree showing the reasoning path

    The proof tree is returned to the frontend and displayed
    as an expandable MUI TreeView component.
    """

    def __init__(self, knowledge_base: dict):
        """
        Initialize the backward chainer.

        Args:
            knowledge_base: dict with:
                - 'facts': dict of known facts (user's nutrition data)
                - 'rules': list of rule dicts (same format as ForwardChainer)
        """
        self.facts = knowledge_base.get('facts', {})
        self.rules = knowledge_base.get('rules', [])
        self.max_depth = 10  # Prevent infinite recursion
        self.proof_steps = []  # Ordered list of proof steps for timeline display

    def solve(self, goal: str) -> dict:
        """
        Main entry point: try to prove or disprove a goal.

        Args:
            goal: string name of the fact to prove (e.g., 'anaemia_risk')

        Returns:
            dict with:
                - 'goal': the original goal
                - 'proved': bool — was the goal proved?
                - 'proof_tree': nested dict showing the proof
                - 'proof_steps': ordered list for timeline display
                - 'explanation': human-readable summary
        """
        self.proof_steps = []
        proof_tree = self._prove(goal, depth=0, path=[])

        return {
            'goal': goal,
            'proved': proof_tree.get('proved', False),
            'proof_tree': proof_tree,
            'proof_steps': self.proof_steps,
            'explanation': self._generate_explanation(goal, proof_tree)
        }

    def _prove(self, goal: str, depth: int, path: list) -> dict:
        """
        Recursively prove a goal using backward chaining.

        Args:
            goal: the fact/conclusion to prove
            depth: current recursion depth (for depth limiting)
            path: list of goals already being proved (cycle detection)

        Returns:
            dict representing a node in the proof tree
        """
        # Depth limit check
        if depth > self.max_depth:
            return {
                'goal': goal,
                'proved': False,
                'reason': 'depth_limit_reached',
                'children': []
            }

        # Cycle detection
        if goal in path:
            return {
                'goal': goal,
                'proved': False,
                'reason': 'circular_dependency',
                'children': []
            }

        # BASE CASE: Check if goal is directly in known facts
        if goal in self.facts:
            fact_value = self.facts[goal]
            is_true = bool(fact_value) and fact_value is not False

            step = {
                'step': len(self.proof_steps) + 1,
                'type': 'fact',
                'goal': goal,
                'proved': is_true,
                'value': fact_value,
                'reason': f'Known fact: {goal} = {fact_value}'
            }
            self.proof_steps.append(step)

            return {
                'goal': goal,
                'proved': is_true,
                'type': 'fact',
                'value': fact_value,
                'reason': f'Direct fact: {goal} = {fact_value}',
                'children': []
            }

        # RECURSIVE CASE: Find rules that can prove this goal
        applicable_rules = [r for r in self.rules if r.get('conclusion') == goal]

        if not applicable_rules:
            # No rules can prove this goal and it's not a known fact
            step = {
                'step': len(self.proof_steps) + 1,
                'type': 'unknown',
                'goal': goal,
                'proved': False,
                'reason': f'No rules or facts can prove: {goal}'
            }
            self.proof_steps.append(step)

            return {
                'goal': goal,
                'proved': False,
                'type': 'unknown',
                'reason': f'No rules found to prove: {goal}',
                'children': []
            }

        # Try each applicable rule (OR logic between rules)
        for rule in applicable_rules:
            rule_result = self._try_rule(rule, depth, path + [goal])

            if rule_result['proved']:
                # Rule succeeded — goal is proved
                step = {
                    'step': len(self.proof_steps) + 1,
                    'type': 'rule_success',
                    'goal': goal,
                    'proved': True,
                    'rule_id': rule.get('id'),
                    'rule_name': rule.get('name', rule.get('id')),
                    'explanation': rule.get('explanation', '')
                }
                self.proof_steps.append(step)

                return {
                    'goal': goal,
                    'proved': True,
                    'type': 'rule',
                    'rule_id': rule.get('id'),
                    'rule_name': rule.get('name', rule.get('id')),
                    'explanation': rule.get('explanation', ''),
                    'nutrient': rule.get('nutrient', ''),
                    'severity': rule.get('severity', 'moderate'),
                    'children': rule_result['children']
                }

        # No rule could prove the goal
        return {
            'goal': goal,
            'proved': False,
            'type': 'failed',
            'reason': f'All rules failed to prove: {goal}',
            'children': []
        }

    def _try_rule(self, rule: dict, depth: int, path: list) -> dict:
        """
        Try to prove all conditions of a rule (AND logic).
        All conditions must be provable for the rule to succeed.

        Args:
            rule: rule dict with 'conditions' list
            depth: current recursion depth
            path: current proof path for cycle detection

        Returns:
            dict with 'proved' bool and 'children' list
        """
        conditions = rule.get('conditions', [])
        children = []
        all_proved = True

        for condition in conditions:
            fact_key = condition.get('fact')
            op = condition.get('op')
            threshold = condition.get('value')

            # Try to prove this condition
            condition_result = self._prove_condition(fact_key, op, threshold, depth + 1, path)
            children.append(condition_result)

            if not condition_result.get('proved', False):
                all_proved = False
                # Don't break — continue to show all failed conditions in tree

        return {
            'proved': all_proved,
            'children': children
        }

    def _prove_condition(self, fact_key: str, op: str, threshold, depth: int, path: list) -> dict:
        """
        Prove a specific condition (fact_key op threshold).
        First checks known facts, then tries to derive via rules.

        Args:
            fact_key: the fact to check
            op: comparison operator
            threshold: the value to compare against
            depth: recursion depth
            path: proof path

        Returns:
            dict with proof result
        """
        current_value = self.facts.get(fact_key)

        if current_value is not None:
            # Evaluate the condition directly
            proved = self._evaluate(current_value, op, threshold)
            return {
                'goal': f'{fact_key} {op} {threshold}',
                'proved': proved,
                'type': 'condition',
                'fact': fact_key,
                'actual_value': current_value,
                'operator': op,
                'threshold': threshold,
                'reason': f'{fact_key} = {current_value} (need {op} {threshold})',
                'children': []
            }

        # Try to derive the fact via backward chaining
        sub_proof = self._prove(fact_key, depth, path)

        if sub_proof.get('proved'):
            derived_value = self.facts.get(fact_key)
            if derived_value is not None:
                proved = self._evaluate(derived_value, op, threshold)
                return {
                    'goal': f'{fact_key} {op} {threshold}',
                    'proved': proved,
                    'type': 'derived_condition',
                    'fact': fact_key,
                    'actual_value': derived_value,
                    'operator': op,
                    'threshold': threshold,
                    'children': [sub_proof]
                }

        return {
            'goal': f'{fact_key} {op} {threshold}',
            'proved': False,
            'type': 'unknown_condition',
            'fact': fact_key,
            'reason': f'Cannot determine value of {fact_key}',
            'children': []
        }

    def _evaluate(self, value, op: str, threshold) -> bool:
        """Evaluate a comparison expression."""
        try:
            if op == '<':
                return float(value) < float(threshold)
            elif op == '>':
                return float(value) > float(threshold)
            elif op == '<=':
                return float(value) <= float(threshold)
            elif op == '>=':
                return float(value) >= float(threshold)
            elif op == '==':
                return value == threshold
            elif op == '!=':
                return value != threshold
        except (TypeError, ValueError):
            return value == threshold
        return False

    def _generate_explanation(self, goal: str, proof_tree: dict) -> str:
        """
        Generate a human-readable explanation of the proof result.

        Args:
            goal: the goal that was proved/disproved
            proof_tree: the proof tree dict

        Returns:
            str: human-readable explanation
        """
        goal_names = {
            'anaemia_risk': 'Anaemia Risk',
            'diabetes_risk': 'Diabetes Risk',
            'bp_risk': 'Blood Pressure Risk',
            'osteoporosis_risk': 'Osteoporosis Risk',
            'iron_deficiency': 'Iron Deficiency',
            'protein_deficiency': 'Protein Deficiency',
            'calcium_deficiency': 'Calcium Deficiency',
            'vitD_deficiency': 'Vitamin D Deficiency',
            'vitB12_deficiency': 'Vitamin B12 Deficiency',
        }

        goal_display = goal_names.get(goal, goal.replace('_', ' ').title())

        if proof_tree.get('proved'):
            rule_name = proof_tree.get('rule_name', '')
            explanation = proof_tree.get('explanation', '')
            return (f"{goal_display} was CONFIRMED. "
                    f"Rule applied: '{rule_name}'. {explanation}")
        else:
            return (f"{goal_display} could NOT be confirmed based on current nutrition data. "
                    f"This may mean the condition is not present or data is insufficient.")


def build_bc_knowledge_base(facts: dict, rules: list) -> dict:
    """
    Build the knowledge base dict for BackwardChainer.

    Args:
        facts: current user nutrition facts
        rules: list of rules from build_nutrition_rules()

    Returns:
        dict suitable for BackwardChainer constructor
    """
    return {
        'facts': facts,
        'rules': rules
    }
