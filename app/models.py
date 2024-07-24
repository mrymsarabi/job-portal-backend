from app import mongo

def get_users_collection():
    if mongo.db is None:
        raise RuntimeError("MongoDB not initialized")
    return mongo.db.users
