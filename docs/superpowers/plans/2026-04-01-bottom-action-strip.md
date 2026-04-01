# Bottom Action Strip — Layout Redesign

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 150px sidebar + popover layout with a full-width bottom action strip, giving all operator controls persistent visibility while maximizing content area for the 3D viewer, program, and probing tabs.

**Architecture:** The app layout changes from `[sidebar | main]` (horizontal flex) to `[header] [content] [strip]` (vertical flex). The sidebar is eliminated. Safety controls, mode-exclusive actions (jog/MDI/program), and always-accessible controls (overrides, spindle, coolant, tool, macros) move to a bottom strip. Settings, messages, and G-code reference move to the header. Content tabs (3D viewer, program, probing, tool table) get the full width. Camera becomes a PiP overlay inside the 3D viewer.

**Tech Stack:** Vue 3, TypeScript, CSS custom properties (existing design token system)

**Branch:** `feature/bottom-action-strip`

---

## Design Specification

### New Layout (Landscape)

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
│ [LinuxCNC WebUI]  [status pills...]  [msgs][gref][set][⛶]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CONTENT TABS: ◉3D Viewer  ◉Program  ◉Probing  ◉Tool Table │
│                                                              │
│  (full width × all remaining height)                         │
│  Camera = PiP overlay inside 3D viewer                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ BOTTOM ACTION STRIP                                          │
│ ┌────────┬──────────────────────┬──────────────────────────┐ │
│ │ SAFETY │ MODE: [Jog][MDI][Prg]│ ALWAYS-ON CONTROLS       │ │
│ │        │                      │                          │ │
│ │ 🔒 Arm │  ┌── Jog ─────────┐ │ Overrides: F━━ S━━ R━━  │ │
│ │ ⚠ EStop│  │ XY wheel + Z   │ │ Spindle: FWD STOP REV   │ │
│ │ ⏻ Mach │  │ speed + step   │ │          RPM: [____]     │ │
│ │        │  │ + touchoff     │ │ Coolant: [Flood] [Mist]  │ │
│ │ Status │  └────────────────┘ │ Tool: T# [Meas][Load]    │ │
│ │ pills  │  ┌── MDI ─────────┐ │ Macros: [M1][M2][M3]... │ │
│ │        │  │ input + history │ │                          │ │
│ │        │  └────────────────┘ │                          │ │
│ │        │  ┌── Program ─────┐ │                          │ │
│ │        │  │ Start Pause Stp│ │                          │ │
│ │        │  │ file + progress│ │                          │ │
│ │        │  └────────────────┘ │                          │ │
│ └────────┴──────────────────────┴──────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### DOM & Gate Structure

```
<div class="app">                              ← vertical flex
  <header class="hdr">                         ← no gate (status-only + always buttons)
    [title] [pills] [msgs btn] [gref btn] [settings btn] [fullscreen] [shutdown]
  </header>

  <Gate gate="safety" class="content">         ← outer gate (armed + !estop)
    <TabPanel :tabs="contentTabs">
      #viewer → ThreeViewer (+ camera PiP)
      #gcode  → GcodePanel
      #probe  → ProbePanel
      #tools  → ToolTablePanel (inline, not dialog)
    </TabPanel>
  </Gate>

  <div class="strip">                          ← bottom strip, NOT inside outer gate
    ┌─ SAFETY COLUMN ─────────────────────────┐
    │ <Gate gate="always">                     │  ← arm, estop always work
    │   Arm/Disarm, E-Stop                     │
    │ </Gate>                                  │
    │ <Gate gate="safety">                     │  ← machine on needs armed+!estop
    │   Machine On/Off                         │
    │ </Gate>                                  │
    │ Status indicators (no gate needed)       │
    └──────────────────────────────────────────┘

    ┌─ MODE COLUMN ───────────────────────────┐
    │ <Gate gate="safety">                     │  ← entire mode area
    │   [Jog] [MDI] [Program] tab buttons      │
    │   v-show mode content:                   │
    │     Jog: <Gate gate="jog"> jog controls  │
    │     MDI: <Gate gate="ready"> mdi input   │
    │     Prg: mixed gates (start=ready,       │
    │           pause=pause, resume=resume,     │
    │           abort=abort)                    │
    │ </Gate>                                  │
    └──────────────────────────────────────────┘

    ┌─ CONTROLS COLUMN ──────────────────────┐
    │ <Gate gate="safety">                    │  ← wraps all controls
    │   Overrides: <Gate gate="override">     │
    │   Spindle:   <Gate gate="ready">        │
    │   Coolant:   <Gate gate="ready">        │
    │   Tool:      <Gate gate="ready">        │
    │   Macros:    <Gate gate="ready">        │
    │ </Gate>                                 │
    └─────────────────────────────────────────┘
  </div>
</div>
```

