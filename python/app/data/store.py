"""
app/data/store.py
──────────────────────────────────────────────────────────────────────────────
• Keeps the in-memory Dashboard singleton
• A separate daemon thread calls `_tick_once()` every second
• Thread-safe thanks to a single `Lock`
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict

from app.models import Dashboard, Kpi

# ── Tuning knobs ────────────────────────────────────────────────────────────
DECAY_RATE           = 0.99     # 1 % speed drop **per second of idleness**
IDLE_TICK_FALLBACK   = 1        # seconds to add if last_seen is None
MAX_PEOPLE           = 5        # keep only the N most-recent operators
TICK_INTERVAL        = 1.0      # seconds between background ticks

# ── The “database” ──────────────────────────────────────────────────────────
_db: Dict[str, Dashboard] = {
    "default": Dashboard(
        title="Sorting",
        status="good",
        kpis=[
            Kpi(label="Error belt filling level",  value=0, unit="packages"),
            Kpi(label="Single belt filling level", value=0, unit="packages"),
            Kpi(label="Multi belt filling level",  value=0, unit="packages"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    )
}

# ── Synchronisation primitives ──────────────────────────────────────────────
_tick_lock      = threading.Lock()      # protects the critical section
_shutdown_event = threading.Event()     # so we can cleanly exit if needed


# ── Background ticker ───────────────────────────────────────────────────────
def _tick_once() -> None:
    """
    Apply **one second** worth of decay to every person.
    Safe to call from multiple threads, but we only call it from the
    background ticker held by `_tick_lock`.
    """
    now = datetime.now(timezone.utc)
    db  = _db["default"]

    for p in db.people:
        # 1. idleSeconds -----------------------------------------------------
        if p.last_seen:
            p.idleSeconds = int((now - p.last_seen).total_seconds())
        else:
            p.idleSeconds += IDLE_TICK_FALLBACK

        # 2. speed decay -----------------------------------------------------
        if p.idleSeconds and p.speed:
            p.speed = max(0, int(p.speed * DECAY_RATE))

    # House-keeping: keep only the latest N operators
    db.people.sort(key=lambda person: person.last_seen or now, reverse=True)
    db.people[:] = db.people[:MAX_PEOPLE]


def _ticker_loop() -> None:
    """
    Runs in its own daemon thread; sleeps `TICK_INTERVAL` seconds between
    calls to `_tick_once()`.
    """
    while not _shutdown_event.is_set():
        started = time.time()
        with _tick_lock:
            _tick_once()
        # sleep the remainder of the interval (drift-corrected)
        elapsed = time.time() - started
        time_to_sleep = max(0.0, TICK_INTERVAL - elapsed)
        if _shutdown_event.wait(time_to_sleep):
            break


# Start the background thread exactly once at import time
_thread = threading.Thread(target=_ticker_loop, daemon=True, name="decay-ticker")
_thread.start()


# ── Public API ──────────────────────────────────────────────────────────────
def get_db() -> Dict[str, Dashboard]:
    """
    Return the singleton Dashboard.

    No decay is applied here any more – the dedicated ticker thread already
    takes care of it once per second, regardless of how often (or seldom)
    you call `get_db()`.
    """
    # You *could* grab the lock here if you need strong consistency for
    # reads, but in practice it isn't necessary for simple dashboards:
    # with _tick_lock:
    return _db


# (Optional) helper so your app can shut down cleanly if you ever need it
def stop_decay_thread() -> None:
    _shutdown_event.set()
    _thread.join(timeout=1)
