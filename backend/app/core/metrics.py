"""Per-process HTTP metrics with bounded labels and no request payloads."""

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram
from prometheus_client import generate_latest as render_metrics
from starlette.responses import Response


class HTTPMetrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        labels = ("method", "route", "status_code")
        self.requests = Counter(
            "marketplace_http_requests_total",
            "Completed HTTP requests",
            labels,
            registry=self.registry,
        )
        self.duration = Histogram(
            "marketplace_http_request_duration_seconds",
            "HTTP response duration",
            labels,
            registry=self.registry,
        )

    def observe(self, method: str, route: str, status: int, elapsed: float) -> None:
        if route in {"/metrics", "/health/live", "/health/ready"}:
            return
        allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        method = method if method in allowed_methods else "OTHER"
        labels = (method, route, str(status))
        self.requests.labels(*labels).inc()
        self.duration.labels(*labels).observe(elapsed)

    def response(self) -> Response:
        return Response(
            render_metrics(self.registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
        )
