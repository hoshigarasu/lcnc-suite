# Machine Controls Catalog — Predefined Control Types

**Date:** 2026-03-28
**Status:** Design

## Problem

The current UI has ~158 buttons and ~130 interactive inputs/toggles/sliders, each individually gated by wrapper `<Gate>` components. A new developer must trace up through the DOM to find which Gate wraps a button, understand the permission hierarchy, and know whether a `:disabled` binding is for permissions (redundant with Gate) or app state (necessary). The nested Gate pattern in sections like the GcodePanel control row is hard to follow.

QtPyVCP solves this differently: predefined widget types (MDIButton, ActionButton, JogButton) that inherit their enable conditions, styling, and behavior from the widget class. You place the widget and configure the action — the rest is automatic.

## Solution

A catalog of predefined machine control types. Nine components, one catalog file, one source of truth for permissions.

The outer Gate on mainArea stays as the enforcement layer (browser-enforced fieldset). The catalog components add the correct visual feedback (dimming) at the right permission level. If a developer forgets the `type` prop, the outer Gate still blocks the click — fail-safe.

## Architecture

Three layers, each with one job:

1. **Outer Gate** (fieldset) — enforcement, browser blocks clicks when disarmed
2. **Machine* components** (catalog) — visual feedback at correct permission level
3. **`:disabled` prop** — app state only (loading, no file, probing)

## Catalog File (`machineControls.ts`)

Single source of truth for all control permissions:

```ts
import type { Permissions } from './permissions';

export type ControlGate = keyof Permissions;

// ── Button definitions ──

export interface ButtonDef {
  gate: ControlGate;
  variant: 'default' | 'primary' | 'ok' | 'danger' | 'estop';
  size: 'xs' | 'sm' | 'md' | 'lg';
}

export const BUTTON_TYPES = {
  // Program control
  start:          { gate: 'ready',    variant: 'primary', size: 'md' },
  step:           { gate: 'ready',    variant: 'default', size: 'md' },
  pause:          { gate: 'pause',    variant: 'default', size: 'md' },
  resume:         { gate: 'resume',   variant: 'default', size: 'md' },
  abort:          { gate: 'abort',    variant: 'danger',  size: 'md' },

  // MDI / motion
  mdi:            { gate: 'ready',    variant: 'default', size: 'md' },
  goTo:           { gate: 'ready',    variant: 'default', size: 'md' },
  home:           { gate: 'idle',     variant: 'default', size: 'md' },
  unhome:         { gate: 'idle',     variant: 'default', size: 'md' },

  // Probe
  probe:          { gate: 'probe',    variant: 'default', size: 'md' },

  // Tool
  toolLoad:       { gate: 'ready',    variant: 'primary', size: 'md' },
  toolMeasure:    { gate: 'ready',    variant: 'ok',      size: 'md' },
  toolUnload:     { gate: 'ready',    variant: 'default', size: 'md' },

  // Spindle
  spindleFwd:     { gate: 'ready',    variant: 'default', size: 'md' },
  spindleRev:     { gate: 'ready',    variant: 'default', size: 'md' },
  spindleStop:    { gate: 'ready',    variant: 'danger',  size: 'md' },

  // Coolant
  flood:          { gate: 'ready',    variant: 'default', size: 'md' },
  mist:           { gate: 'ready',    variant: 'default', size: 'md' },

  // Overrides
  overridePreset: { gate: 'override', variant: 'default', size: 'xs' },
  overrideReset:  { gate: 'override', variant: 'default', size: 'xs' },

  // File operations
  fileOp:         { gate: 'idle',     variant: 'default', size: 'md' },
  fileSave:       { gate: 'idle',     variant: 'primary', size: 'md' },

  // Settings / tool table management
  manage:         { gate: 'idle',     variant: 'default', size: 'md' },
  reset:          { gate: 'idle',     variant: 'danger',  size: 'md' },

  // WCS selection
  wcs:            { gate: 'ready',    variant: 'default', size: 'sm' },

  // Zero / touchoff
  zero:           { gate: 'zero',     variant: 'default', size: 'md' },

  // Macros
  macro:          { gate: 'ready',    variant: 'default', size: 'lg' },

  // Shutdown
  shutdown:       { gate: 'abort',    variant: 'danger',  size: 'md' },
} as const satisfies Record<string, ButtonDef>;

export type ButtonType = keyof typeof BUTTON_TYPES;

// ── Input gate definitions ──
// All non-button controls share this lookup. The gate determines
// when the control is interactive vs disabled.

export const INPUT_GATES = {
  // Motion parameters
  jogSpeed:        'jog',
  jogIncrement:    'jog',
  jogWheel:        'jog',       // SVG wheel sectors
  jogAxis:         'jog',       // JogButton press-hold
  mdiText:         'ready',
  touchoff:        'zero',
  rpmInput:        'ready',

  // Override sliders
  feedOverride:    'override',
  spindleOverride: 'override',
  rapidOverride:   'override',

  // Probe parameters
  probeParam:      'ready',
  scanParam:       'ready',

  // Toolsetter parameters
  toolsetterParam: 'ready',

  // Tool table editing
  toolEdit:        'idle',
  toolSearch:      'idle',

  // 3D Viewer settings
  viewerSetting:   'idle',
  cameraSetting:   'idle',

  // Display settings
  displaySetting:  'idle',

  // Macro editing
  macroEdit:       'idle',

  // Keyboard/gamepad config
  inputConfig:     'idle',

  // Program toggles
  optionalStop:    'override',
  blockDelete:     'override',
} as const satisfies Record<string, ControlGate>;

export type InputType = keyof typeof INPUT_GATES;
```

