import * as THREE from "three";

/**
 * Assign vertex colors to a BufferGeometry based on Z height.
 * Below fluteLen: cutterColor. Above shoulderLen: shaftColor.
 * Between: linear blend.
 */
export function applyToolVertexColors(
  geo: THREE.BufferGeometry,
  fluteLen: number,
  shoulderLen: number,
  cutterColor: THREE.Color,
  shaftColor: THREE.Color
): void {
  const pos = geo.getAttribute("position");
  const colors = new Float32Array(pos.count * 3);
  const tmp = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const z = pos.getZ(i);
    if (z <= fluteLen) {
      tmp.copy(cutterColor);
    } else if (shoulderLen > fluteLen && z <= shoulderLen) {
      const t = (z - fluteLen) / (shoulderLen - fluteLen);
      tmp.copy(cutterColor).lerp(shaftColor, t);
    } else {
      tmp.copy(shaftColor);
    }
    colors[i * 3] = tmp.r;
    colors[i * 3 + 1] = tmp.g;
    colors[i * 3 + 2] = tmp.b;
  }
  geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
}

/**
 * Build a fallback two-cylinder tool geometry (cutter + shaft).
 * Supports different shaft diameter. Tool tip at Z=0, extends in +Z.
 */
export function buildFallbackCylinder(
  diam: number,
  len: number,
  fluteLen: number,
  shaftDiam?: number,
  segments = 24
): { cutter: THREE.BufferGeometry; shaft: THREE.BufferGeometry } {
  const r = diam / 2;
  const sr = (shaftDiam ?? diam) / 2;
  const cutterGeo = new THREE.CylinderGeometry(r, r, fluteLen, segments)
    .rotateX(Math.PI / 2)
    .translate(0, 0, fluteLen / 2);
  const shaftLen = Math.max(len - fluteLen, 0.1);
  const shaftGeo = new THREE.CylinderGeometry(sr, sr, shaftLen, segments)
    .rotateX(Math.PI / 2)
    .translate(0, 0, fluteLen + shaftLen / 2);
  return { cutter: cutterGeo, shaft: shaftGeo };
}
