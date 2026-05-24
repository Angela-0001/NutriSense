"""Auth routes — register, login, profile update."""

import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import db, User

auth_bp = Blueprint('auth', __name__)


def token_required(f):
    """JWT auth decorator — attach current_user to request."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def _make_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'email, password, and name are required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        name=data['name'],
        age=data.get('age'),
        gender=data.get('gender'),
        weight_kg=data.get('weight_kg'),
        height_cm=data.get('height_cm'),
        budget_monthly_inr=data.get('budget_monthly_inr', 3000.0),
        diet_type=data.get('diet_type', 'veg'),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'token': _make_token(user.id), 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not check_password_hash(user.password_hash, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    return jsonify({'token': _make_token(user.id), 'user': user.to_dict()})


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify(current_user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json() or {}
    fields = ['name', 'age', 'gender', 'weight_kg', 'height_cm',
              'budget_monthly_inr', 'diet_type', 'allergies']
    for field in fields:
        if field in data:
            setattr(current_user, field, data[field])
    db.session.commit()
    return jsonify(current_user.to_dict())
