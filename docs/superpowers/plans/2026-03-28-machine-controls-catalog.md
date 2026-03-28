# Machine Controls Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace scattered wrapper Gates and per-button permission bindings with a catalog of predefined Machine* components that self-gate.

**Architecture:** A catalog file (`machineControls.ts`) defines button types and input gates. Nine Machine* components look up their permission from the catalog and self-disable. The outer Gate on mainArea stays as the enforcement layer. Wrapper Gates around button/input groups are removed — each control gates itself.

**Tech Stack:** Vue 3, TypeScript, existing permissions.ts + Gate.vue

**Spec:** `docs/superpowers/specs/2026-03-28-machine-controls-catalog-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `lcnc-webui/src/machineControls.ts` | Catalog: BUTTON_TYPES + INPUT_GATES |
| Create | `lcnc-webui/src/MachineBtn.vue` | Button with catalog-driven gate + variant + size |
| Create | `lcnc-webui/src/MachineInput.vue` | Text/number input with catalog-driven gate |
| Create | `lcnc-webui/src/MachineToggle.vue` | Toggle switch with catalog-driven gate |
| Create | `lcnc-webui/src/MachineSlider.vue` | Range slider with catalog-driven gate |
| Create | `lcnc-webui/src/MachineSelect.vue` | Dropdown with catalog-driven gate |
| Create | `lcnc-webui/src/MachineRadio.vue` | Radio button with catalog-driven gate |
| Create | `lcnc-webui/src/MachineColor.vue` | Color picker with catalog-driven gate |
| Modify | `lcnc-webui/src/JogButton.vue` | Read gate from catalog instead of prop |
| Modify | `lcnc-webui/src/GcodePanel.vue` | Convert control row + file ops + toggles |
| Modify | `lcnc-webui/src/ManualPanel.vue` | Convert MDI, WCS, goto buttons + inputs |
| Modify | `lcnc-webui/src/DroPanel.vue` | Convert home, zero buttons + touchoff inputs |
| Modify | `lcnc-webui/src/ProbePanel.vue` | Convert probe grid, params, toggles |
| Modify | `lcnc-webui/src/App.vue` | Convert sidebar popovers, tool dialog, macros |
| Modify | `lcnc-webui/src/SettingsPanel.vue` | Convert all sub-tab inputs, toggles, selects, radios, colors |
| Modify | `lcnc-webui/src/ToolTablePanel.vue` | Convert table buttons, edit dialog inputs |
| Modify | `lcnc-webui/src/Toolbar.vue` | Convert layer checkboxes, projection radios, workpiece inputs |
| Modify | `lcnc-webui/src/CameraViewer.vue` | Convert overlay controls |
| Modify | `lcnc-webui/src/JogPanel.vue` | Convert sliders, jog wheel, refactor JogButton usage |
| Modify | `lcnc-webui/src/JogHUD.vue` | Same as JogPanel |
| Modify | `lcnc-webui/src/SetupHUD.vue` | Convert home, zero, goto buttons + touchoff inputs |

---

## Important Context for All Tasks

- **Read the spec:** `docs/superpowers/specs/2026-03-28-machine-controls-catalog-design.md`
- **Three layers:** Outer Gate (fieldset enforcement) → Machine* component (visual gating) → `:disabled` (app state only)
- **MachineBtn** uses `type` prop (looks up gate + variant + size from BUTTON_TYPES)
- **All other Machine* components** use `gate` prop (looks up permission from INPUT_GATES)
- **`:disabled` on Machine* components** is for app state ONLY (loading, no file, probing, busy). Never for permissions.
- **Wrapper Gates being removed:** When converting a section, remove the `<Gate :allow="can.X">` wrapper if ALL children are now Machine* components that self-gate. Keep the wrapper Gate if it also contains non-Machine elements (plain text, divs) that need the fieldset for enforcement.
- **Outer Gate stays:** `<Gate :allow="permissions.safety" class="mainArea">` in App.vue is the enforcement layer. Never remove it.
- **Sidebar Gates stay:** `<Gate :allow="permissions.always">`, `<Gate :allow="permissions.safety">`, `<Gate :allow="permissions.abort">` in the sidebar are structural. Never remove them.
- **Dialog inner Gates stay:** `<Gate :allow="can.X" class="dialogActions">` wrapping dialog actions stay — they gate Cancel alongside action buttons.
- **Btn.vue stays:** For non-machine UI buttons (dialog close ×, tab switch, popover dismiss, add panel +). These don't use MachineBtn.
- **Build verification:** Run `cd lcnc-webui && npm run build` after every task. Zero errors required.
- **Line numbers are approximate.** Always read the file before editing.

---

### Task 1: Create machineControls.ts catalog

**Files:**
- Create: `lcnc-webui/src/machineControls.ts`

- [ ] **Step 1: Create the catalog file**

Copy the `BUTTON_TYPES` and `INPUT_GATES` definitions from the spec. Include all types, interfaces, and type exports.

- [ ] **Step 2: Verify build**

Run: `cd lcnc-webui && npm run build`
Expected: PASS (file created but not imported yet)

- [ ] **Step 3: Commit**

```bash
git add lcnc-webui/src/machineControls.ts
git commit -m "feat: add machine controls catalog (BUTTON_TYPES + INPUT_GATES)"
```

---

### Task 2: Create all Machine* components

**Files:**
- Create: `lcnc-webui/src/MachineBtn.vue`
- Create: `lcnc-webui/src/MachineInput.vue`
- Create: `lcnc-webui/src/MachineToggle.vue`
- Create: `lcnc-webui/src/MachineSlider.vue`
- Create: `lcnc-webui/src/MachineSelect.vue`
- Create: `lcnc-webui/src/MachineRadio.vue`
- Create: `lcnc-webui/src/MachineColor.vue`

- [ ] **Step 1: Create MachineBtn.vue**

Per spec. Props: `type: ButtonType`, `disabled?: boolean`, `active?: boolean`, `selected?: boolean`, `muted?: boolean`, `mono?: boolean`, `block?: boolean`, `flashing?: boolean`, `warning?: boolean`. Passes variant/size from catalog, disabled from gate + prop. Uses `<Btn>` internally. Add `defineOptions({ inheritAttrs: true })` so `@click`, `class`, `title` etc pass through.

- [ ] **Step 2: Create MachineInput.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`. Uses `v-bind="$attrs"` for type, min, max, step, v-model pass-through. Add `defineOptions({ inheritAttrs: false })` since we manually bind attrs.

