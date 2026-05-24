"""Foods routes — search, list, get by ID."""

from flask import Blueprint, request, jsonify
from database.models import Food
from routes.auth import token_required

foods_bp = Blueprint('foods', __name__)


@foods_bp.route('/', methods=['GET'])
@token_required
def list_foods(current_user):
    """List foods with optional filters: group, diet_type, search query."""
    query = Food.query

    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(Food.name.ilike(f'%{search}%'))

    group = request.args.get('group', '').strip()
    if group:
        query = query.filter(Food.food_group == group)

    diet = request.args.get('diet_type', '').strip()
    if diet:
        query = query.filter(Food.diet_type == diet)

    limit = min(int(request.args.get('limit', 50)), 200)
    foods = query.limit(limit).all()
    return jsonify([f.to_dict() for f in foods])


@foods_bp.route('/<int:food_id>', methods=['GET'])
@token_required
def get_food(current_user, food_id):
    food = Food.query.get_or_404(food_id)
    return jsonify(food.to_dict())


@foods_bp.route('/groups', methods=['GET'])
@token_required
def get_groups(current_user):
    """Return distinct food groups."""
    groups = db_distinct_groups()
    return jsonify(groups)


def db_distinct_groups():
    from database.models import db
    rows = db.session.query(Food.food_group).distinct().all()
    return sorted([r[0] for r in rows if r[0]])
