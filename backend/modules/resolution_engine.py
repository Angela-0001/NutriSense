"""
NutriSense Resolution Engine
resolution_engine.py

Experiment 7: Resolution Refutation (Proof by Contradiction)

Built completely from scratch — no AI libraries used.
Implements the Resolution Principle for logical inference:
  1. Convert claim to clausal (CNF) form
  2. Negate the claim
  3. Add negated claim to knowledge base
  4. Apply resolution rule repeatedly
  5. If empty clause derived → original claim is VALID (contradiction found)
  6. If no empty clause → claim is INVALID or UNKNOWN

Used in the ClaimValidator page to verify user claims about their diet.
"""


class ResolutionEngine:
    """
    Resolution-based theorem prover for dietary claim validation.

    The Resolution Principle:
        Given clauses C1 = {A, ...} and C2 = {¬A, ...}
        We can resolve them to produce: {... (rest of C1 and C2)}
        If the result is the empty clause {}, a contradiction is found.

    This implements proof by refutation:
        To prove claim P, we assume ¬P and try to derive a contradiction.
        If contradiction found → P is TRUE.
        If no contradiction → P cannot be proved from current knowledge.
    """

    def __init__(self):
        """Initialize the resolution engine."""
        self.resolution_steps = []  # Audit trail of resolution steps

    def convert_to_clausal_form(self, statement: str, facts: dict) -> list:
        """
        Convert a natural language dietary claim to logical clauses.
        Each clause is a frozenset of literals (positive or negative strings).

        A literal 'iron_ok' means iron is adequate.
        A literal '~iron_ok' means iron is NOT adequate (negation).

        Args:
            statement: one of the predefined claim keys (e.g. 'iron_adequate')
            facts: user's current nutrition facts dict

        Returns:
            list of frozensets (clauses in CNF)
        """
        clauses = []

        # Map claim statements to their logical clauses based on facts
        claim_map = {
            'iron_adequate': self._iron_adequate_clauses(facts),
            'protein_adequate': self._protein_adequate_clauses(facts),
            'calcium_adequate': self._calcium_adequate_clauses(facts),
            'vitD_adequate': self._vitD_adequate_clauses(facts),
            'vitB12_adequate': self._vitB12_adequate_clauses(facts),
            'fibre_adequate': self._fibre_adequate_clauses(facts),
            'diet_balanced': self._diet_balanced_clauses(facts),
            'diabetes_safe': self._diabetes_safe_clauses(facts),
            'bp_safe': self._bp_safe_clauses(facts),
        }

        clauses = claim_map.get(statement, [])
        return clauses

    # ── CLAIM CLAUSE BUILDERS ──────────────────────────────────────────

    def _iron_adequate_clauses(self, facts: dict) -> list:
        iron = facts.get('iron_intake', 0)
        rda = facts.get('rda_iron', 21)
        if iron >= rda:
            return [frozenset(['iron_ok'])]
        else:
            return [frozenset(['~iron_ok'])]

    def _protein_adequate_clauses(self, facts: dict) -> list:
        protein = facts.get('protein_intake', 0)
        rda = facts.get('rda_protein', 55)
        if protein >= rda:
            return [frozenset(['protein_ok'])]
        else:
            return [frozenset(['~protein_ok'])]

    def _calcium_adequate_clauses(self, facts: dict) -> list:
        calcium = facts.get('calcium_intake', 0)
        rda = facts.get('rda_calcium', 600)
        if calcium >= rda:
            return [frozenset(['calcium_ok'])]
        else:
            return [frozenset(['~calcium_ok'])]

    def _vitD_adequate_clauses(self, facts: dict) -> list:
        vitD = facts.get('vitD_intake', 0)
        rda = facts.get('rda_vitD', 10)
        if vitD >= rda:
            return [frozenset(['vitD_ok'])]
        else:
            return [frozenset(['~vitD_ok'])]

    def _vitB12_adequate_clauses(self, facts: dict) -> list:
        vitB12 = facts.get('vitB12_intake', 0)
        rda = facts.get('rda_vitB12', 1.0)
        if vitB12 >= rda:
            return [frozenset(['vitB12_ok'])]
        else:
            return [frozenset(['~vitB12_ok'])]

    def _fibre_adequate_clauses(self, facts: dict) -> list:
        fibre = facts.get('fibre_intake', 0)
        rda = facts.get('rda_fibre', 35)
        if fibre >= rda:
            return [frozenset(['fibre_ok'])]
        else:
            return [frozenset(['~fibre_ok'])]

    def _diet_balanced_clauses(self, facts: dict) -> list:
        """Diet is balanced if protein, iron, and fibre are all adequate."""
        protein_ok = facts.get('protein_intake', 0) >= facts.get('rda_protein', 55)
        iron_ok = facts.get('iron_intake', 0) >= facts.get('rda_iron', 21)
        fibre_ok = facts.get('fibre_intake', 0) >= facts.get('rda_fibre', 35)

        clauses = []
        if protein_ok:
            clauses.append(frozenset(['protein_ok']))
        else:
            clauses.append(frozenset(['~protein_ok']))
        if iron_ok:
            clauses.append(frozenset(['iron_ok']))
        else:
            clauses.append(frozenset(['~iron_ok']))
        if fibre_ok:
            clauses.append(frozenset(['fibre_ok']))
        else:
            clauses.append(frozenset(['~fibre_ok']))

        # diet_balanced requires all three
        # diet_balanced ← protein_ok ∧ iron_ok ∧ fibre_ok
        # In CNF: {~protein_ok, ~iron_ok, ~fibre_ok, diet_balanced}
        clauses.append(frozenset(['~protein_ok', '~iron_ok', '~fibre_ok', 'diet_balanced']))
        return clauses

    def _diabetes_safe_clauses(self, facts: dict) -> list:
        sugar_ok = facts.get('sugar_intake', 0) <= 50
        fibre_ok = facts.get('fibre_intake', 0) >= 15
        clauses = []
        clauses.append(frozenset(['sugar_ok']) if sugar_ok else frozenset(['~sugar_ok']))
        clauses.append(frozenset(['fibre_ok']) if fibre_ok else frozenset(['~fibre_ok']))
        clauses.append(frozenset(['~sugar_ok', 'fibre_ok', 'diabetes_safe']))
        return clauses

    def _bp_safe_clauses(self, facts: dict) -> list:
        salt_ok = facts.get('salt_intake', 0) <= 5000
        fat_ok = facts.get('fat_intake', 0) <= 70
        clauses = []
        clauses.append(frozenset(['salt_ok']) if salt_ok else frozenset(['~salt_ok']))
        clauses.append(frozenset(['fat_ok']) if fat_ok else frozenset(['~fat_ok']))
        clauses.append(frozenset(['~salt_ok', '~fat_ok', 'bp_safe']))
        return clauses

    # ── CORE RESOLUTION ALGORITHM ──────────────────────────────────────

    def resolve(self, clause1: frozenset, clause2: frozenset):
        """
        Apply the resolution rule to two clauses.
        Finds a complementary literal pair and resolves.

        Args:
            clause1: frozenset of literals
            clause2: frozenset of literals

        Returns:
            frozenset (resolvent) or None if no resolution possible
        """
        for literal in clause1:
            # Check if negation of this literal is in clause2
            negated = literal[1:] if literal.startswith('~') else f'~{literal}'
            if negated in clause2:
                # Resolve: remove the complementary pair, union the rest
                resolvent = (clause1 - {literal}) | (clause2 - {negated})
                return frozenset(resolvent)
        return None  # No complementary pair found

    def refute(self, kb_clauses: list, negated_goal_clauses: list) -> dict:
        """
        Attempt to derive the empty clause (contradiction) by resolution.

        Args:
            kb_clauses: list of frozensets (knowledge base in CNF)
            negated_goal_clauses: list of frozensets (negated claim)

        Returns:
            dict with 'refuted' bool and 'steps' list
        """
        self.resolution_steps = []
        all_clauses = list(set(kb_clauses + negated_goal_clauses))
        max_steps = 100

        step = 0
        while step < max_steps:
            new_clauses = []
            n = len(all_clauses)

            for i in range(n):
                for j in range(i + 1, n):
                    resolvent = self.resolve(all_clauses[i], all_clauses[j])

                    if resolvent is None:
                        continue

                    step_record = {
                        'step': len(self.resolution_steps) + 1,
                        'clause1': sorted(all_clauses[i]),
                        'clause2': sorted(all_clauses[j]),
                        'resolvent': sorted(resolvent),
                        'is_empty': len(resolvent) == 0
                    }
                    self.resolution_steps.append(step_record)

                    if len(resolvent) == 0:
                        # Empty clause derived → contradiction found → claim is TRUE
                        return {
                            'refuted': True,
                            'steps': self.resolution_steps
                        }

                    if resolvent not in all_clauses:
                        new_clauses.append(resolvent)

            if not new_clauses:
                # Fixed point — no new clauses can be derived
                break

            all_clauses.extend(new_clauses)
            step += 1

        return {
            'refuted': False,
            'steps': self.resolution_steps
        }

    def validate_claim(self, claim: str, facts: dict, rda: dict) -> dict:
        """
        Main entry point: validate a dietary claim using resolution refutation.

        Args:
            claim: claim key string (e.g. 'iron_adequate')
            facts: user's nutrition facts dict
            rda: user's ICMR RDA values

        Returns:
            dict with validation result and proof steps
        """
        # Merge RDA into facts for clause builders
        enriched_facts = {**facts}
        enriched_facts['rda_iron'] = rda.get('iron', 21)
        enriched_facts['rda_protein'] = rda.get('protein', 55)
        enriched_facts['rda_calcium'] = rda.get('calcium', 600)
        enriched_facts['rda_vitD'] = rda.get('vitaminD', 10)
        enriched_facts['rda_vitB12'] = rda.get('vitaminB12', 1.0)
        enriched_facts['rda_fibre'] = rda.get('fibre', 35)

        # Step 1: Convert claim to clausal form (KB)
        kb_clauses = self.convert_to_clausal_form(claim, enriched_facts)

        if not kb_clauses:
            return {
                'claim': claim,
                'valid': False,
                'reason': 'Unknown claim type',
                'steps': [],
                'explanation': f'Claim "{claim}" is not recognized.'
            }

        # Step 2: Negate the claim goal literal
        goal_literal = claim  # e.g. 'iron_adequate' → we want to prove this
        # Map claim key to its conclusion literal
        claim_to_literal = {
            'iron_adequate': 'iron_ok',
            'protein_adequate': 'protein_ok',
            'calcium_adequate': 'calcium_ok',
            'vitD_adequate': 'vitD_ok',
            'vitB12_adequate': 'vitB12_ok',
            'fibre_adequate': 'fibre_ok',
            'diet_balanced': 'diet_balanced',
            'diabetes_safe': 'diabetes_safe',
            'bp_safe': 'bp_safe',
        }
        conclusion_literal = claim_to_literal.get(claim, claim)
        negated_goal = [frozenset([f'~{conclusion_literal}'])]

        # Step 3: Run resolution refutation
        result = self.refute(kb_clauses, negated_goal)

        # Step 4: Build human-readable explanation
        claim_labels = {
            'iron_adequate': 'Iron intake is adequate',
            'protein_adequate': 'Protein intake is adequate',
            'calcium_adequate': 'Calcium intake is adequate',
            'vitD_adequate': 'Vitamin D intake is adequate',
            'vitB12_adequate': 'Vitamin B12 intake is adequate',
            'fibre_adequate': 'Dietary fibre intake is adequate',
            'diet_balanced': 'Overall diet is balanced',
            'diabetes_safe': 'Diet is safe for diabetes risk',
            'bp_safe': 'Diet is safe for blood pressure risk',
        }
        label = claim_labels.get(claim, claim)

        if result['refuted']:
            explanation = (
                f'VALID: "{label}" is TRUE. '
                f'Resolution refutation derived a contradiction in '
                f'{len(result["steps"])} step(s), proving the claim holds.'
            )
        else:
            explanation = (
                f'INVALID: "{label}" cannot be proved. '
                f'No contradiction was derived after {len(result["steps"])} resolution step(s). '
                f'The claim does not hold based on current nutrition data.'
            )

        return {
            'claim': claim,
            'claim_label': label,
            'valid': result['refuted'],
            'steps': result['steps'],
            'explanation': explanation,
            'kb_clauses': [sorted(c) for c in kb_clauses],
            'negated_goal': [sorted(c) for c in negated_goal],
        }


# ── AVAILABLE CLAIMS ───────────────────────────────────────────────────────────

AVAILABLE_CLAIMS = [
    {'key': 'iron_adequate',    'label': 'My iron intake is adequate',         'nutrient': 'iron'},
    {'key': 'protein_adequate', 'label': 'My protein intake is adequate',      'nutrient': 'protein'},
    {'key': 'calcium_adequate', 'label': 'My calcium intake is adequate',      'nutrient': 'calcium'},
    {'key': 'vitD_adequate',    'label': 'My vitamin D intake is adequate',    'nutrient': 'vitaminD'},
    {'key': 'vitB12_adequate',  'label': 'My vitamin B12 intake is adequate',  'nutrient': 'vitaminB12'},
    {'key': 'fibre_adequate',   'label': 'My fibre intake is adequate',        'nutrient': 'fibre'},
    {'key': 'diet_balanced',    'label': 'My overall diet is balanced',        'nutrient': 'overall'},
    {'key': 'diabetes_safe',    'label': 'My diet is safe for diabetes risk',  'nutrient': 'sugar'},
    {'key': 'bp_safe',          'label': 'My diet is safe for blood pressure', 'nutrient': 'sodium'},
]
