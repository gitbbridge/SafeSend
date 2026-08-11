from __future__ import annotations

import argparse
import gc
import queue as thread_queue
import sys
import threading
import time
from pathlib import Path

import tkinter as tk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.db import initialize_database
from app.diagnostics.runtime_monitor import capture_snapshot, format_report, trend_status
from app.ui.components.modern_table import ModernTable
from app.ui.main_window import SafeSendApp
from app.utils.logger import configure_logging


CHECKPOINTS = (1, 10, 25, 50, 75, 100)


def run_navigation_stress(cycles: int = 100, *, withdraw: bool = True) -> int:
    configure_logging()
    initialize_database()
    app = SafeSendApp()
    if withdraw:
        app.root.withdraw()
    app.root.update()

    history = [capture_snapshot(app, "Startup")]
    routes = list(app.routes.keys())
    worker_stop = threading.Event()
    events: thread_queue.Queue[tuple[str, int]] = thread_queue.Queue()
    worker = threading.Thread(target=_simulated_queue_worker, args=(worker_stop, events), name="safesend-simulated-worker", daemon=True)
    worker.start()

    try:
        for cycle in range(1, cycles + 1):
            for route in routes:
                app.navigate(route)
                _drain_events(events)
                app.root.update_idletasks()
                app.root.update()
            if cycle in CHECKPOINTS and cycle != cycles:
                gc.collect()
                history.append(capture_snapshot(app, f"Cycle {cycle}"))
            if cycle in {25, 50, 75}:
                _minimize_restore(app, withdraw=withdraw)
        worker_stop.set()
        worker.join(timeout=3)
        gc.collect()
        history.append(capture_snapshot(app, f"Cycle {cycles}"))
        table_findings = _stress_modern_table(app.root)
    finally:
        worker_stop.set()
        worker.join(timeout=3)
        app.shutdown()
        gc.collect()

    print(format_report(history, cycles=cycles))
    print("")
    print("ModernTable Stress")
    for label, value in table_findings:
        print(f"{label:<18} {value}")

    status = trend_status(history)
    threads_stable = history[-1].threads <= history[0].threads + 1
    screens_stable = history[-1].screen_instances == len(routes)
    return 0 if status in {"STABLE", "WATCH"} and threads_stable and screens_stable else 1


def _simulated_queue_worker(stop_event: threading.Event, events: thread_queue.Queue[tuple[str, int]]) -> None:
    progress = 0
    while not stop_event.is_set():
        progress = (progress + 1) % 101
        events.put(("progress", progress))
        stop_event.wait(0.025)


def _drain_events(events: thread_queue.Queue[tuple[str, int]]) -> None:
    for _ in range(50):
        try:
            events.get_nowait()
        except thread_queue.Empty:
            return


def _minimize_restore(app: SafeSendApp, *, withdraw: bool) -> None:
    if withdraw:
        return
    try:
        app.root.iconify()
        app.root.update()
        app.root.deiconify()
        app.root.update()
    except tk.TclError:
        pass


def _stress_modern_table(root: tk.Widget) -> list[tuple[str, str]]:
    host = tk.Frame(root)
    host.pack_forget()
    table = ModernTable(host, ("id", "email", "status", "actions"), headings=("ID", "Email", "Status", "Actions"), height=20)
    table.pack(fill="both", expand=True)
    findings: list[tuple[str, str]] = []
    for size in (1_000, 5_000, 10_000):
        table.clear()
        for index in range(size):
            table.insert("", "end", values=(index, f"user{index}@example.com", "Draft" if index % 2 else "Sent", "Action"))
        root.update_idletasks()
        root.update()
        findings.append((f"{size:,} rows", f"stored={len(table.get_children()):,} canvas_items={len(table.canvas.find_all()):,}"))
    table.clear()
    root.update_idletasks()
    findings.append(("after clear", f"stored={len(table.get_children()):,} canvas_items={len(table.canvas.find_all()):,}"))
    table.destroy()
    host.destroy()
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="SafeSend development navigation stress test.")
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--show-window", action="store_true", help="Show the application window during the test.")
    args = parser.parse_args()
    return run_navigation_stress(args.cycles, withdraw=not args.show_window)


if __name__ == "__main__":
    raise SystemExit(main())