- [ ] **Step 3: Create MachineToggle.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`, `label?: string`. Uses `defineModel<boolean>()`. Renders `<label class="toggleRow"><input type="checkbox" class="toggle" ...>`.

- [ ] **Step 4: Create MachineSlider.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`, `min?: number`, `max?: number`, `step?: number`. Uses `defineModel<number>()`.

- [ ] **Step 5: Create MachineSelect.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`. Uses `defineModel<string | number>()`. Default slot for `<option>` elements.

- [ ] **Step 6: Create MachineRadio.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`, `name: string`, `value: string | number`. Uses `defineModel<string | number>()`.

- [ ] **Step 7: Create MachineColor.vue**

Per spec. Props: `gate: InputType`, `disabled?: boolean`. Uses `defineModel<string>()`.

- [ ] **Step 8: Verify build**

Run: `cd lcnc-webui && npm run build`
Expected: PASS (components created but not used yet)

- [ ] **Step 9: Commit**

```bash
git add lcnc-webui/src/Machine*.vue
git commit -m "feat: add Machine* catalog components (Btn, Input, Toggle, Slider, Select, Radio, Color)"
```

---

### Task 3: Refactor JogButton to use catalog

**Files:**
- Modify: `lcnc-webui/src/JogButton.vue`

- [ ] **Step 1: Read JogButton.vue**

Understand the current `disabled` prop and `isDisabled` computed.

- [ ] **Step 2: Import catalog and permissions**

Add `import { INPUT_GATES } from './machineControls'` and `import { usePermissions } from './permissions'`.

- [ ] **Step 3: Replace prop-based gating with catalog lookup**

Keep the `disabled` prop for app-state conditions (velocity validity). Add `const can = usePermissions()`. Change `isDisabled` to: `!can.value[INPUT_GATES.jogAxis] || !hasVelocity || props.disabled`.

- [ ] **Step 4: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 5: Commit**

```bash
git add lcnc-webui/src/JogButton.vue
git commit -m "refactor: JogButton reads gate from catalog instead of prop"
```

---

### Task 4: Convert GcodePanel

**Files:**
- Modify: `lcnc-webui/src/GcodePanel.vue`

This is the most visible improvement — the control row with nested Gates.

- [ ] **Step 1: Read GcodePanel.vue control row (~line 528-555)**