### Z-Index Stack (unchanged values)

| Z-Index | Element | Notes |
|---------|---------|-------|
| 1010 | Safety confirmation dialogs | Shutdown confirm, comp toggle |
| 1000 | Dialogs, settings | Position: fixed overlays |
| auto | Strip | Normal flow, bottom of flex |
| auto | Content tabs | Normal flow, flex: 1 |
| auto | Header | Normal flow |

The sidebar z-index (1020) is **removed** — no sidebar exists. Dialog `padding-left: var(--sidebar-total)` is **removed** — dialogs now center over full viewport.

### Gate Rules

- **E-Stop must ALWAYS be accessible** — even when disarmed, even when machine is off. E-Stop and Arm are in `<Gate gate="always">` which is outside the outer Gate. The strip itself is NOT inside the outer Gate.
- **Machine On/Off** needs `gate="safety"` (armed + !estop).
- **Mode tabs** (Jog/MDI/Program labels) are `gate="always"` tab buttons — you can see them always but the mode content has its own gates.
- **Override sliders** use `gate="override"` (base + !busy) — adjustable during program run.
- **Spindle/coolant/tool/macros** use `gate="ready"` — only when idle + homed.
- **Content area** (3D viewer, program, probing) is wrapped in `<Gate gate="safety">` — the outer gate stays.

### Content Tab Changes

| Tab | Current | New |
|-----|---------|-----|
| 3D Viewer | Panel tab | Content tab (full width) |
| Manual Control | Panel tab (DRO+Jog+MDI sub-tabs) | **Removed** — DRO is in HUD, jog/MDI move to strip |
| Program | Panel tab | Content tab |
| Probing | Panel tab | Content tab |
| Camera | Panel tab | **PiP overlay** inside 3D viewer |
| Tool Table | Dialog (opened from sidebar) | Content tab (inline, not dialog) |

### What Moves Where

| Element | From | To |
|---------|------|----|
| Arm/Disarm | Sidebar card 1 | Strip → safety column |
| E-Stop | Sidebar card 1 | Strip → safety column |
| Machine On/Off | Sidebar card 1 | Strip → safety column |
| Status indicators | Sidebar card 2 | Strip → safety column (compact) |
| Spindle controls | Sidebar popover | Strip → controls column (inline) |
| Coolant toggles | Sidebar popover | Strip → controls column (inline) |
| Override sliders | Sidebar popover | Strip → controls column (inline) |
| Tool controls | Sidebar popover → dialog | Strip → controls column (compact) |
| Macros | Sidebar popover | Strip → controls column (row) |
| Offsets table | Sidebar popover | **Content tab or dialog** (too large for strip) |
| Messages | Sidebar popover | Header button → popover/dialog |
| G-code Reference | Sidebar → dialog | Header button → dialog |
| Settings | Sidebar → dialog | Header button → dialog |
| DRO | ManualPanel → DroPanel | **Already in 3D viewer HUD** (no change needed) |
| Jog controls | ManualPanel → JogPanel | Strip → mode column → Jog view |
| MDI input | ManualPanel | Strip → mode column → MDI view |
| Program controls | Header (start/pause/stop) | Strip → mode column → Program view |
| Touchoff | DroPanel | Strip → mode column → Jog view (compact) |
| WCS selector | ManualPanel header | Strip → mode column → Jog view |

### New Catalog Entries Needed

**BUTTON_TYPES additions:**
```ts
stripMode:     { gate: 'always', variant: 'default', size: 'sm', muted: true }  // Jog/MDI/Prg tab
spindleFwd:    { gate: 'ready',  variant: 'default', size: 'sm' }
spindleRev:    { gate: 'ready',  variant: 'default', size: 'sm' }
spindleStop:   { gate: 'ready',  variant: 'default', size: 'sm' }
```

**INPUT_DEFS additions:**
```ts
spindleRpm:    { gate: 'ready',  mono: true, align: 'right' }
```

(Check if these already exist before adding — some may already be defined for sidebar popovers.)

### Files Changed

