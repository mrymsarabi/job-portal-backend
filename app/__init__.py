from flask import Flask
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from config import Config

bcrypt = Bcrypt()
mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    bcrypt.init_app(app)
    mongo.init_app(app)
    
    from app.routes.users import users_bp
    from app.routes.jobs import jobs_bp
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(jobs_bp)
    
    return app
