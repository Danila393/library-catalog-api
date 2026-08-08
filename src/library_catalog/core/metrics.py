from typing import Literal, TypeAlias

from prometheus_client import Counter, Histogram

ExternalRequestOutcome: TypeAlias = Literal[
    "success",
    "timeout",
    "http_error",
    "network_error",
    "circuit_open",
    "cancelled",
    "unexpected_error",
]

_EXTERNAL_REQUEST_LABELS = (
    "client",
    "method",
    "outcome",
)

EXTERNAL_API_REQUESTS_TOTAL = Counter(
    "external_api_requests_total",
    "Total number of external API operations",
    labelnames=_EXTERNAL_REQUEST_LABELS,
    namespace="library_catalog",
)

EXTERNAL_API_REQUEST_DURATION_SECONDS = Histogram(
    "external_api_request_duration_seconds",
    "Duration of external API operations in seconds",
    labelnames=_EXTERNAL_REQUEST_LABELS,
    namespace="library_catalog",
)


def observe_external_api_request(
    *,
    client: str,
    method: str,
    outcome: ExternalRequestOutcome,
    duration_seconds: float,
) -> None:
    """Записать результат и длительность операции внешнего API."""
    EXTERNAL_API_REQUESTS_TOTAL.labels(
        client=client,
        method=method,
        outcome=outcome,
    ).inc()

    EXTERNAL_API_REQUEST_DURATION_SECONDS.labels(
        client=client,
        method=method,
        outcome=outcome,
    ).observe(duration_seconds)
