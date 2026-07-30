import json
import logging
import sys
from datetime import UTC, datetime

from .logging_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Добавить request_id в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        setattr(record, "request_id", request_id_var.get())
        return True


class JsonFormatter(logging.Formatter):
    """Форматировать записи логов как однострочный JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for field in (
            "http_method",
            "http_path",
            "status_code",
            "duration_ms",
        ):
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info,
            )

        return json.dumps(
            log_data,
            ensure_ascii=False,
        )


def setup_logging(
    *,
    level: str = "INFO",
    json_format: bool = False,
) -> None:
    """Настроить логирование приложения."""

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "request_id=%(request_id)s - %(message)s"
            )
        )

    logging.basicConfig(
        level=level.upper(),
        handlers=[handler],
        force=True,
    )