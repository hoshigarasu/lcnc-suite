# lcnc-webui

Reference Vue 3 + TypeScript web interface for lcnc-gateway.

## Table of Contents

- [Development](#development)
- [Architecture](#architecture)
- [Permission System](#permission-system)
- [Panel Layout](#panel-layout)

## Development

```bash
npm install
npm run dev          # Dev server with HMR
npm run build        # Production build
npm run type-check   # TypeScript checking
```

## Architecture

```
App.vue                          Root — state, layout, sidebar, dialogs
├── Sidebar (outside outer Gate) Machine Safety, Status, Controls
│   ├── Gate(always)             Arm/Disarm, E-Stop
│   ├── Gate(safety)             Machine On/Off
│   ├── Status chip popovers    Machine, Program, Overrides (click-to-toggle)
│   └── Gate(abort) Controls    Spindle, Coolant, Tool, Macros popovers
├── Gate(safety) mainArea        Outer Gate — everything below is default-deny
│   ├── Header                   Connection, fullscreen
│   └── Panels
│       ├── ThreeViewer.vue      3D viewer (Three.js)
│       │   ├── JogHUD.vue       Jog overlay pill
│       │   └── SetupHUD.vue     Setup overlay pill (home, zero)
│       └── TabPanel.vue         Content panel tab selector
│           ├── ManualPanel.vue  DRO + jogging + MDI
│           ├── GcodePanel.vue   G-code viewer + program controls
│           ├── ToolTablePanel.vue  Tool table editor
│           ├── ProbePanel.vue   Probe operations
│           ├── CameraViewer.vue Camera feed + overlay
│           ├── SettingsPanel.vue  Settings (sub-tabbed)
│           └── DebugTab.vue     Debug/timing
```

### Services & Catalog

| File | Purpose |
|------|---------|
| `lcncWs.ts` | WebSocket client — status polling, command sending, heartbeat |
| `lcncApi.ts` | REST helpers — file listing, upload |
| `permissions.ts` | Permission evaluation (11 classes) + provide/inject |
| `machineControls.ts` | Machine controls catalog — BUTTON_TYPES + INPUT_GATES |
| `MachineBtn.vue` | Catalog-aware button (wraps Btn.vue) |
| `MachineInput/Toggle/Slider/Select/Radio/Color.vue` | Catalog-aware form controls |
| `Gate.vue` | Permission gate (`<fieldset :disabled>`) |
| `defaults.ts` | Server-synced settings with section registry |

## Permission System & Machine Controls Catalog

All permissions are defined in `permissions.ts` (11 classes) and distributed via Vue provide/inject. All interactive elements use catalog-aware components that look up their permission gate automatically.

See the [permission class table](../README.md#reference-ui-lcnc-webui) in the root README for the full rule matrix.

### Usage — Catalog Components (primary pattern)

```vue
<!-- Buttons: type maps to BUTTON_TYPES catalog entry (gate + variant + size) -->
<MachineBtn type="start" @click="run">Start</MachineBtn>
<MachineBtn type="close" @click="dismiss">×</MachineBtn>
<MachineBtn type="tab" :selected="active === 'dro'">DRO</MachineBtn>

<!-- Inputs: gate maps to INPUT_GATES catalog entry -->
<MachineInput gate="mdiText" v-model="mdi" />
<MachineSlider gate="feedOverride" v-model="feed" />
<MachineToggle gate="optionalStop" v-model="m01" label="M01" />
```

### Usage — Gate.vue (section-level gating)

```vue
<Gate :allow="can.ready">
  <!-- All children disabled when gate is false -->
  <MachineBtn type="start" @click="run">Start</MachineBtn>
</Gate>
```

### Architecture

- **Outer Gate** (`permissions.safety`) wraps entire main area — default-deny when disarmed
- **Sidebar** is a DOM sibling of the outer Gate — Arm/E-Stop/Machine On always accessible
- **Catalog components** self-gate for visual dimming during normal operation
- **Backend `require_armed()`** provides defense-in-depth

## Panel Layout

Viewport-locked layout: `html { overflow: auto }`, `body { overflow: hidden; min-width: 760px; min-height: 600px }`. Browser scrollbar appears only when the window is smaller than the minimums. Inside the app, `.panels` scrolls one axis per orientation — horizontal in landscape, vertical in portrait. All `.panel` elements use `box-sizing: border-box` (sizes include padding + border).

### Landscape (side by side, `overflow-x: auto`)

| Panel | Width | Height |
|-------|-------|--------|
| viewer | `flex: 1`, `min-width: 560px` | stretch, `min-height: 400px` |
| manual | `min-width: 560px` | stretch, `min-height: 400px` |
| gcode, tools, messages, settings | `flex: 0.5` | stretch, `min-height: 400px` |

Viewer fills remaining width. Gcode, tools, messages, and settings grow at half rate (`flex: 0.5`). Manual gets a wider `min-width` override. Height is uniform — all panels stretch to `.panels` container height.

### Portrait (stacked, `overflow-y: auto`)

| Panel | Width | Height |
|-------|-------|--------|
| viewer | stretch, `min-width: 560px` | `flex: 1`, `min-height: 500px` |
| manual, settings | stretch, `min-width: 560px` | `flex: 0 0 auto` (content-sized) |
| gcode, tools, messages | stretch, `min-width: 560px` | `flex: 0 0 500px` (fixed for internal scroll) |

Viewer fills remaining height. Static panels (manual, settings) auto-size to their content. Scrollable panels (gcode, tools, messages) use a fixed 500px height to bound their internal scroll areas. Width is uniform — all panels stretch to `.panels` width with a shared `min-width: 560px`.

### Sidebar

The sidebar (left column, 150px wide) contains three sections:

1. **Machine Safety** — Arm/Disarm, E-Stop, Machine On/Off
2. **Machine Status** — Click-to-toggle popovers for Machine, Program, and Overrides
3. **Controls** — Spindle button with popover (direction, RPM, actuals, override slider)
