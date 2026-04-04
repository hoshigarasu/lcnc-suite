# Gate Relaxation — Config/Display Controls to `always`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Relax permission gates on controls that don't command the machine — display settings, saved config, search/filter, and pre-fill inputs — from `idle`/`ready` to `always`, so they're usable whenever armed (the outer Gate enforces armed+!estop via fieldset-disabled).

**Architecture:** Three areas: (1) guard the MDI sync in ProbePanel's `saveParams()` to match SettingsPanel's existing pattern, (2) change catalog gate values in `machineControls.ts`, (3) fix inner `<Gate>` wrappers in templates that would otherwise override relaxed gates. Toolsetter params are excluded — they require the Toolsetter.vue extraction (separate plan) before relaxation is safe.

**Tech Stack:** Vue 3, TypeScript

---

### Task 1: Guard MDI sync in ProbePanel saveParams()

ProbePanel's `saveParams()` unconditionally emits `setProbeVars` (MDI) on every input change. SettingsPanel's `saveTsParams()` already guards this with `if (can.value.ready)`. Make them consistent — the gate belongs on the save function, not buried in the input.

This is safe because every probe/scan execution function (`runGridProbe`, `runBossProbe`, `runRidgeProbe`, `runAngleProbe`, `runCalProbe`, `runSurfaceScan`) already calls `emit("setProbeVars", vars)` right before the MDI call — vars are always synced at execution time.

**Files:**
- Modify: `lcnc-webui/src/ProbePanel.vue:203-208`

- [ ] **Step 1: Add can.ready guard to saveParams()**

Change:
```typescript
function saveParams() {
  saveProbeDefaults({ ...params.value, autoZero: autoZero.value });
  // Sync to var file (and best-effort MDI) on every change
  const varMap = buildVarMap(autoZero.value ? 0 : 1);
  emit("setProbeVars", varMap);
}
```

To:
```typescript
function saveParams() {
  saveProbeDefaults({ ...params.value, autoZero: autoZero.value });
  // Sync to var file when machine is ready (execution functions also sync before each probe)
  if (can.value.ready) emit("setProbeVars", buildVarMap(autoZero.value ? 0 : 1));
}
```

- [ ] **Step 2: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 3: Commit**

```bash
git add lcnc-webui/src/ProbePanel.vue
git commit -m "fix: guard MDI sync in saveParams with can.ready

Match SettingsPanel's saveTsParams pattern — save to server
always, only push to var file when machine is ready. Probe
execution functions already sync vars before each probe call."
```

---

### Task 2: Relax INPUT_DEFS gates in machineControls.ts

**Files:**
- Modify: `lcnc-webui/src/machineControls.ts:113-170`

- [ ] **Step 1: Change 13 input gates to `always`**

Apply these changes to `INPUT_DEFS`:

| Key | From | To | Reason |
|-----|------|----|--------|
| `rpmInput` | `ready` | `always` | Pre-fill value; spindle/load buttons gate execution |
| `probeParam` | `ready` | `always` | Saved settings; MDI guarded in Task 1; execution functions sync before probe |
| `scanParam` | `ready` | `always` | Saved settings; same save function as probeParam |
| `toolSearch` | `idle` | `always` | UI list filtering only |
| `viewerSetting` | `idle` | `always` | 3D viewer display toggles |
| `viewerSettingNum` | `idle` | `always` | Workpiece size/offset display |
| `cameraSetting` | `idle` | `always` | Camera overlay sliders |
| `displaySetting` | `idle` | `always` | Display tab settings |
| `displaySettingNum` | `idle` | `always` | Display tab numeric settings |
| `macroEdit` | `idle` | `always` | Macro name/command form fields |
| `inputConfig` | `idle` | `always` | Gamepad/keyboard mapping |
| `viewerColor` | `idle` | `always` | 3D viewer color pickers |
| `cameraColor` | `idle` | `always` | Camera overlay color picker |

The resulting `INPUT_DEFS`:

```typescript
export const INPUT_DEFS = {
  // Motion parameters
  jogSpeed:        { gate: 'jog',      mono: true, align: 'right' },
  jogIncrement:    { gate: 'jog',      mono: true, align: 'right' },
  jogWheel:        { gate: 'jog' },
  jogAxis:         { gate: 'jog' },
  mdiText:         { gate: 'ready' },
  touchoff:        { gate: 'zero',     mono: true, align: 'right' },
  rpmInput:        { gate: 'always',   mono: true, align: 'right' },
  coolant:         { gate: 'ready' },

  // Override sliders
  feedOverride:    { gate: 'override' },
  spindleOverride: { gate: 'override' },
  rapidOverride:   { gate: 'override' },

  // Probe parameters
  probeParam:      { gate: 'always',   mono: true, align: 'right' },
  scanParam:       { gate: 'always',   mono: true, align: 'right' },

  // Toolsetter parameters (stays ready — prerequisite: Toolsetter.vue extraction)
  toolsetterParam: { gate: 'ready',    mono: true, align: 'right' },

  // Tool table editing
  toolEdit:        { gate: 'idle' },
  toolEditNum:     { gate: 'idle',     mono: true, align: 'right' },
  toolSearch:      { gate: 'always' },

  // 3D Viewer settings
  viewerSetting:   { gate: 'always' },
  viewerSettingNum:{ gate: 'always',   mono: true, align: 'right', size: 'sm' },
  cameraSetting:   { gate: 'always' },

  // Display settings
  displaySetting:  { gate: 'always' },
  displaySettingNum:{ gate: 'always',  mono: true, align: 'right' },

  // Macro editing
  macroEdit:       { gate: 'always' },

  // Keyboard/gamepad config
  inputConfig:     { gate: 'always' },

  // Program toggles
  optionalStop:    { gate: 'override' },
  blockDelete:     { gate: 'override' },

  // Color pickers (used by MachineColor)
  viewerColor:     { gate: 'always' },
  cameraColor:     { gate: 'always' },

  // Offset editing
  offsetEdit:      { gate: 'zero',     mono: true, align: 'right' },

  // UI-only (always enabled)
  search:          { gate: 'always' },
  filter:          { gate: 'always' },
} as const satisfies Record<string, InputDef>;
```

