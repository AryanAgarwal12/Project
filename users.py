from flask import request, jsonify, Blueprint
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_cors import cross_origin
import datetime
from config import mysql, bcrypt

user_bp = Blueprint('users', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    contact = data.get('contact')
    company_name = data.get('company_name')
    password = data.get('password')
    role = data.get('role', 'user')  # default to 'user'

    if not all([name, email, password]):
        return jsonify({"error": "Name, email, and password are required"}), 400

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Email already registered"}), 409

    cursor.execute(
        "INSERT INTO users (name, email, contact, company_name, password_hash, role) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (name, email, contact, company_name, pw_hash, role)
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "User registered successfully"}), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, password_hash, role FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()

    if user and bcrypt.check_password_hash(user[1], password):
        access_token = create_access_token(
            identity=str(user[0]),
            additional_claims={'role': user[2]},
            expires_delta=datetime.timedelta(hours=1)
        )
        return jsonify({"access_token": access_token})

    return jsonify({"error": "Invalid credentials"}), 401

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name, email, contact, company_name, location, role FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "contact": user[3],
        "company_name": user[4],
        "location": user[5],
        "role": user[6]
    })

@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    claims = get_jwt()
    if claims.get('role') != 'company':
        return jsonify({"error": "Unauthorized"}), 403

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name, email, contact, company_name, location FROM users")
    users = cursor.fetchall()
    cursor.close()

    return jsonify([
        {
            "id": u[0],
            "name": u[1],
            "email": u[2],
            "contact": u[3],
            "company_name": u[4],
            "location": u[5]
        } for u in users
    ])

@user_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def get_single_user(id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name, email, contact, company_name, location FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()
    cursor.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "contact": user[3],
        "company_name": user[4],
        "location": user[5]
    })

@user_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    data = request.json
    required = ['name', 'email', 'password', 'contact', 'company_name', 'location']
    if not all(data.get(k) for k in required):
        return jsonify({"error": "All fields are required"}), 400

    pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, contact, company_name, password_hash, location) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (data['name'], data['email'], data['contact'],
         data['company_name'], pw, data['location'])
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "User added successfully"}), 201

@user_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE users SET name=%s, email=%s, contact=%s, company_name=%s, location=%s WHERE id=%s",
        (data['name'], data['email'], data['contact'],
         data['company_name'], data['location'], id)
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "User updated successfully"}), 200

@user_bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    try:
        cursor = mysql.connection.cursor()

        # Check existence
        cursor.execute("SELECT * FROM users WHERE id = %s", (id,))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            return jsonify({"error": "User not found"}), 404

        # Optional: delete related data first if constraints exist

        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        mysql.connection.rollback()
        return jsonify({"error": "Server error during deletion", "details": str(e)}), 500
