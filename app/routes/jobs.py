from flask import Blueprint, request, jsonify
from app.models import get_jobs_collection, get_user_by_id, get_job_applications_collection, get_company_by_id, get_companies_collection
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

    user = get_user_by_id(current_user)
    if user is None:
        return jsonify({"error": "User not found"}), 404

    # Try to retrieve the company associated with the user
    companies_collection = get_companies_collection()  # Call the function to get the collection
    company = companies_collection.find_one({"user_id": ObjectId(current_user)})

    if company:
        company_id = company['_id']
        company_name = company['title']
    else:
        company_id = None  # Set to None if the user has no associated company
        company_name = None

    # Prepare the job document
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
        "posted_by": {
            "user_id": ObjectId(current_user),
            "company_id": company_id  # Set company_id to None if no company
        },
        "company_name": company_name  # Set company_name to None if no company
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
        job['posted_by']['user_id'] = str(job['posted_by']['user_id'])
        job['posted_by']['company_id'] = str(job['posted_by']['company_id'])
        job['counter'] = index

    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "jobs": jobs
    }), 200

@jobs_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_by_id(job_id):
    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if job:
            # Convert ObjectId to string for JSON serialization
            job['_id'] = str(job['_id'])
            job['posted_by']['user_id'] = str(job['posted_by']['user_id'])
            job['posted_by']['company_id'] = str(job['posted_by']['company_id'])
            return jsonify(job), 200
        else:
            return jsonify({"error": "Job not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@jobs_bp.route('/jobs/user/<user_id>', methods=['GET'])
def get_jobs_by_user(user_id):
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = jobs_collection.find({"posted_by.user_id": ObjectId(user_id)})
    total_count = jobs_collection.count_documents({"posted_by.user_id": ObjectId(user_id)})

    if current_page == 0:
        jobs = list(query)
    else:
        jobs = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for index, job in enumerate(jobs, start=(current_page - 1) * page_size + 1):
        job['_id'] = str(job['_id'])
        job['posted_by']['user_id'] = str(job['posted_by']['user_id'])
        job['posted_by']['company_id'] = str(job['posted_by']['company_id'])
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
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = jobs_collection.find({"posted_by.user_id": ObjectId(current_user)})
    total_count = jobs_collection.count_documents({"posted_by.user_id": ObjectId(current_user)})

    if current_page == 0:
        jobs = list(query)
    else:
        jobs = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for index, job in enumerate(jobs, start=(current_page - 1) * page_size + 1):
        job['_id'] = str(job['_id'])
        job['posted_by']['user_id'] = str(job['posted_by']['user_id'])
        job['posted_by']['company_id'] = str(job['posted_by']['company_id'])
        job['counter'] = index

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

    if str(job['posted_by']['user_id']) != current_user:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        jobs_collection.delete_one({"_id": ObjectId(job_id)})
        return jsonify({"message": "Job deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
