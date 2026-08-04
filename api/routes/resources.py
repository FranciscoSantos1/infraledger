from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from models.environment import Environment
from models.resources import Resource
from models.team import Team
from services.pricing_service import calculate_monthly_cost

resources_bp = Blueprint("resources", __name__)


def _error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


def _get_or_create_team(name):
    team = Team.query.filter_by(name=name).first()
    if team is None:
        team = Team(name=name)
        db.session.add(team)
        db.session.flush()  # flushes all the object changes into the database
    return team


def _get_or_create_environment(name):
    environment = Environment.query.filter_by(name=name).first()
    if environment is None:
        environment = Environment(name=name)
        db.session.add(environment)
        db.session.flush()  # flushes all the object changes into the database
    return environment


def _serialize_resource(resource):
    return {
        "id": resource.id,
        "name": resource.name,
        "type": resource.type,
        "provider_region": resource.provider_region,
        "provider_sku": resource.provider_sku,
        "team": resource.team.name,
        "environment": resource.environment.name,
        "owner": resource.owner,
        "is_active": resource.is_active,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }


@resources_bp.route("/resources", methods=["GET"])
def list_resources():
    resources = Resource.query.all()
    return jsonify({"resources": [_serialize_resource(r) for r in resources]})


@resources_bp.route("/resources/<resource_id>", methods=["GET"])
def get_resource(resource_id):
    resource = Resource.query.get(resource_id)
    if resource is None:
        return _error("resource_not_found", f"Resource with id {resource_id}", 404)

    return jsonify(_serialize_resource(resource))


@resources_bp.route("/resources", methods=["POST"])
def create_resource():
    body = request.get_json(silent=True)
    if body is None:
        return _error("invalid_body", "Request body must be valid JSON", 400)

    required = ["name", "type", "provider_sku", "team", "environment", "owner"]
    missing = [field for field in required if not body.get(field)]
    if missing:
        return _error(
            "validation_error", f"Missing required fields: {', '.join(missing)}", 400
        )

    valid_types = ["ec2", "rds", "s3", "vm", "k8s_node", "load_balancer"]
    if body["type"] not in valid_types:
        return _error("validation_error", f"type must be one of {valid_types}", 400)

    team = _get_or_create_team(body["team"])
    environment = _get_or_create_environment(body["environment"])

    resource = Resource(
        name=body["name"],
        type=body["type"],
        provider_region=body.get("provider_region", "eu-west-1"),
        provider_sku=body["provider_sku"],
        team_id=team.id,
        environment_id=environment.id,
        owner=body["owner"],
    )

    db.session.add(resource)
    db.session.commit()

    try:
        calculate_monthly_cost(resource)
    except ValueError as e:
        # Resource was created successfully even if pricing failed —
        # e.g. an unsupported type, or no pricing match from AWS.
        # We don't want a pricing hiccup to block resource registration.
        current_app.logger.warning(
            f"Could not calculate cost for resource {resource.id}: {e}"
        )

    return jsonify(_serialize_resource(resource)), 201


# PATCH endpoint to update a resource
@resources_bp.route("/resources/<resource_id>", methods=["PATCH"])
def update_resource(resource_id):
    resource = Resource.query.get(resource_id)
    if resource is None:
        return _error(
            "resource_not_found", f"Resource with id {resource_id} does not exist", 404
        )

    body = request.get_json(silent=True)
    if body is None:
        return _error("invalid_body", "Request body must be valid JSON", 400)

    valid_types = ["ec2", "rds", "s3", "vm", "k8s_node", "load_balancer"]
    if "type" in valid_types and body["type"] not in valid_types:
        return _error("validation_error", f"type must be one of {valid_types}", 400)

    updatable_fields = [
        "name",
        "type",
        "provider_region",
        "provider_sku",
        "owner",
        "is_active",
    ]
    for field in updatable_fields:
        if field in body:
            setattr(resource, field, body[field])

    if "team" in body:
        team = _get_or_create_team(body["team"])
        resource.team_id = team.id

    if "environment" in body:
        environment = _get_or_create_environment(body["environment"])
        resource.environment_id = environment.id

    db.session.commit()
    return jsonify(_serialize_resource(resource))


@resources_bp.route("/resources/<resource_id>", methods=["DELETE"])
def delete_resource(resource_id):
    resource = Resource.query.get(resource_id)
    if resource is None:
        return _error(
            "resource_not_found", f"Resource with id {resource_id} does not exist", 404
        )

    resource.is_active = False
    db.session.commit()

    return "", 204
