from flask import Blueprint, request, jsonify
from app.models import get_users_collection, get_jobs_collection, get_job_applications_collection
from app.decorators import token_required_admin 
from bson.objectid import ObjectId
import datetime

reports_bp = Blueprint('reports', __name__)

users_collection = get_users_collection()
jobs_collection = get_jobs_collection()
applicants_collection = get_job_applications_collection()

# Helper function to parse dates and times
def parse_datetime(datetime_str):
    try:
        return datetime.datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None

@reports_bp.route('/report/users', methods=['GET'])
@token_required_admin
def report_users(current_admin):  # Accept the current_admin argument
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"status": "error", "message": "Start date and end date are required"}), 400

    # Parse the dates using parse_datetime to handle date + time
    start_date_parsed = parse_datetime(start_date)
    end_date_parsed = parse_datetime(end_date)

    if not start_date_parsed or not end_date_parsed:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS."}), 400

    # Filter users based on creation date (assuming 'createdAt' field exists)
    user_count = users_collection.count_documents({
        "createdAt": {"$gte": start_date_parsed, "$lt": end_date_parsed}
    })

    return jsonify({
        "status": "success",
        "start_date": start_date,
        "end_date": end_date,
        "user_count": user_count
    }), 200
