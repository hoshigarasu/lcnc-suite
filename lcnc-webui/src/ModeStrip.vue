<script setup lang="ts">
import { ref, computed } from "vue";
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import MachineInput from "./MachineInput.vue";
import JogHUD from "./JogHUD.vue";

type StripMode = "jog" | "mdi" | "program";
const mode = ref<StripMode>("jog");

const props = defineProps<{
  // Jog
  axes: string[];
  jogVel: number;
  angularJogVel: number;
  linearUnit: string;
  maxJogVel: number;
  maxAngularJogVel: number;
  minAngularJogVel: number;
  jogIncrement: number;
  minJogVel: number;
  iniIncrements: number[] | null;
  isTeleop: boolean;
  isHomed: boolean;
  homedJoints: boolean[];
  jogDisabled: boolean;
  touchoff: number[];
  g5xLabel: string;
  // MDI
  mdiText: string;
  // Program
  activeFile: string | null;
  isPaused: boolean;
  isRunning: boolean;
  elapsed: string;
  optionalStop: boolean;
  blockDelete: boolean;
}>();

const emit = defineEmits<{
  // Jog
  (e: "update:jogVel", v: number): void;
  (e: "update:angularJogVel", v: number): void;
  (e: "update:jogIncrement", v: number): void;
  (e: "toggleTeleop"): void;
  (e: "homeAll"): void;
  (e: "unhomeAll"): void;
  (e: "setAxis", axis: number, value: number): void;
  (e: "setAll", values: number[]): void;
  (e: "update:touchoff", values: number[]): void;
  (e: "setG5x", gcode: string): void;
  (e: "goToG30"): void;
  (e: "goToHome"): void;
  (e: "goToZero"): void;
  // MDI
  (e: "update:mdiText", text: string): void;
  (e: "sendMdi"): void;
  // Program
  (e: "cycleStart"): void;
  (e: "cyclePause"): void;
  (e: "cycleResume"): void;
  (e: "cycleStep"): void;
  (e: "abort"): void;
  (e: "toggleOptionalStop"): void;
  (e: "toggleBlockDelete"): void;
}>();

// ─── MDI History ─────────────────────────────────────────────
const history = ref<string[]>([]);
const historyIndex = ref(-1);
const savedInput = ref("");

function handleSend() {
  const cmd = props.mdiText.trim();
  if (cmd) {
    if (history.value[0] !== cmd) {
      history.value.unshift(cmd);
      if (history.value.length > 50) history.value.length = 50;
    }
  }
  historyIndex.value = -1;
  savedInput.value = "";
  emit("sendMdi");
}

function onMdiKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowUp") {
    e.preventDefault();
    if (history.value.length === 0) return;
    if (historyIndex.value === -1) {
      savedInput.value = props.mdiText;
    }
    if (historyIndex.value < history.value.length - 1) {
      historyIndex.value++;
      emit("update:mdiText", history.value[historyIndex.value] ?? "");
    }
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (historyIndex.value === -1) return;
    historyIndex.value--;
    if (historyIndex.value === -1) {
      emit("update:mdiText", savedInput.value);
    } else {
      emit("update:mdiText", history.value[historyIndex.value] ?? "");
    }
    return;
  }
}

function clearHistory() {
  history.value = [];
  historyIndex.value = -1;
}

// ─── WCS options ─────────────────────────────────────────────
const g5xOptions = ["G54", "G55", "G56", "G57", "G58", "G59", "G59.1", "G59.2", "G59.3"];

// ─── Touchoff helpers ────────────────────────────────────────
const primaryAxes = computed(() => {
  const PRIMARY = new Set(["X", "Y", "Z"]);
  return props.axes
    .map((l, i) => ({ letter: l, index: i }))
    .filter(a => PRIMARY.has(a.letter));
});

function updateTouchoff(axis: number, val: number) {
  const copy = [...props.touchoff];
  copy[axis] = val;
  emit("update:touchoff", copy);
}

// ─── Program helpers ─────────────────────────────────────────
const fileName = computed(() => {
  if (!props.activeFile) return "No file loaded";
  const parts = props.activeFile.split("/");
  return parts[parts.length - 1] ?? props.activeFile;
});
</script>

