from flask import Blueprint, request, jsonify, current_app
from app.models import get_jobs_collection, get_user_by_id
from app.decorators import token_required
from bson.objectid import ObjectId
import datetime

jobs_bp = Blueprint('jobs', __name__)
jobs_collection = get_jobs_collection()

@jobs_bp.route('/jobs', methods=['POST'])
@token_required
def add_job(current_user):
    data = request.get_json()
    required_fields = ('title', 'sector', 'salary', 'location', 'job_type', 'requirements', 'description', 'benefits')

    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    # Retrieve the user document
    user = get_user_by_id(current_user)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    job = {
        "title": data['title'],
        "date_posted": datetime.datetime.utcnow(),
        "sector": data['sector'],
        "salary": data['salary'],
        "location": data['location'],
        "job_type": data['job_type'],
        "requirements": data['requirements'],
        "description": data['description'],
        "benefits": data['benefits'],
        "company_id": current_user,
        "company_name": user.get('username')  # Now user is defined and you can access the username
    }

    try:
        jobs_collection.insert_one(job)
        return jsonify({"message": "Job posted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/jobs', methods=['GET'])
def get_jobs():
    jobs = list(jobs_collection.find())
    for job in jobs:
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
    return jsonify(jobs), 200

@jobs_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if job:
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
        return jsonify(job), 200
    else:
        return jsonify({"error": "Job not found"}), 404

@jobs_bp.route('/jobs/<job_id>', methods=['DELETE'])
@token_required
def delete_job(current_user, job_id):
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if job and str(job['company_id']) == current_user:
        jobs_collection.delete_one({"_id": ObjectId(job_id)})
        return jsonify({"message": "Job deleted successfully"}), 200
    else:
        return jsonify({"error": "Job not found or unauthorized"}), 404

@jobs_bp.route('/jobs/<job_id>', methods=['PUT'])
@token_required
def update_job(current_user, job_id):
    data = request.get_json()
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})

    if job and str(job['company_id']) == current_user:
        updated_fields = {}
        for key in ('title', 'sector', 'salary', 'location', 'job_type', 'requirements', 'description', 'benefits'):
            if key in data:
                updated_fields[key] = data[key]
        
        if updated_fields:
            jobs_collection.update_one({"_id": ObjectId(job_id)}, {"$set": updated_fields})
            return jsonify({"message": "Job updated successfully"}), 200
        else:
            return jsonify({"error": "No fields to update"}), 400
    else:
        return jsonify({"error": "Job not found or unauthorized"}), 404

@jobs_bp.route('/jobs/user', methods=['GET'])
@token_required
def get_jobs_by_user(current_user):
    jobs = list(jobs_collection.find({"company_id": current_user}))
    for job in jobs:
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
    return jsonify(jobs), 200

@jobs_bp.route('/test', methods=['GET'])
def test_route():
    return "Test route is working!"
