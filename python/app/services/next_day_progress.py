import asyncio
import logging
import os
import time
from datetime import date
from typing import Any, Dict, List, Optional

from datadog_logger import log_datadog_event

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 15.0

NEXT_DAY_SQL = """
SELECT
    trunc(sysdate) as load_date,
    ch.cgccha as load_code,
    ch.cglcha as load_designation,
    ch.cghdch as planned_loading_time,
    trim(em.emc1em) || trim(em.emc2em) || trim(em.emc3em) as dock,
    sum(case when pv.pvtvpr = '1' then 1 else 0 end) as picks_confirmed,
    count(pv.pvnpre) as picks_total,
    round(100 * sum(case when pv.pvtvpr = '1' then 1 else 0 end) / nullif(count(pv.pvnpre), 0)) as pick_pct
FROM hlcharp ch
LEFT JOIN hlemplp em
    ON em.emcdpo = ch.cgcdpo
    AND em.emnemp = ch.cgnemp
LEFT JOIN hlprenp pe
    ON pe.pecdpo = ch.cgcdpo
    AND pe.peanca = ch.cganca
    AND pe.pemoca = ch.cgmoca
    AND pe.pejoca = ch.cgjoca
    AND pe.peccha = ch.cgccha
LEFT JOIN hlprelp pv
    ON pv.pvcdpo = pe.pecdpo
    AND pv.pvcact = pe.pecact
    AND pv.pvnanp = pe.penann
    AND pv.pvnpre = pe.penpre
WHERE ch.cganca = to_number(to_char(sysdate, 'YY'))
    AND ch.cgmoca = to_number(to_char(sysdate, 'MM'))
    AND ch.cgjoca = to_number(to_char(sysdate, 'DD'))
    AND trim(ch.cgccha) IN ('PNLPAR', 'PNLMAI', 'DHLFY')
GROUP BY
    ch.cgcdpo, ch.cganca, ch.cgmoca, ch.cgjoca, ch.cgccha,
    ch.cglcha, ch.cghdch,
    em.emc1em, em.emc2em, em.emc3em
ORDER BY ch.cghdch, ch.cgccha
"""

FALLBACK_NEXT_DAY_LOADS: List[Dict[str, Any]] = [
    {
        "id": "load-pnlmai",
        "load_date": str(date.today()),
        "load_code": "PNLMAI",
        "load_designation": "PostNL Brievenbuspakje",
        "carrier": "PostNL Brievenbuspakje",
        "dock": "DOCK002",
        "planned_loading_time": "223000",
        "scheduled_time": "22:30",
        "picks_confirmed": 412,
        "picks_done": 412,
        "picks_total": 460,
        "pick_pct": 90,
        "picks_percentage": 90.0,
    },
    {
        "id": "load-pnlpar",
        "load_date": str(date.today()),
        "load_code": "PNLPAR",
        "load_designation": "PostNL Pakketten",
        "carrier": "PostNL Pakketten",
        "dock": "DOCK003",
        "planned_loading_time": "230000",
        "scheduled_time": "23:00",
        "picks_confirmed": 582,
        "picks_done": 582,
        "picks_total": 970,
        "pick_pct": 60,
        "picks_percentage": 60.0,
    },
    {
        "id": "load-dhlfy",
        "load_date": str(date.today()),
        "load_code": "DHLFY",
        "load_designation": "DHL For You",
        "carrier": "DHL For You",
        "dock": "DOCK005",
        "planned_loading_time": "233000",
        "scheduled_time": "23:30",
        "picks_confirmed": 145,
        "picks_done": 145,
        "picks_total": 520,
        "pick_pct": 28,
        "picks_percentage": 28.0,
    },
]

_cached_loads: Optional[List[Dict[str, Any]]] = None
_cache_expiry: float = 0.0
_lock = asyncio.Lock()


