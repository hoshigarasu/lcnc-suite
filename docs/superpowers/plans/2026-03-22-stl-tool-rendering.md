# STL-Based Tool Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace parametric Fusion 360 geometry generation with per-tool STL files, falling back to a simple cylinder, with Z-height-based vertex coloring for cutter/shaft distinction and a 2D side-view preview in the tool table editor.

**Architecture:** Tools are rendered from user-supplied STL files stored in `lcnc-gateway/machine/tools/`. The gateway serves them via the existing `/assets/` static mount and provides an upload endpoint. ThreeViewer loads the STL using the existing `fetchAndParseStl` function, applies vertex colors based on `flute_length`/`shoulder_length` Z thresholds, and positions the tool at the spindle. Tools without an STL get a fallback cylinder built from `diameter` + `overall_length` + optional `shaft_diameter`. The tool table editor shows a small orthographic 2D side-view preview. Fusion import is kept for metadata only — geometry fields no longer drive rendering.

**Tech Stack:** Vue 3 + TypeScript, Three.js (STLLoader, CylinderGeometry for fallback), Python FastAPI, existing WebSocket protocol.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `lcnc-gateway/gateway.py` | Modify | Add `POST /tool-stl/{tool_num}` upload + `DELETE /tool-stl/{tool_num}`, add `stl_file` to `_TOOL_META_FIELDS`, create `machine/tools/` dir, clean up STL on tool delete |
| `lcnc-webui/src/toolGeometry.ts` | Create | Shared tool geometry utilities: `fetchToolSTL`, `applyToolVertexColors`, `buildFallbackCylinder` |
| `lcnc-webui/src/ThreeViewer.vue` | Modify | Replace `buildToolProfile`/`splitProfileAt`/`buildToolGeometry` with STL loading + fallback cylinder from `toolGeometry.ts` |
| `lcnc-webui/src/ToolTablePanel.vue` | Modify | Add STL upload button in edit modal, add `stl_file` to Tool interface |
| `lcnc-webui/src/ToolPreview.vue` | Create | Small orthographic Three.js canvas showing tool side-view with cutter/shaft coloring |

---

## Task 1: Gateway — Tool STL Upload & Serving

**Files:**
- Modify: `lcnc-gateway/gateway.py`

The gateway already serves `machine/` as `/assets/`. Tool STLs go in `machine/tools/` so they're automatically served at `/assets/tools/T1.stl` etc.

- [ ] **Step 1: Create tools subdirectory**

Add to gateway startup (after `MACHINE_DIR` definition around line 27):
```python
TOOLS_STL_DIR = MACHINE_DIR / "tools"
TOOLS_STL_DIR.mkdir(exist_ok=True)
```

- [ ] **Step 2: Add `stl_file` to `_TOOL_META_FIELDS`**

Add `"stl_file"` to the `_TOOL_META_FIELDS` tuple (line ~873). This field stores the STL filename (e.g. `"T5.stl"`) in `tool_library.json`. The frontend constructs the full URL from this filename.

- [ ] **Step 3: Add STL upload endpoint**

Add a `POST /tool-stl/{tool_num}` endpoint that:
1. Accepts a file upload (multipart form)
2. Validates file size (min 84 bytes for valid STL, max 10 MB)
3. Saves to `TOOLS_STL_DIR / f"T{tool_num}.stl"`
4. Updates `tool_library.json` metadata: sets `stl_file = f"T{tool_num}.stl"`
5. Sets `_tool_meta_dirty = True` so the next status poll pushes updated meta to clients
6. Returns `{ ok: true, stl_file: "T5.stl" }`

```python
@app.post("/tool-stl/{tool_num}")
async def upload_tool_stl(tool_num: int, file: UploadFile = File(...)):
    data = await file.read()
    if len(data) < 84:
        return JSONResponse({"ok": False, "error": "File too small for STL"}, 400)
    if len(data) > 10 * 1024 * 1024:
        return JSONResponse({"ok": False, "error": "File too large (max 10 MB)"}, 413)
    # Save atomically
    dest = TOOLS_STL_DIR / f"T{tool_num}.stl"
    with tempfile.NamedTemporaryFile(dir=TOOLS_STL_DIR, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    os.replace(tmp_path, dest)
    # Update metadata
    library = load_tool_library()
    key = str(tool_num)
    if key not in library:
        library[key] = {}
    library[key]["stl_file"] = f"T{tool_num}.stl"
    save_tool_library(library)
    global _tool_meta_dirty
    _tool_meta_dirty = True
    return {"ok": True, "stl_file": f"T{tool_num}.stl"}
```

