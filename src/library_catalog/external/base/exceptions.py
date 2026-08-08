class CircuitBreakerOpenError(RuntimeError):
    """Запрос заблокирован открытым circuit breaker."""

    def __init__(self, client_name: str) -> None:
        self.client_name = client_name
        super().__init__(f"Circuit breaker for '{client_name}' is open")