| File | Action | Description |
|------|--------|-------------|
| `App.vue` | **Major rewrite** | Remove sidebar, add strip, restructure layout |
| `style.css` | **Modify** | Remove `--sidebar-w`, `--sidebar-total`, add `.strip` layout classes, update `.dialogOverlay` |
| `BottomStrip.vue` | **Create** | New component: safety + mode + controls columns |
| `ModeStrip.vue` | **Create** | Mode-exclusive area: Jog/MDI/Program sub-views |
| `ControlsStrip.vue` | **Create** | Always-on controls: overrides, spindle, coolant, tool, macros |
| `SafetyStrip.vue` | **Create** | Arm, E-Stop, Machine On, status indicators |
| `machineControls.ts` | **Modify** | Add new catalog entries if needed |
| `ManualPanel.vue` | **Delete** | Replaced by strip mode views |
| `TabPanel.vue` | **Modify** | Remove closable/multi-panel support (single content area) |
| `ThreeViewer.vue` | **Modify** | Camera PiP overlay |
| `CameraViewer.vue` | **Modify** | PiP mode (small, draggable?) |
| `main.ts` | **Modify** | Remove multi-panel bootstrap |
| `defaults.ts` | **Modify** | Remove panel layout settings, add strip settings |

### Risks & Open Questions

1. **Strip height** — The jog wheel is 200px in JogPanel, 170px in JogHUD. The strip needs enough height for the jog wheel but shouldn't consume more than ~40% of viewport. A compact jog layout (like JogHUD's 170px) is appropriate. The strip height is driven by the tallest mode view.

2. **Touchoff in strip** — Currently DroPanel is a 4-column grid. In the strip's jog mode, touchoff needs to be compact. Options: (a) inline with jog area, (b) separate "Setup" sub-tab within mode strip, (c) keep in 3D viewer's existing SetupHUD.

3. **Tool table as content tab** — Currently a dialog. Moving inline means it needs its own tab. The existing ToolTablePanel component should work with minimal changes.

4. **Offsets** — Too large for the strip. Options: (a) content tab, (b) dialog opened from header or strip, (c) keep as popover from strip. Recommend: dialog opened from a strip button, since offsets are edited occasionally, not continuously.

5. **Multi-panel removal** — Users currently can have 2+ panels. This plan removes that capability. The 3D viewer HUD + strip provide the "see everything at once" experience instead.

---

## Task Breakdown

### Task 1: Strip Layout Shell — App.vue Restructure

**Files:**
- Modify: `lcnc-webui/src/App.vue`
- Modify: `lcnc-webui/src/style.css`

This task replaces the sidebar+main flex layout with header+content+strip vertical flex. The strip is empty initially — just a placeholder div. The sidebar content is commented out but not yet moved.

- [ ] **Step 1: Update style.css — remove sidebar vars, add strip layout**

Remove `--sidebar-w` and `--sidebar-total` CSS custom properties. Add `.strip` layout class. Update `.dialogOverlay` to remove `padding-left: var(--sidebar-total)`.

Add to `style.css`:
```css
/* ---- Bottom Action Strip ---- */
.strip {
  display: flex;
  gap: var(--gap-section);
  padding: var(--gap-controls);
  border-top: 1px solid var(--border);
  background: var(--panel);
  flex-shrink: 0;
  overflow-x: auto;
  overflow-y: hidden;
}
```

- [ ] **Step 2: Update App.vue template — vertical flex layout**

Change `.wrap` from `flex-direction: row` (sidebar | main) to `flex-direction: column` (header | content | strip). Remove the entire `<div class="sidebar">` block (comment it out for reference). Replace multi-panel `.panels` container with a single content area. Add empty `<div class="strip">Strip placeholder</div>`.

The outer `<Gate gate="safety">` wraps the content area (not the strip — strip manages its own gates).

- [ ] **Step 3: Update App.vue CSS — remove sidebar styles**

Remove all sidebar-related CSS: `.sidebar`, `.card`, `.controlBtns`, `.controlGroup`, `.controlBtn`, `.controlIcon`, all `.popover` positioning styles (`.spindlePopover`, `.coolantPopover`, `.overridesPopover`, `.offsetsPopover`, `.macroPopover`, `.messagesPopover`), `.machineStatus`, `.statusRow`, `.safetyBtn`, `.safetyIcon`, `.vsep`.

Update `.wrap` to `flex-direction: column`.

- [ ] **Step 4: Update dialogOverlay — remove sidebar offset**

