from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from config import mysql

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/assets', methods=['POST'])
@jwt_required()
def create_asset():
    claims = get_jwt()
    if claims.get('role') != 'company':
        return jsonify({"error": "Only company can create assets"}), 403

    data = request.json
    required = ['asset_name', 'asset_type', 'serial_number', 'purchase_date', 'warranty_expiry', 'user_id']
    if not all(data.get(k) for k in required):
        return jsonify({"error": "All fields are required"}), 400

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM users WHERE id=%s", (data['user_id'],))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        return jsonify({"error": "User not found"}), 404

    cursor.execute(
        "INSERT INTO assets (asset_name, asset_type, serial_number, purchase_date, warranty_expiry, assigned_to) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (data['asset_name'], data['asset_type'], data['serial_number'],
         data['purchase_date'], data['warranty_expiry'], data['user_id'])
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Asset created successfully"}), 201

@assets_bp.route('/assets', methods=['GET'])
@jwt_required()
def list_assets():
    current_user = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    sel_user = request.args.get('user_id')
    cursor = mysql.connection.cursor()
    if role == 'user':
        cursor.execute(
            "SELECT id, asset_name, asset_type, serial_number, purchase_date, warranty_expiry, status "
            "FROM assets WHERE assigned_to=%s", (current_user,)
        )
    else:
        if sel_user:
            cursor.execute(
                "SELECT id, asset_name, asset_type, serial_number, purchase_date, warranty_expiry, status "
                "FROM assets WHERE assigned_to=%s", (sel_user,)
            )
        else:
            cursor.execute(
                "SELECT id, asset_name, asset_type, serial_number, purchase_date, warranty_expiry, status FROM assets"
            )

    assets = cursor.fetchall()
    cursor.close()
    return jsonify([
        {
            "id": a[0],
            "asset_name": a[1],
            "asset_type": a[2],
            "serial_number": a[3],
            "purchase_date": str(a[4]) if a[4] else None,
            "warranty_expiry": str(a[5]) if a[5] else None,
            "status": a[6]
        } for a in assets
    ]), 200

@assets_bp.route('/assets/<int:asset_id>', methods=['GET'])
@jwt_required()
def get_asset(asset_id):
    claims = get_jwt()
    user_id = get_jwt_identity()
    role = claims.get('role')

    cursor = mysql.connection.cursor()

    if role == 'user':
        cursor.execute(
            "SELECT id, asset_name, asset_type, serial_number, purchase_date, warranty_expiry, status, assigned_to "
            "FROM assets WHERE id=%s AND assigned_to=%s", (asset_id, user_id)
        )
    else:
        cursor.execute(
            "SELECT id, asset_name, asset_type, serial_number, purchase_date, warranty_expiry, status, assigned_to "
            "FROM assets WHERE id=%s", (asset_id,)
        )

    asset = cursor.fetchone()
    cursor.close()

    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    return jsonify({
        "id": asset[0],
        "asset_name": asset[1],
        "asset_type": asset[2],
        "serial_number": asset[3],
        "purchase_date": str(asset[4]),
        "warranty_expiry": str(asset[5]),
        "status": asset[6],
        "user_id": asset[7]
    }), 200

@assets_bp.route('/assets/<int:asset_id>', methods=['DELETE'])
@jwt_required()
def delete_asset(asset_id):
    claims = get_jwt()
    if claims.get('role') != 'company':
        return jsonify({"error": "Only company can delete assets"}), 403

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM assets WHERE id=%s", (asset_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Asset not found"}), 404

    cursor.execute("DELETE FROM maintenance_records WHERE asset_id=%s", (asset_id,))
    cursor.execute("DELETE FROM assets WHERE id=%s", (asset_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Asset deleted successfully"}), 200

@assets_bp.route('/assets/<int:asset_id>', methods=['PUT'])
@jwt_required()
def update_asset(asset_id):
    claims = get_jwt()
    if claims.get('role') != 'company':
        return jsonify({"error": "Only company can update assets"}), 403

    data = request.json
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM assets WHERE id=%s", (asset_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Asset not found"}), 404

    cursor.execute(
        "UPDATE assets SET asset_name=%s, asset_type=%s, serial_number=%s, "
        "purchase_date=%s, warranty_expiry=%s, status=%s, assigned_to=%s WHERE id=%s",
        (
            data.get('asset_name'),
            data.get('asset_type'),
            data.get('serial_number'),
            data.get('purchase_date'),
            data.get('warranty_expiry'),
            data.get('status'),
            data.get('user_id'),
            asset_id
        )
    )
    mysql.connection.commit()
    cursor.close()
    return jsonify({"message": "Asset updated successfully"}), 200

# Ensure /users route returns username
@assets_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    cursor.close()
    return jsonify([
        {"id": u[0], "username": u[1]} for u in users
    ])
