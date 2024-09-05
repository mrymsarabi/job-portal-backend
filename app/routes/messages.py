from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.models import get_messages_collection, get_message_by_id, mark_message_as_read, get_messages_by_application_id, get_users_collection, get_jobs_collection
from app.decorators import token_required
import datetime

messages_bp = Blueprint('messages', __name__)

# Get all messages for a specific application
@messages_bp.route('/application/<application_id>', methods=['GET'])
@token_required
def get_messages_for_application(current_user, application_id):
    try:
        messages = get_messages_by_application_id(application_id)
        if not messages:
            return jsonify({"status": "error", "error": "No messages found"}), 404

        return jsonify({"status": "success", "messages": messages}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Get all messages for the current logged-in user (receiver)
@messages_bp.route('/user/messages', methods=['GET'])
@token_required
def get_messages_for_user(current_user):
    try:
        # Fetch page_size and current_page from query parameters, with defaults
        page_size = int(request.args.get('page_size', 10))  # Default to 10 messages per page
        current_page = int(request.args.get('current_page', 1))  # Default to the first page

        messages_collection = get_messages_collection()
        users_collection = get_users_collection()
        jobs_collection = get_jobs_collection()

        # Get total count of messages for the user
        total_count = messages_collection.count_documents({"receiver_id": ObjectId(current_user)})

        # Pagination logic - Skip the messages for previous pages and limit the results
        if current_page > 0:
            skip_count = (current_page - 1) * page_size
            messages_cursor = messages_collection.find({"receiver_id": ObjectId(current_user)}).skip(skip_count).limit(page_size)
        else:
            # If current_page is 0, return the whole list
            messages_cursor = messages_collection.find({"receiver_id": ObjectId(current_user)})

        messages = list(messages_cursor)

        if not messages:
            return jsonify({"status": "error", "error": "No messages found"}), 404

        # Convert ObjectId to string for JSON serialization and enrich with sender, receiver, and job info
        enriched_messages = []
        counter = (current_page - 1) * page_size + 1  # Start the counter based on the page

        for message in messages:
            message['_id'] = str(message['_id'])
            message['job_id'] = str(message['job_id'])
            message['application_id'] = str(message['application_id'])
            message['sender_id'] = str(message['sender_id'])
            message['receiver_id'] = str(message['receiver_id'])

            # Fetch the sender's and receiver's user details
            sender = users_collection.find_one({"_id": ObjectId(message['sender_id'])}, {"username": 1, "_id": 0})
            receiver = users_collection.find_one({"_id": ObjectId(message['receiver_id'])}, {"username": 1, "_id": 0})

            # Fetch job details
            job = jobs_collection.find_one({"_id": ObjectId(message['job_id'])})

            # Enrich the message with sender and receiver usernames and job details
            enriched_message = {
                'counter': counter,
                'message': message['message'],
                'status': message['status'],
                'read_status': message['read_status'],
                'timestamp': message['timestamp'],
                'sender_username': sender['username'] if sender else 'Unknown',
                'receiver_username': receiver['username'] if receiver else 'Unknown',
                'job_name': job['title'] if job else 'Unknown Job',
                'company_name': job['company_name'] if job else 'Unknown Company'
            }

            enriched_messages.append(enriched_message)
            counter += 1  # Increment the counter for each message

        return jsonify({
            "status": "success",
            "messages": enriched_messages,
            "total_count": total_count,
            "current_page": current_page,
            "page_size": page_size
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
        
# Mark a message as read
@messages_bp.route('/<message_id>/read', methods=['PATCH'])
@token_required
def mark_message_as_read_route(current_user, message_id):
    message = get_message_by_id(message_id)
    
    if not message or message.get('receiver_id') != ObjectId(current_user):
        return jsonify({"status": "error", "error": "Message not found or unauthorized"}), 404

    try:
        mark_message_as_read(message_id)
        return jsonify({"status": "success", "message": "Message marked as read"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Send a new message related to a job application
@messages_bp.route('/application/<application_id>/send', methods=['POST'])
@token_required
def send_message(current_user, application_id):
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({"status": "error", "error": "Message content is missing"}), 400

    message_data = {
        "application_id": ObjectId(application_id),
        "sender_id": ObjectId(current_user),
        "receiver_id": ObjectId(data['receiver_id']),  # Assuming you send receiver_id in the request body
        "message": data['message'],
        "status": data.get('status', 'unread'),  # Default status to 'unread'
        "timestamp": datetime.datetime.utcnow()
    }

    try:
        messages_collection = get_messages_collection()
        messages_collection.insert_one(message_data)
        return jsonify({"status": "success", "message": "Message sent successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
