from flask_pymongo import PyMongo

mongo = PyMongo()

def get_users_collection():
    return mongo.db.users

# def get_other_collection():
#     return mongo.db.other_collection
