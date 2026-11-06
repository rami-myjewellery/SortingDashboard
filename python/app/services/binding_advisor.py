import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from datadog_logger import log_datadog_event

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 10.0

CART_CAPACITY_BY_TYPE: Dict[str, int] = {
    "BKL": 65,
    "BGR": 16,
    "PDL": 9,
    "PDM": 9,
    "PDS": 18,
}

BINDING_ADVISOR_SQL = """
SELECT *
FROM (
    SELECT
        ci.C5CTCO AS carton_type,
        mi.MIPMIS AS pick_batch_priority_code,
        COUNT(DISTINCT pc.PRCNCOL) AS no_of_cartons,
        CAST(
            COUNT(DISTINCT pc.PRCNCOL)
            / CASE
                WHEN ci.C5CTCO = 'BKL' THEN 65
                WHEN ci.C5CTCO = 'BGR' THEN 16
                WHEN ci.C5CTCO = 'PDL' THEN 9
                WHEN ci.C5CTCO = 'PDM' THEN 9
                WHEN ci.C5CTCO = 'PDS' THEN 18
            END
        AS NUMBER(9, 1)) AS no_of_full_carts,
        TO_TIMESTAMP(
            TO_CHAR(MIN(NULLIF(
                pe.PESCRE * 1000000000000
                + pe.PEACRE * 10000000000
                + pe.PEMCRE * 100000000
                + pe.PEJCRE * 1000000
                + pe.PEHCRE
            , 0)), 'FM99999999999999'),
            'YYYYMMDDHH24MISS'
        ) AS oldest_creation_datetime
    FROM HLMISSP mi
    INNER JOIN HLPRELP pv
        ON mi.MICDPO = pv.PVCDPO
        AND mi.MINANN = pv.PVNANM
        AND mi.MINMIS = pv.PVNMIS
    INNER JOIN HLPRCOP pc
        ON pv.PVCDPO = pc.PRCCDPO
        AND pv.PVCACT = pc.PRCCACT
        AND pv.PVNANP = pc.PRCNANN
        AND pv.PVNPRE = pc.PRCNPRE
    INNER JOIN HLCOLPP co
        ON pc.PRCNCOL = co.O3NCOL
        AND co.O3CDEC = '010'  -- carton to pick
    INNER JOIN HLCOLIP ci
        ON pc.PRCNCOL = ci.C5NCOL
        AND ci.C5CTCO <> 'PRP'
    INNER JOIN HLPRENP pe
        ON pc.PRCCDPO = pe.PECDPO
        AND pc.PRCCACT = pe.PECACT
        AND pc.PRCNANN = pe.PENANN
        AND pc.PRCNPRE = pe.PENPRE
    WHERE mi.MITMVA = '0'  -- pick batch not confirmed
        AND mi.MITEVM = '0'  -- pick batch not being confirmed
        AND mi.MITECT = '0'  -- pick batch not being processed
        AND mi.MITBPM = 0  -- nothing picked yet (in base LVs)
        AND mi.MIIMIS = 'FMA'
        AND mi.MIPMIS <> '0'
        AND ci.C5CTCO <> 'WD1'
    GROUP BY ci.C5CTCO, mi.MIPMIS
)
ORDER BY
    CASE WHEN no_of_full_carts >= 1 THEN 0 ELSE 1 END,  -- at least 1 full cart first
    pick_batch_priority_code,  -- lower code = higher priority
    oldest_creation_datetime  -- oldest first
"""

FALLBACK_BINDING_ROWS: List[Dict[str, Any]] = [
    {
        "carton_type": "PDL",
        "pick_batch_priority_code": "5",
        "no_of_cartons": 10,
        "no_of_full_carts": 1.1,
        "oldest_creation_datetime": "2026-11-03 09:06:23.000",
    },
    {
        "carton_type": "PDS",
        "pick_batch_priority_code": "2",
        "no_of_cartons": 2,
        "no_of_full_carts": 0.1,
        "oldest_creation_datetime": "2026-11-02 20:27:29.000",
    },
    {
        "carton_type": "BKL",
        "pick_batch_priority_code": "5",
        "no_of_cartons": 5,
        "no_of_full_carts": 0.1,
        "oldest_creation_datetime": "2026-11-03 06:39:05.000",
    },
    {
        "carton_type": "PDM",
        "pick_batch_priority_code": "5",
        "no_of_cartons": 4,
        "no_of_full_carts": 0.4,
        "oldest_creation_datetime": "2026-11-03 09:07:06.000",
    },
]

_cached_rows: Optional[List[Dict[str, Any]]] = None
_cache_expiry: float = 0.0
_lock = asyncio.Lock()


def format_oldest_datetime(raw_val: Any) -> str:
    if raw_val is None:
        return "—"
    if isinstance(raw_val, datetime):
        return raw_val.strftime("%Y-%m-%d %H:%M:%S.000")
    s = str(raw_val).strip()
    if not s:
        return "—"
    if "T" in s:
        s = s.replace("T", " ")
    if "." not in s and len(s) == 19:
        return f"{s}.000"
    return s


def _query_binding_advisor_sync() -> List[Dict[str, Any]]:
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
            cur.execute(BINDING_ADVISOR_SQL)
            columns = [col[0].upper() for col in cur.description]
            raw_rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    result: List[Dict[str, Any]] = []
    for r in raw_rows:
        carton_type = str(r.get("CARTON_TYPE") or "").strip()
        priority_code = str(r.get("PICK_BATCH_PRIORITY_CODE") or "").strip()
        no_of_cartons = int(r.get("NO_OF_CARTONS") or 0)
        raw_full_carts = r.get("NO_OF_FULL_CARTS")
        if raw_full_carts is not None:
            no_of_full_carts = round(float(raw_full_carts), 1)
        else:
            cap = CART_CAPACITY_BY_TYPE.get(carton_type)
            no_of_full_carts = round(no_of_cartons / cap, 1) if cap else 0.0

        oldest_dt = format_oldest_datetime(r.get("OLDEST_CREATION_DATETIME"))

        result.append(
            {
                "carton_type": carton_type,
                "pick_batch_priority_code": priority_code,
                "no_of_cartons": no_of_cartons,
                "no_of_full_carts": no_of_full_carts,
                "oldest_creation_datetime": oldest_dt,
            }
        )
    return result


async def get_binding_advisor_rows() -> List[Dict[str, Any]]:
    global _cached_rows, _cache_expiry

    now = time.monotonic()
    if _cached_rows is not None and _cache_expiry > now:
        return _cached_rows

    async with _lock:
        if _cached_rows is not None and _cache_expiry > time.monotonic():
            return _cached_rows

        try:
            rows = await asyncio.to_thread(_query_binding_advisor_sync)
            _cached_rows = rows
            _cache_expiry = time.monotonic() + CACHE_TTL_SECONDS
            return rows
        except Exception as exc:
            logger.warning("Reflex BindingAdvisor query failed (%s); serving cached/fallback rows", exc)
            log_datadog_event(
                status="warning",
                message=f"BindingAdvisor Oracle query failed, using fallback: {exc}",
                event_type="binding_advisor.query",
                function_name="get_binding_advisor_rows",
            )
            if _cached_rows is not None:
                return _cached_rows

        return FALLBACK_BINDING_ROWS
