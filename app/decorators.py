from functools import wraps
from flask import request, jsonify, current_app
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing!"}), 403
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user_id']
        except Exception as e:
            return jsonify({"error": f"Token is invalid: {str(e)}"}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated
