from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import mysql

maintenance_bp = Blueprint('maintenance', __name__)

# Get all maintenance records for a specific asset
@maintenance_bp.route('/assets/<int:asset_id>/maintenance', methods=['GET'])
@jwt_required()
def get_maintenance(asset_id):
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM assets WHERE id=%s AND assigned_to=%s", (asset_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Asset not found or not authorized"}), 404

    cursor.execute(
        "SELECT id, maintenance_date, maintenance_type, performed_by, notes, created_at, status FROM maintenance_records WHERE asset_id=%s",
        (asset_id,)
    )
    records = cursor.fetchall()
    cursor.close()

    return jsonify([{
        "id": r[0],
        "maintenance_date": str(r[1]),
        "maintenance_type": r[2],
        "performed_by": r[3],
        "notes": r[4],
        "created_at": str(r[5]),
        "status": r[6]
    } for r in records])


# Add maintenance record
@maintenance_bp.route('/assets/<int:asset_id>/maintenance', methods=['POST'])
@jwt_required()
def add_maintenance(asset_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['maintenance_date', 'maintenance_type', 'performed_by', 'status']
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM assets WHERE id=%s AND assigned_to=%s", (asset_id, user_id))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Asset not found or not authorized"}), 404

    cursor.execute(
        '''
        INSERT INTO maintenance_records 
        (asset_id, maintenance_date, maintenance_type, performed_by, notes, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        ''',
        (
            asset_id,
            data['maintenance_date'],
            data['maintenance_type'],
            data['performed_by'],
            data.get('notes', ''),
            data['status']
        )
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Maintenance record added successfully"}), 201


# Get single maintenance record
@maintenance_bp.route('/maintenance/<int:maintenance_id>', methods=['GET'])
@jwt_required()
def get_maintenance_detail(maintenance_id):
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT mr.id, mr.maintenance_date, mr.maintenance_type, mr.performed_by, mr.notes, mr.created_at, mr.status
        FROM maintenance_records mr
        JOIN assets a ON mr.asset_id = a.id
        WHERE mr.id = %s AND a.assigned_to = %s
    ''', (maintenance_id, user_id))

    record = cursor.fetchone()
    cursor.close()

    if not record:
        return jsonify({"error": "Maintenance record not found or not authorized"}), 404

    return jsonify({
        "id": record[0],
        "maintenance_date": str(record[1]),
        "maintenance_type": record[2],
        "performed_by": record[3],
        "notes": record[4],
        "created_at": str(record[5]),
        "status": record[6]
    })


# Update maintenance record
@maintenance_bp.route('/maintenance/<int:maintenance_id>', methods=['PUT'])
@jwt_required()
def update_maintenance(maintenance_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT mr.id FROM maintenance_records mr
        JOIN assets a ON mr.asset_id = a.id
        WHERE mr.id = %s AND a.assigned_to = %s
    ''', (maintenance_id, user_id))

    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Record not found or not authorized"}), 404

    cursor.execute(
        '''
        UPDATE maintenance_records 
        SET maintenance_date=%s, maintenance_type=%s, performed_by=%s, notes=%s, status=%s 
        WHERE id=%s
        ''',
        (
            data.get('maintenance_date'),
            data.get('maintenance_type'),
            data.get('performed_by'),
            data.get('notes', ''),
            data.get('status'),
            maintenance_id
        )
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Record updated successfully"}), 200


# Delete maintenance record
@maintenance_bp.route('/maintenance/<int:maintenance_id>', methods=['DELETE'])
@jwt_required()
def delete_maintenance(maintenance_id):
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT mr.id FROM maintenance_records mr
        JOIN assets a ON mr.asset_id = a.id
        WHERE mr.id = %s AND a.assigned_to = %s
    ''', (maintenance_id, user_id))

    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Record not found or not authorized"}), 404

    cursor.execute("DELETE FROM maintenance_records WHERE id=%s", (maintenance_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Record deleted successfully"}), 200

# Get all maintenance records for company user
@maintenance_bp.route('/maintenance/all', methods=['GET'])
@jwt_required()
def get_all_maintenance():
    user_id = get_jwt_identity()
    cursor = mysql.connection.cursor()

    # Check user role
    cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
    user_role = cursor.fetchone()[0]

    if user_role == "company":
        cursor.execute("""
            SELECT mr.id, mr.maintenance_date, mr.maintenance_type, mr.performed_by, mr.notes, 
                   mr.created_at, mr.status, mr.asset_id, a.name
            FROM maintenance_records mr
            JOIN assets a ON mr.asset_id = a.id
            ORDER BY mr.maintenance_date DESC
        """)
    else:
        cursor.execute("""
            SELECT mr.id, mr.maintenance_date, mr.maintenance_type, mr.performed_by, mr.notes, 
                   mr.created_at, mr.status, mr.asset_id, a.name
            FROM maintenance_records mr
            JOIN assets a ON mr.asset_id = a.id
            WHERE a.assigned_to = %s
            ORDER BY mr.maintenance_date DESC
        """, (user_id,))

    records = cursor.fetchall()
    cursor.close()

    return jsonify([{
        "id": r[0],
        "maintenance_date": str(r[1]),
        "maintenance_type": r[2],
        "performed_by": r[3],
        "notes": r[4],
        "created_at": str(r[5]),
        "status": r[6],
        "asset_id": r[7],
        "asset_name": r[8] or f"# {r[7]}"  # Fallback if name is None
    } for r in records])
