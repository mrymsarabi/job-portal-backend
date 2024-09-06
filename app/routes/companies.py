from flask import Blueprint, request, jsonify
from app.models import get_companies_collection, get_user_by_id
from app.decorators import token_required
from bson.objectid import ObjectId
import datetime

companies_bp = Blueprint('companies', __name__)
companies_collection = get_companies_collection()

@companies_bp.route('/companies', methods=['POST'])
@token_required
def add_company(current_user):
    data = request.get_json()
    required_fields = ('title', 'about_us', 'number_of_employees', 'founded_date')

    # Check if required fields are present
    if not all(key in data for key in required_fields):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    user = get_user_by_id(current_user)
    if user is None:
        return jsonify({"status": "error", "message": "User not found"}), 404

    company = {
        "title": data['title'],
        "about_us": data['about_us'],
        "number_of_employees": data['number_of_employees'],
        "founded_date": data['founded_date'],
        "user_id": ObjectId(current_user),  # Associate the company with the user
        "created_at": datetime.datetime.utcnow()
    }

    try:
        result = companies_collection.insert_one(company)
        return jsonify({
            "status": "success",
            "message": "Company added successfully",
            "company_id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@companies_bp.route('/companies/<company_id>', methods=['PUT'])
@token_required
def update_company(current_user, company_id):
    data = request.get_json()

    # Check if the company exists and is associated with the current user
    company = companies_collection.find_one({"_id": ObjectId(company_id), "user_id": ObjectId(current_user)})
    if company is None:
        return jsonify({"status": "error", "message": "Company not found or unauthorized"}), 404

    update_data = {}
    
    # Collect the fields to update
    if 'title' in data:
        update_data['title'] = data['title']
    if 'about_us' in data:
        update_data['about_us'] = data['about_us']
    if 'number_of_employees' in data:
        update_data['number_of_employees'] = data['number_of_employees']
    if 'founded_date' in data:
        update_data['founded_date'] = data['founded_date']

    # If no fields are provided for update, return an error
    if not update_data:
        return jsonify({"status": "error", "message": "No data provided for update"}), 400

    try:
        # Perform the update
        companies_collection.update_one({"_id": ObjectId(company_id)}, {"$set": update_data})
        return jsonify({"status": "success", "message": "Company updated successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@companies_bp.route('/companies', methods=['GET'])
def get_all_companies():
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = companies_collection.find()
    total_count = companies_collection.count_documents({})  # Count total documents

    if current_page == 0:
        companies = list(query)
    else:
        companies = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for company in companies:
        company['_id'] = str(company['_id'])
        company['user_id'] = str(company['user_id'])

    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "companies": companies
    }), 200

@companies_bp.route('/companies/user/<user_id>', methods=['GET'])
def get_companies_by_user(user_id):
    page_size = int(request.args.get('page_size', 10))  # Default page size is 10
    current_page = int(request.args.get('current_page', 1))  # Default to the first page

    query = companies_collection.find({"user_id": ObjectId(user_id)})
    total_count = companies_collection.count_documents({"user_id": ObjectId(user_id)})

    if current_page == 0:
        companies = list(query)
    else:
        companies = list(query.skip(page_size * (current_page - 1)).limit(page_size))

    for company in companies:
        company['_id'] = str(company['_id'])
        company['user_id'] = str(company['user_id'])

    return jsonify({
        "total_count": total_count,
        "page_size": page_size,
        "current_page": current_page,
        "companies": companies
    }), 200

@companies_bp.route('/companies/<company_id>', methods=['GET'])
def get_company(company_id):
    company = companies_collection.find_one({"_id": ObjectId(company_id)})

    if not company:
        return jsonify({"status": "error", "message": "Company not found"}), 404

    company['_id'] = str(company['_id'])
    company['user_id'] = str(company['user_id'])

    return jsonify({"status": "success", "company": company}), 200

@companies_bp.route('/companies/mine', methods=['GET'])
@token_required
def get_my_company(current_user):
    try:
        # Find the company associated with the current user
        company = companies_collection.find_one({"user_id": ObjectId(current_user)})

        if not company:
            return jsonify({"status": "error", "message": "Company not found"}), 404

        # Format the company data to match the structure provided
        formatted_company = {
            "_id": str(company["_id"]),
            "title": company.get("title", ""),
            "about_us": company.get("about_us", ""),
            "number_of_employees": company.get("number_of_employees", ""),
            "founded_date": company.get("founded_date", ""),
            "user_id": str(company["user_id"]),
            "created_at": company["created_at"].isoformat() if company.get("created_at") else None
        }

        return jsonify({"status": "success", "company": formatted_company}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

