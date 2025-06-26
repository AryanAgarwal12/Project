from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
import datetime
from config import mysql

services_bp = Blueprint('services', __name__)

@services_bp.route('/services', methods=['GET'])
def get_services():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, service_name, description FROM services")
    services = cursor.fetchall()
    cursor.close()

    return jsonify([{
        "id": s[0],
        "service_name": s[1],
        "description": s[2]
    } for s in services])

@services_bp.route('/services', methods=['POST'])
@jwt_required()
def add_service():
    data = request.json
    service_name = data.get('service_name')
    description = data.get('description')

    if not service_name:
        return jsonify({"error": "Service name is required"}), 400

    created_at = datetime.datetime.utcnow()
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO services (service_name, description, created_at) VALUES (%s, %s, %s)",
        (service_name, description, created_at)
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Service added successfully"}), 201

@services_bp.route('/user-services', methods=['POST'])
@jwt_required()
def user_service_request():
    user_id = get_jwt_identity()
    data = request.get_json()
    service_id = data.get('service_id')

    if not service_id:
        return jsonify({"error": "Service ID is required"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM services WHERE id=%s", (service_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Invalid service ID"}), 404

    cursor.execute(
        "INSERT INTO user_services (user_id, service_id) VALUES (%s, %s)",
        (user_id, service_id)
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Service requested successfully"}), 201

@services_bp.route('/user-services', methods=['GET'])
@jwt_required()
def get_user_requested_services():
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT us.id, s.service_name, s.description, us.created_at
        FROM user_services us
        JOIN services s ON us.service_id = s.id
        WHERE us.user_id = %s
    """, (user_id,))
    records = cursor.fetchall()
    cursor.close()

    return jsonify([{
        "id": r[0],
        "service_name": r[1],
        "description": r[2],
        "requested_at": str(r[3])
    } for r in records])
