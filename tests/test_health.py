def test_health(client):
    # Arrange
    # No data is needed.

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}