# Toolsetter.vue Extraction

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract toolsetter logic from three files (SettingsPanel.vue, ControlsStrip.vue, App.vue) into a cohesive structure so that params, var mapping, and execution live together — fixing the var sync gap where `measureAuto()` fires M600 without syncing toolsetter vars.

**Architecture:** Extract `buildToolsetterVarMap()` to a shared module (`toolsetterVars.ts`). Extract the toolsetter settings template from SettingsPanel into `ToolsetterSettings.vue`. Fix App.vue to sync vars before M600/load/unload — matching the ProbePanel pattern where execution functions always call `setProbeVars` before MDI. Then relax `toolsetterParam` gate to `always`.

**Tech Stack:** Vue 3, TypeScript

**Prerequisite:** Gate relaxation plan (Task 1 — ProbePanel saveParams guard) should be completed first, as this plan follows the same pattern.

---

### Task 1: Extract buildToolsetterVarMap to shared module

The var map builder is currently inside SettingsPanel.vue (lines 298-310). It's a pure function of the saved defaults — no reactive state needed. Extract to a shared module so both ToolsetterSettings.vue and App.vue can use it.

**Files:**
- Create: `lcnc-webui/src/toolsetterVars.ts`
- Modify: `lcnc-webui/src/SettingsPanel.vue`

- [ ] **Step 1: Create toolsetterVars.ts**

```typescript
import { loadToolsetterDefaults } from "./defaults";

/** Build LinuxCNC var# → value map from saved toolsetter defaults.
 *  Used by both ToolsetterSettings (on param change) and App (before M600). */
export function buildToolsetterVarMap(): Record<string, number> {
  const p = loadToolsetterDefaults();
  return {
    "3004": p.fastFeed, "3005": p.slowFeed, "3006": p.traverseFeed,
    "3007": p.maxZTravel, "3009": p.retractDist, "3010": p.spindleZeroHeight,
    "3013": p.offsetDirection,
    "3100": p.touchX, "3101": p.touchY, "3102": p.touchZ,
    "3103": p.useToolTable, "3104": p.toolMinDis, "3105": p.brakeAfter,
    "3106": p.goBackToStart, "3107": p.spindleStopM, "3108": p.disablePrePos,
    "3109": p.addReps, "3110": p.lastTry, "3111": p.offsetDiameter,
    "3112": p.offsetValue, "3113": p.finderTouchX, "3114": p.finderTouchY,
    "3115": p.finderDiffZ,
  };
}
```

- [ ] **Step 2: Update SettingsPanel to use shared function**

Replace the local `buildVarMap()` function (lines 298-310) with an import:

```typescript
import { buildToolsetterVarMap } from "./toolsetterVars";
```

Update `saveTsParams()` to use it:

```typescript
function saveTsParams() {
  saveToolsetterDefaults({ ...tsParams.value });
  if (can.value.ready) emit("setProbeVars", buildToolsetterVarMap());
}
```

- [ ] **Step 3: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/toolsetterVars.ts lcnc-webui/src/SettingsPanel.vue
git commit -m "refactor: extract buildToolsetterVarMap to shared module

