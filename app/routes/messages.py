from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from app.models import get_messages_collection, get_message_by_id, mark_message_as_read, get_messages_by_application_id
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
        # Fetch messages where receiver_id matches the current_user
        messages_collection = get_messages_collection()
        messages = list(messages_collection.find({"receiver_id": ObjectId(current_user)}))

        if not messages:
            return jsonify({"status": "error", "error": "No messages found"}), 404

        # Convert ObjectId to string for JSON serialization
        for message in messages:
            message['_id'] = str(message['_id'])
            message['application_id'] = str(message['application_id'])
            message['sender_id'] = str(message['sender_id'])
            message['receiver_id'] = str(message['receiver_id'])

        return jsonify({"status": "success", "messages": messages}), 200

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
