from flask import Flask
from flask_cors import CORS
from config import app  # Ensure app is created in config.py
from users import user_bp
from assets import assets_bp
from services import services_bp
from maintenance import maintenance_bp

# Enable CORS
CORS(app, supports_credentials=True)

# Register blueprints ONLY ONCE
app.register_blueprint(user_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(services_bp)
app.register_blueprint(maintenance_bp)

@app.route('/test_db')
def test_db():
    from config import mysql
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT NOW()")
        now = cursor.fetchone()
        cursor.close()
        return {"status": "connected", "now": str(now[0])}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=True)