Identify the 4 wrapper Gates (ready, pause/resume, abort, override) and all buttons/toggles inside.

- [ ] **Step 2: Replace control row buttons with MachineBtn**

Remove the 4 wrapper Gates. Replace each `<Btn>` with `<MachineBtn type="...">`. Keep `:disabled` for app state only (activeFile, editing). The Pause/Resume dual button needs special handling — use `type="pause"` or `type="resume"` conditionally, or keep both and v-if.

- [ ] **Step 3: Replace M01/BD toggles with MachineToggle**

Replace `<label><input type="checkbox" class="toggle" ...>` with `<MachineToggle gate="optionalStop" ...>` and `<MachineToggle gate="blockDelete" ...>`.

- [ ] **Step 4: Replace file operation buttons**

Read the file ops area (~line 428-445). Replace wrapper Gate + Btn with MachineBtn type="fileOp" / type="fileSave".

- [ ] **Step 5: Replace edit area buttons**

Read edit area (~line 599-620). Replace wrapper Gate + Btn with MachineBtn type="fileSave" (Save) and type="fileOp" (Discard). Keep `:disabled="saving"`.

- [ ] **Step 6: Remove Gate import if no longer used**

Check if GcodePanel still uses any `<Gate>` wrappers (file browser Gate, dialog actions Gate). If all Gates are removed, remove the import. If some remain, keep it.

- [ ] **Step 7: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 8: Commit**

```bash
git add lcnc-webui/src/GcodePanel.vue
git commit -m "refactor: convert GcodePanel to Machine* catalog components"
```

---

### Task 5: Convert ManualPanel

**Files:**
- Modify: `lcnc-webui/src/ManualPanel.vue`

- [ ] **Step 1: Read ManualPanel.vue**

Identify: WCS selector buttons (~line 149), goto buttons (~line 179-183), MDI input + send button (~line 211-225), clear history button (~line 229).

- [ ] **Step 2: Replace WCS buttons with MachineBtn**

Remove wrapper Gate. Replace each `<Btn>` with `<MachineBtn type="wcs" :selected="g === g5xLabel" ...>`.

- [ ] **Step 3: Replace goto buttons with MachineBtn**

Remove wrapper Gate. Replace with `<MachineBtn type="goTo" ...>`.

- [ ] **Step 4: Replace MDI input + send button**

Remove wrapper Gate. Replace `<input>` with `<MachineInput gate="mdiText" ...>`. Replace send `<Btn>` with `<MachineBtn type="mdi" ...>`. Keep `:disabled="history.length === 0"` on clear history (app state).

- [ ] **Step 5: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 6: Commit**

```bash
git add lcnc-webui/src/ManualPanel.vue
git commit -m "refactor: convert ManualPanel to Machine* catalog components"
```

---

### Task 6: Convert DroPanel

**Files:**
- Modify: `lcnc-webui/src/DroPanel.vue`

- [ ] **Step 1: Read DroPanel.vue**

Identify: home/unhome buttons (~line 81-86), touchoff inputs + set buttons (~line 66-71), wrapper Gates (can.idle, can.zero).

- [ ] **Step 2: Replace home/unhome buttons**

Remove wrapper Gate. Replace with `<MachineBtn type="home" ...>` and `<MachineBtn type="unhome" ...>`.

- [ ] **Step 3: Replace touchoff inputs + set buttons**

Remove wrapper Gate. Replace `<input type="number">` with `<MachineInput gate="touchoff" ...>`. Replace set buttons with `<MachineBtn type="zero" ...>`.

- [ ] **Step 4: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 5: Commit**

```bash
git add lcnc-webui/src/DroPanel.vue
git commit -m "refactor: convert DroPanel to Machine* catalog components"
```

---

### Task 7: Convert ProbePanel

**Files:**
- Modify: `lcnc-webui/src/ProbePanel.vue`

Largest component — 13 Gate wrappers, ~40 probe buttons, ~20 parameter inputs, 2 toggles.

- [ ] **Step 1: Read ProbePanel.vue**

Map all wrapper Gates, buttons, inputs, and toggles.

- [ ] **Step 2: Replace WCS selector buttons**

Same as ManualPanel — `<MachineBtn type="wcs" ...>`.

- [ ] **Step 3: Replace probe grid buttons**

Remove `<Gate :allow="can.probe">` wrappers. Replace each probe `<Btn>` with `<MachineBtn type="probe" :disabled="probing" ...>`.