Pure function of saved defaults — no reactive state needed.
Enables App.vue to sync vars before M600 execution."
```

---

### Task 2: Fix App.vue to sync toolsetter vars before M600

This is the core fix. `measureAuto()`, `loadTool()`, and `unloadTool()` fire M600 without syncing toolsetter vars to the LinuxCNC var file. The M600 subroutine reads stale values.

Match the ProbePanel pattern: sync vars right before execution.

**Files:**
- Modify: `lcnc-webui/src/App.vue` (lines 680-706)

- [ ] **Step 1: Import buildToolsetterVarMap**

Add to the imports section of App.vue:

```typescript
import { buildToolsetterVarMap } from "./toolsetterVars";
```

- [ ] **Step 2: Sync vars before M600 in measureAuto()**

Change (lines 680-684):
```typescript
function measureAuto() {
  if (!permissions.value.ready || st.value.probing) return;
  saveToolNumber();
  fire({ cmd: "mdi", text: `T${toolNumber.value} M600` });
}
```

To:
```typescript
function measureAuto() {
  if (!permissions.value.ready || st.value.probing) return;
  saveToolNumber();
  send({ cmd: "set_probe_vars", vars: buildToolsetterVarMap() });
  fire({ cmd: "mdi", text: `T${toolNumber.value} M600` });
}
```

- [ ] **Step 3: Sync vars before M600 in loadTool()**

Change (lines 686-696):
```typescript
function loadTool() {
  if (!permissions.value.ready || st.value.probing) return;
  saveToolNumber();
  const n = toolNumber.value;
  const mode = loadMachineDefaults().toolChangeMode;
  if (mode === "m600") {
    fire({ cmd: "mdi", text: `T${n} M600` });
  } else {
    fire({ cmd: "mdi", text: `T${n} M6 G43 H${n}` });
  }
}
```

To:
```typescript
function loadTool() {
  if (!permissions.value.ready || st.value.probing) return;
  saveToolNumber();
  const n = toolNumber.value;
  const mode = loadMachineDefaults().toolChangeMode;
  if (mode === "m600") {
    send({ cmd: "set_probe_vars", vars: buildToolsetterVarMap() });
    fire({ cmd: "mdi", text: `T${n} M600` });
  } else {
    fire({ cmd: "mdi", text: `T${n} M6 G43 H${n}` });
  }
}
```

- [ ] **Step 4: Sync vars before M600 in unloadTool()**

Change (lines 698-706):
```typescript
function unloadTool() {
  if (!permissions.value.ready) return;
  const mode = loadMachineDefaults().toolChangeMode;
  if (mode === "m600") {
    fire({ cmd: "mdi", text: "T0 M600" });
  } else {
    fire({ cmd: "mdi", text: "T0 M6 G49" });
  }
}
```

To:
```typescript
function unloadTool() {
  if (!permissions.value.ready) return;
  const mode = loadMachineDefaults().toolChangeMode;
  if (mode === "m600") {
    send({ cmd: "set_probe_vars", vars: buildToolsetterVarMap() });
    fire({ cmd: "mdi", text: "T0 M600" });
  } else {
    fire({ cmd: "mdi", text: "T0 M6 G49" });
  }
}
```

- [ ] **Step 5: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 6: Commit**

```bash
git add lcnc-webui/src/App.vue
git commit -m "fix: sync toolsetter vars before M600 execution

measureAuto, loadTool, unloadTool now call set_probe_vars before
firing M600 — matching ProbePanel's pattern where execution
functions always sync vars before MDI. Fixes stale var file when
toolsetter params were edited but not yet synced."
```

---

### Task 3: Extract ToolsetterSettings.vue from SettingsPanel

Extract the toolsetter settings sub-tab into its own component. This reduces SettingsPanel's size and gives the toolsetter settings a clear home.

**Files:**
- Create: `lcnc-webui/src/ToolsetterSettings.vue`
- Modify: `lcnc-webui/src/SettingsPanel.vue`

- [ ] **Step 1: Create ToolsetterSettings.vue**

Extract from SettingsPanel:
- **Props:** `serverSettingsReady: boolean` (from SettingsPanel)
- **Emits:** `setProbeVars`, `mdi`
- **Script:** `tsParams` ref (lines 267-291), `loadTsParams()`, `saveTsParams()`, boolean wrappers (lines 323-326), G30 refs + `loadG30()`/`setG30()` (lines 329-356), constants (`OFFSET_DIR_LABELS`, `BRAKE_LABELS`), `probeTool` computed, `settingsVersion` watcher, `onMounted(loadTsParams)`
- **Template:** The toolsetter tab content (lines 841-960)
- **CSS:** `.tsGrid`, `.tsToggleGrid`, `.tsBtnRow`, `.readonlyVal` (lines 1570-1603)

```vue
<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { usePermissions } from "./permissions";
import {
  loadToolsetterDefaults,
  saveToolsetterDefaults,
  loadProbeDefaults,
  settingsVersion,
} from "./defaults";
import { buildToolsetterVarMap } from "./toolsetterVars";
import { fetchG30 } from "./lcncApi";
import MachineInput from "./MachineInput.vue";
import MachineToggle from "./MachineToggle.vue";
import MachineRadio from "./MachineRadio.vue";
import MachineBtn from "./MachineBtn.vue";
import { RefreshCw } from "lucide-vue-next";

