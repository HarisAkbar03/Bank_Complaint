import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "operation": getattr(record, "operation", None),
            "outcome": getattr(record, "outcome", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "correlation_id": getattr(record, "correlation_id", None),
        }

        return json.dumps(log_data)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logger = logging.getLogger("banking_api")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logging()

def log_operation(
    operation: str,
    outcome: str,
    duration_ms: float,
    correlation_id: str
):
    logger.info(
        "Request completed",
        extra={
            "operation": operation,
            "outcome": outcome,
            "duration_ms": round(duration_ms, 2),
            "correlation_id": correlation_id,
        }
    )