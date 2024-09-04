from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.models import get_users_collection, get_resumes_collection
from app.decorators import token_required

resume_bp = Blueprint('resume', __name__)
users_collection = get_users_collection()
resumes_collection = get_resumes_collection()

# Schema for the resume collection
def create_resume_schema():
    return {
        "user_id": None,
        "about": "",
        "education": [],
        "experience": [],
        "licenses_and_certificates": [],
        "skills": [],
        "languages": [],
        "projects": [],
        "hobbies": [],
        "references": []
    }

# Add or update resume section
@resume_bp.route('/resume', methods=['POST'])
@token_required
def add_resume_section(current_user):
    data = request.get_json()
    user_id = ObjectId(current_user)

    # Retrieve the existing resume or create a new one
    resume = resumes_collection.find_one({"user_id": user_id})
    if not resume:
        # Initialize a new resume if none exists
        resume = create_resume_schema()
        resume["user_id"] = user_id

    # Update the resume fields with the provided data, replacing existing data
    for key in resume.keys():
        if key in data:
            resume[key] = data[key]

    # Upsert the resume (insert if not exists, update otherwise)
    try:
        resumes_collection.update_one(
            {"user_id": user_id},
            {"$set": resume},
            upsert=True
        )
        return jsonify({"status": "success", "message": "Resume updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Get the resume of the logged-in user
@resume_bp.route('/resume', methods=['GET'])
@token_required
def get_resume(current_user):
    user_id = ObjectId(current_user)
    try:
        resume = resumes_collection.find_one({"user_id": user_id}, {"_id": 0})
        if resume:
            # Convert ObjectId to string
            resume["user_id"] = str(resume["user_id"])
            return jsonify({"status": "success", "resume": resume}), 200
        else:
            return jsonify({"status": "error", "message": "Resume not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# Get a specific resume by resume_id
@resume_bp.route('/resume/<resume_id>', methods=['GET'])
@token_required
def get_resume_by_id(current_user, resume_id):
    try:
        # Validate the resume_id
        resume_id = ObjectId(resume_id)
        
        # Retrieve the resume by ID
        resume = resumes_collection.find_one({"_id": resume_id})
        
        if resume:
            # Convert ObjectId to string for JSON response
            resume["user_id"] = str(resume["user_id"])
            return jsonify({"status": "success", "resume": resume}), 200
        else:
            return jsonify({"status": "error", "message": "Resume not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Get the resume by user_id
@resume_bp.route('/resume/user/<user_id>', methods=['GET'])
@token_required
def get_resume_by_user_id(current_user, user_id):
    try:
        # Check if the user_id is valid
        if not ObjectId.is_valid(user_id):
            return jsonify({"status": "error", "message": "Invalid user ID"}), 400
        
        # Retrieve the resume by user_id
        resume = resumes_collection.find_one({"user_id": ObjectId(user_id)}, {"_id": 0})
        if resume:
            # Convert ObjectId to string
            resume["user_id"] = str(resume["user_id"])
            return jsonify({"status": "success", "resume": resume}), 200
        else:
            return jsonify({"status": "error", "message": "Resume not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500