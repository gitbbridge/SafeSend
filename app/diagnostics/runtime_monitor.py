from __future__ import annotations

import ctypes
import gc
import os
import threading
from dataclasses import dataclass
from typing import Any


try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    psutil = None


@dataclass(frozen=True)
class RuntimeSnapshot:
    label: str
    active_route: str
    rss_mb: float
    python_objects: int
    threads: int
    screen_instances: int
    tk_widgets: int
    gc_counts: tuple[int, int, int]


def capture_snapshot(app: Any, label: str = "") -> RuntimeSnapshot:
    root = getattr(app, "root", None)
    return RuntimeSnapshot(
        label=label,
        active_route=str(getattr(app, "current_route", "")),
        rss_mb=process_rss_mb(),
        python_objects=len(gc.get_objects()),
        threads=len(threading.enumerate()),
        screen_instances=len(getattr(app, "page_cache", {}) or {}),
        tk_widgets=count_tk_widgets(root) if root is not None else 0,
        gc_counts=gc.get_count(),
    )


def process_rss_mb() -> float:
    if psutil is not None:
        return float(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024))
    if os.name == "nt":
        return _windows_working_set_mb()
    return 0.0


def count_tk_widgets(widget: Any) -> int:
    if widget is None:
        return 0
    try:
        children = widget.winfo_children()
    except Exception:
        return 0
    return 1 + sum(count_tk_widgets(child) for child in children)


def trend_status(history: list[RuntimeSnapshot]) -> str:
    if len(history) < 4:
        return "UNKNOWN"
    rss = [snapshot.rss_mb for snapshot in history if snapshot.rss_mb > 0]
    if len(rss) < 4:
        return "UNKNOWN"
    first = rss[0]
    last_window = rss[-3:]
    previous_window = rss[-6:-3] if len(rss) >= 6 else rss[:-3]
    if not previous_window:
        return "UNKNOWN"
    recent_delta = max(last_window) - min(last_window)
    growth_since_previous = max(last_window) - max(previous_window)
    total_growth = rss[-1] - first
    if growth_since_previous <= max(8.0, first * 0.08) and recent_delta <= max(10.0, first * 0.1):
        return "STABLE"
    if total_growth > max(75.0, first * 0.35) and growth_since_previous > max(16.0, first * 0.12):
        return "GROWING"
    return "WATCH"


def format_report(history: list[RuntimeSnapshot], *, cycles: int = 0, title: str = "SafeSend Runtime Diagnostic") -> str:
    latest = history[-1] if history else None
    lines = [title, ""]
    if latest:
        lines.extend(
            [
                f"Route: {latest.active_route}",
                f"RSS Memory:        {latest.rss_mb:.1f} MB",
                f"Python Objects:    {latest.python_objects:,}",
                f"Threads:           {latest.threads}",
                f"Screen Instances:  {latest.screen_instances}",
                f"Tk Widgets:         {latest.tk_widgets}",
                "",
                f"Navigation Cycles: {cycles}",
                "",
            ]
        )
    lines.append("Memory History")
    for snapshot in history:
        lines.append(f"{snapshot.label:<18} {snapshot.rss_mb:>8.1f} MB   threads={snapshot.threads:<3} screens={snapshot.screen_instances:<3} widgets={snapshot.tk_widgets}")
    lines.extend(["", f"STATUS: {trend_status(history)}"])
    return "\n".join(lines)


def _windows_working_set_mb() -> float:
    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    if not ok:
        return 0.0
    return float(counters.WorkingSetSize / (1024 * 1024))
