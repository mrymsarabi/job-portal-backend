from app import mongo
from bson.objectid import ObjectId

def get_users_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.users

def get_jobs_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.jobs

def get_user_by_id(user_id):
    users_collection = get_users_collection()
    return users_collection.find_one({"_id": ObjectId(user_id)})
