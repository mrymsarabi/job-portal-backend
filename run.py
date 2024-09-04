from app import create_app
from flask_cors import CORS

app = create_app()
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"])


if __name__ == '__main__':
    app.run(debug=True)