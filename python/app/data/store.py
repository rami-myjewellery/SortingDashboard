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
    ),
    # New Dashboards for segmented categories
    "fma": Dashboard(
        title="FMA",
        status="good",
        kpis=[
            Kpi(label="FMA Belt filling level", value=0, unit="packages"),
            Kpi(label="FMA Error Rate", value=0, unit="%"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    ),
    "monopicking": Dashboard(
        title="MonoPicking",
        status="good",
        kpis=[
            Kpi(label="Mono Picking Speed", value=0, unit="items/sec"),
            Kpi(label="Mono Picking Efficiency", value=0, unit="%"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    ),
    "inbound_and_bulk": Dashboard(
        title="InboundAndBulk",
        status="good",
        kpis=[
            Kpi(label="Inbound Process Time", value=0, unit="seconds"),
            Kpi(label="Bulk Processing Rate", value=0, unit="items/sec"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    ),
    "returns": Dashboard(
        title="Returns",
        status="good",
        kpis=[
            Kpi(label="Returns Process Time", value=0, unit="seconds"),
            Kpi(label="Returns Rate", value=0, unit="%"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    ),
    "errorlanes": Dashboard(
        title="Error Lanes",
        status="good",
        kpis=[
            Kpi(label="Error Action Count", value=0, unit="actions"),
            Kpi(label="Error Action Duration", value=0, unit="seconds"),
        ],
        historyText="",
        people=[],
        idleThreshold=60,
    ),
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
    now = datetime.now(timezone.utc)  # Make sure `now` is aware with UTC timezone

    db = get_db()["default"]

    for p in db.people:
        if p.last_seen:
            # Ensure p.last_seen is aware by converting it to the same timezone as `now`
            if p.last_seen.tzinfo is None:
                # Convert naive to aware using UTC timezone
                p.last_seen = p.last_seen.replace(tzinfo=timezone.utc)

            p.idleSeconds = int((now - p.last_seen).total_seconds())
        else:
            p.idleSeconds += IDLE_TICK_FALLBACK  # Use fallback if `last_seen` is None

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
    return _db


# (Optional) helper so your app can shut down cleanly if you ever need it
def stop_decay_thread() -> None:
    _shutdown_event.set()
    _thread.join(timeout=1)
