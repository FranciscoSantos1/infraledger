from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func

from app.extensions import db
from models.resources import Resource
from models.cost_entry import CostEntry
from models.team import Team
from models.environment import Environment
from routes.resources import _serialize_resource

insights_bp = Blueprint("insights", __name__)

def _latest_cost_entries():
    """
    Return a query of CostEntry rows, one per resource - the most
    recent one.
    """

    latest_per_resource = (
        db.session.query(
            CostEntry.resource_id,
            func.max(CostEntry.calculated_at).label("max_calculated_at")
        )
        .group_by(CostEntry.resource_id)
        .subquery()
    )

    return CostEntry.query.join(
        latest_per_resource,
        db.and_(
            CostEntry.resource_id == latest_per_resource.c.resource_id,
            CostEntry.calculated_at == latest_per_resource.c.max_calculated_at,
        ),
    )


@insights_bp.route("/resources/inactive", methods=["GET"])
def inactive_resources():
    cutoff = datetime.utcnow() - timedelta(
        days=current_app.config["INACTIVE_THRESHOLD_DAYS"]
    )

    _latest_cost_per_resource = (
        db.session.query(
            CostEntry.resource_id,
            func.max(CostEntry.calculated_at).label("latest_cost_at"),
        )
        .group_by(CostEntry.resource_id)
        .subquery()
    )

    resources = (
        Resource.query
        .outerjoin(
            _latest_cost_per_resource,
            Resource.id == _latest_cost_per_resource.c.resource_id,
        )
        .filter(
            db.or_(
                Resource.is_active.is_(False),
                _latest_cost_per_resource.c.latest_cost_at.is_(None),
                _latest_cost_per_resource.c.latest_cost_at < cutoff,
            )
        )
        .all()
    )

    return jsonify({"resources": [_serialize_resource(r) for r in resources]})

@insights_bp.route("/resources/expensive", methods=["GET"])
def expensive_resourves():
    limit = request.args.get("limit", default=5, type=int)

    entries = (
        _latest_cost_entries()
        .order_by(CostEntry.estimated_monthly_cost.desc())
        .limit(limit)
        .all()
    )

    return jsonify({
        "resources": [{**_serialize_resource(e.resource), "estimated_monthly_cost": float(e.estimated_monthly_cost)}for e in entries]
    })

@insights_bp.route("/dashboard", methods=["GET"])
def dashboard():
    latest_entries = _latest_cost_entries().all()
    total_cost = sum(e.estimated_monthly_cost for e in latest_entries)

    cost_by_team = {}
    cost_by_environment = {}
    for entry in latest_entries:
        team_name = entry.resource.team.name
        env_name = entry.resource.environment.name
        cost_by_team[team_name] = cost_by_team.get(team_name, 0) + float(entry.estimated_monthly_cost)
        cost_by_environment[env_name] = cost_by_environment.get(env_name, 0) + float(entry.estimated_monthly_cost)

        top_expensive = sorted(latest_entries, key=lambda e: e.estimated_monthly_cost, reverse=True)[:5]

        inactive_count = Resource.query.filter(Resource.is_active.is_(False)).count()

        return jsonify({
        "total_estimated_monthly_cost": float(total_cost),
        "cost_by_team": cost_by_team,
        "cost_by_environment": cost_by_environment,
        "top_expensive_resources": [
            {"resource_id": e.resource_id, "name": e.resource.name, "estimated_monthly_cost": float(e.estimated_monthly_cost)}
            for e in top_expensive
        ],
        "inactive_resource_count": inactive_count,
    })
