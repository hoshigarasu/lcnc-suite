<script setup lang="ts">
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import MachineSlider from "./MachineSlider.vue";
import MachineInput from "./MachineInput.vue";
import { RotateCw, RotateCcw, Square } from "lucide-vue-next";
import { STEP_RPM, STEP_OVERRIDE, STEP_RAPID_OVERRIDE, STEP_DEFAULT, type MacroDef } from "./defaults";

const props = defineProps<{
  // Overrides
  feedSlider: number;
  spindleSlider: number;
  rapidSlider: number;
  feedOvrEnabled: boolean;
  spindleOvrEnabled: boolean;
  maxFeedOverride: number;
  minSpindleOverride: number;
  maxSpindleOverride: number;
  // Spindle
  isForward: boolean;
  isReverse: boolean;
  isSpinning: boolean;
  rpmInput: number;
  spindleActual: number | null;
  spindleSpeed: number | null;
  spindleLoad: number | null;
  minSpindleSpeed: number;
  maxSpindleSpeed: number;
  // Coolant
  floodOn: boolean;
  mistOn: boolean;
  // Tool
  toolNumber: number;
  currentTool: number;
  probing: boolean;
  // Macros
  userMacros: MacroDef[];
}>();

const emit = defineEmits<{
  // Overrides
  (e: "update:feedSlider", v: number): void;
  (e: "update:spindleSlider", v: number): void;
  (e: "update:rapidSlider", v: number): void;
  (e: "feedChange"): void;
  (e: "spindleSliderChange"): void;
  (e: "rapidChange"): void;
  (e: "overridePreset", type: "feed" | "spindle" | "rapid", percent: number): void;
  (e: "resetAllOverrides"): void;
  // Spindle
  (e: "spindleFwd", speed: number): void;
  (e: "spindleRev", speed: number): void;
  (e: "spindleStop"): void;
  (e: "update:rpmInput", v: number): void;
  // Coolant
  (e: "toggleFlood"): void;
  (e: "toggleMist"): void;
  // Tool
  (e: "update:toolNumber", v: number): void;
  (e: "saveToolNumber"): void;
  (e: "measureAuto"): void;
  (e: "loadTool"): void;
  (e: "unloadTool"): void;
  (e: "openToolTable"): void;
  // Macros
  (e: "executeMacro", m: MacroDef): void;
}>();

function formatRpm(val: number | null): string {
  if (val == null) return "---";
  return Math.round(val).toLocaleString();
}

function onFeedSlider(v: number) { emit('update:feedSlider', v); }
function onSpindleSlider(v: number) { emit('update:spindleSlider', v); }
function onRapidSlider(v: number) { emit('update:rapidSlider', v); }
</script>

