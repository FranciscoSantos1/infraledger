from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    db_status = 'ok'
    status_code = 200

    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = 'error'
        status_code = 503

    return jsonify({"status": "ok" if db_status == "ok" else "error",
                   "database" : db_status}), status_code
