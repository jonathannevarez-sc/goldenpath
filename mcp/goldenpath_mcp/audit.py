"""Audit logging for MCP write tools."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


def audit(event: str, **fields: Any) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    print(json.dumps(record), file=sys.stderr, flush=True)