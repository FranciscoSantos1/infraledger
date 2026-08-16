from unittest.mock import patch, MagicMock
import json

from models.price_cache import PriceCache
from app.extensions import db
from decimal import Decimal

SAMPLE_PRICE_LIST_ITEM = json.dumps({
    "terms": {
        "OnDemand": {
            "term-key-abc": {
                "priceDimensions": {
                    "dimension-key-xyz": {
                        "unit": "Hrs",
                        "pricePerUnit": {"USD": "0.0456000000"},
                    }
                }
            }
        }
    }
})


def test_extract_on_demand_price():
    from services.pricing_service import _extract_on_demand_price

    price_item = json.loads(SAMPLE_PRICE_LIST_ITEM)
    price, unit = _extract_on_demand_price(price_item)

    assert price == 0.0456
    assert unit == "Hrs"


def test_fetch_price_from_aws_creates_cache_entry(app):
    from services.pricing_service import fetch_price_from_aws

    with app.app_context():
        mock_response = {"PriceList": [SAMPLE_PRICE_LIST_ITEM]}

        with patch("services.pricing_service._pricing_client") as mock_client:
            mock_client.get_products.return_value = mock_response

            result = fetch_price_from_aws("AmazonEC2", "t3.medium", "eu-west-1")

            assert result.price_per_unit == Decimal("0.0456")
            assert result.unit == "Hrs"
            assert result.service_code == "AmazonEC2"
            assert result.sku == "t3.medium"
            assert result.region == "eu-west-1"

            mock_client.get_products.assert_called_once()
            call_kwargs = mock_client.get_products.call_args.kwargs
            assert call_kwargs["ServiceCode"] == "AmazonEC2"


def test_fetch_price_from_aws_updates_existing_cache_entry(app):
    from services.pricing_service import fetch_price_from_aws

    with app.app_context():
        existing = PriceCache(
            service_code="AmazonEC2",
            sku="t3.medium",
            region="eu-west-1",
            price_per_unit=999,
            unit="Hrs",
        )
        db.session.add(existing)
        db.session.commit()
        existing_id = existing.id

        mock_response = {"PriceList": [SAMPLE_PRICE_LIST_ITEM]}
        with patch("services.pricing_service._pricing_client") as mock_client:
            mock_client.get_products.return_value = mock_response

            result = fetch_price_from_aws("AmazonEC2", "t3.medium", "eu-west-1")

            assert result.id == existing_id  # same row, not a duplicate
            assert result.price_per_unit == Decimal("0.0456")

            all_entries = PriceCache.query.filter_by(
                service_code="AmazonEC2", sku="t3.medium", region="eu-west-1"
            ).all()
            assert len(all_entries) == 1  # confirms upsert, not duplicate insert


def test_fetch_price_from_aws_raises_on_no_results(app):
    from services.pricing_service import fetch_price_from_aws

    with app.app_context():
        with patch("services.pricing_service._pricing_client") as mock_client:
            mock_client.get_products.return_value = {"PriceList": []}

            try:
                fetch_price_from_aws("AmazonEC2", "t3.medium", "eu-west-1")
                assert False, "expected a ValueError"
            except ValueError:
                pass


def test_get_price_uses_fresh_cache_without_calling_aws(app):
    from services.pricing_service import get_price
    from datetime import datetime, timezone

    with app.app_context():
        cached = PriceCache(
            service_code="AmazonEC2",
            sku="t3.medium",
            region="eu-west-1",
            price_per_unit=0.05,
            unit="Hrs",
            fetched_at=datetime.now(timezone.utc),
        )
        db.session.add(cached)
        db.session.commit()

        with patch("services.pricing_service._pricing_client") as mock_client:
            result = get_price("AmazonEC2", "t3.medium", "eu-west-1")

            assert result.price_per_unit == Decimal("0.05")
            mock_client.get_products.assert_not_called()  # cache hit, no AWS call


def test_calculate_monthly_cost_creates_cost_entry(app):
    from services.pricing_service import calculate_monthly_cost
    from models.resources import Resource
    from models.team import Team
    from models.environment import Environment

    with app.app_context():
        team = Team(name="checkout")
        environment = Environment(name="prod")
        db.session.add_all([team, environment])
        db.session.flush()

        resource = Resource(
            name="test-ec2",
            type="ec2",
            provider_region="eu-west-1",
            provider_sku="t3.medium",
            team_id=team.id,
            environment_id=environment.id,
            owner="francisco",
        )
        db.session.add(resource)
        db.session.commit()

        mock_response = {"PriceList": [SAMPLE_PRICE_LIST_ITEM]}
        with patch("services.pricing_service._pricing_client") as mock_client:
            mock_client.get_products.return_value = mock_response

            entry = calculate_monthly_cost(resource)

            assert entry.currency == "USD"
            assert float(entry.estimated_monthly_cost) == 33.29  # 0.0456 * 730, rounded


def test_calculate_monthly_cost_raises_for_unsupported_type(app):
    from services.pricing_service import calculate_monthly_cost
    from models.resources import Resource
    from models.team import Team
    from models.environment import Environment

    with app.app_context():
        team = Team(name="checkout")
        environment = Environment(name="prod")
        db.session.add_all([team, environment])
        db.session.flush()

        resource = Resource(
            name="test-s3",
            type="s3",
            provider_region="eu-west-1",
            provider_sku="standard",
            team_id=team.id,
            environment_id=environment.id,
            owner="francisco",
        )
        db.session.add(resource)
        db.session.commit()

        try:
            calculate_monthly_cost(resource)
            assert False, "expected a ValueError"
        except ValueError:
            pass