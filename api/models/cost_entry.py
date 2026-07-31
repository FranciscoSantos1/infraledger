import uuid

from app.extensions import db


class CostEntry(db.Model):
    __tablename__ = "cost_entries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    resource_id = db.Column(db.String(36), db.ForeignKey("resources.id"), nullable=False)

    estimated_monthly_cost = db.Column(db.Numeric(10,2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")

    calculated_at = db.Column(db.DateTime, server_default=db.func.now())

    resource = db.relationship("Resource", backref="cost_entries")