<template>
  <div class="modeStrip">
    <!-- Mode tabs -->
    <div class="row-tight modeTabs">
      <MachineBtn type="tab" :selected="mode === 'jog'" @click="mode = 'jog'">Jog</MachineBtn>
      <MachineBtn type="tab" :selected="mode === 'mdi'" @click="mode = 'mdi'">MDI</MachineBtn>
      <MachineBtn type="tab" :selected="mode === 'program'" @click="mode = 'program'">Program</MachineBtn>
    </div>

    <!-- ═══ JOG VIEW ═══ -->
    <div v-show="mode === 'jog'" class="modeContent">
      <div class="jogLayout">
        <JogHUD
          :axes="axes"
          :jogVel="jogVel"
          :angularJogVel="angularJogVel"
          :linearUnit="linearUnit"
          :maxJogVel="maxJogVel"
          :maxAngularJogVel="maxAngularJogVel"
          :minAngularJogVel="minAngularJogVel"
          :jogIncrement="jogIncrement"
          :minJogVel="minJogVel"
          :iniIncrements="iniIncrements"
          :isTeleop="isTeleop"
          :isHomed="isHomed"
          :disabled="jogDisabled"
          @update:jogVel="emit('update:jogVel', $event)"
          @update:angularJogVel="emit('update:angularJogVel', $event)"
          @update:jogIncrement="emit('update:jogIncrement', $event)"
          @toggleTeleop="emit('toggleTeleop')"
        />

        <!-- Touchoff + WCS (compact) -->
        <div class="jogSide">
          <div class="row-tight wcsRow">
            <MachineBtn
              v-for="g in g5xOptions.slice(0, 6)"
              :key="g"
              type="wcs"
              muted
              :selected="g === g5xLabel"
              @click="emit('setG5x', g)"
            >{{ g.replace('G', '') }}</MachineBtn>
          </div>

          <Gate gate="zero" class="touchoffGrid">
            <template v-for="a in primaryAxes" :key="a.letter">
              <span class="axLetter">{{ a.letter }}</span>
              <MachineInput
                gate="touchoff"
                type="number"
                :modelValue="touchoff[a.index]"
                @update:modelValue="updateTouchoff(a.index, Number($event))"
                class="touchInput"
              />
              <MachineBtn type="zero" @click="emit('setAxis', a.index, touchoff[a.index] ?? 0)">Set</MachineBtn>
            </template>
          </Gate>

          <div class="row-tight goRow">
            <MachineBtn type="goTo" @click="emit('goToG30')">G30</MachineBtn>
            <MachineBtn type="goTo" @click="emit('goToZero')">Zero</MachineBtn>
            <MachineBtn v-if="!isHomed" type="home" @click="emit('homeAll')" block>Home All</MachineBtn>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ MDI VIEW ═══ -->
    <div v-show="mode === 'mdi'" class="modeContent">
      <Gate gate="ready" class="mdiLayout">
        <div class="mdiRow">
          <MachineInput
            gate="mdiText"
            type="text"
            class="mdiInput"
            :value="mdiText"
            @input="emit('update:mdiText', ($event.target as HTMLInputElement).value)"
            @keyup.enter="handleSend"
            @keydown="onMdiKeydown"
            placeholder="G-code command..."
          />
          <MachineBtn type="mdi" @click="handleSend">Send</MachineBtn>
        </div>
        <div class="mdiHistoryHeader">
          <span class="mdiHistLabel">History</span>
          <MachineBtn type="inline" @click="clearHistory" :disabled="history.length === 0">Clear</MachineBtn>
        </div>
        <div class="mdiHistoryList scroll-thin">
          <button v-for="(cmd, i) in history" :key="i" class="mdiHistoryItem"
               :class="{ active: historyIndex === i }"
               @click="emit('update:mdiText', cmd)">{{ cmd }}</button>
          <div v-if="history.length === 0" class="mdiHistoryEmpty">No history</div>
        </div>
      </Gate>
    </div>

    <!-- ═══ PROGRAM VIEW ═══ -->
    <div v-show="mode === 'program'" class="modeContent">
      <Gate gate="safety" class="prgLayout">
        <div class="prgFile">{{ fileName }}</div>
        <div class="prgBtns">
          <MachineBtn type="start" @click="emit('cycleStart')" :disabled="!activeFile">Start</MachineBtn>
          <MachineBtn type="step" @click="emit('cycleStep')" :disabled="!activeFile">Step</MachineBtn>
          <MachineBtn
            :type="isPaused ? 'resume' : 'pause'"
            @click="isPaused ? emit('cycleResume') : emit('cyclePause')"
            :disabled="!isRunning && !isPaused"
          >{{ isPaused ? 'Resume' : 'Pause' }}</MachineBtn>
          <MachineBtn type="abort" @click="emit('abort')">Stop</MachineBtn>
        </div>
        <div class="prgStatus">
          <span class="prgElapsed">{{ elapsed }}</span>
        </div>
      </Gate>
    </div>
  </div>
</template>

<style scoped>
.modeStrip {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--gap-tight);
}
.modeTabs {
  flex-shrink: 0;
}
.modeContent {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
/* ── Jog ── */
.jogLayout {
  display: flex;
  gap: var(--gap-section);
  height: 100%;
}
.jogSide {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
  min-width: 160px;
}
.wcsRow {
  flex-wrap: wrap;
}
.touchoffGrid {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: var(--gap-tight);
  align-items: center;
}
.axLetter {
  font-weight: var(--fw-bold);
  font-size: var(--fs-sm);
}
.touchInput {
  width: 70px;
}
.goRow {
  flex-wrap: wrap;
}
/* ── MDI ── */
.mdiLayout {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
  height: 100%;
}
.mdiRow {
  display: flex;
  gap: var(--gap-tight);
}
.mdiInput {
  flex: 1;
}
.mdiHistLabel {
  font-size: var(--fs-sm);
  opacity: var(--opacity-muted);
}
.mdiHistoryHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.mdiHistoryList {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}
.mdiHistoryItem {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--gap-tight) var(--gap-controls);
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  border: none;
  background: none;
  color: inherit;
  cursor: pointer;
}
.mdiHistoryItem:hover,
.mdiHistoryItem.active {
  background: var(--hl-hover);
}
.mdiHistoryEmpty {
  padding: var(--gap-section);
  text-align: center;
  opacity: var(--opacity-muted);
  font-size: var(--fs-sm);
}
/* ── Program ── */
.prgLayout {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
}
.prgFile {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
  opacity: var(--opacity-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.prgBtns {
  display: flex;
  gap: var(--gap-tight);
  flex-wrap: wrap;
}
.prgStatus {
  display: flex;
  gap: var(--gap-controls);
  align-items: center;
}
.prgElapsed {
  font-family: var(--font-mono);
  font-size: var(--fs-sm);
}
</style>