- [ ] **Step 4: Add STL delete endpoint**

Add `DELETE /tool-stl/{tool_num}` that removes the STL file and clears the `stl_file` metadata field:
```python
@app.delete("/tool-stl/{tool_num}")
async def delete_tool_stl(tool_num: int):
    stl_path = TOOLS_STL_DIR / f"T{tool_num}.stl"
    if stl_path.exists():
        stl_path.unlink()
    library = load_tool_library()
    key = str(tool_num)
    if key in library:
        library[key].pop("stl_file", None)
        save_tool_library(library)
    global _tool_meta_dirty
    _tool_meta_dirty = True
    return {"ok": True}
```

- [ ] **Step 5: Clean up STL on tool deletion**

In the existing `delete_tool` WebSocket handler (~line 1923), after removing the tool from `tool_library.json`, also delete the associated STL file:
```python
# After removing from library and tool table:
stl_path = TOOLS_STL_DIR / f"T{tool_num}.stl"
if stl_path.exists():
    stl_path.unlink()
```

- [ ] **Step 6: Commit**

```bash
git add lcnc-gateway/gateway.py
git commit -m "feat: add tool STL upload/serve/delete endpoints and stl_file metadata"
```

---

## Task 2: Shared Tool Geometry Module

**Files:**
- Create: `lcnc-webui/src/toolGeometry.ts`

Create the shared module FIRST so both ThreeViewer and ToolPreview can import from it.

- [ ] **Step 1: Create `toolGeometry.ts` with `applyToolVertexColors`**

```typescript
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
```

- [ ] **Step 2: Add `buildFallbackCylinder` to `toolGeometry.ts`**

Two cylinders (cutter + shaft), supports different shaft diameter:
```typescript
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
```

- [ ] **Step 3: Run `npm run build`**

Verify zero TS errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/toolGeometry.ts
git commit -m "feat: create shared tool geometry utilities module"
```

---

## Task 3: ThreeViewer — STL Loading & Fallback Cylinder

**Files:**
- Modify: `lcnc-webui/src/ThreeViewer.vue`

Replace the parametric profile generation with: load STL if available, otherwise generate a simple cylinder.

- [ ] **Step 1: Add `stl_file` to `ToolMeta` interface**

```typescript
interface ToolMeta {
  // ... existing fields ...
  stl_file?: string;  // STL filename in machine/tools/ (e.g. "T5.stl")
}
```

The frontend constructs the full URL: `${stlBaseUrl}tools/${meta.stl_file}`.

- [ ] **Step 2: Import shared utilities**

```typescript
import { applyToolVertexColors, buildFallbackCylinder } from "./toolGeometry";
```

- [ ] **Step 3: Add vertex-color material for STL tools**

```typescript
// In the MAT object or alongside it:
const MAT_TOOL_STL = new THREE.MeshStandardMaterial({
  vertexColors: true,
  metalness: 0.2,
  roughness: 0.4,
});
```

Separate from `MAT.tool` and `MAT.cutter` which remain for the fallback cylinder.

- [ ] **Step 4: Add `loadToolSTL` function**

```typescript
async function loadToolSTL(
  stlFile: string, fluteLen: number, shoulderLen: number
): Promise<THREE.BufferGeometry> {
  const url = `${_stlBaseUrl}tools/${stlFile}`;
  const geo = await fetchAndParseStl(url);
  applyToolVertexColors(geo, fluteLen, shoulderLen, MAT.cutter.color, MAT.tool.color);
  return geo;
}
```

Uses the existing `fetchAndParseStl` function (line ~43) and `_stlBaseUrl` from `viewer_init`.

Note: `_stlBaseUrl` is set from `init.stl_base_url` during `viewer_init`. It already points to `http://{host}:8000/assets/`. Tool STLs at `/assets/tools/T5.stl` are reached via `${_stlBaseUrl}tools/T5.stl`.

- [ ] **Step 5: Rewrite `buildToolGroup` as async**

