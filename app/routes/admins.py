from flask import Blueprint, request, jsonify, current_app
from app import bcrypt
from app.models import get_admin_by_email, get_admin_by_username, create_admin
from app.decorators import token_required_admin
import jwt
import datetime

admins_bp = Blueprint('admins', __name__)

@admins_bp.route('/signup', methods=['POST'])
def signup_admin():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    if get_admin_by_email(email):
        return jsonify({'status': 'error', 'message': 'Admin with this email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    create_admin(username, email, hashed_password)

    return jsonify({'status': 'success', 'message': 'Admin registered successfully'}), 201

@admins_bp.route('/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    login_identifier = data.get('username') or data.get('email')
    password = data.get('password')

    if not login_identifier or not password:
        return jsonify({'status': 'error', 'message': 'Username/Email and password required'}), 400

    admin = get_admin_by_username(login_identifier) or get_admin_by_email(login_identifier)

    if not admin:
        return jsonify({'status': 'error', 'message': 'Invalid username/email or password'}), 401

    if not bcrypt.check_password_hash(admin['password'], password):
        return jsonify({'status': 'error', 'message': 'Invalid username/email or password'}), 401

    token = jwt.encode({
        'admin_id': str(admin['_id']),
        'role': 'admin',
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'status': 'success', 'message': 'Login successful', 'token': token}), 200