- [ ] **Step 4: Replace parameter inputs**

Remove `<Gate :allow="can.ready">` wrappers around param inputs. Replace with `<MachineInput gate="probeParam" ...>` for probe params, `<MachineInput gate="scanParam" ...>` for surface scan params.

- [ ] **Step 5: Replace toggles**

Replace Auto Zero and Set Rotation toggles with `<MachineToggle gate="probeParam" ...>`.

- [ ] **Step 6: Replace control bar buttons**

Abort button → `<MachineBtn type="abort" ...>`. Other action buttons → appropriate MachineBtn types.

- [ ] **Step 7: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 8: Commit**

```bash
git add lcnc-webui/src/ProbePanel.vue
git commit -m "refactor: convert ProbePanel to Machine* catalog components"
```

---

### Task 8: Convert App.vue sidebar popovers + tool dialog

**Files:**
- Modify: `lcnc-webui/src/App.vue`

The sidebar has spindle, coolant, overrides, tool, and macro popovers with inner Gates.

- [ ] **Step 1: Read App.vue sidebar (~line 1336-1710)**

Map all inner Gates, buttons, inputs, sliders in popovers.

- [ ] **Step 2: Convert spindle popover buttons + RPM input**

Remove inner `<Gate :allow="permissions.ready">`. Replace buttons with `<MachineBtn type="spindleFwd/spindleRev/spindleStop" ...>`. Replace RPM input with `<MachineInput gate="rpmInput" ...>`. Keep `:disabled="!isSpinning"` on stop (app state).

- [ ] **Step 3: Convert coolant popover buttons**

Replace with `<MachineBtn type="flood/mist" :active="floodOn/mistOn" ...>`.

- [ ] **Step 4: Convert override sliders + presets**

Replace sliders with `<MachineSlider gate="feedOverride/spindleOverride/rapidOverride" ...>`. Replace preset buttons with `<MachineBtn type="overridePreset" ...>`. Replace reset button with `<MachineBtn type="overrideReset" ...>`. Keep `:disabled="!feedOvrEnabled"` etc (app state from HAL).

- [ ] **Step 5: Convert tool dialog buttons + input**

Replace tool # input with `<MachineInput gate="rpmInput" ...>` — wait, tool number should be `toolEdit` or a new gate. Check catalog and use appropriate gate. Replace Measure/Load/Unload/Abort buttons with MachineBtn. Keep `:disabled="!!st.probing"` (app state).

- [ ] **Step 6: Convert work offsets table buttons**

Replace WCS clear buttons and offset input with appropriate Machine* components.

- [ ] **Step 7: Convert macro execution buttons**

Replace with `<MachineBtn type="macro" ...>`.

- [ ] **Step 8: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 9: Commit**

```bash
git add lcnc-webui/src/App.vue
git commit -m "refactor: convert App.vue sidebar to Machine* catalog components"
```

---

### Task 9: Convert SettingsPanel

**Files:**
- Modify: `lcnc-webui/src/SettingsPanel.vue`

Most inputs in the codebase. 50+ interactive elements across 10 sub-tabs.

- [ ] **Step 1: Read SettingsPanel.vue, map all sub-tabs**

Identify every Gate wrapper, input, toggle, select, radio, color, slider by sub-tab.

- [ ] **Step 2: Convert 3D Viewer sub-tab**

Replace color pickers with `<MachineColor gate="viewerSetting" ...>`. Replace opacity sliders with `<MachineSlider gate="viewerSetting" ...>`. Replace edge toggle with `<MachineToggle gate="viewerSetting" ...>`. Remove wrapper Gates.

- [ ] **Step 3: Convert Machine sub-tab**

Replace radio buttons with `<MachineRadio gate="displaySetting" ...>`. Replace text inputs with `<MachineInput gate="displaySetting" ...>`. Replace run-from-line toggle with `<MachineToggle gate="displaySetting" ...>`.

- [ ] **Step 4: Convert Toolsetter sub-tab**

Replace all coordinate/feed/distance inputs with `<MachineInput gate="toolsetterParam" ...>`. Replace option toggles with `<MachineToggle gate="toolsetterParam" ...>`. Replace radio buttons with `<MachineRadio gate="toolsetterParam" ...>`. Remove wrapper Gates.

- [ ] **Step 5: Convert Display sub-tab**

Replace theme radios with `<MachineRadio gate="displaySetting" ...>`. Replace fullscreen toggle with `<MachineToggle gate="displaySetting" ...>`.

