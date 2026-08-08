from contextvars import ContextVar

REQUEST_ID_HEADER = "X-Request-ID"

request_id_var: ContextVar[str] = ContextVar(
    "request_id",
    default="-",
)