defineProps<{
  serverSettingsReady: boolean;
  status: { position: { x: number; y: number; z: number } } | null;
}>();

const emit = defineEmits<{
  (e: "setProbeVars", vars: Record<string, number>): void;
  (e: "mdi", text: string): void;
  (e: "resetSection", section: string): void;
}>();

const can = usePermissions();

const STEP_DEFAULT = 0.001;
const STEP_FEED = 1;
const OFFSET_DIR_LABELS: Record<number, string> = { 0: "X-", 1: "X+", 2: "Y-", 3: "Y+" };
const BRAKE_LABELS: Record<number, string> = { 0: "None", 1: "M00", 2: "M01" };

const probeTool = computed(() => loadProbeDefaults().probeTool);

// ─── Toolsetter params ───
const tsParams = ref({
  fastFeed: 0, slowFeed: 0, traverseFeed: 0, maxZTravel: 0,
  retractDist: 0, spindleZeroHeight: 0, offsetDirection: 0,
  touchX: 0, touchY: 0, touchZ: 0,
  useToolTable: 0, toolMinDis: 0, brakeAfter: 0, goBackToStart: 0,
  spindleStopM: 5, disablePrePos: 0, addReps: 0, lastTry: 0,
  offsetDiameter: 0, offsetValue: 0,
  finderTouchX: 0, finderTouchY: 0, finderDiffZ: 0,
});

function loadTsParams() {
  Object.assign(tsParams.value, loadToolsetterDefaults());
}

function saveTsParams() {
  saveToolsetterDefaults({ ...tsParams.value });
  if (can.value.ready) emit("setProbeVars", buildToolsetterVarMap());
}

// Boolean wrappers (0/1 ↔ boolean)
const tsUseToolTable = computed({ get: () => tsParams.value.useToolTable === 1, set: (v: boolean) => { tsParams.value.useToolTable = v ? 1 : 0; saveTsParams(); } });
const tsGoBackToStart = computed({ get: () => tsParams.value.goBackToStart === 1, set: (v: boolean) => { tsParams.value.goBackToStart = v ? 1 : 0; saveTsParams(); } });
const tsDisablePrePos = computed({ get: () => tsParams.value.disablePrePos === 1, set: (v: boolean) => { tsParams.value.disablePrePos = v ? 1 : 0; saveTsParams(); } });
const tsLastTry = computed({ get: () => tsParams.value.lastTry === 1, set: (v: boolean) => { tsParams.value.lastTry = v ? 1 : 0; saveTsParams(); } });

// ─── G30 tool change position ───
const g30X = ref<number | null>(null);
const g30Y = ref<number | null>(null);
const g30Z = ref<number | null>(null);
const g30Loading = ref(false);

async function loadG30() {
  g30Loading.value = true;
  try {
    const data = await fetchG30();
    if (data.ok) { g30X.value = data.x; g30Y.value = data.y; g30Z.value = data.z; }
  } finally { g30Loading.value = false; }
}

function setG30() {
  emit("mdi", "G30.1");
  // Update display from current position after brief delay
  // (actual implementation reads from status prop)
}

