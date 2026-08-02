from flask import Blueprint, jsonify, request
from sqlalchemy import func

from models.cost_entry import CostEntry
from models.resources import Resource
from models.team import Team
from models.environment import Environment

costs_bp = Blueprint("costs", __name__)


def _serialize_cost_entry(entry):
    return {
        "id": entry.id,
        "resource_id": entry.resource_id,
        "resource_name": entry.resource.name,
        "estimated_monthly_cost": float(entry.estimated_monthly_cost),
        "currency": entry.currency,
        "calculated_at": entry.calculated_at.isoformat() if entry.calculated_at else None,
    }


@costs_bp.route("/costs", methods=["GET"])
def list_costs():
    query = CostEntry.query.join(Resource)

    team = request.args.get("team")
    if team:
        query = query.join(Team).filter(Team.name == team)

    environment = request.args.get("environment")
    if environment:
        query = query.join(Environment).filter(Environment.name == environment)

    resource_id = request.args.get("resource_id")
    if resource_id:
        query = query.filter(CostEntry.resource_id == resource_id)

    entries = query.order_by(CostEntry.calculated_at.desc()).all()
    return jsonify({"costs": [_serialize_cost_entry(e) for e in entries]})


@costs_bp.route("/costs/monthly", methods=["GET"])
def monthly_costs():
    from app.extensions import db
    # Latest CostEntry per resource, summed — not every historical entry,
    # or a resource priced 5 times would get counted 5 times.
    latest_per_resource = (
        db.session.query(
            CostEntry.resource_id,
            func.max(CostEntry.calculated_at).label("max_calculated_at"),
        )
        .group_by(CostEntry.resource_id)
        .subquery()
    )

    entries = (
        CostEntry.query
        .join(
            latest_per_resource,
            db.and_(
                CostEntry.resource_id == latest_per_resource.c.resource_id,
                CostEntry.calculated_at == latest_per_resource.c.max_calculated_at,
            ),
        )
        .all()
    )

    total = sum(entry.estimated_monthly_cost for entry in entries)

    return jsonify({
        "total_estimated_monthly_cost": float(total),
        "currency": "USD",
    })


@costs_bp.route("/costs/team/<team>", methods=["GET"])
def costs_by_team(team):
    entries = (
        CostEntry.query
        .join(Resource)
        .join(Team)
        .filter(Team.name == team)
        .order_by(CostEntry.calculated_at.desc())
        .all()
    )
    total = sum(entry.estimated_monthly_cost for entry in entries)
    return jsonify({
        "team": team,
        "total_estimated_monthly_cost": float(total),
        "costs": [_serialize_cost_entry(e) for e in entries],
    })


@costs_bp.route("/costs/environment/<environment>", methods=["GET"])
def costs_by_environment(environment):
    entries = (
        CostEntry.query
        .join(Resource)
        .join(Environment)
        .filter(Environment.name == environment)
        .order_by(CostEntry.calculated_at.desc())
        .all()
    )
    total = sum(entry.estimated_monthly_cost for entry in entries)
    return jsonify({
        "environment": environment,
        "total_estimated_monthly_cost": float(total),
        "costs": [_serialize_cost_entry(e) for e in entries],
    })