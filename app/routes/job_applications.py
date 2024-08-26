from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.models import get_jobs_collection, get_resumes_collection, get_job_applications_collection, get_user_by_id, get_job_application_by_id
from app.decorators import token_required
import datetime

job_applications_bp = Blueprint('job_applications', __name__)
job_applications_collection = get_job_applications_collection()
jobs_collection = get_jobs_collection()
resumes_collection = get_resumes_collection()

# Apply for a Job
@job_applications_bp.route('/apply', methods=['POST'])
@token_required
def apply_for_job(current_user):
    data = request.get_json()
    
    required_fields = ('job_id',)
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    job = jobs_collection.find_one({"_id": ObjectId(data['job_id'])})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    resume = resumes_collection.find_one({"user_id": ObjectId(current_user)})
    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    application = {
        "job_id": ObjectId(data['job_id']),
        "user_id": ObjectId(current_user),
        "resume_id": resume["_id"],
        "date_applied": datetime.datetime.utcnow(),
    }

    try:
        job_applications_collection.insert_one(application)
        return jsonify({"message": "Job application submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Applications for a Specific Job
@job_applications_bp.route('/applications/<job_id>', methods=['GET'])
@token_required
def get_applications_for_job(current_user, job_id):
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job['company_id']) != current_user:
        return jsonify({"error": "Unauthorized"}), 403

    applications = job_applications_collection.find({"job_id": ObjectId(job_id)})
    application_list = []
    for application in applications:
        user = get_user_by_id(application["user_id"])
        resume = resumes_collection.find_one({"_id": application["resume_id"]})

        application_list.append({
            "application_id": str(application["_id"]),
            "user_id": str(application["user_id"]),
            "user_name": f"{user['first_name']} {user['last_name']}",
            "resume_id": str(application["resume_id"]),
            "resume": resume,
            "date_applied": application["date_applied"],
        })

    return jsonify({"applications": application_list}), 200

@job_applications_bp.route('/my-applications', methods=['GET'])
@token_required  # Ensure that the user is authenticated
def get_my_applications(current_user):
    applications = job_applications_collection.find({"user_id": ObjectId(current_user)})
    
    applied_jobs = []
    for application in applications:
        job = jobs_collection.find_one({"_id": application["job_id"]})
        if job:
            applied_jobs.append({
                "application_id": str(application["_id"]),
                "job_id": str(job["_id"]),
                "job_title": job["title"],
                "company_name": job.get("company_name", "N/A"),
                "location": job["location"],
                "date_applied": application["date_applied"]
            })
    
    return jsonify({"applied_jobs": applied_jobs}), 200

# Delete a Job Application
@job_applications_bp.route('/applications/<application_id>', methods=['DELETE'])
@token_required
def delete_job_application(current_user, application_id):
    application = get_job_application_by_id(application_id)
    if not application:
        return jsonify({"error": "Application not found"}), 404

    if str(application['user_id']) != current_user:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        job_applications_collection.delete_one({"_id": ObjectId(application_id)})
        return jsonify({"message": "Job application deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