## Nine Components

### 1. `MachineBtn` — action buttons

Wraps Btn. Looks up gate, variant, size from catalog.

```vue
<script setup lang="ts">
import { computed } from 'vue';
import Btn from './Btn.vue';
import { usePermissions } from './permissions';
import { BUTTON_TYPES, type ButtonType } from './machineControls';

const props = defineProps<{
  type: ButtonType;
  disabled?: boolean;  // app-state only
  active?: boolean;
  selected?: boolean;
}>();

const can = usePermissions();
const def = computed(() => BUTTON_TYPES[props.type]);
const gateAllowed = computed(() => can.value[def.value.gate]);
</script>

<template>
  <Btn
    :variant="def.variant"
    :size="def.size"
    :active="active"
    :selected="selected"
    :disabled="!gateAllowed || disabled"
  >
    <slot />
  </Btn>
</template>
```

Usage:
```vue
<MachineBtn type="abort" @click="emit('abort')">Abort</MachineBtn>
<MachineBtn type="start" :disabled="!activeFile" @click="onStart">Start</MachineBtn>
<MachineBtn type="wcs" :selected="g === g5x" @click="setG5x(g)">{{ g }}</MachineBtn>
```

### 2. `MachineInput` — text and number inputs

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
}>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <input v-bind="$attrs" :disabled="isDisabled">
</template>
```

Usage:
```vue
<MachineInput gate="rpmInput" type="number" v-model="rpm" :min="0" :step="100" />
<MachineInput gate="mdiText" type="text" v-model="mdiText" @keyup.enter="send" />
<MachineInput gate="touchoff" type="number" v-model="offset" :step="0.001" />
```

### 3. `MachineToggle` — checkbox toggle switches

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
  label?: string;
}>();
const model = defineModel<boolean>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <label class="toggleRow">
    <input type="checkbox" class="toggle" v-model="model" :disabled="isDisabled">
    {{ label }}
  </label>
</template>
```

Usage:
```vue
<MachineToggle gate="optionalStop" v-model="optStopOn" label="M01" />
<MachineToggle gate="viewerSetting" v-model="machineEdgesOn" label="Edges" />
```

### 4. `MachineSlider` — range inputs

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
  min?: number;
  max?: number;
  step?: number;
}>();
const model = defineModel<number>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <input type="range" v-model.number="model" :min="min" :max="max" :step="step" :disabled="isDisabled">
</template>
```

Usage:
```vue
<MachineSlider gate="jogSpeed" v-model="jogVel" :min="minVel" :max="maxVel" :step="0.1" />
<MachineSlider gate="feedOverride" v-model="feedOvr" :min="0" :max="200" :step="1" />
```

### 5. `MachineSelect` — dropdowns

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
}>();
const model = defineModel<string | number>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <select v-model="model" :disabled="isDisabled">
    <slot />
  </select>
</template>
```

Usage:
```vue
<MachineSelect gate="toolEdit" v-model="editForm.type">
  <option v-for="t in toolTypes" :value="t.id">{{ t.label }}</option>
</MachineSelect>
```