```typescript
let _toolBuildGen = 0;

async function buildToolGroup(
  diam: number, len: number, meta: ToolMeta | null
): Promise<THREE.Group> {
  const group = new THREE.Group();
  const fluteLen = meta?.flute_length ?? len * 0.6;
  const shoulderLen = meta?.shoulder_length ?? fluteLen;

  if (meta?.stl_file) {
    // STL path: single mesh with vertex colors
    try {
      const geo = await loadToolSTL(meta.stl_file, fluteLen, shoulderLen);
      const mesh = new THREE.Mesh(geo, MAT_TOOL_STL);
      group.add(mesh);
      toolBodyMesh = mesh;
      toolCutterMesh = null;
    } catch (e) {
      console.warn("Failed to load tool STL, falling back to cylinder:", e);
      addFallbackCylinder(group, diam, len, fluteLen, meta?.shaft_diameter);
    }
  } else {
    addFallbackCylinder(group, diam, len, fluteLen, meta?.shaft_diameter);
  }

  // Holder (unchanged)
  if (meta?.holder_segments?.length) {
    const holderGeo = buildHolderGeometry(meta.holder_segments, meta.oal ?? len);
    if (holderGeo) {
      holderMesh = new THREE.Mesh(holderGeo, MAT.holder);
      group.add(holderMesh);
    }
  }
  return group;
}

function addFallbackCylinder(
  group: THREE.Group, diam: number, len: number,
  fluteLen: number, shaftDiam?: number
): void {
  const { cutter, shaft } = buildFallbackCylinder(diam, len, fluteLen, shaftDiam);
  toolCutterMesh = new THREE.Mesh(cutter, MAT.cutter);
  toolBodyMesh = new THREE.Mesh(shaft, MAT.tool);
  group.add(toolCutterMesh, toolBodyMesh);
}
```

- [ ] **Step 6: Update watcher call sites for async**

The watcher that rebuilds the tool (~line 1456) needs an async IIFE with a generation counter to cancel stale loads:

```typescript
// In the tool rebuild watcher:
const gen = ++_toolBuildGen;
(async () => {
  const newGroup = await buildToolGroup(diam, len, meta);
  if (gen !== _toolBuildGen) {
    // A newer build started while we were loading — discard this one
    newGroup.traverse(c => { if ((c as any).geometry) (c as any).geometry.dispose(); });
    return;
  }
  // Remove old tool group, add new one
  if (_toolGrp) {
    _toolGrp.traverse(c => { if ((c as any).geometry) (c as any).geometry.dispose(); });
    groups.root.remove(_toolGrp);
  }
  _toolGrp = newGroup;
  groups.root.add(_toolGrp);
  requestRender();
})();
```

The fallback path (no STL) is effectively synchronous — `buildToolGroup` returns immediately after `addFallbackCylinder` since there's no `await` on that path.

- [ ] **Step 7: Update `setToolColors` for STL vertex colors**

When colors change and the current tool is STL-based (has vertex colors), reapply vertex colors:
```typescript
function setToolColors(toolColor: string | null, cutterColor: string | null): void {
  if (toolColor) MAT.tool.color.set(toolColor);
  if (cutterColor) MAT.cutter.color.set(cutterColor);
  // Re-color STL mesh if it uses vertex colors
  if (toolBodyMesh?.geometry?.getAttribute("color")) {
    const meta = _toolMetaCache.get(_currentToolNum) ?? null;
    const fluteLen = meta?.flute_length ?? _currentToolLen * 0.6;
    const shoulderLen = meta?.shoulder_length ?? fluteLen;
    applyToolVertexColors(
      toolBodyMesh.geometry, fluteLen, shoulderLen,
      MAT.cutter.color, MAT.tool.color
    );
    requestRender();
  }
}
```

- [ ] **Step 8: Remove old parametric code**

Delete these functions and their helpers:
- `buildToolProfile` (~200 lines, all per-type switch cases)
- `splitProfileAt`
- `buildToolGeometry`
- `addShoulder` helper closure
- `ProfileSegment` interface
- Formmill arc interpolation code

Keep: `HolderSegment` interface, `buildHolderGeometry` — holder rendering stays unchanged.

- [ ] **Step 9: Run `npm run build`**

Verify zero TS errors.

- [ ] **Step 10: Commit**

```bash
git add lcnc-webui/src/ThreeViewer.vue
git commit -m "feat: STL-based tool rendering with fallback cylinder"
```

---

## Task 4: ToolTablePanel — STL Upload UI

**Files:**
- Modify: `lcnc-webui/src/ToolTablePanel.vue`

Add an STL upload control in the tool edit modal.

- [ ] **Step 1: Add `stl_file` to Tool interface and editForm**

Add `stl_file: string | null` to the `Tool` interface (~line 23) and populate it in the edit form setup.

- [ ] **Step 2: Add STL upload section to edit modal**

