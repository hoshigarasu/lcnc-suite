"""Suite-wide structured trace bus.

Every component (gateway, hal_reader, hal_watchdog) imports this module and
calls `init(<proc_name>)` once at startup, then `emit(tag, **fields)` for
each event. All events land in /tmp/lcnc-trace.log as one NDJSON line each.

Why one shared file across processes: Linux guarantees atomic O_APPEND writes
up to PIPE_BUF (4096 B), so concurrent appends from multiple processes are
line-atomic. Each line carries `proc` + `pid` so the bundler can demux later.

Why direct file write (not queue + thread): NDJSON encoding is < 50 us per
event; line-buffered O_APPEND write is 1-10 us uncached. At our event rate
(~50/s steady, ~500/s burst) the cost is negligible vs the asyncio loop's
heartbeat budget.

Format example:
    {"t_wall_ns": 1735000000123456789, "t_mono_ms": 12345.6,
     "proc": "gateway", "pid": 1234,
     "tag": "lag", "level": "warn", "msg": "loop stalled",
     "drift_ms": 646}
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from typing import Any, Optional

TRACE_PATH = "/tmp/lcnc-trace.log"
_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
_BACKUPS = 5
_LOGGER_NAME = "lcnc.trace"

_proc_name: str = "?"
_pid: int = 0
_t0_mono: float = 0.0
_t0_wall_ns: int = 0
_logger: Optional[logging.Logger] = None
_initialized: bool = False


def init(proc_name: str) -> None:
    """Call once at process start. Records the boot time anchor and opens
    the trace file with rotation."""
    global _proc_name, _pid, _t0_mono, _t0_wall_ns, _logger, _initialized
    if _initialized:
        return
    _proc_name = proc_name
    _pid = os.getpid()
    _t0_mono = time.monotonic()
    _t0_wall_ns = time.time_ns()
    try:
        logger = logging.getLogger(_LOGGER_NAME)
        # Keep our handler isolated from the root logger.
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        # Don't double-attach if a previous init partially ran.
        if not any(isinstance(h, logging.handlers.RotatingFileHandler)
                   for h in logger.handlers):
            handler = logging.handlers.RotatingFileHandler(
                TRACE_PATH, maxBytes=_MAX_BYTES, backupCount=_BACKUPS
            )
            # We pre-encode NDJSON in the message; the formatter just emits
            # the message verbatim with a trailing newline (logging adds one).
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
        _logger = logger
    except Exception as e:
        print(f"[TRACE] init failed: {e}", file=sys.stderr, flush=True)
        _logger = None
    _initialized = True
    emit(
        "boot",
        t0_wall_ns=_t0_wall_ns,
        t0_mono=_t0_mono,
        argv=sys.argv,
        msg=f"{proc_name} trace started",
    )


def emit(tag: str, level: str = "info", msg: str = "", **fields: Any) -> None:
    """Append one NDJSON line to the trace bus. Never raises.

    Cheap and thread-safe (Python's logging module serializes via a lock).
    """
    if not _initialized or _logger is None:
        return
    now = time.monotonic()
    rec = {
        "t_wall_ns": time.time_ns(),
        "t_mono_ms": round((now - _t0_mono) * 1000, 3),
        "proc": _proc_name,
        "pid": _pid,
        "tag": tag,
        "level": level,
    }
    if msg:
        rec["msg"] = msg
    for k, v in fields.items():
        rec[k] = v
    try:
        line = json.dumps(rec, separators=(",", ":"), default=_json_default)
    except Exception as e:
        try:
            line = json.dumps(
                {"t_wall_ns": rec["t_wall_ns"], "t_mono_ms": rec["t_mono_ms"],
                 "proc": rec["proc"], "pid": rec["pid"], "tag": tag,
                 "level": "error", "msg": f"trace_encode_err: {e}"},
                separators=(",", ":"),
            )
        except Exception:
            return
    try:
        _logger.info(line)
    except Exception:
        pass


def _json_default(o: Any) -> Any:
    if isinstance(o, (set, frozenset, tuple)):
        return list(o)
    if isinstance(o, bytes):
        try:
            return o.decode("utf-8", errors="replace")
        except Exception:
            return repr(o)
    return repr(o)