def format_hhmmss(raw_val: Any) -> tuple[str, str]:
    """
    Convert Reflex HHMMSS time (e.g. 230000 or '230000' or 93000) into
    (raw_hhmmss_str, 'HH:MM').
    """
    if raw_val is None:
        return ("000000", "00:00")
    s = str(raw_val).strip()
    if ":" in s:
        parts = s.split(":")
        hh = parts[0].zfill(2)
        mm = (parts[1] if len(parts) > 1 else "00").zfill(2)
        ss = (parts[2] if len(parts) > 2 else "00").zfill(2)
        return (f"{hh}{mm}{ss}", f"{hh}:{mm}")
    try:
        digits = str(int(float(s))).zfill(6)
    except ValueError:
        digits = "000000"
    return (digits, f"{digits[:2]}:{digits[2:4]}")


def _query_reflex_sync() -> List[Dict[str, Any]]:
    import oracledb

    host = os.getenv("REFLEX_DB_HOST", "10.202.9.75")
    port = int(os.getenv("REFLEX_DB_PORT", "1521"))
    service_name = os.getenv("REFLEX_DB_SERVICE", "MYJRWSP1_RO.prod.hco")
    user = os.getenv("REFLEX_DB_USER", "report")
    password = os.getenv("REFLEX_DB_PASSWORD", "reporting")

    dsn = oracledb.makedsn(host, port, service_name=service_name)
    with oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
        tcp_connect_timeout=4.0,
    ) as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("ALTER SESSION SET CURRENT_SCHEMA = REFLEX")
            except Exception:
                pass
            cur.execute(NEXT_DAY_SQL)
            columns = [col[0].upper() for col in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    loads: List[Dict[str, Any]] = []
    for idx, r in enumerate(rows):
        code = str(r.get("LOAD_CODE") or "").strip()
        designation = str(r.get("LOAD_DESIGNATION") or "").strip() or code
        raw_hhmmss, hh_mm = format_hhmmss(r.get("PLANNED_LOADING_TIME"))
        dock = str(r.get("DOCK") or "").strip() or "—"
        confirmed = int(r.get("PICKS_CONFIRMED") or 0)
        total = int(r.get("PICKS_TOTAL") or 0)
        raw_pct = r.get("PICK_PCT")
        if raw_pct is None:
            pct = round(100 * confirmed / total) if total > 0 else 0
        else:
            pct = int(round(float(raw_pct)))

        load_date_val = r.get("LOAD_DATE")
        load_date_str = (
            load_date_val.strftime("%Y-%m-%d")
            if hasattr(load_date_val, "strftime")
            else str(load_date_val or date.today())
        )

        loads.append(
            {
                "id": f"load-{code.lower()}-{idx}",
                "load_date": load_date_str,
                "load_code": code,
                "load_designation": designation,
                "carrier": designation,
                "dock": dock,
                "planned_loading_time": raw_hhmmss,
                "scheduled_time": hh_mm,
                "picks_confirmed": confirmed,
                "picks_done": confirmed,
                "picks_total": total,
                "pick_pct": pct,
                "picks_percentage": float(pct),
            }
        )
    return loads


async def get_next_day_loads() -> List[Dict[str, Any]]:
    global _cached_loads, _cache_expiry

    now = time.monotonic()
    if _cached_loads is not None and _cache_expiry > now:
        return _cached_loads

    async with _lock:
        if _cached_loads is not None and _cache_expiry > time.monotonic():
            return _cached_loads

        try:
            loads = await asyncio.to_thread(_query_reflex_sync)
            if loads:
                _cached_loads = loads
                _cache_expiry = time.monotonic() + CACHE_TTL_SECONDS
                return loads
            logger.info("Reflex NextDayProgress query returned 0 rows; serving fallback loads")
        except Exception as exc:
            logger.warning("Reflex NextDayProgress query failed (%s); serving cached/fallback loads", exc)
            log_datadog_event(
                status="warning",
                message=f"NextDayProgress Oracle query failed, using fallback: {exc}",
                event_type="next_day_progress.query",
                function_name="get_next_day_loads",
            )
            if _cached_loads:
                return _cached_loads

        return FALLBACK_NEXT_DAY_LOADS
