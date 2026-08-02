import json
from unittest.mock import patch


def _create_resource(client, **overrides):
    payload = {
        "name": "test-resource",
        "type": "ec2",
        "provider_sku": "t3.medium",
        "team": "checkout",
        "environment": "prod",
        "owner": "francisco",
    }
    payload.update(overrides)

    with patch("routes.resources.calculate_monthly_cost") as mock_calc:
        response = client.post(
            "/api/v1/resources",
            data=json.dumps(payload),
            content_type="application/json",
        )
    return response, mock_calc


def test_create_resource_returns_201(client):
    response, mock_calc = _create_resource(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "test-resource"
    assert body["team"] == "checkout"
    assert body["environment"] == "prod"
    mock_calc.assert_called_once()


def test_create_resource_missing_fields_returns_400(client):
    response, _ = _create_resource(client, name=None)

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_create_resource_invalid_type_returns_400(client):
    response, _ = _create_resource(client, type="not-a-real-type")

    assert response.status_code == 400


def test_list_resources_returns_created_resource(client):
    _create_resource(client)

    response = client.get("/api/v1/resources")

    assert response.status_code == 200
    resources = response.get_json()["resources"]
    assert len(resources) == 1
    assert resources[0]["name"] == "test-resource"


def test_get_resource_by_id(client):
    created, _ = _create_resource(client)
    resource_id = created.get_json()["id"]

    response = client.get(f"/api/v1/resources/{resource_id}")

    assert response.status_code == 200
    assert response.get_json()["id"] == resource_id


def test_get_resource_not_found_returns_404(client):
    response = client.get("/api/v1/resources/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "resource_not_found"


def test_patch_resource_updates_only_given_fields(client):
    created, _ = _create_resource(client)
    resource_id = created.get_json()["id"]

    response = client.patch(
        f"/api/v1/resources/{resource_id}",
        data=json.dumps({"owner": "new-owner"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["owner"] == "new-owner"
    assert body["name"] == "test-resource"  # untouched


def test_delete_resource_soft_deletes(client):
    created, _ = _create_resource(client)
    resource_id = created.get_json()["id"]

    delete_response = client.delete(f"/api/v1/resources/{resource_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/resources/{resource_id}")
    assert get_response.status_code == 200  # still exists
    assert get_response.get_json()["is_active"] is False