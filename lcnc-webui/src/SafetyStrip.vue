<script setup lang="ts">
import { computed } from "vue";
import Gate from "./Gate.vue";
import MachineBtn from "./MachineBtn.vue";
import { Lock, LockOpen, TriangleAlert, Power } from "lucide-vue-next";

const props = defineProps<{
  armed: boolean;
  busy: boolean;
  isEstop: boolean;
  isEnabled: boolean;
  isHomed: boolean;
  canEstop: boolean;
  canResetEstop: boolean;
}>();

const emit = defineEmits<{
  (e: "arm", value: boolean): void;
  (e: "estop"): void;
  (e: "estopReset"): void;
  (e: "machineOn"): void;
  (e: "machineOff"): void;
}>();

const estopLabel = computed(() => props.isEstop ? "Reset" : "E-Stop");
</script>

<template>
  <div class="safetyStrip">
    <Gate gate="always">
      <div class="safetyBtns">
        <MachineBtn
          type="arm"
          :variant="armed ? 'ok' : 'default'"
          :disabled="busy"
          :title="armed ? 'Disarm' : 'Arm'"
          @click="emit('arm', !armed)"
          block
        >
          <component :is="armed ? LockOpen : Lock" class="safetyIcon" />
        </MachineBtn>

        <MachineBtn
          type="estop"
          :flashing="isEstop"
          :disabled="!(isEstop ? canResetEstop : canEstop)"
          @click="isEstop ? emit('estopReset') : emit('estop')"
        >
          <TriangleAlert class="safetyIcon" />
          <span class="safetyLabel">{{ estopLabel }}</span>
        </MachineBtn>
      </div>
    </Gate>

    <Gate gate="safety">
      <MachineBtn
        type="machineOn"
        :variant="isEnabled ? 'ok' : 'default'"
        @click="isEnabled ? emit('machineOff') : emit('machineOn')"
        block
      >
        <Power class="safetyIcon" />
        <span class="safetyLabel">{{ isEnabled ? "On" : "Off" }}</span>
      </MachineBtn>
    </Gate>

    <div class="stripStatus">
      <div class="statusItem">
        <span class="statusDot" :class="{ on: !isEstop }"></span>
        <span class="statusLabel">E-Stop</span>
      </div>
      <div class="statusItem">
        <span class="statusDot" :class="{ on: isEnabled }"></span>
        <span class="statusLabel">Enabled</span>
      </div>
      <div class="statusItem">
        <span class="statusDot" :class="{ on: isHomed }"></span>
        <span class="statusLabel">Homed</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.safetyStrip {
  display: flex;
  flex-direction: column;
  gap: var(--gap-controls);
  align-items: stretch;
  min-width: 80px;
  max-width: 100px;
}
.safetyBtns {
  display: flex;
  flex-direction: column;
  gap: var(--gap-tight);
}
.safetyIcon {
  width: var(--fs-xl);
  height: var(--fs-xl);
}
.safetyLabel {
  font-size: var(--fs-2xs);
}
.stripStatus {
  display: flex;
  flex-direction: column;
  gap: var(--gap-micro);
  padding-top: var(--gap-tight);
  border-top: 1px solid var(--border);
}
.statusItem {
  display: flex;
  align-items: center;
  gap: var(--gap-tight);
}
.statusDot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--danger);
  flex-shrink: 0;
}
.statusDot.on {
  background: var(--ok);
}
.statusLabel {
  font-size: var(--fs-2xs);
  opacity: var(--opacity-muted);
  white-space: nowrap;
}
</style>