In the edit modal (after the geometry fields section), add:
```html
<div class="sub">Tool Model</div>
<div class="row-controls">
  <label class="file-label" :class="{ inactive: !can.idle }">
    <input type="file" accept=".stl" @change="onStlUpload"
           :disabled="!can.idle" hidden>
    <span class="btn" :disabled="!can.idle">Upload STL</span>
  </label>
  <span v-if="editForm.stl_file" class="stl-name">
    {{ editForm.stl_file }}
    <button class="btn-icon" @click="removeStl" :disabled="!can.idle">×</button>
  </span>
  <span v-else class="hint">No STL — using fallback cylinder</span>
</div>
```

Note: upload gated behind `can.idle` permission.

- [ ] **Step 3: Implement `onStlUpload` handler**

```typescript
async function onStlUpload(e: Event) {
  if (!can.value.idle) return;
  const file = (e.target as HTMLInputElement).files?.[0];
  if (!file || !editForm.value) return;
  const form = new FormData();
  form.append("file", file);
  const toolNum = editForm.value.T;
  const resp = await fetch(`/tool-stl/${toolNum}`, { method: "POST", body: form });
  const data = await resp.json();
  if (data.ok) {
    editForm.value.stl_file = data.stl_file;
  }
  // Reset file input so same file can be re-uploaded
  (e.target as HTMLInputElement).value = "";
}
```

- [ ] **Step 4: Implement `removeStl` handler**

```typescript
async function removeStl() {
  if (!editForm.value || !can.value.idle) return;
  const toolNum = editForm.value.T;
  await fetch(`/tool-stl/${toolNum}`, { method: "DELETE" });
  editForm.value.stl_file = null;
}
```

- [ ] **Step 5: Run `npm run build`**

Verify zero TS errors.

- [ ] **Step 6: Commit**

```bash
git add lcnc-webui/src/ToolTablePanel.vue
git commit -m "feat: add STL upload/remove in tool edit modal"
```

---

## Task 5: ToolPreview Component — 2D Side View

**Files:**
- Create: `lcnc-webui/src/ToolPreview.vue`
- Modify: `lcnc-webui/src/ToolTablePanel.vue`

A small Three.js canvas that renders an orthographic side view of the tool with cutter/shaft coloring.

- [ ] **Step 1: Create `ToolPreview.vue` component**

Props:
```typescript
{
  diameter: number;
  length: number;
  fluteLength: number;
  shoulderLength: number;
  shaftDiameter?: number;
  stlFile: string | null;  // filename, not full URL
  width?: number;           // canvas width (default 80)
  height?: number;          // canvas height (default 120)
}
```

The component creates a tiny Three.js scene with:
1. Orthographic camera looking from the side (+X direction, Z-up)
2. If `stlFile`: loads STL via shared `fetchAndParseStl`, applies vertex colors
3. If no `stlFile`: creates fallback two-cylinder geometry via `buildFallbackCylinder`
4. Auto-fits camera to tool bounding box with 20% padding
5. Single ambient + directional light
6. Renders once (static — no animation loop, no OrbitControls)
7. Re-renders on prop changes via `watch`
8. Disposes renderer on unmount