In `style.css`, remove `padding-left: var(--sidebar-total, 0px)` from `.dialogOverlay`. Dialogs now center over the full viewport.

- [ ] **Step 5: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero TypeScript errors. The app renders with header + empty content + empty strip.

- [ ] **Step 6: Commit**

```bash
git add lcnc-webui/src/App.vue lcnc-webui/src/style.css
git commit -m "refactor: replace sidebar+main layout with header+content+strip vertical flex"
```

---

### Task 2: SafetyStrip Component

**Files:**
- Create: `lcnc-webui/src/SafetyStrip.vue`
- Modify: `lcnc-webui/src/App.vue` (import + place in strip)

Extract safety controls (Arm, E-Stop, Machine On) and compact status indicators into a self-contained strip column. This component lives OUTSIDE the outer Gate — E-Stop is always accessible.

- [ ] **Step 1: Create SafetyStrip.vue**

```vue
<script setup lang="ts">
import { computed } from "vue";
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import { Lock, LockOpen, TriangleAlert, Power } from "lucide-vue-next";

const props = defineProps<{
  armed: boolean;
  isEstop: boolean;
  isEnabled: boolean;
  isHomed: boolean;
  taskState: number;
}>();

const emit = defineEmits<{
  (e: "arm"): void;
  (e: "disarm"): void;
  (e: "estop"): void;
  (e: "estopReset"): void;
  (e: "machineOn"): void;
  (e: "machineOff"): void;
}>();

const estopActive = computed(() => props.taskState === 1);
</script>

<template>
  <div class="safetyStrip">
    <Gate gate="always">
      <div class="safetyBtns">
        <MachineBtn
          type="arm"
          :active="armed"
          @click="armed ? emit('disarm') : emit('arm')"
        >
          <component :is="armed ? LockOpen : Lock" class="stripIcon" />
          <span class="stripLabel">{{ armed ? 'Armed' : 'Disarmed' }}</span>
        </MachineBtn>

        <MachineBtn
          type="estop"
          :flashing="estopActive"
          @click="estopActive ? emit('estopReset') : emit('estop')"
        >
          <TriangleAlert class="stripIcon" />
          <span class="stripLabel">E-Stop</span>
        </MachineBtn>
      </div>
    </Gate>

    <Gate gate="safety">
      <MachineBtn
        type="machineOn"
        :active="isEnabled"
        @click="isEnabled ? emit('machineOff') : emit('machineOn')"
      >
        <Power class="stripIcon" />
        <span class="stripLabel">{{ isEnabled ? 'On' : 'Off' }}</span>
      </MachineBtn>
    </Gate>

    <div class="stripStatus">
      <span class="statusDot" :class="{ on: !isEstop }"></span>
      <span class="statusDot" :class="{ on: isEnabled }"></span>
      <span class="statusDot" :class="{ on: isHomed }"></span>
    </div>
  </div>
</template>

<style scoped>
.safetyStrip {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
  align-items: stretch;
  min-width: 90px;
}
.safetyBtns {
  display: flex;
  flex-direction: column;
  gap: var(--gap-tight);
}
.stripIcon {
  width: var(--fs-lg);
  height: var(--fs-lg);
}
.stripLabel {
  font-size: var(--fs-2xs);
}
.stripStatus {
  display: flex;
  gap: var(--gap-tight);
  justify-content: center;
}
.statusDot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-pill);
  background: var(--danger);
  opacity: var(--opacity-muted);
}
.statusDot.on {
  background: var(--ok);
  opacity: 1;
}
</style>
```

- [ ] **Step 2: Wire SafetyStrip into App.vue strip**

Import `SafetyStrip` in App.vue. Place it as the first child of `.strip`, passing the required props and connecting emits to existing handler functions (which already exist from the sidebar implementation).

```vue
<div class="strip">
  <SafetyStrip
    :armed="armed"
    :is-estop="st.isEstop"
    :is-enabled="st.isEnabled"
    :is-homed="st.isHomed"
    :task-state="st.task_state"
    @arm="doArm"
    @disarm="doDisarm"
    @estop="doEstop"
    @estop-reset="doEstopReset"
    @machine-on="doMachineOn"
    @machine-off="doMachineOff"
  />
</div>
```

