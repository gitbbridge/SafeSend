from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from queue import Empty, Queue
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EngineEventType(str, Enum):
    STATE_CHANGED = "STATE_CHANGED"
    JOB_QUEUED = "JOB_QUEUED"
    JOB_STARTED = "JOB_STARTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_DEFERRED = "JOB_DEFERRED"
    JOB_FAILED = "JOB_FAILED"
    JOB_SUPPRESSED = "JOB_SUPPRESSED"
    ERROR = "ERROR"
    AUDIT = "AUDIT"


@dataclass(slots=True)
class EngineEvent:
    event_type: EngineEventType
    campaign_id: int | None = None
    send_job_id: int | None = None
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)


class UIEventBus:
    """Thread-safe handoff point between background workers and Tk UI code."""

    def __init__(self) -> None:
        self._queue: Queue[EngineEvent] = Queue()

    def publish(self, event: EngineEvent) -> None:
        self._queue.put(event)

    def drain(self, limit: int = 100) -> list[EngineEvent]:
        events: list[EngineEvent] = []
        while len(events) < limit:
            try:
                events.append(self._queue.get_nowait())
            except Empty:
                break
        return events
