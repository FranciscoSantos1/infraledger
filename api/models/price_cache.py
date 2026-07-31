import uuid

from app.extensions import db


class PriceCache(db.Model):
    __tablename__ = "price_cache"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    service_code = db.Column(db.String(50), nullable=False)
    sku = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(30), nullable=False)

    price_per_unit = db.Column(db.Numeric(10, 6), nullable=False)
    unit = db.Column(db.String(20), nullable=False)

    fetched_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (
        db.UniqueConstraint("service_code", "sku", "region", name="uq_price_cache_lookup"),
    )