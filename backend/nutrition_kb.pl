% ============================================================
% NutriSense Prolog Knowledge Base
% nutrition_kb.pl
%
% ARCHITECTURE NOTE:
% This file contains ONLY rules — zero hardcoded food data.
% Python (prolog_interface.py) dynamically asserts food facts
% from SQLite at runtime using pyswip assertz/1.
%
% This implements the DATA vs LOGIC separation:
%   DATA  → SQLite (IFCT 2017 dataset)
%   LOGIC → This file (Prolog inference rules)
%
% Experiment 10: Prolog Knowledge Representation
% ============================================================

:- dynamic protein/2.
:- dynamic iron/2.
:- dynamic calcium/2.
:- dynamic vitaminC/2.
:- dynamic vitaminD/2.
:- dynamic vitaminB12/2.
:- dynamic carbs/2.
:- dynamic fat/2.
:- dynamic fibre/2.
:- dynamic sugar/2.
:- dynamic price/2.
:- dynamic food_group/2.
:- dynamic diet_type_food/2.

:- dynamic daily_iron/2.
:- dynamic daily_protein/2.
:- dynamic daily_calcium/2.
:- dynamic daily_vitD/2.
:- dynamic daily_vitB12/2.
:- dynamic daily_vitC/2.
:- dynamic daily_sugar/2.
:- dynamic daily_fibre/2.
:- dynamic daily_fat/2.
:- dynamic daily_salt/2.

:- dynamic rda_iron/2.
:- dynamic rda_protein/2.
:- dynamic rda_calcium/2.
:- dynamic rda_vitD/2.
:- dynamic rda_vitB12/2.
:- dynamic rda_vitC/2.

:- dynamic diet_type/2.
:- dynamic same_food_group/2.

% ============================================================
% SECTION 1: Nutritional Classification Rules
% These rules classify foods based on their nutrient content.
% Facts (protein/2, iron/2, etc.) are asserted by Python.
% ============================================================

%% high_protein(+Food)
%  True if food has > 15g protein per 100g
high_protein(X) :- protein(X, P), P > 15.

%% low_protein(+Food)
%  True if food has < 5g protein per 100g
low_protein(X) :- protein(X, P), P < 5.

%% moderate_protein(+Food)
%  True if food has 5-15g protein per 100g
moderate_protein(X) :- protein(X, P), P >= 5, P =< 15.

%% iron_rich(+Food)
%  True if food has > 3mg iron per 100g
iron_rich(X) :- iron(X, I), I > 3.

%% very_iron_rich(+Food)
%  True if food has > 8mg iron per 100g (excellent source)
very_iron_rich(X) :- iron(X, I), I > 8.

%% calcium_rich(+Food)
%  True if food has > 200mg calcium per 100g
calcium_rich(X) :- calcium(X, C), C > 200.

%% vitamin_c_rich(+Food)
%  True if food has > 30mg vitaminC per 100g
vitamin_c_rich(X) :- vitaminC(X, V), V > 30.

%% high_vitaminC(+Food)
%  True if food has > 100mg vitaminC per 100g (excellent source)
high_vitaminC(X) :- vitaminC(X, V), V > 100.

%% high_fibre(+Food)
%  True if food has > 5g fibre per 100g
high_fibre(X) :- fibre(X, F), F > 5.

%% high_sugar(+Food)
%  True if food has > 50g carbs per 100g (high glycemic concern)
high_sugar(X) :- carbs(X, C), C > 50.

%% high_fat(+Food)
%  True if food has > 20g fat per 100g
high_fat(X) :- fat(X, F), F > 20.

%% low_calorie(+Food)
%  True if food has < 50 calories per 100g (good for weight management)
low_calorie(X) :- calories(X, C), C < 50.

%% vitaminB12_source(+Food)
%  True if food has > 0.5mcg vitaminB12 per 100g
vitaminB12_source(X) :- vitaminB12(X, V), V > 0.5.

