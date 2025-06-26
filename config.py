from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# CORS Configuration
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'xform_asset_management'

# JWT Configuration
app.config["JWT_SECRET_KEY"] = "super-secret-jwt-key"
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# Extensions
mysql = MySQL(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
