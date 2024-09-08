from flask import Flask
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from config import Config
from flask_cors import CORS

import logging

bcrypt = Bcrypt()
mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)


    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    handler = logging.StreamHandler()  # Log to console
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    # Enable CORS for all routes and origins
    CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"])
    
    bcrypt.init_app(app)
    mongo.init_app(app)
    
    from app.routes.users import users_bp
    from app.routes.jobs import jobs_bp
    from app.routes.resume import resume_bp
    from app.routes.job_applications import job_applications_bp
    from app.routes.companies import companies_bp 
    from app.routes.messages import messages_bp
    from app.routes.admins import admins_bp

    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(job_applications_bp, url_prefix="/job-applications")
    app.register_blueprint(companies_bp, url_prefix="/companies")
    app.register_blueprint(messages_bp, url_prefix='/messages')
    app.register_blueprint(admins_bp, url_prefix='/admins')
    
    return app
