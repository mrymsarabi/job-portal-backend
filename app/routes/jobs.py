from flask import Blueprint, request, jsonify
from app.models import get_jobs_collection, get_user_by_id, get_job_applications_collection
from app.decorators import token_required
from bson.objectid import ObjectId
import datetime

jobs_bp = Blueprint('jobs', __name__)
jobs_collection = get_jobs_collection()
job_applications_collection = get_job_applications_collection()

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
        "company_name": user.get('username')
    }

    try:
        jobs_collection.insert_one(job)
        return jsonify({"message": "Job posted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jobs_bp.route('/jobs', methods=['GET'])
def get_jobs():
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = jobs_collection.find()
    total_count = jobs_collection.count_documents({})  # Count total documents

    if current_page == 0:
        jobs = list(query)
    else:
        jobs = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for index, job in enumerate(jobs, start=(current_page - 1) * page_size + 1):
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
        job['counter'] = index

    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "jobs": jobs
    }), 200


@jobs_bp.route('/jobs/user', methods=['GET'])
def get_jobs_by_user():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = jobs_collection.find({"company_id": user_id})
    total_count = jobs_collection.count_documents({"company_id": user_id})

    if current_page == 0:
        jobs = list(query)
    else:
        jobs = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for index, job in enumerate(jobs, start=(current_page - 1) * page_size + 1):
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
        job['counter'] = index

    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "jobs": jobs
    }), 200


@jobs_bp.route('/jobs/mine', methods=['GET'])
@token_required
def get_my_jobs(current_user):
    # Retrieve pagination parameters from the query string
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    # Query for jobs associated with the current user
    query = jobs_collection.find({"company_id": current_user})
    total_count = jobs_collection.count_documents({"company_id": current_user})

    # Paginate results
    if current_page == 0:  # Fetch all results without pagination
        jobs = list(query)
    else:
        jobs = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    # Convert ObjectIds to strings for JSON serialization and add counters
    for index, job in enumerate(jobs, start=(current_page - 1) * page_size + 1):
        job['_id'] = str(job['_id'])
        job['company_id'] = str(job['company_id'])
        job['counter'] = index

    # Return paginated job results with metadata
    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "jobs": jobs
    }), 200

@jobs_bp.route('/jobs/<job_id>', methods=['DELETE'])
@token_required
def delete_job(current_user, job_id):
    job = jobs_collection.find_one({"_id": ObjectId(job_id)})

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if str(job['company_id']) != current_user:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        jobs_collection.delete_one({"_id": ObjectId(job_id)})
        return jsonify({"message": "Job deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
