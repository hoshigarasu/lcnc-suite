#!/usr/bin/env python3
"""Shared G-code preview canon + var-file patching.

Lives outside gateway.py so the subprocess worker (gcode_parse_worker.py)
can import the same class without dragging gateway state in. Gateway uses
apply_var_patches() when building the context handed to the worker.
"""

from typing import Dict, List
from rs274.interpret import Translated, ArcsToSegmentsMixin, StatMixin


class PreviewCanon(Translated, ArcsToSegmentsMixin, StatMixin):
    """Lightweight canon that collects feed/rapid polylines for 3D preview."""

    def __init__(self, s, random=0):
        StatMixin.__init__(self, s, random)
        self.feed = []          # [(lineno, start_9, end_9, feedrate, tlo_3)]
        self.rapid = []         # [(lineno, start_9, end_9, tlo_3)]
        self.lineno = -1
        self.feedrate = 1.0
        self.lo = (0,) * 9
        self.first_move = True
        self.suppress = 0
        self.arc_dist = 0.0
        self.arc_moves = 0
        self.tools_used = set()
        self.tool_changes = 0
        self.xo = self.yo = self.zo = 0.0
        self.ao = self.bo = self.co = 0.0
        self.uo = self.vo = self.wo = 0.0
        self.g5x_index = 1
        self.plane = 1
        self.arcdivision = 64

    def next_line(self, st):
        self.state = st
        self.lineno = st.sequence_number

    def set_feed_rate(self, f): self.feedrate = f / 60.0
    def set_spindle_rate(self, _): pass
    def select_plane(self, _): pass
    def comment(self, _): pass
    def message(self, _): pass
    def check_abort(self): pass
    def user_defined_function(self, i, p, q): pass
    def dwell(self, _): pass

    def change_tool(self, idx):
        StatMixin.change_tool(self, idx)
        self.first_move = True
        self.tool_changes += 1
        if idx > 0:
            self.tools_used.add(idx)

    def tool_offset(self, xo, yo, zo, ao, bo, co, uo, vo, wo):
        self.first_move = True
        x, y, z, a, b, c, u, v, w = self.lo
        self.lo = (x - xo + self.xo, y - yo + self.yo, z - zo + self.zo,
                   a - ao + self.ao, b - bo + self.bo, c - co + self.co,
                   u - uo + self.uo, v - vo + self.vo, w - wo + self.wo)
        self.xo, self.yo, self.zo = xo, yo, zo
        self.ao, self.bo, self.co = ao, bo, co
        self.uo, self.vo, self.wo = uo, vo, wo

    # rotate_and_translate keeps straight moves in the same translated frame
    # gcode.arc_to_segments produces for arcs; WCS offsets subtract once at
    # extraction time (not here).
    def straight_traverse(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0: return
        l = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
        if not self.first_move:
            self.rapid.append((self.lineno, self.lo, l, (self.xo, self.yo, self.zo)))
        self.lo = l

    def straight_feed(self, x, y, z, a, b, c, u, v, w):
        if self.suppress > 0: return
        self.first_move = False
        l = self.rotate_and_translate(x, y, z, a, b, c, u, v, w)
        self.feed.append((self.lineno, self.lo, l, self.feedrate, (self.xo, self.yo, self.zo)))
        self.lo = l

    straight_probe = straight_feed

    def rigid_tap(self, x, y, z):
        if self.suppress > 0: return
        self.first_move = False
        l = self.rotate_and_translate(x, y, z, 0, 0, 0, 0, 0, 0)[:3]
        l += (self.lo[3], self.lo[4], self.lo[5],
              self.lo[6], self.lo[7], self.lo[8])
        self.feed.append((self.lineno, self.lo, l, self.feedrate, (self.xo, self.yo, self.zo)))
        self.feed.append((self.lineno, l, self.lo, self.feedrate, (self.xo, self.yo, self.zo)))

    def straight_arcsegments(self, segs):
        self.first_move = False
        lo = self.lo
        for l in segs:
            self.feed.append((self.lineno, lo, l, self.feedrate, (self.xo, self.yo, self.zo)))
            dx, dy, dz = l[0] - lo[0], l[1] - lo[1], l[2] - lo[2]
            self.arc_dist += (dx * dx + dy * dy + dz * dz) ** 0.5
            self.arc_moves += 1
            lo = l
        self.lo = lo


def apply_var_patches(path: str, patches: Dict[str, str]) -> None:
    """Overwrite numeric-parameter lines in a LinuxCNC var file in place.

    LinuxCNC only writes the var file on shutdown, so runtime edits (e.g.
    G10 L2 R rotation) don't reach disk until then. Gateway hands us the
    fresh values; we rewrite the temp copy the parser will read.
    """
    if not patches:
        return
    lines: List[str] = []
    seen: set = set()
    try:
        with open(path, "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[0] in patches:
                    lines.append(f"{parts[0]}\t{patches[parts[0]]}\n")
                    seen.add(parts[0])
                else:
                    lines.append(line)
        for pnum, val in patches.items():
            if pnum not in seen:
                lines.append(f"{pnum}\t{val}\n")
        with open(path, "w") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"[GCODE] var file patch failed: {e}")