The STL URL is constructed as `/assets/tools/${stlFile}` (direct fetch, no `_stlBaseUrl` needed since ToolPreview doesn't have access to viewer_init).

- [ ] **Step 2: Add ToolPreview to the edit modal in ToolTablePanel**

Place the preview canvas next to the geometry fields:
```html
<ToolPreview
  :diameter="editForm.D"
  :length="editForm.oal ?? Math.abs(editForm.Z) ?? 50"
  :flute-length="editForm.flute_length ?? (editForm.oal ?? 50) * 0.6"
  :shoulder-length="editForm.shoulder_length ?? editForm.flute_length ?? (editForm.oal ?? 50) * 0.6"
  :shaft-diameter="editForm.shaft_diameter ?? editForm.D"
  :stl-file="editForm.stl_file"
  :width="100"
  :height="160"
/>
```

The preview updates live as the user edits diameter, flute length, etc.

- [ ] **Step 3: Run `npm run build`**

Verify zero TS errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/ToolPreview.vue lcnc-webui/src/ToolTablePanel.vue
git commit -m "feat: add 2D tool preview in tool table editor"
```

---

## Task 6: Clean Up Fusion Geometry Import

**Files:**
- Modify: `lcnc-gateway/gateway.py`
- Modify: `lcnc-webui/src/ThreeViewer.vue`

Keep Fusion import for metadata, remove geometry-specific processing.

- [ ] **Step 1: Simplify `_parse_fusion_library` in gateway**

Keep parsing: `type`, `description`, `number`, `DC`, `NOF`, `OAL`, `LCF`, `RE`, `SFDM`, `TA`, `SIG`, `tip-diameter`, `shoulder-length`, `shoulder-diameter`, `LB`, `BMC`, `holder`, `presets`.

These fields remain as informational metadata — useful for display, filtering, and the fallback cylinder (diameter + OAL + shaft_diameter).

Remove: `profile` segment parsing (form mill outlines) — no longer used for geometry.

- [ ] **Step 2: Verify dead code removal from ThreeViewer**

Confirm that Task 3 Step 8 fully removed: `buildToolProfile`, `splitProfileAt`, `buildToolGeometry`, `addShoulder`, `ProfileSegment` interface, formmill arc interpolation.

Confirm kept: `HolderSegment` interface, `buildHolderGeometry`.

- [ ] **Step 3: Run `npm run build`**

Verify zero TS errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-gateway/gateway.py lcnc-webui/src/ThreeViewer.vue
git commit -m "chore: remove formmill profile parsing, keep Fusion metadata import"
```

---

## Task 7: Update Documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md**

- Update Frontend Structure to mention `ToolPreview.vue` and `toolGeometry.ts`
- Update Key Patterns: remove references to `buildToolProfile` per-type cases, `splitProfileAt`, `addShoulder`
- Add note: "Tool geometry from per-tool STL files in `machine/tools/`, fallback to diameter+length cylinder. Vertex colors split by `flute_length`/`shoulder_length` Z thresholds."
- Add lesson learned: "Fusion 360 tool library geometry params (`TA`, `LCF`, `LB`, `shoulder-length`) are ambiguous per tool type with no official docs. STL import eliminates the interpretation guesswork."

- [ ] **Step 2: Update README.md**

- Update 3D visualization feature: mention STL tool models with per-tool upload
- Update tool table features: STL upload, 2D preview, fallback cylinder
- Update settings sync list if needed

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md README.md
git commit -m "docs: update for STL-based tool rendering"
```

---

## Execution Order & Dependencies

```
Task 1 (Gateway endpoints)
    ↓
Task 2 (Shared toolGeometry.ts)
    ↓
Task 3 (ThreeViewer STL loading) ←──── Task 4 (Upload UI)
    ↓                                      ↓
Task 5 (ToolPreview component) ←───────────┘
    ↓
Task 6 (Clean up Fusion geometry)
    ↓
Task 7 (Documentation)
```

All tasks are sequential. Task 1 provides the backend. Task 2 creates the shared module. Task 3 rewrites ThreeViewer using the shared module. Task 4 adds the upload UI (can be done alongside Task 3 since they touch different files, but both depend on Task 1). Task 5 creates ToolPreview using the shared module. Task 6 cleans up. Task 7 documents.

---

## Key Decisions & Trade-offs

1. **STL origin convention**: Tool tip center at (0, 0, 0), tool extends in +Z. Users must orient their STLs to this convention. Document clearly in the upload UI.

2. **Frontend constructs STL URL from `stl_file` filename**: Avoids duplicating URL computation in multiple gateway code paths (REST merge vs WebSocket tool_meta push). The frontend knows the base URL and just appends `tools/${stl_file}`.

3. **Vertex colors vs multi-mesh for STL**: STL tools use a single mesh with vertex colors (avoids splitting arbitrary geometry at a Z plane). Fallback cylinder uses two meshes with separate materials (trivial geometry, existing coloring approach).

4. **Shoulder blend zone**: Linear color interpolation between `flute_length` and `shoulder_length`. If equal, hard boundary.

5. **No STL caching in IndexedDB**: Tool STLs are small (<10 MB limit, typically <1 MB) and served with cache headers via `CacheStaticAssets` middleware. Browser HTTP cache is sufficient.

6. **Fusion import preserved**: Still useful for bulk-importing metadata (flutes, material, type, description, holder segments). No longer drives geometry.

7. **Fallback cylinder uses `shaft_diameter`**: When available from tool metadata, the shaft section uses a different diameter than the cutter section, giving a more realistic silhouette even without an STL.

8. **Tool deletion cleans up STL**: The existing `delete_tool` handler also removes the STL file to prevent orphaned files.

9. **Async `buildToolGroup` with generation counter**: Prevents race conditions when tool changes rapidly while an STL is still loading. Stale loads are discarded.
