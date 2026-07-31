import uuid
from datetime import datetime

from app.extensions import db

class Resource(db.Model):
    __tablename__ = "resources"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(
        db.Enum("ec2", "rds", "s3", "vm", "k8s_node", "load_balancer", name="resource_type"),
        nullable=False
    )

    provider_region = db.Column(db.String(36), nullable=False, default="eu-west-1")
    provider_sku = db.Column(db.String(36), nullable=False)

    team_id = db.Column(db.String(36), db.ForeignKey("teams.id"), nullable=False)
    environment_id = db.Column(db.String(36), db.ForeignKey("environments.id"), nullable=False)

    owner = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=datetime.utcnow())

    team = db.relationship("Team", backref="resources")
    environment = db.relationship("Environment", backref="resources")
    