%% vitaminD_source(+Food)
%  True if food has > 1mcg vitaminD per 100g
vitaminD_source(X) :- vitaminD(X, V), V > 1.

% ============================================================
% SECTION 2: Deficiency Detection Rules
% These rules detect nutritional deficiencies for a user.
% daily_* facts and rda_* facts are asserted by Python
% from the user's food log and ICMR RDA table.
% ============================================================

%% iron_deficient(+User)
%  True if user's daily iron intake is below ICMR RDA
iron_deficient(User) :-
    daily_iron(User, I),
    rda_iron(User, R),
    I < R.

%% protein_deficient(+User)
%  True if user's daily protein intake is below ICMR RDA
protein_deficient(User) :-
    daily_protein(User, P),
    rda_protein(User, R),
    P < R.

%% calcium_deficient(+User)
%  True if user's daily calcium intake is below ICMR RDA
calcium_deficient(User) :-
    daily_calcium(User, C),
    rda_calcium(User, R),
    C < R.

%% vitD_deficient(+User)
%  True if user's daily vitamin D intake is below ICMR RDA
vitD_deficient(User) :-
    daily_vitD(User, V),
    rda_vitD(User, R),
    V < R.

%% vitB12_deficient(+User)
%  True if user's daily vitamin B12 intake is below ICMR RDA
vitB12_deficient(User) :-
    daily_vitB12(User, V),
    rda_vitB12(User, R),
    V < R.

%% vitC_deficient(+User)
%  True if user's daily vitamin C intake is below ICMR RDA
vitC_deficient(User) :-
    daily_vitC(User, V),
    rda_vitC(User, R),
    V < R.

% ============================================================
% SECTION 3: Balanced Meal Rules
% Rules for evaluating meal quality and balance.
% ============================================================

%% balanced_meal(+Breakfast, +Lunch, +Dinner)
%  True if the three meals together form a nutritionally balanced day
balanced_meal(Breakfast, Lunch, Dinner) :-
    high_protein(Breakfast),
    high_fibre(Lunch),
    iron_rich(Dinner).

%% protein_balanced_meal(+Food1, +Food2)
%  True if combining two foods gives adequate protein
protein_balanced_meal(F1, F2) :-
    protein(F1, P1),
    protein(F2, P2),
    Total is P1 + P2,
    Total > 20.

%% iron_vitC_combo(+IronFood, +VitCFood)
%  True if pairing iron food with vitC food enhances absorption
iron_vitC_combo(IronFood, VitCFood) :-
    iron_rich(IronFood),
    vitamin_c_rich(VitCFood).

% ============================================================
% SECTION 4: Food Alternative Rules
% Rules for finding affordable nutritional substitutes.
% Python asserts same_food_group/2 facts from SQLite data.
% ============================================================

%% affordable_alternative(+ExpensiveFood, -CheaperFood)
%  Finds a cheaper food in the same group with similar nutrition
affordable_alternative(X, Y) :-
    same_food_group(X, Y),
    price(Y, PY),
    price(X, PX),
    PY < PX,
    similar_nutrition(X, Y),
    X \= Y.

%% similar_nutrition(+Food1, +Food2)
%  True if two foods have similar protein and iron content (within tolerance)
similar_nutrition(X, Y) :-
    protein(X, PX), protein(Y, PY),
    DiffP is abs(PX - PY),
    DiffP < 5,
    iron(X, IX), iron(Y, IY),
    DiffI is abs(IX - IY),
    DiffI < 2.

%% budget_friendly(+Food, +MaxPrice)
%  True if food costs less than MaxPrice per 100g
budget_friendly(Food, MaxPrice) :-
    price(Food, P),
    P =< MaxPrice.

% ============================================================
% SECTION 5: Disease Risk Logic Rules
% Rules for predicting disease risk based on dietary patterns.
% ============================================================

%% diabetes_risk_high(+User)
%  High diabetes risk if sugar intake > 50g AND fibre < 15g daily
diabetes_risk_high(User) :-
    daily_sugar(User, S), S > 50,
    daily_fibre(User, F), F < 15.

