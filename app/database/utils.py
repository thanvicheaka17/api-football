import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def params_hash(params: dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_empty_response(
    endpoint: str,
    params: dict[str, Any],
    message: str = "No data found in database",
) -> dict[str, Any]:
    response_value: Any = {} if endpoint == "status" else []
    return {
        "get": endpoint,
        "parameters": params,
        "errors": {"database": message},
        "results": 0,
        "paging": {"current": 1, "total": 1},
        "response": response_value,
    }
