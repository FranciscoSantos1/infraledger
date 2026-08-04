import uuid

from app.extensions import db


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
