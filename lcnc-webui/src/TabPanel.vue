<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  tabs: Array<{ id: string; label: string }>;
  modelValue: string;
  badges?: Record<string, number>;
  closable?: boolean;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", id: string): void;
  (e: "close"): void;
}>();

const totalBadge = computed(() => {
  if (!props.badges) return 0;
  return Object.values(props.badges).reduce((sum, n) => sum + n, 0);
});
</script>

<template>
  <div class="tab-panel">
    <!-- Top bar: tab selector + optional close button -->
    <div class="topBar">
      <div class="tabPill">
        <span class="pillLabel">
          {{ tabs.find(t => t.id === modelValue)?.label || 'Tab' }}
          <span v-if="totalBadge" class="pillBadge">{{ totalBadge > 99 ? '99+' : totalBadge }}</span>
        </span>
        <div class="pillPopover">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="tabOption"
            :class="{ active: modelValue === tab.id }"
            @click="emit('update:modelValue', tab.id)"
          >
            {{ tab.label }}
            <span v-if="badges?.[tab.id]" class="badge">{{ badges[tab.id]! > 99 ? '99+' : badges[tab.id] }}</span>
          </button>
        </div>
      </div>
      <button v-if="closable" class="panelClose" @click="emit('close')">&times;</button>
    </div>

    <div class="tab-content">
      <template v-for="tab in tabs" :key="tab.id">
        <div v-show="modelValue === tab.id" class="tab-pane">
          <slot :name="tab.id" />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.tab-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* ---- Top bar row ---- */
.topBar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.tabPill {
  position: relative;
  flex: 1;
  min-width: 0;
  cursor: default;
}

.pillLabel {
  display: block;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 6px;
  background: color-mix(in oklab, #000 75%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #ccc;
  border: 1px solid rgba(255,255,255,0.08);
  user-select: none;
}

.tabPill:hover > .pillLabel {
  color: #fff;
  background: color-mix(in oklab, #000 85%, transparent);
}

/* ---- Popover (opens downward) ---- */
.pillPopover {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  padding: 14px 8px 8px 8px;
  border-radius: 8px;
  background: color-mix(in oklab, #000 80%, transparent);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
  z-index: 30;
  min-width: 140px;
  flex-direction: column;
  gap: 2px;
}

.tabPill:hover > .pillPopover {
  display: flex;
}

/* ---- Tab options ---- */
.tabOption {
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  color: #ddd;
  cursor: pointer;
  white-space: nowrap;
  text-align: left;
  transition: background 0.12s;
}

.tabOption:hover {
  background: rgba(255,255,255,0.15);
  color: #fff;
}

.tabOption.active {
  background: rgba(255,255,255,0.15);
  color: #fff;
  font-weight: 600;
}

.tabOption:active {
  transform: scale(0.97);
}

/* ---- Close button ---- */
.panelClose {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.08);
  background: color-mix(in oklab, #000 75%, transparent);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #ccc;
  font-size: 16px;
  cursor: pointer;
  opacity: 0.5;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.15s;
}

.panelClose:hover {
  opacity: 1;
  color: #fff;
}

/* ---- Content ---- */
.tab-content {
  flex: 1;
  min-height: 660px;
}

.tab-pane {
  height: 100%;
}

/* ---- Badges ---- */
.pillBadge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  margin-left: 5px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 700;
  background: #b00020;
  color: #fff;
  line-height: 1;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 6px;
  border-radius: 9px;
  font-size: 10px;
  font-weight: 700;
  background: #b00020;
  color: #fff;
  line-height: 1;
}
</style>
