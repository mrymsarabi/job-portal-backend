from flask import Blueprint, request, jsonify
from app.models import get_users_collection, get_jobs_collection, get_job_applications_collection
from app.decorators import token_required_admin 
import datetime

reports_bp = Blueprint('reports', __name__)

# Getting the collections
users_collection = get_users_collection()
jobs_collection = get_jobs_collection()
applicants_collection = get_job_applications_collection()

# Helper function to parse dates and times
def parse_datetime(datetime_str):
    try:
        return datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None

# Report for counting users registered between a given date range
@reports_bp.route('/report/users', methods=['GET'])
@token_required_admin
def report_users(current_admin):
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Start date and end date are required"}), 400

    # Parse the dates using parse_datetime
    start_date_parsed = parse_datetime(start_date)
    end_date_parsed = parse_datetime(end_date)

    if not start_date_parsed or not end_date_parsed:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS."}), 400

    # Count users created in the given date range
    user_count = users_collection.count_documents({
        "createdAt": {"$gte": start_date_parsed, "$lt": end_date_parsed}
    })

    return jsonify({
        "status": "success",
        "start_date": start_date,
        "end_date": end_date,
        "user_count": user_count
    }), 200


# Report for counting jobs posted between a given date range
@reports_bp.route('/report/jobs', methods=['GET'])
@token_required_admin
def report_jobs(current_admin):
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Start date and end date are required"}), 400

    # Parse the dates using parse_datetime
    start_date_parsed = parse_datetime(start_date)
    end_date_parsed = parse_datetime(end_date)

    if not start_date_parsed or not end_date_parsed:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS."}), 400

    # Count jobs posted in the given date range
    job_count = jobs_collection.count_documents({
        "date_posted": {"$gte": start_date_parsed, "$lt": end_date_parsed}
    })

    return jsonify({
        "status": "success",
        "start_date": start_date,
        "end_date": end_date,
        "job_count": job_count
    }), 200
