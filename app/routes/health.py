from flask import Blueprint, jsonify
# This code defines a Flask blueprint for a health check endpoint. 
# The `/health` route returns a JSON response indicating that the service is healthy, along with an HTTP status code of 200
health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