### 6. `MachineRadio` — radio button groups

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
  name: string;
  value: string | number;
}>();
const model = defineModel<string | number>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <input type="radio" :name="name" :value="value" v-model="model" :disabled="isDisabled">
</template>
```

Usage:
```vue
<label><MachineRadio gate="displaySetting" name="theme" value="dark" v-model="theme" /> Dark</label>
<label><MachineRadio gate="displaySetting" name="theme" value="light" v-model="theme" /> Light</label>
```

### 7. `MachineColor` — color pickers

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { usePermissions } from './permissions';
import { INPUT_GATES, type InputType } from './machineControls';

const props = defineProps<{
  gate: InputType;
  disabled?: boolean;
}>();
const model = defineModel<string>();

const can = usePermissions();
const isDisabled = computed(() => !can.value[INPUT_GATES[props.gate]] || props.disabled);
</script>

<template>
  <input type="color" v-model="model" :disabled="isDisabled">
</template>
```

### 8. `JogButton` — press-and-hold (existing, refactored)

JogButton already exists as a specialized component with pointer capture. The refactor: replace the `disabled` prop with a catalog lookup.

```ts
// Inside JogButton.vue setup
import { INPUT_GATES } from './machineControls';
const can = usePermissions();
const gateAllowed = computed(() => can.value[INPUT_GATES.jogAxis]);
const isDisabled = computed(() => !gateAllowed.value || !hasVelocity.value);
```

The parent no longer passes `:disabled="!can.jog"`. JogButton reads it from the catalog.

### 9. Jog wheel sectors — SVG (handler refactored)

The jog wheel SVG sectors in JogPanel and JogHUD use pointer event handlers. The refactor: the handler checks the catalog before starting a jog.

```ts
// Inside jog wheel handler
import { INPUT_GATES } from './machineControls';
const can = usePermissions();

function startJog(sector: Sector, e: PointerEvent) {
  if (!can.value[INPUT_GATES.jogWheel]) return;
  // ... existing jog logic
}
```

The SVG paths get `:class="{ disabled: !can[INPUT_GATES.jogWheel] }"` for visual feedback.

## What stays

- **Outer Gate on mainArea** — browser-enforced fieldset, fail-safe enforcement layer
- **Sidebar Gates** — always (Arm, E-Stop), safety (Machine On/Off), abort (Controls)
- **Dialog inner Gates** — wrapping dialogActions divs (Cancel + action buttons locked together)
- **Gate.vue** — still exists for structural gates above
- **Btn.vue** — stays for non-machine UI buttons (dialog close, tab switch, popover dismiss)
- **permissions.ts** — unchanged, catalog reads from it

## What gets removed

- **Wrapper Gates around button/input groups** — replaced by Machine* components with type props
- **Redundant `:disabled="!can.X"`** — Machine* handles it
- **Nested Gates in control rows** — each control gates itself
- **~50 wrapper Gate elements** (~100 lines of template)
- **~76 redundant `:disabled` bindings**

## Migration path

Incremental — one component at a time:

1. Create `machineControls.ts` + all 7 new Machine* components
2. Refactor JogButton + jog wheel to use catalog lookup
3. Convert GcodePanel control row (most visible improvement)
4. Convert ManualPanel (MDI, WCS, goto)
5. Convert DroPanel (home, zero, touchoff)
6. Convert ProbePanel (probe grid, params, toggles)
7. Convert App.vue sidebar (spindle, coolant, overrides, tool, macros)
8. Convert SettingsPanel (all sub-tabs)
9. Convert ToolTablePanel (table, edit dialog)
10. Convert Toolbar (layers, workpiece, projection)
11. Convert CameraViewer (overlay controls)
12. Remove emptied wrapper Gates
13. Update CLAUDE.md

Each step: replace wrapper Gate + element with Machine* component, verify build, commit.

## Decisions

- **Machine* wraps native elements** — doesn't replace Btn.vue. Btn stays for non-machine UI.
- **`gate` prop on inputs, `type` prop on buttons** — buttons need variant/size lookup, inputs just need the gate name
- **Outer Gate stays** — browser enforcement layer, non-negotiable
- **No `allow="true"`, no `#exempt`** — catalog components handle visual gating, outer Gate handles enforcement
- **Incremental migration** — no big bang, one component at a time
- **JogButton and jog wheel** read from the same catalog — specialized rendering, centralized permission
