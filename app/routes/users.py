from flask import Blueprint, request, jsonify, current_app
from app import bcrypt
from app.models import get_users_collection
from app.decorators import token_required
from bson.objectid import ObjectId
import jwt
import datetime

users_bp = Blueprint('users', __name__)
users_collection = get_users_collection()

@users_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required_fields = ('first_name', 'last_name', 'username', 'email', 'password', 'birth_date')
    
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    if users_collection.find_one({"email": data['email']}):
        return jsonify({"error": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    user = {
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "username": data['username'],
        "email": data['email'],
        "password": hashed_password,
        "birth_date": data['birth_date']
    }
    
    try:
        users_collection.insert_one(user)
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({"username": data['username']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({"message": "Login successful", "token": token, "user_id": str(user['_id'])}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        user = users_collection.find_one({"_id": ObjectId(current_user)})
        if user:
            # Remove sensitive information
            user_data = {
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "email": user["email"],
                "birth_date": user["birth_date"]
            }
            return jsonify({"user": user_data}), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_bp.route('/remove_account', methods=['DELETE'])
@token_required
def remove_account(current_user):
    user = users_collection.find_one({"_id": ObjectId(current_user)})
    
    if user and bcrypt.check_password_hash(user['password'], request.get_json()['password']):
        users_collection.delete_one({"_id": ObjectId(user['_id'])})
        return jsonify({"message": "Account deleted successfully"}), 200
    else:
        return jsonify({"error": "Invalid password"}), 401

@users_bp.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user):
    return jsonify({"message": f"Hello, user {current_user}!"})
