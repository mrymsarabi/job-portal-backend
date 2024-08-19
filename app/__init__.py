from flask import Flask
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo
from config import Config
from flask_cors import CORS

bcrypt = Bcrypt()
mongo = PyMongo()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for all routes and origins
    CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"])
    
    bcrypt.init_app(app)
    mongo.init_app(app)
    
    from app.routes.users import users_bp
    from app.routes.jobs import jobs_bp
    from app.routes.resume import resume_bp
    from app.routes.job_applications from job_applications_bp
    
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(job_applications_bp, url_prefix="/job-applications")
    
    return app
