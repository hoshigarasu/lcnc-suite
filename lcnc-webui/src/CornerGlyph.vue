<script setup lang="ts">
// SVG glyphs for the probe-grid buttons. Replaces 18 near-identical inline
// <svg> blocks in ProbePanel.vue (9 outside-grid + 9 inside-grid). Geometry
// is table-driven; arrow polygons are computed from {tipX, tipY, dir} so the
// only per-cell data is "where the arrow lands and which way it points".
//
// Visual classes (.gridIcon/.workpiece/.probeTip/.arrowHead/.crosshair/
// .gridZLabel) are global in style.css so the inline SVGs that remain in
// ProbePanel (boss/angle/ridge grids) keep matching styles.
import { computed } from 'vue';

type Corner = 'bl' | 'b' | 'br' | 'l' | 'z' | 'r' | 'fl' | 'f' | 'fr';
type Mode = 'outside' | 'inside';
type ArrowDir = 'up' | 'down' | 'left' | 'right';
type Workpiece =
  | { tag: 'rect'; x: number; y: number; w: number; h: number }
  | { tag: 'path'; d: string };

interface Spec {
  workpiece: Workpiece;
  probeTip: { cx: number; cy: number; r?: number };
  arrows: Array<{ x: number; y: number; dir: ArrowDir }>;
  crosshair: { cx: number; cy: number; r?: number };
  zLabel?: boolean;
}

// Corner is typed loosely (`string`) at the prop boundary because the grid
// arrays in ProbePanel are typed `GridOp[]` with `id: string` — narrowing
// would force a parallel CornerOp type for outside/inside vs. boss/angle/
// ridge grids. We trust the caller; the spec lookup just returns undefined
// if a non-corner id slips in, and the template renders nothing.
const props = defineProps<{ corner: string; mode: Mode }>();

// Outside grid: 60×60 rect workpiece; probe approaches every edge from outside.
const RECT_60: Workpiece = { tag: 'rect', x: 10, y: 10, w: 60, h: 60 };

const OUTSIDE: Record<Corner, Spec> = {
  bl: { workpiece: RECT_60, probeTip: { cx: 28, cy: 28 }, arrows: [{ x: 28, y: 10, dir: 'down' }, { x: 10, y: 28, dir: 'right' }], crosshair: { cx: 10, cy: 10 } },
  b:  { workpiece: RECT_60, probeTip: { cx: 40, cy: 28 }, arrows: [{ x: 40, y: 10, dir: 'down' }],                                  crosshair: { cx: 40, cy: 10 } },
  br: { workpiece: RECT_60, probeTip: { cx: 52, cy: 28 }, arrows: [{ x: 52, y: 10, dir: 'down' }, { x: 70, y: 28, dir: 'left' }],   crosshair: { cx: 70, cy: 10 } },
  l:  { workpiece: RECT_60, probeTip: { cx: 28, cy: 40 }, arrows: [{ x: 10, y: 40, dir: 'right' }],                                 crosshair: { cx: 10, cy: 40 } },
  z:  { workpiece: RECT_60, probeTip: { cx: 40, cy: 40, r: 5 }, arrows: [], crosshair: { cx: 40, cy: 40, r: 9 }, zLabel: true },
  r:  { workpiece: RECT_60, probeTip: { cx: 52, cy: 40 }, arrows: [{ x: 70, y: 40, dir: 'left' }],                                  crosshair: { cx: 70, cy: 40 } },
  fl: { workpiece: RECT_60, probeTip: { cx: 28, cy: 52 }, arrows: [{ x: 28, y: 70, dir: 'up' }, { x: 10, y: 52, dir: 'right' }],    crosshair: { cx: 10, cy: 70 } },
  f:  { workpiece: RECT_60, probeTip: { cx: 40, cy: 52 }, arrows: [{ x: 40, y: 70, dir: 'up' }],                                    crosshair: { cx: 40, cy: 70 } },
  fr: { workpiece: RECT_60, probeTip: { cx: 52, cy: 52 }, arrows: [{ x: 52, y: 70, dir: 'up' }, { x: 70, y: 52, dir: 'left' }],     crosshair: { cx: 70, cy: 70 } },
};

