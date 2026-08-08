import asyncio
import logging
from abc import ABC, abstractmethod
from time import perf_counter
from typing import Any, cast

import httpx
from purgatory import AsyncCircuitBreakerFactory
from purgatory.domain.model import OpenedState

from ...core.metrics import ExternalRequestOutcome, observe_external_api_request
from .exceptions import CircuitBreakerOpenError


def _is_client_error(exc: BaseException) -> bool:
    """Не учитывать HTTP-ответы 4xx как сбой внешнего сервиса."""
    return (
        isinstance(exc, httpx.HTTPStatusError) and 400 <= exc.response.status_code < 500
    )


class BaseApiClient(ABC):
    """
    Базовый класс для HTTP клиентов внешних API.

    Включает:
    - Retry логику
    - Обработку ошибок
    - Логирование
    - Timeout management
    - Circuit breaker
    - Prometheus metrics
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        retries: int = 3,
        backoff: float = 0.5,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_recovery_timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff

        self._circuit_breaker_factory = AsyncCircuitBreakerFactory(
            default_threshold=circuit_breaker_failure_threshold,
            default_ttl=circuit_breaker_recovery_timeout,
            exclude=[(httpx.HTTPStatusError, _is_client_error)],
        )

        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )

        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=limits,
        )
        self.logger = logging.getLogger(self.client_name())

    @abstractmethod
    def client_name(self) -> str:
        """Имя клиента для логирования."""
        pass

    def _build_url(self, path: str) -> str:
        """Построить полный URL."""
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Выполнить HTTP-запрос под защитой circuit breaker."""
        client_name = self.client_name()
        started_at = perf_counter()
        outcome: ExternalRequestOutcome = "unexpected_error"

        try:
            circuit_breaker = await self._circuit_breaker_factory.get_breaker(
                client_name
            )

            async with circuit_breaker:
                result = await self._request_with_retries(
                    method=method,
                    path=path,
                    params=params,
                    json=json,
                    headers=headers,
                )

            outcome = "success"
            return result

        except OpenedState as exc:
            outcome = "circuit_open"
            self.logger.warning(
                "Circuit breaker is open for %s",
                client_name,
            )
            raise CircuitBreakerOpenError(client_name) from exc

        except asyncio.CancelledError:
            outcome = "cancelled"
            raise

        except httpx.TimeoutException:
            outcome = "timeout"
            raise

        except httpx.HTTPStatusError:
            outcome = "http_error"
            raise

        except httpx.RequestError:
            outcome = "network_error"
            raise

        finally:
            observe_external_api_request(
                client=client_name,
                method=method.upper(),
                outcome=outcome,
                duration_seconds=perf_counter() - started_at,
            )

    async def _request_with_retries(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Выполнить HTTP запрос с retry логикой.
        """
        url = self._build_url(path)

        for attempt in range(self.retries):
            try:
                self.logger.debug(f"{method} {url} params={params}")

                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )

                response.raise_for_status()
                return cast(dict[str, Any], response.json())

            except httpx.TimeoutException:
                if attempt == self.retries - 1:
                    self.logger.error(f"Timeout after {self.retries} attempts")
                    raise

                wait_time = self.backoff * (2**attempt)
                self.logger.warning(f"Timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)  # Асинхронное ожидание!

            except httpx.HTTPStatusError as e:
                # 5xx ошибки - retry
                if e.response.status_code >= 500 and attempt < self.retries - 1:
                    wait_time = self.backoff * (2**attempt)
                    self.logger.warning(f"Server error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"HTTP error: {e}")
                    raise

        raise RuntimeError("HTTP request attempts exhausted")

    async def _get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """GET запрос."""
        return await self._request(
            "GET",
            path,
            params=params,
            headers=headers,
        )

    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        await self._client.aclose()