- [ ] **Step 3: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors. Safety controls render in the bottom strip.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/SafetyStrip.vue lcnc-webui/src/App.vue
git commit -m "feat: add SafetyStrip component to bottom action strip"
```

---

### Task 3: ControlsStrip Component — Overrides, Spindle, Coolant

**Files:**
- Create: `lcnc-webui/src/ControlsStrip.vue`
- Modify: `lcnc-webui/src/App.vue` (import + place in strip)
- Modify: `lcnc-webui/src/machineControls.ts` (add any missing catalog entries)

Move overrides (feed/spindle/rapid sliders), spindle controls (FWD/REV/STOP + RPM), and coolant toggles (Flood/Mist) from sidebar popovers into an inline strip section. These are always-visible, no popovers.

- [ ] **Step 1: Check machineControls.ts for existing entries**

Verify these catalog entries exist. The sidebar already uses MachineBtn/MachineSlider/MachineToggle with gates — the same types should carry over. Check for: `spindleFwd`, `spindleRev`, `spindleStop` in BUTTON_TYPES and `spindleRpm`, `feedOverride`, `spindleOverride`, `rapidOverride` in INPUT_DEFS. Add any that are missing.

- [ ] **Step 2: Create ControlsStrip.vue**

This component renders three inline sections side by side:

1. **Overrides** — Three sliders (feed/spindle/rapid) with percentage readouts. Gate: `override`.
2. **Spindle** — FWD/STOP/REV buttons + RPM input + actual RPM readout. Gate: `ready` for buttons, `override` for speed display.
3. **Coolant** — Flood/Mist toggle buttons. Gate: `ready`.
4. **Tool** — Current tool display + Measure/Load buttons. Gate: `ready`.
5. **Macros** — Row of user macro buttons. Gate: `ready`.

Each section is wrapped in its own `<Gate>` with the appropriate permission.

The layout is a vertical stack of compact rows, designed to fit beside the mode column.

```vue
<script setup lang="ts">
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import MachineSlider from "./MachineSlider.vue";
import MachineToggle from "./MachineToggle.vue";
import MachineInput from "./MachineInput.vue";

// Props: override values, spindle state, coolant state, tool state, macros
// Emits: setFeedOverride, setSpindleOverride, setRapidOverride,
//        spindleFwd, spindleRev, spindleStop, setSpindleSpeed,
//        floodToggle, mistToggle, toolMeasure, toolLoad, runMacro
</script>
```

Structure the template as a flex column with labeled rows. Each row is a `<Gate>` wrapper with inline controls. Use existing catalog component types — never raw HTML inputs.

- [ ] **Step 3: Wire ControlsStrip into App.vue**

Import and place as the third child of `.strip` (after SafetyStrip and ModeStrip placeholder). Connect all emits to existing App.vue handler functions.

- [ ] **Step 4: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 5: Commit**

```bash
git add lcnc-webui/src/ControlsStrip.vue lcnc-webui/src/App.vue lcnc-webui/src/machineControls.ts
git commit -m "feat: add ControlsStrip — inline overrides, spindle, coolant, tool, macros"
```

---

### Task 4: ModeStrip Component — Jog / MDI / Program

**Files:**
- Create: `lcnc-webui/src/ModeStrip.vue`
- Modify: `lcnc-webui/src/App.vue` (import + place in strip)

The mode strip contains three mutually exclusive views (only one shown at a time), selected by tab buttons at the top:

1. **Jog** — Compact jog controls (reuse JogHUD layout: 170px wheel + Z buttons + ABC/UVW). Add compact touchoff row and WCS selector.
2. **MDI** — Input field + send button + scrollable command history.
3. **Program** — Start/Pause/Resume/Stop/Step buttons + loaded file name + progress indicator.

The tab buttons themselves are `gate="always"` (you can see them always). The content of each view has its own gate.

- [ ] **Step 1: Create ModeStrip.vue**

```vue
<script setup lang="ts">
import { ref } from "vue";
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
// ... imports for jog, MDI, program sub-views

type StripMode = "jog" | "mdi" | "program";
const mode = ref<StripMode>("jog");
</script>

