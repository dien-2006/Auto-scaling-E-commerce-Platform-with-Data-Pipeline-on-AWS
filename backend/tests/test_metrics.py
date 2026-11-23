from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_metrics_use_route_templates_and_exclude_health_checks():
    app = create_app(Settings(environment="test"))

    @app.get("/metrics-test/{resource_id}")
    async def resource(resource_id: str):
        return {"id": resource_id}

    with TestClient(app) as client:
        client.get("/metrics-test/private-id-one?token=private-token")
        client.get("/metrics-test/private-id-two")
        client.get("/missing-private-path")
        client.get("/health/live")
        first = client.get("/metrics")
        second = client.get("/metrics")
    assert first.status_code == 200
    assert "text/plain" in first.headers["content-type"]
    assert first.text == second.text
    assert 'route="/metrics-test/{resource_id}"' in first.text
    for private in ("private-id-one", "private-id-two", "private-token", "missing-private-path"):
        assert private not in first.text
    for route in ("/health/live", 'route="/metrics"'):
        assert route not in first.text
    assert app.state.metrics.registry.get_sample_value(
        "marketplace_http_requests_total",
        {"method": "GET", "route": "/metrics-test/{resource_id}", "status_code": "200"},
    ) == 2
    assert app.state.metrics.registry.get_sample_value(
        "marketplace_http_requests_total",
        {"method": "GET", "route": "<unmatched>", "status_code": "404"},
    ) == 1


def test_metrics_count_failures_and_keep_app_registries_separate():
    app = create_app(Settings(environment="test"))
    other = create_app(Settings(environment="test"))

    @app.get("/metrics-failure")
    async def failure():
        raise RuntimeError("private error")

    with TestClient(app) as client:
        assert client.get("/metrics-failure").status_code == 500
    labels = {"method": "GET", "route": "/metrics-failure", "status_code": "500"}
    assert app.state.metrics.registry.get_sample_value(
        "marketplace_http_requests_total", labels
    ) == 1
    assert other.state.metrics.registry.get_sample_value(
        "marketplace_http_requests_total", labels
    ) is None