%% bp_risk_high(+User)
%  High blood pressure risk if salt > 5g AND fat > 70g daily
bp_risk_high(User) :-
    daily_salt(User, S), S > 5,
    daily_fat(User, F), F > 70.

%% anaemia_risk_high(+User)
%  High anaemia risk if both iron AND vitB12 deficient
anaemia_risk_high(User) :-
    iron_deficient(User),
    vitB12_deficient(User).

%% osteoporosis_risk(+User)
%  Osteoporosis risk if calcium deficient AND vitD deficient
osteoporosis_risk(User) :-
    calcium_deficient(User),
    vitD_deficient(User).

%% metabolic_syndrome_risk(+User)
%  Risk if high sugar + high fat + low fibre
metabolic_syndrome_risk(User) :-
    daily_sugar(User, S), S > 40,
    daily_fat(User, F), F > 60,
    daily_fibre(User, Fi), Fi < 20.

% ============================================================
% SECTION 6: Vegetarian/Vegan Specific Rules
% Special rules for plant-based diet nutritional concerns.
% ============================================================

%% veg_protein_concern(+User)
%  Protein concern for vegetarians who are protein deficient
veg_protein_concern(User) :-
    diet_type(User, vegetarian),
    protein_deficient(User).

%% vegan_b12_risk(+User)
%  B12 risk for vegans (no animal products)
vegan_b12_risk(User) :-
    diet_type(User, vegan),
    vitB12_deficient(User).

%% veg_iron_concern(+User)
%  Iron concern for vegetarians (non-heme iron less bioavailable)
veg_iron_concern(User) :-
    diet_type(User, vegetarian),
    iron_deficient(User).

% ============================================================
% SECTION 7: Absorption Enhancement Rules
% Rules about nutrient interactions that affect absorption.
% ============================================================

%% iron_absorption_enhanced(+User)
%  Iron absorption is enhanced when vitC intake is adequate
iron_absorption_enhanced(User) :-
    daily_vitC(User, V), V > 40.

%% calcium_absorption_enhanced(+User)
%  Calcium absorption is enhanced when vitD is adequate
calcium_absorption_enhanced(User) :-
    daily_vitD(User, V), V > 5.

%% iron_absorption_inhibited(+User)
%  Iron absorption is inhibited when calcium is very high
iron_absorption_inhibited(User) :-
    daily_calcium(User, C), C > 1500.

% ============================================================
% SECTION 8: Food Recommendation Rules
% Rules for recommending specific foods to fix deficiencies.
% ============================================================

%% recommend_for_iron(+Food)
%  Recommend this food to fix iron deficiency
recommend_for_iron(Food) :-
    iron_rich(Food).

%% recommend_for_protein(+Food)
%  Recommend this food to fix protein deficiency
recommend_for_protein(Food) :-
    high_protein(Food).

%% recommend_for_calcium(+Food)
%  Recommend this food to fix calcium deficiency
recommend_for_calcium(Food) :-
    calcium_rich(Food).

%% recommend_for_vitC(+Food)
%  Recommend this food to fix vitamin C deficiency
recommend_for_vitC(Food) :-
    vitamin_c_rich(Food).

%% recommend_for_vitB12(+Food)
%  Recommend this food to fix vitamin B12 deficiency
recommend_for_vitB12(Food) :-
    vitaminB12_source(Food).

%% recommend_for_vitD(+Food)
%  Recommend this food to fix vitamin D deficiency
recommend_for_vitD(Food) :-
    vitaminD_source(Food).

%% affordable_iron_source(+Food, +MaxPrice)
%  Affordable food that is iron-rich
affordable_iron_source(Food, MaxPrice) :-
    iron_rich(Food),
    budget_friendly(Food, MaxPrice).

%% affordable_protein_source(+Food, +MaxPrice)
%  Affordable food that is high in protein
affordable_protein_source(Food, MaxPrice) :-
    high_protein(Food),
    budget_friendly(Food, MaxPrice).