<template>
  <div class="controlsStrip">
    <!-- Overrides -->
    <Gate gate="override" class="ctrlSection">
      <div class="ctrlLabel">Overrides</div>
      <div class="ovrRow">
        <span class="ovrName">F</span>
        <MachineSlider
          gate="feedOverride"
          :modelValue="feedSlider"
          @update:model-value="onFeedSlider(Number($event))"
          @change="emit('feedChange')"
          :min="0" :max="maxFeedOverride" :step="STEP_OVERRIDE"
          :disabled="!feedOvrEnabled"
          class="ovrSlider"
        />
        <span class="ovrVal" :class="{ warn: feedSlider !== 100 }">{{ feedSlider }}%</span>
      </div>
      <div class="ovrRow">
        <span class="ovrName">S</span>
        <MachineSlider
          gate="spindleOverride"
          :modelValue="spindleSlider"
          @update:model-value="onSpindleSlider(Number($event))"
          @change="emit('spindleSliderChange')"
          :min="minSpindleOverride" :max="maxSpindleOverride" :step="STEP_OVERRIDE"
          :disabled="!spindleOvrEnabled"
          class="ovrSlider"
        />
        <span class="ovrVal" :class="{ warn: spindleSlider !== 100 }">{{ spindleSlider }}%</span>
      </div>
      <div class="ovrRow">
        <span class="ovrName">R</span>
        <MachineSlider
          gate="rapidOverride"
          :modelValue="rapidSlider"
          @update:model-value="onRapidSlider(Number($event))"
          @change="emit('rapidChange')"
          :min="25" :max="100" :step="STEP_RAPID_OVERRIDE"
          class="ovrSlider"
        />
        <span class="ovrVal" :class="{ warn: rapidSlider !== 100 }">{{ rapidSlider }}%</span>
      </div>
      <MachineBtn type="overrideReset" @click="emit('resetAllOverrides')" block>Reset</MachineBtn>
    </Gate>

    <!-- Spindle -->
    <Gate gate="ready" class="ctrlSection">
      <div class="ctrlLabel">Spindle</div>
      <div class="spRow">
        <MachineBtn type="spindleRev" :active="isReverse" @click="emit('spindleRev', rpmInput)" title="Reverse (CCW)">
          <RotateCcw :size="14" />
        </MachineBtn>
        <MachineBtn type="spindleStop" :active="isSpinning" :disabled="!isSpinning" @click="emit('spindleStop')" title="Stop">
          <Square :size="14" />
        </MachineBtn>
        <MachineBtn type="spindleFwd" :active="isForward" @click="emit('spindleFwd', rpmInput)" title="Forward (CW)">
          <RotateCw :size="14" />
        </MachineBtn>
      </div>
      <div class="spRpmRow">
        <MachineInput
          gate="rpmInput"
          type="number"
          :modelValue="rpmInput"
          @update:modelValue="emit('update:rpmInput', Number($event))"
          :min="minSpindleSpeed" :max="maxSpindleSpeed" :step="STEP_RPM"
          class="spRpmInput"
        />
        <span class="spUnit">RPM</span>
      </div>
      <div class="spActual">
        <span>{{ formatRpm(spindleActual) }}</span>
        <span class="spUnit">act</span>
      </div>
    </Gate>

    <!-- Coolant -->
    <Gate gate="ready" class="ctrlSection">
      <div class="ctrlLabel">Coolant</div>
      <div class="clRow">
        <MachineBtn type="flood" :active="floodOn" @click="emit('toggleFlood')" block>
          Flood {{ floodOn ? 'ON' : 'OFF' }}
        </MachineBtn>
        <MachineBtn type="mist" :active="mistOn" @click="emit('toggleMist')" block>
          Mist {{ mistOn ? 'ON' : 'OFF' }}
        </MachineBtn>
      </div>
    </Gate>

    <!-- Tool -->
    <Gate gate="ready" class="ctrlSection">
      <div class="ctrlLabel">Tool</div>
      <div class="toolRow">
        <span class="toolCurrent">T{{ currentTool }}</span>
        <MachineInput
          gate="toolEdit"
          type="number"
          :modelValue="toolNumber"
          @update:modelValue="emit('update:toolNumber', Number($event))"
          @change="emit('saveToolNumber')"
          :min="1" :step="STEP_DEFAULT"
          :disabled="probing"
          class="toolInput"
        />
      </div>
      <div class="toolActions">
        <MachineBtn type="toolMeasure" :disabled="probing" @click="emit('measureAuto')">Meas</MachineBtn>
        <MachineBtn type="toolLoad" :disabled="probing" @click="emit('loadTool')">Load</MachineBtn>
      </div>
    </Gate>

    <!-- Macros -->
    <Gate gate="ready" class="ctrlSection" v-if="userMacros.length > 0">
      <div class="ctrlLabel">Macros</div>
      <div class="macroRow">
        <MachineBtn
          v-for="m in userMacros"
          :key="m.id"
          type="macro"
          @click="emit('executeMacro', m)"
        >{{ m.name }}</MachineBtn>
      </div>
    </Gate>
  </div>
</template>

<style scoped>
.controlsStrip {
  display: flex;
  gap: var(--gap-section);
  align-items: flex-start;
  flex-shrink: 0;
}
.ctrlSection {
  display: flex;
  flex-direction: column;
  gap: var(--gap-tight);
  min-width: 0;
}
.ctrlLabel {
  font-size: var(--fs-2xs);
  opacity: var(--opacity-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}
/* Overrides */
.ovrRow {
  display: flex;
  align-items: center;
  gap: var(--gap-tight);
}
.ovrName {
  font-size: var(--fs-sm);
  font-weight: var(--fw-bold);
  width: 12px;
  text-align: center;
  flex-shrink: 0;
}
.ovrSlider {
  flex: 1;
  min-width: 80px;
}
.ovrVal {
  font-size: var(--fs-sm);
  font-family: var(--font-mono);
  width: 42px;
  text-align: right;
  flex-shrink: 0;
}
.ovrVal.warn {
  color: var(--warn);
}
/* Spindle */
.spRow {
  display: flex;
  gap: var(--gap-tight);
}
.spRpmRow {
  display: flex;
  align-items: center;
  gap: var(--gap-tight);
}
.spRpmInput {
  width: 70px;
}
.spUnit {
  font-size: var(--fs-2xs);
  opacity: var(--opacity-muted);
}
.spActual {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  display: flex;
  align-items: baseline;
  gap: var(--gap-tight);
}
/* Coolant */
.clRow {
  display: flex;
  flex-direction: column;
  gap: var(--gap-tight);
}
/* Tool */
.toolRow {
  display: flex;
  align-items: center;
  gap: var(--gap-tight);
}
.toolCurrent {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  font-weight: var(--fw-bold);
  color: var(--active-tool);
}
.toolInput {
  width: 50px;
}
.toolActions {
  display: flex;
  gap: var(--gap-tight);
}
/* Macros */
.macroRow {
  display: flex;
  flex-wrap: wrap;
  gap: var(--gap-tight);
}
</style>
