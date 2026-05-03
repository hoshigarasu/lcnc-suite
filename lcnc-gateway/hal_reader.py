#!/usr/bin/env python3
"""HAL reader for the web UI gateway.

Loaded by LinuxCNC HAL config:  loadusr -W hal_reader.py
Owns the `webui-reader` HAL component so the gateway process never has to
import `hal` directly.

Two responsibilities, both over a single Unix socket:

1. Push a snapshot of the pins the gateway needs to render the UI (tool
   change request, spindle RPM, eoffset, probe input, comp method/version,
   safety trip-count) at 30 Hz to the connected gateway.

2. Serve on-demand requests from the gateway:
     - "set_p"          → hal.set_p(pin, value)   (compensation reload bumps)
     - "halshow_dump"   → hal.get_info_pins/signals/params for the diag tab

Why split this from hal_watchdog.py?  hal_watchdog is the safety-supervisor
process — it owns trip detection and the trip-latch.  Keeping it small and
single-purpose makes it easier to audit.  hal_reader is pure observation
(plus a couple of writes); its failure mode is "display values stale, comp
reload skipped" — never a safety regression.

See plan: ~/.claude/plans/eager-snuggling-badger.md
See also: GitHub issue #9 (history of the previous in-gateway approach).
"""
import os
import sys
import json
import signal
import time
import socket
import select
import hal

import lcnc_trace as _trace
_trace.init("hal_reader")

COMP_NAME = "webui-reader"
SOCK_PATH = "/tmp/webui-reader.sock"
POLL_HZ = 30
SELECT_TIMEOUT = 1.0 / POLL_HZ

# (source pin name, snapshot field name, coerce fn)
SNAPSHOT_PINS = [
    ("iocontrol.0.tool-change",      "tool_change",       bool),
    ("iocontrol.0.tool-prep-number", "tool_prep_number",  int),
    ("spindle.0.speed-in",           "spindle_speed_in",  float),
    ("axis.z.eoffset",               "z_eoffset",         float),
    ("axis.z.eoffset-enable",        "z_eoffset_enable",  bool),
    ("motion.probe-input",           "probe_input",       bool),
    ("compensation.method",          "comp_method",       int),
    ("compensation.grid-version",    "comp_grid_version", int),
    ("webui-safety.trip-count",      "trip_count",        int),
]

# ---- Create HAL component ----
try:
    comp = hal.component(COMP_NAME)
    comp.ready()
except Exception as e:
    print(f"HAL component '{COMP_NAME}' failed: {e}", file=sys.stderr, flush=True)
    sys.exit(1)


print(f"[READER] watching {len(SNAPSHOT_PINS)} pins (no startup probe — every read attempted every tick)", flush=True)
print("OK", flush=True)  # signal to loadusr -W


# ---- Unix socket server ----
if os.path.exists(SOCK_PATH):
    os.unlink(SOCK_PATH)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCK_PATH)
server.listen(1)
server.setblocking(False)

client = None
buf = ""


def _format_hal_value(v) -> str:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _drop_client(c) -> None:
    """Close a client socket, ignoring already-closed / broken-pipe errors.
    Caller is responsible for `client = None; buf = ""` if those locals exist."""
    try:
        c.close()
    except Exception:
        pass


def _halshow_dump():
    out = {"pins": {}, "signals": {}, "params": {}}
    for entry in hal.get_info_pins():
        out["pins"][entry["NAME"]] = _format_hal_value(entry["VALUE"])
    for entry in hal.get_info_signals():
        out["signals"][entry["NAME"]] = _format_hal_value(entry["VALUE"])
    for entry in hal.get_info_params():
        out["params"][entry["NAME"]] = _format_hal_value(entry["VALUE"])
    return out


def _handle_request(msg: dict) -> dict:
    """Dispatch a gateway request. Returns a reply dict (with the same id)."""
    req_id = msg.get("id")
    req = msg.get("req")
    t0 = time.monotonic()
    try:
        if req == "set_p":
            hal.set_p(msg["pin"], str(msg["value"]))
            reply = {"type": "reply", "id": req_id, "ok": True}
        elif req == "halshow_dump":
            reply = {"type": "reply", "id": req_id, "ok": True, "result": _halshow_dump()}
        else:
            reply = {"type": "reply", "id": req_id, "ok": False, "error": f"unknown req '{req}'"}
    except Exception as e:
        reply = {"type": "reply", "id": req_id, "ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        _trace.emit(
            "reader.rpc",
            op=str(req),
            handler_ms=round((time.monotonic() - t0) * 1000, 2),
        )
    return reply