- [ ] **Step 2: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors — `'always'` is a valid `keyof Permissions`.

- [ ] **Step 3: Commit**

```bash
git add lcnc-webui/src/machineControls.ts
git commit -m "feat: relax 13 config/display input gates to always

RPM, probe/scan params, viewer/camera/display settings,
macro/input config, and tool search no longer require idle/ready.
Outer Gate (safety) still enforces armed+!estop via fieldset.
Toolsetter params excluded — requires Toolsetter.vue extraction."
```

---

### Task 3: Relax inner Gate wrappers in templates

Three template-level Gates override relaxed catalog gates via fieldset-disabled cascade.

**Files:**
- Modify: `lcnc-webui/src/GcodeReferenceDialog.vue:55,101`
- Modify: `lcnc-webui/src/SettingsPanel.vue:1093,1099`

- [ ] **Step 1: GcodeReferenceDialog — remove idle Gate from content**

The G-code reference is read-only. Search, filter, and sort should always work.

Change line 55:
```vue
<Gate gate="idle" class="stack-controls refContent">
```
To:
```vue
<div class="stack-controls refContent">
```

Change line 101:
```vue
</Gate>
```
To:
```vue
</div>
```

Remove the `Gate` import if no longer used elsewhere in the file.

- [ ] **Step 2: SettingsPanel — remove idle Gate from macro edit actions**

Macro editing is saved config, not machine commands. The edit/delete/move buttons already use `listAction` (gate: `always`). Only the dialog save/cancel wrapper and "Add Macro" button are still gated.

Change line 1093:
```vue
<Gate gate="idle" class="macroEditActions">
```
To:
```vue
<div class="macroEditActions">
```

Change the matching closing `</Gate>` to `</div>`.

- [ ] **Step 3: SettingsPanel — change Add Macro from `manage` to `inline`**

The `manage` button type is shared with tool table operations (must stay `idle`). Change the Add Macro button to `inline` (gate: `always`) since it's a config action.

Change line 1099:
```vue
<MachineBtn v-if="!editingMacro && macros.length < 20" type="manage" @click="addMacro">Add Macro</MachineBtn>
```
To:
```vue
<MachineBtn v-if="!editingMacro && macros.length < 20" type="inline" @click="addMacro">Add Macro</MachineBtn>
```

- [ ] **Step 4: Build verification**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 5: Commit**

```bash
git add lcnc-webui/src/GcodeReferenceDialog.vue lcnc-webui/src/SettingsPanel.vue
git commit -m "fix: relax inner Gate wrappers for config/reference controls

- GcodeReferenceDialog: remove idle Gate — reference is read-only
- SettingsPanel: remove idle Gate from macro edit dialog actions
- SettingsPanel: Add Macro button manage→inline (manage shared with tool table)"
```

---

## Excluded — requires separate work

| Control | Current Gate | Blocker |
|---------|-------------|---------|
| `toolsetterParam` | `ready` | `measureAuto()` in App.vue fires M600 without var sync. Requires Toolsetter.vue extraction so params + execution live in same component (see separate plan). |
| `manage` button type | `idle` | Shared between tool table ops (must stay `idle`) and macro add. Macro add handled by switching to `inline` in Task 3. |
| Reset dialog Gate (SettingsPanel:1397) | `idle` | Destructive config reset. Could be `always` but low priority — leave for now. |

## What stays gated (no changes)

| Control | Gate | Reason |
|---------|------|--------|
| Jog buttons/speed/increment | `jog` | Direct motion |
| MDI text input | `ready` | Sends G-code |
| Touchoff inputs + zero buttons | `zero` | Writes G5x offsets |
| Spindle FWD/REV/STOP | `ready` | Motion commands |
| Coolant flood/mist | `ready` | Motion commands |
| Tool Load/Unload/Measure | `ready` | Motion commands |
| Feed/Spindle/Rapid overrides | `override` | Live override commands |
| Override reset buttons | `override` | Sends override reset |
| Optional Stop / Block Delete | `override` | Program mode commands |
| Cycle Start/Step/Pause/Resume/Abort | respective | Program control |
| Probe grid (36 buttons) | `probe` | Probe motion |
| Surface scan Start button | `probe` | Probe motion |
| Comp toggle button | `ready` | Eoffset command |
| Tool table add/edit/delete | `idle` | Writes tool table file |
| Tool edit form fields | `idle` | Writes tool table |
| Offset panel clear/edit | `idle`/`zero` | Writes G5x offsets |
| File browser / upload | `idle` | File operations |
| Tool change mode / RFL toggle | `idle` | Machine behavior config |
| WCS selector buttons | `ready` | Sends G5x select |
| Home/Unhome buttons | `idle` | Homing motion |
| Macro execute buttons | `ready` | Sends MDI |
| Toolsetter params | `ready` | Pending Toolsetter.vue extraction |
