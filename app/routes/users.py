from flask import Blueprint, request, jsonify
from app import bcrypt
from app.models import get_users_collection
from bson.objectid import ObjectId

users_bp = Blueprint('users', __name__)
users_collection = get_users_collection()

@users_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    required_fields = ('first_name', 'last_name', 'username', 'email', 'password', 'birth_date')
    
    # Check for missing fields
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    # Check if the email already exists
    if users_collection.find_one({"email": data['email']}):
        return jsonify({"error": "Email already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Create the user object
    user = {
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "username": data['username'],
        "email": data['email'],
        "password": hashed_password,
        "birth_date": data['birth_date']
    }
    
    try:
        # Insert the user into the collection
        users_collection.insert_one(user)
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@users_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Find the user by email
    user = users_collection.find_one({"username": data['username']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@users_bp.route('/remove_account', methods=['DELETE'])
def remove_account():
    data = request.get_json()
    
    # Find the user by email
    user = users_collection.find_one({"email": data['email']})
    
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        # Remove the user from the collection
        users_collection.delete_one({"_id": ObjectId(user['_id'])})
        return jsonify({"message": "Account deleted successfully"}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401
