from fastapi import status


def test_health(client):
    # Arrange
    # No data is needed.

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}