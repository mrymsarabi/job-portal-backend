from functools import wraps
from flask import request, jsonify, current_app
import jwt

# Used for collections related to the users:
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except Exception as e:
            return jsonify({"error": "Token is invalid!", "message": str(e)}), 401

        return f(current_user, *args, **kwargs)
    
    return decorated_function

# Used for collections related to the admins:
def token_required_admin(f): 
     @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing!"}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(" ")[1]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            if data.get('role') != 'admin':
                return jsonify({"error": "Admin access required!"}), 403
            
            current_admin = data['admin_id']
        except Exception as e:
            return jsonify({"error": "Token is invalid!", "message": str(e)}), 401

        return f(current_admin, *args, **kwargs)
    
    return decorated_function