<template>
  <div class="modeStrip">
    <!-- Mode tabs -->
    <div class="row-tight modeTabs">
      <MachineBtn type="tab" :selected="mode === 'jog'" @click="mode = 'jog'">Jog</MachineBtn>
      <MachineBtn type="tab" :selected="mode === 'mdi'" @click="mode = 'mdi'">MDI</MachineBtn>
      <MachineBtn type="tab" :selected="mode === 'program'" @click="mode = 'program'">Program</MachineBtn>
    </div>

    <!-- Jog view (compact — JogHUD-style) -->
    <div v-show="mode === 'jog'" class="modeContent">
      <Gate gate="jog">
        <!-- JogHUD-style wheel + Z + ABC/UVW -->
        <!-- Compact WCS selector row -->
        <!-- Compact touchoff row -->
      </Gate>
    </div>

    <!-- MDI view -->
    <div v-show="mode === 'mdi'" class="modeContent">
      <Gate gate="ready">
        <!-- MDI input + send + history -->
      </Gate>
    </div>

    <!-- Program view -->
    <div v-show="mode === 'program'" class="modeContent">
      <Gate gate="safety">
        <!-- Start (gate=ready), Pause (gate=pause), Resume (gate=resume), Stop (gate=abort) -->
        <!-- Each button has its own type from catalog — MachineBtn self-gates -->
        <!-- File name + progress -->
      </Gate>
    </div>
  </div>
</template>
```

The jog sub-view should reuse the existing `JogHUD` component (170px wheel, compact sizing) rather than duplicating the jog wheel code. Pass the same props that ThreeViewer currently passes to JogHUD.

- [ ] **Step 2: Wire ModeStrip into App.vue**

Import and place between SafetyStrip and ControlsStrip in the `.strip` div. The ModeStrip gets `flex: 1` to take remaining horizontal space. Connect all emits.

- [ ] **Step 3: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/ModeStrip.vue lcnc-webui/src/App.vue
git commit -m "feat: add ModeStrip — jog/MDI/program mode-exclusive views"
```

---

### Task 5: Content Area — Single TabPanel, Remove Multi-Panel

**Files:**
- Modify: `lcnc-webui/src/App.vue`
- Modify: `lcnc-webui/src/defaults.ts` (remove panel layout settings)
- Modify: `lcnc-webui/src/main.ts` (remove multi-panel bootstrap)

Replace the multi-panel system (1-4 panels, each with its own TabPanel) with a single content TabPanel. Remove the "Add Panel" button and panel management logic.

Content tabs: `3D Viewer | Program | Probing | Tool Table`

- [ ] **Step 1: Simplify App.vue template**

Replace the `v-for="panel in panels"` multi-panel loop with a single `<TabPanel>`. Remove `.addPanel` button. Remove panel management functions (`addPanel`, `removePanel`, `loadPanelsDefaults`, `savePanelsDefaults`).

```vue
<Gate gate="safety" class="content">
  <TabPanel :tabs="contentTabs" v-model="activeTab">
    <template #viewer>
      <ThreeViewer ... />
    </template>
    <template #gcode>
      <GcodePanel ... />
    </template>
    <template #probe>
      <ProbePanel ... />
    </template>
    <template #tools>
      <ToolTablePanel ... />
    </template>
  </TabPanel>
</Gate>
```

- [ ] **Step 2: Define contentTabs**

```ts
const contentTabs = [
  { id: "viewer", label: "3D Viewer" },
  { id: "gcode",  label: "Program" },
  { id: "probe",  label: "Probing" },
  { id: "tools",  label: "Tool Table" },
];
const activeTab = ref("viewer");
```

- [ ] **Step 3: Update content CSS**

```css
.content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
```

Remove `.panels` horizontal scroll container, `.panel` sizing, `.panel-viewer`/`.panel-manual`/etc. width rules, `.addPanel` button styles.

- [ ] **Step 4: Remove ManualPanel from content tabs**

