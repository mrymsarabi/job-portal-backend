from flask import Blueprint, request, jsonify, session
from app import bcrypt
from app.models import get_admin_by_email, get_admin_by_username, get_admin_by_id, create_admin

admins_bp = Blueprint('admins', __name__)

# Admin Registration
@admins_bp.route('/register', methods=['POST'])
def register_admin():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if the email already exists
    if get_admin_by_email(email):
        return jsonify({'error': 'Admin with this email already exists'}), 400

    # Hash the password using bcrypt
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create the admin
    create_admin(username, email, hashed_password)

    return jsonify({'message': 'Admin registered successfully'}), 201

# Admin Login
@admins_bp.route('/login', methods=['POST'])
def login_admin():
    data = request.get_json()
    login_identifier = data.get('username') or data.get('email')  # Accept both username and email
    password = data.get('password')

    if not login_identifier or not password:
        return jsonify({'error': 'Username/Email and password required'}), 400

    # Find the admin by username or email
    admin = get_admin_by_username(login_identifier) or get_admin_by_email(login_identifier)

    if not admin:
        return jsonify({'error': 'Invalid username/email or password'}), 401

    # Check if the password matches using bcrypt
    if not bcrypt.check_password_hash(admin['password'], password):
        return jsonify({'error': 'Invalid username/email or password'}), 401

    # Set admin session (or token-based authentication)
    session['admin_id'] = str(admin['_id'])

    return jsonify({'message': 'Login successful', 'admin_id': str(admin['_id'])}), 200
