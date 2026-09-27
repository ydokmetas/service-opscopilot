from fastapi import status


def valid_document_data(**overrides):
    payload = {
        "title": "Checkout Runbook",
        "document_type": "runbook",
        "content": "When checkout returns 503, check the upstream service.",
    }

    payload.update(overrides)
    return payload


def create_document(client, **overrides):
    response = client.post(
        "/documents",
        json=valid_document_data(**overrides),
    )

    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def test_create_document(client):
    # Arrange
    payload = valid_document_data()

    # Act
    response = client.post("/documents", json=payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED

    body = response.json()

    assert body["title"] == payload["title"]
    assert body["document_type"] == payload["document_type"]
    assert body["content"] == payload["content"]
    assert isinstance(body["id"], int)
    assert body["created_at"] is not None


def test_list_documents(client):
    # Arrange
    first = create_document(
        client,
        title="Checkout Runbook",
    )
    second = create_document(
        client,
        title="Payments Runbook",
    )

    # Act
    response = client.get("/documents")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()

    assert isinstance(body, list)
    assert len(body) == 2
    assert {item["id"] for item in body} == {
        first["id"],
        second["id"],
    }


def test_get_document(client):
    # Arrange
    created = create_document(client)

    # Act
    response = client.get(f"/documents/{created['id']}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    body = response.json()

    assert body["id"] == created["id"]
    assert body["title"] == created["title"]
    assert body["document_type"] == created["document_type"]
    assert body["content"] == created["content"]


def test_delete_document(client):
    # Arrange
    created = create_document(client)
    document_id = created["id"]

    # Act
    delete_response = client.delete(f"/documents/{document_id}")

    # Assert the delete response
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert delete_response.content == b""

    # Confirm the document no longer exists.
    get_response = client.get(f"/documents/{document_id}")

    assert get_response.status_code == status.HTTP_404_NOT_FOUND
    assert get_response.json() == {"detail": "Document not found"}


def test_create_document_rejects_invalid_input(client):
    # Arrange
    payload = valid_document_data(title="")

    # Act
    response = client.post("/documents", json=payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    validation_errors = response.json()["detail"]
    assert any(
        error["loc"][-1] == "title"
        for error in validation_errors
    )

    # Rejected input must not create a database record.
    list_response = client.get("/documents")
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.json() == []


def test_get_missing_document(client):
    response = client.get("/documents/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Document not found"}


def test_delete_missing_document(client):
    response = client.delete("/documents/999999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Document not found"}