def _send(sock, obj: dict):
    sock.sendall((json.dumps(obj) + "\n").encode())


def _build_snapshot() -> dict:
    snap = {"type": "snapshot", "ts": int(time.time() * 1000)}
    for source, field, coerce in SNAPSHOT_PINS:
        try:
            snap[field] = coerce(hal.get_value(source))
        except Exception as e:
            # Pin missing right now — log every tick. The gateway will see
            # the field absent from the snapshot and surface that honestly.
            print(f"[READER] read '{source}' failed: {e}", flush=True)
    return snap


# Aggregate stats for reader.tick: emit one summary every N ticks rather
# than spamming every 33 ms. (The merged trace would be unreadable
# otherwise; we want signal, not raw cadence.)
_tick_count = 0
_tick_max_pin_ms = 0.0
_tick_max_send_ms = 0.0
_tick_total_pin_ms = 0.0
_tick_total_send_ms = 0.0
_TICK_SUMMARY_EVERY = 30  # ~1 s at POLL_HZ=30


next_push = time.monotonic()

# Cooperative shutdown: halrun sends SIGTERM on unload. select.select() is
# interrupted by the signal in the main thread, so the loop exits within
# one tick (~33 ms at 30 Hz) instead of waiting for halrun's SIGKILL.
_running = True
def _stop(*_):
    global _running
    _running = False
signal.signal(signal.SIGTERM, _stop)
signal.signal(signal.SIGINT, _stop)

try:
    while _running:
        socks = [server]
        if client is not None:
            socks.append(client)

        timeout = max(0.0, next_push - time.monotonic())
        readable, _, _ = select.select(socks, [], [], timeout)

        # Incoming connections / requests
        for sock in readable:
            if sock is server:
                new_client, _ = server.accept()
                new_client.setblocking(False)
                if client is not None:
                    _drop_client(client)
                client = new_client
                buf = ""
            elif sock is client:
                try:
                    data = client.recv(65536)
                except Exception:
                    data = b""
                if not data:
                    _drop_client(client)
                    client = None
                    buf = ""
                    continue
                buf += data.decode()
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except Exception as e:
                        print(f"[READER] bad json from gateway: {e}", flush=True)
                        continue
                    reply = _handle_request(msg)
                    try:
                        _send(client, reply)
                    except Exception:
                        _drop_client(client)
                        client = None
                        buf = ""
                        break

        # Periodic snapshot push
        now = time.monotonic()
        if now >= next_push:
            next_push = now + (1.0 / POLL_HZ)
            if client is not None:
                _t0 = time.monotonic()
                snap = _build_snapshot()
                _t1 = time.monotonic()
                try:
                    _send(client, snap)
                except Exception:
                    _drop_client(client)
                    client = None
                    buf = ""
                _t2 = time.monotonic()
                pin_ms = (_t1 - _t0) * 1000
                send_ms = (_t2 - _t1) * 1000
                _tick_count += 1
                _tick_total_pin_ms += pin_ms
                _tick_total_send_ms += send_ms
                if pin_ms > _tick_max_pin_ms:
                    _tick_max_pin_ms = pin_ms
                if send_ms > _tick_max_send_ms:
                    _tick_max_send_ms = send_ms
                if _tick_count >= _TICK_SUMMARY_EVERY:
                    _trace.emit(
                        "reader.tick_summary",
                        count=_tick_count,
                        avg_pin_ms=round(_tick_total_pin_ms / _tick_count, 3),
                        max_pin_ms=round(_tick_max_pin_ms, 3),
                        avg_send_ms=round(_tick_total_send_ms / _tick_count, 3),
                        max_send_ms=round(_tick_max_send_ms, 3),
                    )
                    _tick_count = 0
                    _tick_max_pin_ms = 0.0
                    _tick_max_send_ms = 0.0
                    _tick_total_pin_ms = 0.0
                    _tick_total_send_ms = 0.0
                # Always-on individual-tick event for slow ticks: anything
                # over 5 ms is unusual at 30 Hz and worth surfacing.
                if pin_ms > 5 or send_ms > 5:
                    _trace.emit(
                        "reader.tick_slow", level="warn",
                        pin_ms=round(pin_ms, 2),
                        send_ms=round(send_ms, 2),
                    )
except KeyboardInterrupt:
    pass
finally:
    if client:
        _drop_client(client)
    server.close()
    if os.path.exists(SOCK_PATH):
        os.unlink(SOCK_PATH)
    try:
        comp.exit()
    except Exception as e:
        print(f"[READER] comp.exit failed: {e}", flush=True)
