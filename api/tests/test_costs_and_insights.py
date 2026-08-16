import json
from unittest.mock import patch
from datetime import datetime, timedelta, timezone


from app.extensions import db
from models.team import Team
from models.environment import Environment
from models.resources import Resource
from models.cost_entry import CostEntry


def _create_priced_resource(name, team_name, env_name, monthly_cost):
    team = Team.query.filter_by(name=team_name).first()
    if team is None:
        team = Team(name=team_name)
        db.session.add(team)
        db.session.flush()

    environment = Environment.query.filter_by(name=env_name).first()
    if environment is None:
        environment = Environment(name=env_name)
        db.session.add(environment)
        db.session.flush()

    resource = Resource(
        name=name,
        type="ec2",
        provider_region="eu-west-1",
        provider_sku="t3.medium",
        team_id=team.id,
        environment_id=environment.id,
        owner="francisco",
    )
    db.session.add(resource)
    db.session.flush()

    entry = CostEntry(
        resource_id=resource.id,
        estimated_monthly_cost=monthly_cost,
        currency="USD",
    )
    db.session.add(entry)
    db.session.commit()

    return resource


def test_list_costs_returns_created_entries(client, app):
    with app.app_context():
        _create_priced_resource("r1", "checkout", "prod", 33.29)

    response = client.get("/api/v1/costs")
    assert response.status_code == 200
    costs = response.get_json()["costs"]
    assert len(costs) == 1
    assert costs[0]["estimated_monthly_cost"] == 33.29


from datetime import datetime, timedelta, timezone

def test_monthly_costs_sums_latest_entry_per_resource(client, app):
    with app.app_context():
        resource = _create_priced_resource("r1", "checkout", "prod", 33.29)

        # explicitly set an earlier timestamp on the first entry, so the
        # second one is unambiguously "latest" — avoids relying on real-time
        # gaps between statements, which SQLite may not distinguish
        first_entry = CostEntry.query.filter_by(resource_id=resource.id).first()
        first_entry.calculated_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.session.commit()

        second_entry = CostEntry(
            resource_id=resource.id,
            estimated_monthly_cost=40.00,
            currency="USD",
        )
        db.session.add(second_entry)
        db.session.commit()

        _create_priced_resource("r2", "checkout", "prod", 10.00)

    response = client.get("/api/v1/costs/monthly")
    assert response.status_code == 200
    body = response.get_json()
    assert body["total_estimated_monthly_cost"] == 50.00


def test_costs_by_team_filters_correctly(client, app):
    with app.app_context():
        _create_priced_resource("r1", "checkout", "prod", 20.00)
        _create_priced_resource("r2", "platform", "prod", 15.00)

    response = client.get("/api/v1/costs/team/checkout")
    assert response.status_code == 200
    body = response.get_json()
    assert body["team"] == "checkout"
    assert len(body["costs"]) == 1


def test_costs_by_environment_filters_correctly(client, app):
    with app.app_context():
        _create_priced_resource("r1", "checkout", "prod", 20.00)
        _create_priced_resource("r2", "checkout", "staging", 5.00)

    response = client.get("/api/v1/costs/environment/staging")
    assert response.status_code == 200
    body = response.get_json()
    assert body["environment"] == "staging"
    assert len(body["costs"]) == 1


def test_expensive_resources_orders_by_cost_desc(client, app):
    with app.app_context():
        _create_priced_resource("cheap", "checkout", "prod", 5.00)
        _create_priced_resource("expensive", "checkout", "prod", 100.00)

    response = client.get("/api/v1/resources/expensive?limit=2")
    assert response.status_code == 200
    resources = response.get_json()["resources"]
    assert resources[0]["name"] == "expensive"
    assert resources[0]["estimated_monthly_cost"] == 100.00


def test_dashboard_returns_expected_shape(client, app):
    with app.app_context():
        _create_priced_resource("r1", "checkout", "prod", 33.29)

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.get_json()
    assert "total_estimated_monthly_cost" in body
    assert "cost_by_team" in body
    assert "cost_by_environment" in body
    assert "top_expensive_resources" in body
    assert "inactive_resource_count" in body
    assert body["cost_by_team"]["checkout"] == 33.29