// Inside grid: L-shape walls (corners) or half-rect strips (edges); probe
// inside the corner reaching out toward each wall.
const INSIDE: Record<Corner, Spec> = {
  bl: { workpiece: { tag: 'path', d: 'M0 0H80V35H35V80H0Z' },        probeTip: { cx: 24, cy: 24 }, arrows: [{ x: 52, y: 35, dir: 'up' },  { x: 35, y: 52, dir: 'right' }], crosshair: { cx: 35, cy: 35 } },
  b:  { workpiece: { tag: 'rect', x: 0, y: 0, w: 80, h: 35 },         probeTip: { cx: 40, cy: 55 }, arrows: [{ x: 40, y: 35, dir: 'up' }],                                   crosshair: { cx: 40, cy: 35 } },
  br: { workpiece: { tag: 'path', d: 'M0 0H80V80H45V35H0Z' },        probeTip: { cx: 56, cy: 24 }, arrows: [{ x: 28, y: 35, dir: 'up' },  { x: 45, y: 52, dir: 'left' }],  crosshair: { cx: 45, cy: 35 } },
  l:  { workpiece: { tag: 'rect', x: 0, y: 0, w: 35, h: 80 },         probeTip: { cx: 55, cy: 40 }, arrows: [{ x: 35, y: 40, dir: 'right' }],                                crosshair: { cx: 35, cy: 40 } },
  z:  { workpiece: { tag: 'rect', x: 0, y: 0, w: 80, h: 80 },         probeTip: { cx: 40, cy: 40, r: 5 }, arrows: [], crosshair: { cx: 40, cy: 40, r: 9 }, zLabel: true },
  r:  { workpiece: { tag: 'rect', x: 45, y: 0, w: 35, h: 80 },        probeTip: { cx: 25, cy: 40 }, arrows: [{ x: 45, y: 40, dir: 'left' }],                                 crosshair: { cx: 45, cy: 40 } },
  fl: { workpiece: { tag: 'path', d: 'M0 0H35V45H80V80H0Z' },        probeTip: { cx: 24, cy: 56 }, arrows: [{ x: 52, y: 45, dir: 'down' }, { x: 35, y: 28, dir: 'right' }], crosshair: { cx: 35, cy: 45 } },
  f:  { workpiece: { tag: 'rect', x: 0, y: 45, w: 80, h: 35 },        probeTip: { cx: 40, cy: 25 }, arrows: [{ x: 40, y: 45, dir: 'down' }],                                 crosshair: { cx: 40, cy: 45 } },
  fr: { workpiece: { tag: 'path', d: 'M45 0H80V80H0V45H45Z' },        probeTip: { cx: 56, cy: 56 }, arrows: [{ x: 28, y: 45, dir: 'down' }, { x: 45, y: 28, dir: 'left' }],  crosshair: { cx: 45, cy: 45 } },
};

// Tip is at (x, y); base is offset 9 units away in the opposite direction
// of `dir`. Half-width 5. e.g. dir='down' means base ABOVE tip in screen
// coordinates (tip is below base; arrow visually points down).
const BASE_DIST = 9;
const HALF_WIDTH = 5;
function arrowPoints(x: number, y: number, dir: ArrowDir): string {
  switch (dir) {
    case 'down':  return `${x},${y} ${x - HALF_WIDTH},${y - BASE_DIST} ${x + HALF_WIDTH},${y - BASE_DIST}`;
    case 'up':    return `${x},${y} ${x - HALF_WIDTH},${y + BASE_DIST} ${x + HALF_WIDTH},${y + BASE_DIST}`;
    case 'right': return `${x},${y} ${x - BASE_DIST},${y - HALF_WIDTH} ${x - BASE_DIST},${y + HALF_WIDTH}`;
    case 'left':  return `${x},${y} ${x + BASE_DIST},${y - HALF_WIDTH} ${x + BASE_DIST},${y + HALF_WIDTH}`;
  }
}

const spec = computed<Spec | undefined>(() => {
  const map = props.mode === 'outside' ? OUTSIDE : INSIDE;
  return (map as Record<string, Spec>)[props.corner];
});
</script>

<template>
  <svg v-if="spec" viewBox="0 0 80 80" class="gridIcon">
    <rect
      v-if="spec.workpiece.tag === 'rect'"
      :x="spec.workpiece.x" :y="spec.workpiece.y"
      :width="spec.workpiece.w" :height="spec.workpiece.h"
      class="workpiece"
    />
    <path v-else :d="spec.workpiece.d" class="workpiece" />

    <circle :cx="spec.probeTip.cx" :cy="spec.probeTip.cy" :r="spec.probeTip.r ?? 4" class="probeTip" />

    <polygon v-for="(a, i) in spec.arrows" :key="i" :points="arrowPoints(a.x, a.y, a.dir)" class="arrowHead" />

    <circle :cx="spec.crosshair.cx" :cy="spec.crosshair.cy" :r="spec.crosshair.r ?? 2.5" class="crosshair" />

    <text v-if="spec.zLabel" x="40" y="60" class="gridZLabel">Z</text>
  </svg>
</template>
