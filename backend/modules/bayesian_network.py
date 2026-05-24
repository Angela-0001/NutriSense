"""
NutriSense Bayesian Network Module
bayesian_network.py

Experiment 11: Bayesian Network for Disease Risk Prediction

Uses pgmpy library to build a Bayesian Network with:
- Conditional Probability Tables (CPTs) based on medical research
- BeliefPropagation for exact inference
- Evidence from user's nutrition data

Network structure models probabilistic relationships between
dietary factors and disease risks.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import pgmpy — graceful fallback if not installed
try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import BeliefPropagation, VariableElimination
    PGMPY_AVAILABLE = True
except Exception:
    PGMPY_AVAILABLE = False
    logger.warning("pgmpy not available. Using fallback Bayesian calculations.")


class BayesianRiskPredictor:
    """
    Bayesian Network for predicting disease risk from nutritional data.

    Network nodes:
        Evidence (observed): sugar_intake, fibre_intake, bmi, salt_intake,
                             fat_intake, iron_intake, vitB12_intake, gender,
                             calcium_intake, vitD_intake, age, sunlight_exposure
        Target (query):      diabetes_risk, bp_risk, anaemia_risk,
                             osteoporosis_risk, vitD_deficiency_risk

    CPT values are based on:
    - ICMR epidemiological studies on Indian population
    - WHO Global Burden of Disease data
    - Published medical literature on diet-disease relationships
    """

    def __init__(self):
        """Initialize and build the Bayesian Network."""
        self.model = None
        self.inference = None
        self._build_network()

    def _build_network(self):
        """
        Construct the Bayesian Network structure and CPTs.
        Each node is discretized into binary states (0=low/normal, 1=high/risk).
        """
        if not PGMPY_AVAILABLE:
            logger.info("Using fallback risk calculation (pgmpy not available).")
            return

        try:
            # ── NETWORK STRUCTURE ──────────────────────────────────────
            # Edges represent causal/correlational relationships
            self.model = BayesianNetwork([
                # Diabetes risk factors
                ('sugar_intake', 'diabetes_risk'),
                ('fibre_intake', 'diabetes_risk'),
                ('bmi', 'diabetes_risk'),

                # Blood pressure risk factors
                ('salt_intake', 'bp_risk'),
                ('fat_intake', 'bp_risk'),

                # Anaemia risk factors
                ('iron_intake', 'anaemia_risk'),
                ('vitB12_intake', 'anaemia_risk'),
                ('gender', 'anaemia_risk'),

                # Osteoporosis risk factors
                ('calcium_intake', 'osteoporosis_risk'),
                ('vitD_intake', 'osteoporosis_risk'),
                ('age', 'osteoporosis_risk'),

                # Vitamin D deficiency risk factors
                ('sunlight_exposure', 'vitD_deficiency_risk'),
                ('vitD_intake', 'vitD_deficiency_risk'),
            ])

            # ── CONDITIONAL PROBABILITY TABLES ────────────────────────
            # All nodes are binary: 0 = normal/low, 1 = high/risk
            # P(node=0) + P(node=1) = 1.0

            # Prior probabilities for evidence nodes
            # Based on ICMR/NFHS-5 prevalence data for Indian population

            cpd_sugar = TabularCPD('sugar_intake', 2, [[0.45], [0.55]])
            cpd_fibre = TabularCPD('fibre_intake', 2, [[0.60], [0.40]])
            cpd_bmi = TabularCPD('bmi', 2, [[0.55], [0.45]])
            cpd_salt = TabularCPD('salt_intake', 2, [[0.50], [0.50]])
            cpd_fat = TabularCPD('fat_intake', 2, [[0.55], [0.45]])
            cpd_iron = TabularCPD('iron_intake', 2, [[0.40], [0.60]])
            cpd_vitB12 = TabularCPD('vitB12_intake', 2, [[0.35], [0.65]])
            cpd_gender = TabularCPD('gender', 2, [[0.50], [0.50]])
            cpd_calcium = TabularCPD('calcium_intake', 2, [[0.45], [0.55]])
            cpd_vitD = TabularCPD('vitD_intake', 2, [[0.30], [0.70]])
            cpd_age = TabularCPD('age', 2, [[0.65], [0.35]])
            cpd_sunlight = TabularCPD('sunlight_exposure', 2, [[0.40], [0.60]])

            # ── DIABETES RISK CPT ──────────────────────────────────────
            # P(diabetes_risk | sugar_intake, fibre_intake, bmi)
            # 8 combinations: sugar(2) x fibre(2) x bmi(2)
            # Medical basis: High sugar + low fibre + high BMI = highest risk
            # Values from ICMR diabetes prevalence studies
            cpd_diabetes = TabularCPD(
                variable='diabetes_risk',
                variable_card=2,
                values=[
                    # P(diabetes=0 | combinations)
                    [0.95, 0.85, 0.80, 0.65, 0.75, 0.55, 0.50, 0.25],
                    # P(diabetes=1 | combinations)
                    [0.05, 0.15, 0.20, 0.35, 0.25, 0.45, 0.50, 0.75],
                ],
                evidence=['sugar_intake', 'fibre_intake', 'bmi'],
                evidence_card=[2, 2, 2]
            )

            # ── BLOOD PRESSURE RISK CPT ────────────────────────────────
            # P(bp_risk | salt_intake, fat_intake)
            # 4 combinations: salt(2) x fat(2)
            cpd_bp = TabularCPD(
                variable='bp_risk',
                variable_card=2,
                values=[
                    # P(bp=0 | combinations)
                    [0.90, 0.70, 0.65, 0.30],
                    # P(bp=1 | combinations)
                    [0.10, 0.30, 0.35, 0.70],
                ],
                evidence=['salt_intake', 'fat_intake'],
                evidence_card=[2, 2]
            )

            # ── ANAEMIA RISK CPT ───────────────────────────────────────
            # P(anaemia_risk | iron_intake, vitB12_intake, gender)
            # 8 combinations: iron(2) x vitB12(2) x gender(2)
            # Women have higher anaemia risk (NFHS-5: 57% of women anaemic)
            cpd_anaemia = TabularCPD(
                variable='anaemia_risk',
                variable_card=2,
                values=[
                    # P(anaemia=0 | combinations)
                    [0.95, 0.80, 0.75, 0.55, 0.85, 0.65, 0.60, 0.35],
                    # P(anaemia=1 | combinations)
                    [0.05, 0.20, 0.25, 0.45, 0.15, 0.35, 0.40, 0.65],
                ],
                evidence=['iron_intake', 'vitB12_intake', 'gender'],
                evidence_card=[2, 2, 2]
            )

            # ── OSTEOPOROSIS RISK CPT ──────────────────────────────────
            # P(osteoporosis_risk | calcium_intake, vitD_intake, age)
            # 8 combinations: calcium(2) x vitD(2) x age(2)
            cpd_osteoporosis = TabularCPD(
                variable='osteoporosis_risk',
                variable_card=2,
                values=[
                    # P(osteoporosis=0 | combinations)
                    [0.97, 0.85, 0.80, 0.65, 0.85, 0.65, 0.55, 0.30],
                    # P(osteoporosis=1 | combinations)
                    [0.03, 0.15, 0.20, 0.35, 0.15, 0.35, 0.45, 0.70],
                ],
                evidence=['calcium_intake', 'vitD_intake', 'age'],
                evidence_card=[2, 2, 2]
            )

            # ── VITAMIN D DEFICIENCY RISK CPT ─────────────────────────
            # P(vitD_deficiency_risk | sunlight_exposure, vitD_intake)
            # 4 combinations: sunlight(2) x vitD(2)
            cpd_vitD_risk = TabularCPD(
                variable='vitD_deficiency_risk',
                variable_card=2,
                values=[
                    # P(vitD_def=0 | combinations)
                    [0.85, 0.60, 0.55, 0.20],
                    # P(vitD_def=1 | combinations)
                    [0.15, 0.40, 0.45, 0.80],
                ],
                evidence=['sunlight_exposure', 'vitD_intake'],
                evidence_card=[2, 2]
            )

            # Add all CPDs to the model
            self.model.add_cpds(
                cpd_sugar, cpd_fibre, cpd_bmi, cpd_salt, cpd_fat,
                cpd_iron, cpd_vitB12, cpd_gender, cpd_calcium,
                cpd_vitD, cpd_age, cpd_sunlight,
                cpd_diabetes, cpd_bp, cpd_anaemia,
                cpd_osteoporosis, cpd_vitD_risk
            )

            # Validate the model
            assert self.model.check_model(), "Bayesian Network model validation failed!"

            # Initialize inference engine (Variable Elimination for exact inference)
            self.inference = VariableElimination(self.model)
            logger.info("Bayesian Network built and validated successfully.")

        except Exception as e:
            logger.error(f"Error building Bayesian Network: {e}")
            self.model = None
            self.inference = None

    def _discretize_evidence(self, nutrition: dict, user_profile: dict) -> dict:
        """
        Convert continuous nutrition values to binary evidence for the network.
        Thresholds based on ICMR guidelines and medical literature.

        Args:
            nutrition: dict of daily nutrition totals
            user_profile: dict of user demographic info

        Returns:
            dict of binary evidence values (0 or 1)
        """
        # Get values with defaults
        sugar = nutrition.get('sugar', 0)
        fibre = nutrition.get('fibre', 0)
        salt = nutrition.get('salt', 0)  # sodium in mg
        fat = nutrition.get('fat', 0)
        iron = nutrition.get('iron', 0)
        vitB12 = nutrition.get('vitaminB12', 0)
        calcium = nutrition.get('calcium', 0)
        vitD = nutrition.get('vitaminD', 0)

        age = user_profile.get('age', 30)
        gender = user_profile.get('gender', 'male')
        bmi = user_profile.get('bmi', 22)
        sunlight = user_profile.get('sunlight_hours', 1)  # hours/day

        # Discretize: 1 = high/risk, 0 = normal/low
        return {
            'sugar_intake': 1 if sugar > 50 else 0,
            'fibre_intake': 1 if fibre < 15 else 0,   # 1 = LOW fibre (risk)
            'bmi': 1 if bmi > 25 else 0,
            'salt_intake': 1 if salt > 5000 else 0,   # sodium > 5000mg
            'fat_intake': 1 if fat > 70 else 0,
            'iron_intake': 1 if iron < 10 else 0,     # 1 = LOW iron (risk)
            'vitB12_intake': 1 if vitB12 < 0.5 else 0,  # 1 = LOW B12 (risk)
            'gender': 1 if gender == 'female' else 0,
            'calcium_intake': 1 if calcium < 400 else 0,  # 1 = LOW calcium (risk)
            'vitD_intake': 1 if vitD < 5 else 0,      # 1 = LOW vitD (risk)
            'age': 1 if age > 40 else 0,
            'sunlight_exposure': 1 if sunlight < 1 else 0,  # 1 = LOW sunlight (risk)
        }

    def predict(self, nutrition: dict, user_profile: dict) -> list:
        """
        Run Bayesian inference to predict disease risks.

        Args:
            nutrition: dict of daily nutrition totals
            user_profile: dict with age, gender, bmi, sunlight_hours

        Returns:
            list of disease risk dicts with probability and level
        """
        evidence = self._discretize_evidence(nutrition, user_profile)

        if self.inference and PGMPY_AVAILABLE:
            return self._pgmpy_inference(evidence, nutrition, user_profile)
        else:
            return self._fallback_inference(evidence, nutrition, user_profile)

    def _pgmpy_inference(self, evidence: dict, nutrition: dict, user_profile: dict) -> list:
        """
        Use pgmpy BeliefPropagation for exact Bayesian inference.

        Args:
            evidence: discretized binary evidence dict
            nutrition: raw nutrition values
            user_profile: user demographic info

        Returns:
            list of disease risk results
        """
        diseases = [
            {
                'node': 'diabetes_risk',
                'name': 'Type 2 Diabetes',
                'evidence_nodes': ['sugar_intake', 'fibre_intake', 'bmi'],
                'factors': ['High sugar intake', 'Low dietary fibre', 'High BMI'],
                'color': '#f44336',
                'icon': 'bloodtype'
            },
            {
                'node': 'bp_risk',
                'name': 'Hypertension (High BP)',
                'evidence_nodes': ['salt_intake', 'fat_intake'],
                'factors': ['High sodium intake', 'High fat intake'],
                'color': '#e91e63',
                'icon': 'favorite'
            },
            {
                'node': 'anaemia_risk',
                'name': 'Anaemia',
                'evidence_nodes': ['iron_intake', 'vitB12_intake', 'gender'],
                'factors': ['Low iron intake', 'Low vitamin B12', 'Female gender'],
                'color': '#ff5722',
                'icon': 'opacity'
            },
            {
                'node': 'osteoporosis_risk',
                'name': 'Osteoporosis',
                'evidence_nodes': ['calcium_intake', 'vitD_intake', 'age'],
                'factors': ['Low calcium intake', 'Low vitamin D', 'Age > 40'],
                'color': '#795548',
                'icon': 'accessibility'
            },
            {
                'node': 'vitD_deficiency_risk',
                'name': 'Vitamin D Deficiency',
                'evidence_nodes': ['sunlight_exposure', 'vitD_intake'],
                'factors': ['Low sunlight exposure', 'Low dietary vitamin D'],
                'color': '#ff9800',
                'icon': 'wb_sunny'
            },
        ]

        results = []
        for disease in diseases:
            try:
                # Query the network with relevant evidence
                query_evidence = {k: v for k, v in evidence.items()
                                  if k in disease['evidence_nodes']}

                result = self.inference.query(
                    variables=[disease['node']],
                    evidence=query_evidence,
                    show_progress=False
                )

                # P(disease=1) = risk probability
                risk_prob = float(result.values[1])

                # Determine contributing factors
                contributing = self._get_contributing_factors(
                    disease['factors'], disease['evidence_nodes'], evidence
                )

                results.append({
                    'disease': disease['name'],
                    'risk_probability': round(risk_prob, 3),
                    'risk_level': self._prob_to_level(risk_prob),
                    'main_contributing_factors': contributing,
                    'color': disease['color'],
                    'icon': disease['icon'],
                    'evidence_used': query_evidence,
                    'dietary_changes': self._get_dietary_changes(disease['node'], evidence)
                })

            except Exception as e:
                logger.error(f"Inference error for {disease['name']}: {e}")
                results.append(self._fallback_single(disease, evidence))

        return results

    def _fallback_inference(self, evidence: dict, nutrition: dict, user_profile: dict) -> list:
        """
        Fallback risk calculation when pgmpy is not available.
        Uses simple weighted scoring based on evidence.
        """
        results = []

        # Diabetes risk
        diabetes_score = (
            evidence.get('sugar_intake', 0) * 0.40 +
            evidence.get('fibre_intake', 0) * 0.35 +
            evidence.get('bmi', 0) * 0.25
        )
        results.append({
            'disease': 'Type 2 Diabetes',
            'risk_probability': round(min(diabetes_score, 0.95), 3),
            'risk_level': self._prob_to_level(diabetes_score),
            'main_contributing_factors': self._get_contributing_factors(
                ['High sugar intake', 'Low dietary fibre', 'High BMI'],
                ['sugar_intake', 'fibre_intake', 'bmi'], evidence),
            'color': '#f44336',
            'icon': 'bloodtype',
            'dietary_changes': self._get_dietary_changes('diabetes_risk', evidence)
        })

        # BP risk
        bp_score = (
            evidence.get('salt_intake', 0) * 0.55 +
            evidence.get('fat_intake', 0) * 0.45
        )
        results.append({
            'disease': 'Hypertension (High BP)',
            'risk_probability': round(min(bp_score, 0.95), 3),
            'risk_level': self._prob_to_level(bp_score),
            'main_contributing_factors': self._get_contributing_factors(
                ['High sodium intake', 'High fat intake'],
                ['salt_intake', 'fat_intake'], evidence),
            'color': '#e91e63',
            'icon': 'favorite',
            'dietary_changes': self._get_dietary_changes('bp_risk', evidence)
        })

        # Anaemia risk
        anaemia_score = (
            evidence.get('iron_intake', 0) * 0.45 +
            evidence.get('vitB12_intake', 0) * 0.35 +
            evidence.get('gender', 0) * 0.20
        )
        results.append({
            'disease': 'Anaemia',
            'risk_probability': round(min(anaemia_score, 0.95), 3),
            'risk_level': self._prob_to_level(anaemia_score),
            'main_contributing_factors': self._get_contributing_factors(
                ['Low iron intake', 'Low vitamin B12', 'Female gender'],
                ['iron_intake', 'vitB12_intake', 'gender'], evidence),
            'color': '#ff5722',
            'icon': 'opacity',
            'dietary_changes': self._get_dietary_changes('anaemia_risk', evidence)
        })

        # Osteoporosis risk
        osteo_score = (
            evidence.get('calcium_intake', 0) * 0.40 +
            evidence.get('vitD_intake', 0) * 0.35 +
            evidence.get('age', 0) * 0.25
        )
        results.append({
            'disease': 'Osteoporosis',
            'risk_probability': round(min(osteo_score, 0.95), 3),
            'risk_level': self._prob_to_level(osteo_score),
            'main_contributing_factors': self._get_contributing_factors(
                ['Low calcium intake', 'Low vitamin D', 'Age > 40'],
                ['calcium_intake', 'vitD_intake', 'age'], evidence),
            'color': '#795548',
            'icon': 'accessibility',
            'dietary_changes': self._get_dietary_changes('osteoporosis_risk', evidence)
        })

        # Vitamin D deficiency risk
        vitD_score = (
            evidence.get('sunlight_exposure', 0) * 0.50 +
            evidence.get('vitD_intake', 0) * 0.50
        )
        results.append({
            'disease': 'Vitamin D Deficiency',
            'risk_probability': round(min(vitD_score, 0.95), 3),
            'risk_level': self._prob_to_level(vitD_score),
            'main_contributing_factors': self._get_contributing_factors(
                ['Low sunlight exposure', 'Low dietary vitamin D'],
                ['sunlight_exposure', 'vitD_intake'], evidence),
            'color': '#ff9800',
            'icon': 'wb_sunny',
            'dietary_changes': self._get_dietary_changes('vitD_deficiency_risk', evidence)
        })

        return results

    def _fallback_single(self, disease: dict, evidence: dict) -> dict:
        """Fallback for a single disease when pgmpy query fails."""
        return {
            'disease': disease['name'],
            'risk_probability': 0.5,
            'risk_level': 'Moderate',
            'main_contributing_factors': [],
            'color': disease['color'],
            'icon': disease['icon'],
            'dietary_changes': []
        }

    def _prob_to_level(self, prob: float) -> str:
        """Convert probability to risk level label."""
        if prob < 0.25:
            return 'Low'
        elif prob < 0.50:
            return 'Moderate'
        elif prob < 0.75:
            return 'High'
        else:
            return 'Critical'

    def _get_contributing_factors(self, factor_names: list,
                                   evidence_nodes: list, evidence: dict) -> list:
        """Return list of factors that are actually contributing (evidence=1)."""
        contributing = []
        for name, node in zip(factor_names, evidence_nodes):
            if evidence.get(node, 0) == 1:
                contributing.append(name)
        return contributing

    def _get_dietary_changes(self, disease_node: str, evidence: dict) -> list:
        """Return dietary change recommendations based on evidence."""
        changes_map = {
            'diabetes_risk': [
                'Replace white rice with brown rice or millets',
                'Add 2 servings of vegetables per meal',
                'Include bitter gourd (karela) in weekly diet',
                'Reduce sugar in tea/coffee',
                'Eat whole fruits instead of juices'
            ],
            'bp_risk': [
                'Reduce salt to less than 5g per day',
                'Limit fried and processed foods',
                'Increase potassium-rich foods (banana, coconut water)',
                'Add garlic to daily cooking',
                'Reduce pickles and papad'
            ],
            'anaemia_risk': [
                'Eat spinach or methi daily',
                'Pair iron-rich foods with vitamin C sources',
                'Include dairy products for vitamin B12',
                'Add jaggery instead of sugar',
                'Eat drumstick leaves (moringa) weekly'
            ],
            'osteoporosis_risk': [
                'Drink 2 glasses of milk daily',
                'Include ragi in weekly diet',
                'Get 15-20 minutes of morning sunlight',
                'Add sesame seeds (til) to food',
                'Include paneer or curd in daily diet'
            ],
            'vitD_deficiency_risk': [
                'Get 15-20 minutes of morning sunlight daily',
                'Include eggs in diet (if not vegan)',
                'Eat fatty fish like sardines or mackerel',
                'Consider vitamin D fortified milk',
                'Mushrooms exposed to sunlight are a plant source'
            ]
        }
        return changes_map.get(disease_node, [])
