"""Food log routes — log meals, get daily summary, delete entries."""

from datetime import date, datetime
from flask import Blueprint, request, jsonify
from database.models import db, Food, FoodLog, NutritionDaily
from routes.auth import token_required

logs_bp = Blueprint('logs', __name__)


def _upsert_daily_nutrition(user_id: int, log_date: date):
    """Recompute and upsert the NutritionDaily row for a given user+date."""
    logs = FoodLog.query.filter_by(user_id=user_id, date=log_date).all()

    totals = {k: 0.0 for k in ['calories', 'protein', 'iron', 'calcium',
                                 'vitC', 'vitD', 'vitB12', 'fibre',
                                 'carbs', 'fat', 'sugar', 'salt']}
    for log in logs:
        n = log.get_nutrition()
        totals['calories'] += n.get('calories', 0)
        totals['protein']  += n.get('protein', 0)
        totals['iron']     += n.get('iron', 0)
        totals['calcium']  += n.get('calcium', 0)
        totals['vitC']     += n.get('vitaminC', 0)
        totals['vitD']     += n.get('vitaminD', 0)
        totals['vitB12']   += n.get('vitaminB12', 0)
        totals['fibre']    += n.get('fibre', 0)
        totals['carbs']    += n.get('carbs', 0)
        totals['fat']      += n.get('fat', 0)
        totals['sugar']    += n.get('sugar', 0)
        totals['salt']     += n.get('sodium', 0)

    nd = NutritionDaily.query.filter_by(user_id=user_id, date=log_date).first()
    if not nd:
        nd = NutritionDaily(user_id=user_id, date=log_date)
        db.session.add(nd)

    nd.total_calories = round(totals['calories'], 2)
    nd.total_protein  = round(totals['protein'], 2)
    nd.total_iron     = round(totals['iron'], 2)
    nd.total_calcium  = round(totals['calcium'], 2)
    nd.total_vitC     = round(totals['vitC'], 2)
    nd.total_vitD     = round(totals['vitD'], 2)
    nd.total_vitB12   = round(totals['vitB12'], 2)
    nd.total_fibre    = round(totals['fibre'], 2)
    nd.total_carbs    = round(totals['carbs'], 2)
    nd.total_fat      = round(totals['fat'], 2)
    nd.total_sugar    = round(totals['sugar'], 2)
    nd.total_salt     = round(totals['salt'], 2)
    db.session.commit()
    return nd


@logs_bp.route('/', methods=['POST'])
@token_required
def add_log(current_user):
    """Log a food item for a meal."""
    data = request.get_json() or {}
    food = Food.query.get(data.get('food_id'))
    if not food:
        return jsonify({'error': 'Food not found'}), 404

    log_date = date.fromisoformat(data.get('date', date.today().isoformat()))
    log = FoodLog(
        user_id=current_user.id,
        date=log_date,
        meal_type=data.get('meal_type', 'lunch'),
        food_id=food.id,
        quantity_grams=float(data.get('quantity_grams', 100)),
        logged_at=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    _upsert_daily_nutrition(current_user.id, log_date)
    return jsonify(log.to_dict()), 201


@logs_bp.route('/', methods=['GET'])
@token_required
def get_logs(current_user):
    """Get food logs for a specific date (default: today)."""
    log_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    logs = FoodLog.query.filter_by(user_id=current_user.id, date=log_date).all()
    return jsonify([l.to_dict() for l in logs])


@logs_bp.route('/<int:log_id>', methods=['DELETE'])
@token_required
def delete_log(current_user, log_id):
    log = FoodLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
    log_date = log.date
    db.session.delete(log)
    db.session.commit()
    _upsert_daily_nutrition(current_user.id, log_date)
    return jsonify({'message': 'Deleted'})


@logs_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_summary(current_user):
    """Get aggregated daily nutrition for a date."""
    log_date = date.fromisoformat(request.args.get('date', date.today().isoformat()))
    nd = NutritionDaily.query.filter_by(user_id=current_user.id, date=log_date).first()
    if not nd:
        return jsonify(None)
    return jsonify(nd.to_dict())


@logs_bp.route('/weekly', methods=['GET'])
@token_required
def get_weekly_summary(current_user):
    """Get last 7 days of daily nutrition summaries."""
    from datetime import timedelta
    today = date.today()
    week = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        nd = NutritionDaily.query.filter_by(user_id=current_user.id, date=d).first()
        week.append(nd.to_dict() if nd else {'date': d.isoformat()})
    return jsonify(week)