- [ ] **Step 6: Convert Camera sub-tab**

Replace overlay toggles with `<MachineToggle gate="cameraSetting" ...>`. Replace number inputs with `<MachineInput gate="cameraSetting" ...>`. Replace opacity slider with `<MachineSlider gate="cameraSetting" ...>`. Replace color picker with `<MachineColor gate="cameraSetting" ...>`.

- [ ] **Step 7: Convert Macros sub-tab**

Replace macro name/command inputs with `<MachineInput gate="macroEdit" ...>`. Replace param inputs with `<MachineInput gate="macroEdit" ...>`. Replace management buttons (edit, delete, move, save, add) with `<MachineBtn type="manage" ...>`.

- [ ] **Step 8: Convert Gamepad sub-tab**

Replace enable/invert toggles with `<MachineToggle gate="inputConfig" ...>`. Replace button mapping selects with `<MachineSelect gate="inputConfig" ...>`. Replace dead zone slider with `<MachineSlider gate="inputConfig" ...>`.

- [ ] **Step 9: Convert Keyboard sub-tab**

Replace enable/jog toggles with `<MachineToggle gate="inputConfig" ...>`. Replace reset button with `<MachineBtn type="reset" ...>`.

- [ ] **Step 10: Remove emptied wrapper Gates**

After converting all sub-tabs, remove any `<Gate>` wrappers that no longer contain un-converted elements. Keep Gate import if dialog Gates remain.

- [ ] **Step 11: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 12: Commit**

```bash
git add lcnc-webui/src/SettingsPanel.vue
git commit -m "refactor: convert SettingsPanel to Machine* catalog components"
```

---

### Task 10: Convert ToolTablePanel

**Files:**
- Modify: `lcnc-webui/src/ToolTablePanel.vue`

- [ ] **Step 1: Read ToolTablePanel.vue**

Identify: header buttons (Add, Import, Refresh), table row buttons (Load, Edit, Delete), search input, edit dialog inputs, STL upload.

- [ ] **Step 2: Convert header buttons**

Remove wrapper Gate. Replace with `<MachineBtn type="manage" ...>`. Keep `:disabled="loading"` on Refresh.

- [ ] **Step 3: Convert table row buttons**

Replace Load with `<MachineBtn type="toolLoad" ...>`. Replace Edit/Delete with `<MachineBtn type="manage" ...>`.

- [ ] **Step 4: Convert search input**

Replace with `<MachineInput gate="toolSearch" ...>`.

- [ ] **Step 5: Convert edit dialog inputs**

Replace all tool form inputs with `<MachineInput gate="toolEdit" ...>`. Replace type select with `<MachineSelect gate="toolEdit" ...>`.

- [ ] **Step 6: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 7: Commit**

```bash
git add lcnc-webui/src/ToolTablePanel.vue
git commit -m "refactor: convert ToolTablePanel to Machine* catalog components"
```

---

### Task 11: Convert Toolbar

**Files:**
- Modify: `lcnc-webui/src/Toolbar.vue`

- [ ] **Step 1: Read Toolbar.vue**

Identify: projection radios, layer checkboxes, path-on-top toggle, tracking radios, workpiece size/offset inputs.

- [ ] **Step 2: Convert all controls**

Replace radios with `<MachineRadio gate="viewerSetting" ...>`. Replace checkboxes with `<MachineToggle gate="viewerSetting" ...>` (or plain checkbox with gate). Replace number inputs with `<MachineInput gate="viewerSetting" ...>`. Remove wrapper Gate.

- [ ] **Step 3: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/Toolbar.vue
git commit -m "refactor: convert Toolbar to Machine* catalog components"
```

---

### Task 12: Convert CameraViewer

**Files:**
- Modify: `lcnc-webui/src/CameraViewer.vue`

- [ ] **Step 1: Read CameraViewer.vue overlay controls**

Identify: 3 toggle buttons (crosshair, circle, grid), radius slider, spacing slider, color picker.

- [ ] **Step 2: Convert all controls**

Replace toggle Btn components with `<MachineBtn type="manage" ...>` with `:active` state. Replace sliders with `<MachineSlider gate="cameraSetting" ...>`. Replace color picker with `<MachineColor gate="cameraSetting" ...>`. Remove wrapper Gate.

- [ ] **Step 3: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/CameraViewer.vue
git commit -m "refactor: convert CameraViewer to Machine* catalog components"
```

---

