import uuid

from app.extensions import db


class Environment(db.Model):
    __tablename__ = "environments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=True)