onMounted(loadTsParams);
watch(settingsVersion, () => { loadTsParams(); });
</script>
```

The template is the entire toolsetter tab content from SettingsPanel lines 841-960 (position inputs, probe settings, options toggles, diameter offset, edge-finder, reset button). Copy it verbatim.

The scoped CSS is `.tsGrid`, `.tsToggleGrid`, `.tsBtnRow`, `.readonlyVal` from SettingsPanel lines 1570-1603. Copy verbatim.

- [ ] **Step 2: Update SettingsPanel to use ToolsetterSettings.vue**

Replace the toolsetter tab content (lines 841-960) with:

```vue
<template #toolsetter>
  <div v-if="!serverSettingsReady" class="settingsLoading">Waiting for server settings…</div>
  <ToolsetterSettings
    v-else
    :serverSettingsReady="serverSettingsReady"
    :status="status"
    @setProbeVars="emit('setProbeVars', $event)"
    @mdi="emit('mdi', $event)"
    @resetSection="resetTarget = $event"
  />
</template>
```

Remove from SettingsPanel:
- `tsParams` ref and all ts* computed wrappers
- `buildVarMap()` (already replaced in Task 1)
- `loadTsParams()`, `saveTsParams()`
- G30 refs and functions
- `OFFSET_DIR_LABELS`, `BRAKE_LABELS`
- `probeTool` computed
- Toolsetter CSS classes
- Unused imports (`loadToolsetterDefaults`, `saveToolsetterDefaults`, `TOOLSETTER_FALLBACK`, `buildToolsetterVarMap`)

- [ ] **Step 3: Verify SettingsPanel still has status prop**

ToolsetterSettings needs `status.position` for the G30 "Set" button. Verify SettingsPanel passes this through (it may already have status from App.vue, or it may need a new prop).

- [ ] **Step 4: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 5: Commit**

```bash
git add lcnc-webui/src/ToolsetterSettings.vue lcnc-webui/src/SettingsPanel.vue
git commit -m "refactor: extract ToolsetterSettings.vue from SettingsPanel

Toolsetter settings (params, var mapping, G30, boolean wrappers)
now live in a dedicated component. Reduces SettingsPanel size and
gives toolsetter logic a clear, single home."
```

---

### Task 4: Relax toolsetterParam gate to `always`

Now that var sync before M600 is fixed (Task 2) and the code is organized (Task 3), it's safe to relax the gate. Users can configure toolsetter params while the machine isn't ready — values save to server immediately, var file syncs at execution time.

**Files:**
- Modify: `lcnc-webui/src/machineControls.ts:134`

- [ ] **Step 1: Change gate**

```typescript
// Before
toolsetterParam: { gate: 'ready',    mono: true, align: 'right' },

// After
toolsetterParam: { gate: 'always',   mono: true, align: 'right' },
```

- [ ] **Step 2: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 3: Commit**

```bash
git add lcnc-webui/src/machineControls.ts
git commit -m "feat: relax toolsetterParam gate to always

Safe because measureAuto/loadTool/unloadTool now sync vars
before M600 execution (Task 2). Settings save to server
immediately; var file syncs at execution time."
```

---

## Data flow after extraction

```
┌──────────────────────┐     ┌────────────────────────┐
│   ControlsStrip.vue  │     │ ToolsetterSettings.vue  │
│ (sidebar buttons)    │     │ (settings tab)          │
│                      │     │                         │
│ Measure ──emit──┐    │     │ tsParams ─→ save ─→ server
│ Load    ──emit──┤    │     │         └─→ setProbeVars│
│ Unload  ──emit──┤    │     │             (if ready)  │
└─────────────────┼────┘     └────────────┬────────────┘
                  │                        │
                  ▼                        ▼
           ┌──────────────────────────────────┐
           │           App.vue                 │
           │                                   │
           │ measureAuto():                    │
           │   1. send(set_probe_vars, vars)  ◄── buildToolsetterVarMap()
           │   2. fire(mdi, "T# M600")        │   reads from server defaults
           └──────────────────────────────────┘
```

**Var file is synced at two points:**
1. On param change in ToolsetterSettings — if `can.ready` (immediate feedback)
2. Before M600 execution in App.vue — always (guaranteed fresh, from `toolsetterVars.ts`)

Same pattern as ProbePanel where execution functions sync before every probe.
