def valid_incident_data(**overrides):
    payload = {
        "title": "Checkout failure",
        "description": "Checkout is returning HTTP 503",
        "service": "checkout",
        "severity": "critical",
    }

    payload.update(overrides)
    return payload


def create_incident(client, **overrides):
    response = client.post(
        "/incidents",
        json=valid_incident_data(**overrides),
    )

    assert response.status_code == 201
    return response.json()


def test_create_incident(client):
    # Arrange
    payload = valid_incident_data()

    # Act
    response = client.post("/incidents", json=payload)

    # Assert
    assert response.status_code == 201

    body = response.json()

    assert body["title"] == payload["title"]
    assert body["description"] == payload["description"]
    assert body["service"] == payload["service"]
    assert body["severity"] == payload["severity"]
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert body["created_at"] is not None


def test_get_incident(client):
    # Arrange
    created = create_incident(client)

    # Act
    response = client.get(f"/incidents/{created['id']}")

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert body["id"] == created["id"]
    assert body["title"] == created["title"]
    assert body["service"] == created["service"]
    assert body["severity"] == created["severity"]


def test_list_incidents(client):
    # Arrange
    first = create_incident(
        client,
        title="Checkout failure",
        service="checkout",
    )
    second = create_incident(
        client,
        title="Payment failure",
        service="payments",
    )

    # Act
    response = client.get("/incidents")

    # Assert
    assert response.status_code == 200
    body = response.json()

    assert isinstance(body, list)
    assert len(body) == 2
    assert {item["id"] for item in body} == {
        first["id"],
        second["id"],
    }


def test_update_incident(client):
    # Arrange
    created = create_incident(client)

    # Act
    update_response = client.patch(
        f"/incidents/{created['id']}",
        json={
            "status": "resolved",
            "severity": "high",
        },
    )

    # Assert the update response
    assert update_response.status_code == 200
    updated = update_response.json()

    assert updated["status"] == "resolved"
    assert updated["severity"] == "high"
    assert updated["title"] == created["title"]

    # Read again to prove the changes were persisted.
    get_response = client.get(f"/incidents/{created['id']}")

    assert get_response.status_code == 200
    persisted = get_response.json()
    assert persisted["status"] == "resolved"
    assert persisted["severity"] == "high"


def test_delete_incident(client):
    # Arrange
    created = create_incident(client)
    incident_id = created["id"]

    # Act
    delete_response = client.delete(f"/incidents/{incident_id}")

    # Assert the delete response
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # Confirm the incident no longer exists.
    get_response = client.get(f"/incidents/{incident_id}")

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Incident not found"}


def test_get_missing_incident(client):
    # Arrange
    missing_id = 999999

    # Act
    response = client.get(f"/incidents/{missing_id}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}

def test_create_incident_rejects_invalid_severity(client):
    # Arrange
    payload = valid_incident_data(severity="banana")

    # Act
    response = client.post("/incidents", json=payload)

    # Assert
    assert response.status_code == 422

    validation_errors = response.json()["detail"]

    assert any(
        error["loc"][-1] == "severity"
        for error in validation_errors
    )

    # Rejected input must not create a database record.
    list_response = client.get("/incidents")
    assert list_response.status_code == 200
    assert list_response.json() == []

def test_update_missing_incident(client):
    response = client.patch(
        "/incidents/999999",
        json={"status": "resolved"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}


def test_delete_missing_incident(client):
    response = client.delete("/incidents/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}
