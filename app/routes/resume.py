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

@resume_bp.route('/resume', methods=['POST'])
@token_required
def add_resume_section(current_user):
    data = request.get_json()
    user_id = ObjectId(current_user)

    resume = resumes_collection.find_one({"user_id": user_id})
    if not resume:
        # Initialize a new resume if none exists
        resume = create_resume_schema()
        resume["user_id"] = user_id

    # Update the resume fields with provided data
    if "about" in data:
        resume["about"] = data["about"]
    if "education" in data:
        resume["education"].extend(data["education"])
    if "experience" in data:
        resume["experience"].extend(data["experience"])
    if "licenses_and_certificates" in data:
        resume["licenses_and_certificates"].extend(data["licenses_and_certificates"])
    if "skills" in data:
        resume["skills"].extend(data["skills"])
    if "languages" in data:
        resume["languages"].extend(data["languages"])
    if "projects" in data:
        resume["projects"].extend(data["projects"])
    if "hobbies" in data:
        resume["hobbies"].extend(data["hobbies"])
    if "references" in data:
        resume["references"].extend(data["references"])

    # Upsert the resume (insert if not exists, update otherwise)
    try:
        resumes_collection.update_one(
            {"user_id": user_id},
            {"$set": resume},
            upsert=True
        )
        return jsonify({"message": "Resume updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@resume_bp.route('/resume', methods=['GET'])
@token_required
def get_resume(current_user):
    user_id = ObjectId(current_user)
    try:
        resume = resumes_collection.find_one({"user_id": user_id}, {"_id": 0})
        if resume:
            return jsonify({"resume": resume}), 200
        else:
            return jsonify({"message": "Resume not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ensure this route is protected, as the resume data is sensitive and should only be accessed by the respective user.
@resume_bp.route('/resume', methods=['DELETE'])
@token_required
def delete_resume_section(current_user):
    data = request.get_json()
    user_id = ObjectId(current_user)

    try:
        resume = resumes_collection.find_one({"user_id": user_id})
        if not resume:
            return jsonify({"message": "Resume not found"}), 404

        # Remove specific sections or entire resume
        for key in data.keys():
            if key in resume:
                resume.pop(key, None)

        if resume == {"user_id": user_id}:
            # If all fields are removed, delete the entire document
            resumes_collection.delete_one({"user_id": user_id})
        else:
            # Otherwise, update the document with the remaining fields
            resumes_collection.update_one({"user_id": user_id}, {"$set": resume})

        return jsonify({"message": "Resume section(s) deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