### Task 13: Convert JogPanel + JogHUD

**Files:**
- Modify: `lcnc-webui/src/JogPanel.vue`
- Modify: `lcnc-webui/src/JogHUD.vue`

- [ ] **Step 1: Read JogPanel.vue**

Identify: jog speed sliders (linear + rotary), increment buttons, mode toggle, jog wheel SVG handler, JogButton instances, wrapper Gate.

- [ ] **Step 2: Convert JogPanel sliders**

Replace speed sliders with `<MachineSlider gate="jogSpeed" ...>`. Remove wrapper Gate around sliders.

- [ ] **Step 3: Convert JogPanel increment buttons + mode toggle**

Replace increment `<Btn>` with `<MachineBtn type="manage" ...>` or a new jogIncrement button type if needed. Replace mode toggle.

- [ ] **Step 4: Refactor JogPanel wheel handler**

Add catalog check at the start of `startJog()`: `if (!can.value[INPUT_GATES.jogWheel]) return;`. Add disabled class to SVG sectors.

- [ ] **Step 5: Update JogButton usage**

JogButton now reads the gate from catalog (Task 3). Remove `:disabled="!can.jog"` from all JogButton instances — they self-gate.

- [ ] **Step 6: Remove wrapper Gate if empty**

If all children are Machine* or self-gating JogButton, remove the `<Gate :allow="can.jog">` wrapper.

- [ ] **Step 7: Repeat for JogHUD**

Same conversions as JogPanel — sliders, wheel, JogButton instances.

- [ ] **Step 8: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 9: Commit**

```bash
git add lcnc-webui/src/JogPanel.vue lcnc-webui/src/JogHUD.vue
git commit -m "refactor: convert JogPanel and JogHUD to Machine* catalog components"
```

---

### Task 14: Convert SetupHUD

**Files:**
- Modify: `lcnc-webui/src/SetupHUD.vue`

- [ ] **Step 1: Read SetupHUD.vue**

Identify: home/unhome buttons, touchoff inputs + set buttons, goto buttons.

- [ ] **Step 2: Convert all controls**

Replace home/unhome with `<MachineBtn type="home/unhome" ...>`. Replace touchoff inputs with `<MachineInput gate="touchoff" ...>`. Replace set buttons with `<MachineBtn type="zero" ...>`. Replace goto buttons with `<MachineBtn type="goTo" ...>`. Remove wrapper Gates.

- [ ] **Step 3: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/SetupHUD.vue
git commit -m "refactor: convert SetupHUD to Machine* catalog components"
```

---

### Task 15: Cleanup — remove emptied Gates, update docs

**Files:**
- Modify: `lcnc-webui/src/*.vue` (any remaining wrapper Gates)
- Modify: `CLAUDE.md`

- [ ] **Step 1: Grep for remaining wrapper Gates**

Run: `grep -rn '<Gate ' lcnc-webui/src/ --include="*.vue"`. Every remaining Gate should be one of:
- Outer Gate on mainArea (`permissions.safety`)
- Sidebar Gates (`permissions.always`, `permissions.safety`, `permissions.abort`)
- Dialog action Gates (`dialogActions`)

Any other `<Gate>` is a leftover wrapper that should be converted or removed.

- [ ] **Step 2: Remove leftover wrapper Gates**

For each leftover, check if all children are Machine* components. If yes, remove the Gate and close tag. If some children are non-Machine elements, keep the Gate.

- [ ] **Step 3: Grep for redundant `:disabled="!can.`**

Run: `grep -rn ':disabled="!can\.' lcnc-webui/src/ --include="*.vue"`. Every remaining binding should be:
- App-state + permission combo where the Machine* component doesn't cover it
- JogButton internal guard (if any remains)

Remove any that duplicate the Machine* component's gate.

- [ ] **Step 4: Update CLAUDE.md**

Add Machine Controls Catalog section:
- Machine* components are the standard for all machine-action controls
- Btn.vue is for non-machine UI buttons only
- Gate.vue is for structural gates (outer, sidebar, dialog actions) only
- Permission defined once in `machineControls.ts`, not per-element
- `:disabled` is app state only, never permissions

- [ ] **Step 5: Verify build**

Run: `cd lcnc-webui && npm run build`

- [ ] **Step 6: Commit**

```bash
git add -A lcnc-webui/src/ CLAUDE.md
git commit -m "refactor: cleanup — remove emptied Gates, update docs for Machine* catalog"
```
