from app import mongo
from bson.objectid import ObjectId

# Collection Access Functions

def get_users_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.users

def get_jobs_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.jobs

def get_resumes_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.resumes

def get_job_applications_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.job_applications

def get_companies_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.companies

def get_messages_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.messages

# Helper Functions

def get_user_by_id(user_id):
    users_collection = get_users_collection()
    return users_collection.find_one({"_id": ObjectId(user_id)})

def get_job_application_by_id(application_id):
    applications_collection = get_job_applications_collection()
    return applications_collection.find_one({"_id": ObjectId(application_id)})

def get_company_by_id(company_id):
    companies_collection = get_companies_collection()
    return companies_collection.find_one({"_id": ObjectId(company_id)})

def get_message_by_id(message_id):
    messages_collection = get_messages_collection()
    return messages_collection.find_one({"_id": ObjectId(message_id)})

def get_messages_by_application_id(application_id):
    messages_collection = get_messages_collection()
    return list(messages_collection.find({"application_id": ObjectId(application_id)}))

def mark_message_as_read(message_id):
    messages_collection = get_messages_collection()
    return messages_collection.update_one(
        {"_id": ObjectId(message_id)},
        {"$set": {"read_status": "read"}}
    )
