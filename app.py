"""Small apps to demonstrate endpoints with basic feature - CRUD"""

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import jwt
from api.auth.endpoints import auth_endpoints
from api.profile.endpoints import profile_endpoints
from api.instruments.endpoints import instruments_endpoints
from api.loan.endpoints import loan_endpoints
from api.reviews.endpoints import reviews_endpoints
from api.data_protected.endpoints import protected_endpoints
from config import Config
from static.static_file_server import static_file_server

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


jwt.init_app(app)

# register the blueprint
app.register_blueprint(auth_endpoints, url_prefix='/api/v1/auth')
app.register_blueprint(protected_endpoints,
                       url_prefix='/api/v1/protected')
app.register_blueprint(static_file_server, url_prefix='/static/')
app.register_blueprint(profile_endpoints, url_prefix='/api/v1/profile')
app.register_blueprint(instruments_endpoints, url_prefix='/api/v1/instruments')
app.register_blueprint(loan_endpoints, url_prefix='/api/v1/loan')
app.register_blueprint(reviews_endpoints, url_prefix='/api/v1/reviews')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
