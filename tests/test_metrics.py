from fastapi import status


def test_metrics_endpoint(client):
    # Arrange and Act
    client.get("/health")
    response = client.get("/metrics")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    body = response.text

    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body


def test_health_request_is_measured(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == status.HTTP_200_OK
    assert 'route="/health"' in response.text