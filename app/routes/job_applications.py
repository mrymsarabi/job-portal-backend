from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.models import get_jobs_collection, get_resumes_collection, get_job_applications_collection, get_user_by_id, get_messages_collection
from app.decorators import token_required
import datetime

# Initialize Blueprint and collections
job_applications_bp = Blueprint('job_applications', __name__)
job_applications_collection = get_job_applications_collection()
jobs_collection = get_jobs_collection()
resumes_collection = get_resumes_collection()
messages_collection = get_messages_collection()

# Define the helper function
def get_job_application_by_id(application_id):
    # Validate the application_id to ensure it's a valid ObjectId
    if not ObjectId.is_valid(application_id):
        return None
    
    # Retrieve the application from the database
    application = job_applications_collection.find_one({"_id": ObjectId(application_id)})
    
    return application

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
        "status": "pending",  # New status field
    }

    try:
        job_applications_collection.insert_one(application)
        return jsonify({"message": "Job application submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Applications for a Job (Employer)
@job_applications_bp.route('/applications/<job_id>', methods=['GET'])
@token_required
def get_applications_for_job(current_user, job_id):
    try:
        # Retrieve the job document
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        
        if not job:
            return jsonify({"status": "error", "message": "Job not found"}), 404
        
        # Ensure current user is authorized (job poster)
        user_id = job.get('posted_by', {}).get('user_id')
        if str(user_id) != current_user:
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        # Pagination parameters
        page_size = int(request.args.get('page_size', 10))
        current_page = int(request.args.get('current_page', 1))

        # Fetch applications with pagination
        total_count = job_applications_collection.count_documents({"job_id": ObjectId(job_id)})
        query = job_applications_collection.find({"job_id": ObjectId(job_id)})
        
        if current_page == 0:
            applications = list(query)
        else:
            applications = list(query.skip(page_size * (current_page - 1)).limit(page_size))

        application_list = []
        # Start counter based on the current page and page size
        counter_start = (current_page - 1) * page_size + 1

        for index, application in enumerate(applications):
            user = get_user_by_id(application["user_id"])
            application_list.append({
                "counter": counter_start + index,  # Counter value
                "application_id": str(application["_id"]),  # Include application ID
                "user_id": str(application["user_id"]),  # Include user ID
                "job_id": str(application["job_id"]),  # Include job ID
                "username": user.get("username", "Unknown"),  # Assuming 'username' is a field in user document
                "date_applied": application["date_applied"].isoformat(),  # Convert to ISO format for consistency
                "status": application["status"]
            })

        return jsonify({
            "status": "success",
            "total_count": total_count,
            "page_size": page_size,
            "current_page": current_page,
            "applications": application_list
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Get My Applications with Pagination and Messages
@job_applications_bp.route('/my-applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    # Pagination parameters
    page_size = int(request.args.get('page_size', 10))
    current_page = int(request.args.get('current_page', 1))

    # Fetch applications with pagination
    total_count = job_applications_collection.count_documents({"user_id": ObjectId(current_user)})
    query = job_applications_collection.find({"user_id": ObjectId(current_user)})
    
    if current_page == 0:
        applications = list(query)
    else:
        applications = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    applied_jobs = []
    for index, application in enumerate(applications, start=(current_page - 1) * page_size + 1):
        job = jobs_collection.find_one({"_id": application["job_id"]})
        if job:
            messages = list(messages_collection.find({"application_id": application["_id"]}))
            applied_jobs.append({
                "counter": index,
                "application_id": str(application["_id"]),
                "job_id": str(job["_id"]),
                "job_title": job["title"],
                "company_name": job.get("company_name", "N/A"),
                "location": job["location"],
                "date_applied": application["date_applied"].isoformat(),
                "status": application["status"],  # Include the status
                "messages": [
                    {
                        "sender_id": str(message["sender_id"]),
                        "message": message["message"],
                        "status": message["status"],
                        "timestamp": message["timestamp"].isoformat()
                    } for message in messages
                ]  # Include the messages
            })
    
    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "applied_jobs": applied_jobs
    }), 200

from bson.objectid import ObjectId


# Update Application Status (Employer)
@job_applications_bp.route('/applications/<application_id>/status', methods=['PATCH'])
@token_required
def update_application_status(current_user, application_id):
    data = request.get_json()

    # Validate the incoming request data
    if not data or 'status' not in data or 'message' not in data:
        return jsonify({"status": "error", "error": "Missing status or message"}), 400

    # Validate and retrieve the application by ID
    application = get_job_application_by_id(application_id)
    if not application:
        return jsonify({"status": "error", "error": "Application not found"}), 404

    # Retrieve the associated job
    job = jobs_collection.find_one({"_id": application['job_id']})
    if not job or str(job['posted_by']['user_id']) != current_user:
        return jsonify({"status": "error", "error": "Unauthorized"}), 403

    try:
        # Update the application status
        job_applications_collection.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"status": data['status']}}
        )

        # Add a message to the messages collection
        message_data = {
            "application_id": ObjectId(application_id),
            "sender_id": ObjectId(current_user),
            "receiver_id": application['applicant_id'],  # Assuming application has `applicant_id`
            "message": data['message'],
            "status": data['status'],
            "read_status": "unread",  # Default to unread
            "timestamp": datetime.datetime.utcnow()
        }
        messages_collection.insert_one(message_data)

        return jsonify({"status": "success", "message": "Application status updated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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