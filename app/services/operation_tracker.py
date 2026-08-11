from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any, Callable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class OperationSnapshot:
    operation_id: str
    title: str
    detail: str = ""
    current: int | None = None
    total: int | None = None
    indeterminate: bool = True
    cancellable: bool = True
    critical: bool = True
    active: bool = True
    started_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)

    @property
    def percent(self) -> float | None:
        if self.current is None or self.total in (None, 0):
            return None
        return max(0.0, min(1.0, self.current / self.total))

    @property
    def label(self) -> str:
        base = self.detail or self.title
        if self.current is not None and self.total:
            return f"{base} - {self.current:,} / {self.total:,}"
        return base


class OperationHandle:
    def __init__(self, tracker: "OperationTracker", snapshot: OperationSnapshot, cancel_event: threading.Event) -> None:
        self.tracker = tracker
        self.snapshot = snapshot
        self.cancel_event = cancel_event
        self._last_update_at = 0.0

    @property
    def operation_id(self) -> str:
        return self.snapshot.operation_id

    def update(
        self,
        detail: str = "",
        current: int | None = None,
        total: int | None = None,
        indeterminate: bool | None = None,
        *,
        force: bool = False,
    ) -> None:
        now = time.monotonic()
        is_terminal_progress = current is not None and total not in (None, 0) and current >= total
        if not force and not is_terminal_progress and now - self._last_update_at < self.tracker.min_update_interval:
            return
        self._last_update_at = now
        self.tracker.update(self.operation_id, detail=detail, current=current, total=total, indeterminate=indeterminate)

    def cancel_requested(self) -> bool:
        return self.cancel_event.is_set()

    def complete(self) -> None:
        self.tracker.complete(self.operation_id)


class OperationTracker:
    def __init__(self, min_update_interval: float = 0.2) -> None:
        self.min_update_interval = min_update_interval
        self._lock = threading.Lock()
        self._operations: dict[str, OperationSnapshot] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._queue: Queue[OperationSnapshot] = Queue()

    def begin(
        self,
        title: str,
        detail: str = "",
        *,
        total: int | None = None,
        cancellable: bool = True,
        critical: bool = True,
    ) -> OperationHandle:
        operation_id = uuid.uuid4().hex
        cancel_event = threading.Event()
        snapshot = OperationSnapshot(
            operation_id=operation_id,
            title=title,
            detail=detail or title,
            total=total,
            current=0 if total else None,
            indeterminate=total is None,
            cancellable=cancellable,
            critical=critical,
        )
        with self._lock:
            self._operations[operation_id] = snapshot
            self._cancel_events[operation_id] = cancel_event
        self._queue.put(snapshot)
        return OperationHandle(self, snapshot, cancel_event)

    def update(
        self,
        operation_id: str,
        *,
        detail: str = "",
        current: int | None = None,
        total: int | None = None,
        indeterminate: bool | None = None,
    ) -> None:
        with self._lock:
            existing = self._operations.get(operation_id)
            if not existing:
                return
            snapshot = OperationSnapshot(
                operation_id=existing.operation_id,
                title=existing.title,
                detail=detail or existing.detail,
                current=current if current is not None else existing.current,
                total=total if total is not None else existing.total,
                indeterminate=(indeterminate if indeterminate is not None else existing.indeterminate),
                cancellable=existing.cancellable,
                critical=existing.critical,
                active=True,
                started_at=existing.started_at,
                updated_at=_utc_now(),
            )
            self._operations[operation_id] = snapshot
        self._queue.put(snapshot)

    def complete(self, operation_id: str) -> None:
        with self._lock:
            existing = self._operations.pop(operation_id, None)
            self._cancel_events.pop(operation_id, None)
        if existing:
            completed = OperationSnapshot(
                operation_id=existing.operation_id,
                title=existing.title,
                detail=existing.detail,
                current=existing.current,
                total=existing.total,
                indeterminate=existing.indeterminate,
                cancellable=existing.cancellable,
                critical=existing.critical,
                active=False,
                started_at=existing.started_at,
                updated_at=_utc_now(),
            )
            self._queue.put(completed)

    def cancel_all(self) -> None:
        with self._lock:
            for event in self._cancel_events.values():
                event.set()

    def has_active_critical(self) -> bool:
        with self._lock:
            return any(item.active and item.critical for item in self._operations.values())

    def active_operations(self) -> list[OperationSnapshot]:
        with self._lock:
            return list(self._operations.values())

    def drain_updates(self, limit: int = 100) -> list[OperationSnapshot]:
        updates: list[OperationSnapshot] = []
        while len(updates) < limit:
            try:
                updates.append(self._queue.get_nowait())
            except Empty:
                break
        return updates


def run_operation(
    tracker: OperationTracker,
    title: str,
    worker: Callable[[OperationHandle], Any],
    *,
    detail: str = "",
    total: int | None = None,
    on_complete: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> threading.Thread:
    handle = tracker.begin(title, detail, total=total)

    def target() -> None:
        try:
            result = worker(handle)
            if on_complete:
                on_complete(result)
        except Exception as exc:
            if on_error:
                on_error(exc)
        finally:
            handle.complete()

    thread = threading.Thread(target=target, name=f"SafeSendOperation-{title}", daemon=True)
    thread.start()
    return thread
