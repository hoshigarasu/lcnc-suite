<script setup lang="ts">
defineProps<{
  workPos: number[];
  machinePos: number[];
}>();

const emit = defineEmits<{
  (e: "zeroAxis", axis: number): void;
  (e: "homeAll"): void;
}>();

function fmt(n: any) {
  const x = Number(n);
  return Number.isFinite(x) ? x.toFixed(3) : "-";
}
</script>

<template>
  <div class="container">
    <div class="section">
      <div class="sub">Work Position</div>
      <div class="dro">
        <div class="axisRow">
          <div class="axis"><span>X</span><b>{{ fmt(workPos[0]) }}</b></div>
          <button class="zeroBtn" @click="emit('zeroAxis', 0)">Zero X</button>
        </div>
        <div class="axisRow">
          <div class="axis"><span>Y</span><b>{{ fmt(workPos[1]) }}</b></div>
          <button class="zeroBtn" @click="emit('zeroAxis', 1)">Zero Y</button>
        </div>
        <div class="axisRow">
          <div class="axis"><span>Z</span><b>{{ fmt(workPos[2]) }}</b></div>
          <button class="zeroBtn" @click="emit('zeroAxis', 2)">Zero Z</button>
        </div>
      </div>
    </div>

    <div class="separator"></div>

    <div class="section">
      <div class="sub">Machine Position</div>
      <div class="dro">
        <div class="axis"><span>X</span><b>{{ fmt(machinePos[0]) }}</b></div>
        <div class="axis"><span>Y</span><b>{{ fmt(machinePos[1]) }}</b></div>
        <div class="axis"><span>Z</span><b>{{ fmt(machinePos[2]) }}</b></div>
      </div>

      <button class="homeBtn" @click="emit('homeAll')">Home All Axes</button>
    </div>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub {
  font-size: 12px;
  opacity: 0.65;
  margin-bottom: 8px;
}

.dro {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.axisRow {
  display: flex;
  align-items: center;
  gap: 16px;
}

.axis {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 24px;
  min-width: 180px;
}

.axis span {
  font-size: 12px;
  opacity: 0.7;
  width: 14px;
}

.zeroBtn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--button-bg);
  color: var(--fg);
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.zeroBtn:hover {
  background: color-mix(in oklab, var(--button-bg) 85%, var(--fg));
}

.zeroBtn:active {
  transform: scale(0.98);
}

.homeBtn {
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--button-bg);
  color: var(--fg);
  cursor: pointer;
  transition: all 0.15s ease;
  margin-top: 4px;
}

.homeBtn:hover {
  background: color-mix(in oklab, var(--button-bg) 85%, var(--fg));
}

.homeBtn:active {
  transform: scale(0.98);
}

.separator {
  height: 1px;
  background: var(--border);
  opacity: 0.3;
}
</style>