ManualPanel is no longer a content tab — its contents have moved to the strip. Remove the `#manual` slot and ManualPanel import (but don't delete ManualPanel.vue yet — do that in cleanup).

- [ ] **Step 5: Move ToolTablePanel from dialog to content tab**

Currently ToolTablePanel opens as a dialog overlay from the sidebar Tool button. Move it to be an inline content tab instead. Remove the dialog overlay wrapper. The ToolTablePanel component itself should work inline with minimal changes (it's already a full panel).

- [ ] **Step 6: Update defaults.ts**

Remove `loadPanelsDefaults` / `savePanelsDefaults` if they exist. Add `activeTab` to a settings section if tab persistence is desired.

- [ ] **Step 7: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 8: Commit**

```bash
git add lcnc-webui/src/App.vue lcnc-webui/src/defaults.ts lcnc-webui/src/main.ts
git commit -m "refactor: single content TabPanel, remove multi-panel system"
```

---

### Task 6: Header Restructure — Move Settings, Messages, G-code Ref

**Files:**
- Modify: `lcnc-webui/src/App.vue`

Move Settings, Messages, and G-code Reference from sidebar to header. These open as dialogs/popovers from header icon buttons. Shutdown button stays in header.

- [ ] **Step 1: Add header icon buttons**

Add three icon buttons to the header right section:

```vue
<MachineBtn type="headerIcon" @click="toggleMessages" :warning="hasUnreadMessages">
  <MessageSquare class="headerIcon" />
</MachineBtn>
<MachineBtn type="headerIcon" @click="openGcodeRef">
  <BookOpen class="headerIcon" />
</MachineBtn>
<MachineBtn type="headerIcon" @click="openSettings">
  <SlidersHorizontal class="headerIcon" />
</MachineBtn>
```

These use the existing `headerIcon` button type from the catalog. The dialog-open handlers already exist in App.vue.

- [ ] **Step 2: Messages — popover or dialog from header**

The messages popover currently anchors to the sidebar button. Restructure it as a dropdown from the header button, or convert to a dialog. A dropdown popover anchored to the header button is more natural (like notification dropdowns in web apps).

Position: `position: absolute; top: 100%; right: 0;` relative to the header button.

- [ ] **Step 3: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/App.vue
git commit -m "feat: move settings, messages, gcode ref to header"
```

---

### Task 7: Camera PiP Overlay in 3D Viewer

**Files:**
- Modify: `lcnc-webui/src/ThreeViewer.vue`
- Modify: `lcnc-webui/src/App.vue` (remove camera content tab, pass camera props to ThreeViewer)

Camera becomes a small picture-in-picture overlay inside the 3D viewer, toggled by a toolbar button.

- [ ] **Step 1: Add camera PiP to ThreeViewer**

Add a `<div class="cameraPip">` overlay inside ThreeViewer, positioned bottom-right (or user-configurable). Contains a small `<img>` element for the MJPEG stream. Toggled via a toolbar button or the existing layer toggle system.

```css
.cameraPip {
  position: absolute;
  bottom: var(--gap-section);
  right: var(--gap-section);
  width: 320px;
  aspect-ratio: 16/9;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  z-index: 10; /* above canvas, below HUD buttons */
}
```

- [ ] **Step 2: Remove Camera content tab**

Remove `#camera` from contentTabs. Remove CameraViewer import from App.vue if no longer needed as a standalone tab.

- [ ] **Step 3: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors.

- [ ] **Step 4: Commit**

```bash
git add lcnc-webui/src/ThreeViewer.vue lcnc-webui/src/App.vue
git commit -m "feat: camera PiP overlay in 3D viewer"
```

---

### Task 8: Cleanup — Remove Dead Code

**Files:**
- Delete: `lcnc-webui/src/ManualPanel.vue`
- Delete: `lcnc-webui/src/DroPanel.vue` (if no longer used — DRO is in HUD)
- Delete: `lcnc-webui/src/MdiPanel.vue` (if it exists as separate file)
- Modify: `lcnc-webui/src/App.vue` (remove dead imports, commented sidebar code)
- Modify: `lcnc-webui/src/style.css` (remove dead sidebar/popover styles)

- [ ] **Step 1: Remove ManualPanel.vue**

Delete the file. It's fully replaced by the strip (jog in ModeStrip, MDI in ModeStrip, DRO in HUD).

- [ ] **Step 2: Remove DroPanel.vue if unused**

Check if DroPanel is still imported anywhere. If only ManualPanel used it and the strip's touchoff uses a compact inline version, delete it.

- [ ] **Step 3: Clean up App.vue**

Remove any commented-out sidebar code. Remove unused imports (ManualPanel, DroPanel, sidebar-specific icons). Remove unused reactive state (openChip, etc.).

- [ ] **Step 4: Clean up style.css**

Remove all sidebar-related CSS that was commented out or left behind in Task 1. Verify no dead selectors remain.

- [ ] **Step 5: Build and verify**

Run: `cd lcnc-webui && npm run build`
Expected: Zero errors. No dead code warnings.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore: remove ManualPanel, DroPanel, dead sidebar code"
```

---

### Task 9: Gate Audit Verification

**Files:**
- No file changes — verification only

- [ ] **Step 1: Start dev server and verify gate audit**

Start the dev server (`WEBUI_DEV=1`). Open the browser. Check the console for gate audit warnings. Every `button`, `input`, `select`, `textarea` in the new strip must be inside a valid `<Gate>` with a `data-gate` attribute from `VALID_GATES`.

- [ ] **Step 2: Check E-Stop accessibility**

Verify E-Stop and Arm buttons are functional when:
- Disarmed (outer gate disabled, but strip safety column is outside outer gate)
- Machine off
- E-Stop active

These buttons must NEVER be disabled by the outer gate.

- [ ] **Step 3: Check permission dimming**

Verify catalog components dim correctly:
- When disarmed: all controls except Arm/E-Stop should be dimmed
- When armed but not homed: jog and MDI should be dimmed, overrides should work
- When running a program: jog tab disabled, overrides work, pause/stop work

- [ ] **Step 4: Check z-index layering**

Open a dialog (Settings, G-code Reference). Verify:
- Dialog overlay covers the content area AND the strip
- E-Stop in the strip is NOT covered by the dialog (strip is outside outer gate, but dialogs are z-index 1000 with position: fixed — they cover everything)

**CRITICAL**: This is a design tension. Dialogs currently use `position: fixed; z-index: 1000` which covers the entire viewport including the strip. E-Stop must remain accessible even with a dialog open. Solutions:
- (a) Dialogs use `position: absolute` inside `.content` instead of fixed — strip stays accessible beneath
- (b) E-Stop gets its own z-index layer above dialogs
- (c) Dialogs don't block pointer events on the strip area

Recommend (a): dialogs overlay only the `.content` area, not the strip. This requires changing `.dialogOverlay` from `position: fixed; inset: 0` to being positioned within `.content`. This change should be made in Task 1 when updating `style.css`.

- [ ] **Step 5: Document any audit violations and fix them**

If any elements show red outlines, fix them by wrapping in appropriate Gates or adding proper catalog types.

---

## Implementation Notes

### Dialog Z-Index — Critical Safety Concern

**The current dialog system uses `position: fixed; inset: 0; z-index: 1000`** which covers the entire viewport. With the sidebar, this was acceptable because E-Stop was in the sidebar at z-index 1020 (above dialogs).

With the strip layout, there is no sidebar at z-index 1020. The strip is in normal flow. **Dialogs would cover the E-Stop button.**

**Resolution:** Dialogs must be scoped to the `.content` area, not the full viewport. Change `.dialogOverlay` to be a child of `.content` with `position: absolute; inset: 0` (content needs `position: relative`). This way the strip remains accessible below any dialog.

This means:
```css
.content {
  position: relative; /* establishes containing block for dialogs */
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.dialogOverlay {
  position: absolute; /* was: fixed */
  inset: 0;
  /* remove: padding-left: var(--sidebar-total) */
  z-index: 1000;
}
```

The strip sits below `.content` in the flex layout and is never covered by `.content`'s absolutely-positioned children.

**Safety confirmation dialogs** (shutdown, comp toggle) currently use z-index 1010. These should also be scoped to `.content` — you shouldn't be able to shut down LinuxCNC without being able to E-Stop.

### Strip Height Management

The strip height is driven by content — no fixed height. The tallest mode (likely Jog with the 170px wheel) sets the strip height. Other modes (MDI, Program) will have extra vertical space — this is acceptable.

To prevent the strip from growing unbounded, add `max-height: 50vh` or similar. If content overflows, `overflow-y: auto` on the mode content area handles it.

### JogHUD Reuse

The JogHUD component already exists with compact sizing (170px wheel, 68×68 Z buttons). It's currently used as an overlay inside ThreeViewer. For the strip, import and use JogHUD directly in ModeStrip's jog view. This avoids duplicating the jog wheel code.

JogHUD props: `jogVel`, `jogVelMax`, `stepIdx`, `stepSizes`, `axes`, `homedJoints`, `teleop`
JogHUD emits: `jog`, `jogStep`, `update:jogVel`, `update:stepIdx`, `homeAll`, `unhomeAll`

### Multi-Panel Removal Impact

The multi-panel system allows showing 2+ tabs simultaneously (e.g., 3D viewer + manual control). With the strip providing persistent controls, the primary use case for multi-panel disappears. The 3D viewer HUD provides DRO + monitoring. The strip provides jog/MDI/overrides. There's no longer a need to see Manual Control alongside the 3D viewer.

Users who want to see the G-code alongside the 3D viewer lose that capability. This is a deliberate trade-off — the strip provides more value than side-by-side panels.
