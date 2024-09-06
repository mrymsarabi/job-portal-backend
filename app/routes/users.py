from flask import Blueprint, request, jsonify, current_app
from app import bcrypt
from app.models import get_users_collection
from app.decorators import token_required
from bson.objectid import ObjectId
import jwt
import datetime
from app.utils import validate_token

users_bp = Blueprint('users', __name__)
users_collection = get_users_collection()

@users_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required_fields = ('first_name', 'last_name', 'username', 'email', 'password', 'birth_date')
    
    if not all(key in data for key in required_fields):
        return jsonify({
            "status": "error",
            "error": "Missing fields"
        }), 400

    if users_collection.find_one({"email": data['email']}):
        return jsonify({
            "status": "error",
            "error": "Email already exists"
        }), 400

    # Check if username already exists
    if users_collection.find_one({"username": data['username']}):
        return jsonify({
            "status": "error",
            "error": "Username already exists"
        }), 400

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
        return jsonify({
        "status": "success",
        "message": "User created successfully"
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({"username": data['username']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            "status": "success", 
            "message": "Login successful", 
            "token": token, 
            "user_id": str(user['_id'])
        }), 200
    else:
        return jsonify({
            "status": "error", 
            "error": "Invalid username or password"
        }), 401

@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        user = users_collection.find_one({"_id": ObjectId(current_user)})
        if user:
            user_data = {
                "user_id": str(user["_id"]),  # Include user_id for updates
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

@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    update_fields = {}

    # Only update fields if they are provided
    if 'first_name' in data:
        update_fields['first_name'] = data['first_name']
    if 'last_name' in data:
        update_fields['last_name'] = data['last_name']
    if 'username' in data:
        if users_collection.find_one({"username": data['username'], "_id": {"$ne": ObjectId(current_user)}}):
            return jsonify({"status": "error", "message": "Username already taken"}), 400
        update_fields['username'] = data['username']
    if 'email' in data:
        if users_collection.find_one({"email": data['email'], "_id": {"$ne": ObjectId(current_user)}}):
            return jsonify({"status": "error", "message": "Email already exists"}), 400
        update_fields['email'] = data['email']
    if 'password' in data:
        update_fields['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    if 'birth_date' in data:
        update_fields['birth_date'] = data['birth_date']

    if not update_fields:
        return jsonify({"status": "error", "message": "No fields to update"}), 400

    try:
        users_collection.update_one({"_id": ObjectId(current_user)}, {"$set": update_fields})
        return jsonify({"status": "success", "message": "Profile updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@users_bp.route('/check_login', methods=['GET'])
def check_login_status():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split(" ")[1]  # Assuming the header is in the format "Bearer <token>"
        is_valid, user_info = validate_token(token)

        if is_valid:
            return jsonify({
                "status": "success",
                "message": "User is logged in",
                "user_id": user_info
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": user_info  # This will return the error message from validate_token
            }), 401
    else:
        return jsonify({
            "status": "error",
            "message": "Token is missing"
        }), 401

@users_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user_by_id(current_user, user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)}, {"password": 0})  # Exclude the password field
        if user:
            user_data = {
                "user_id": str(user["_id"]),  # Convert ObjectId to string
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "username": user["username"],
                "email": user["email"],
                "birth_date": user["birth_date"]
            }
            return jsonify({"status": "success", "user": user_data}), 200
        else:
            return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
