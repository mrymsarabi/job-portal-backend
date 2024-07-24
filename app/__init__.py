from flask import Flask
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from flask_cors import CORS
from config import Config

mongo = PyMongo()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    mongo.init_app(app)
    bcrypt.init_app(app)
    CORS(app)

    from app.routes.users import users_bp
    
    app.register_blueprint(users_bp, url_prefix='/users')

    return app
