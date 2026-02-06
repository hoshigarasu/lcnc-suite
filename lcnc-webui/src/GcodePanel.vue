<script setup lang="ts">
import { computed, ref, watch, nextTick } from "vue";

const props = defineProps<{
  activeFile: string | null;
  gcodeContent: string | null;
  currentLine: number | null;
}>();

const codeViewerRef = ref<HTMLDivElement | null>(null);

const fileName = computed(() => {
  if (!props.activeFile) return "No file loaded";
  return props.activeFile.split("/").pop() || props.activeFile;
});

const lines = computed(() => {
  if (!props.gcodeContent) return [];
  return props.gcodeContent.split("\n");
});

const lineCount = computed(() => lines.value.length);

// Auto-scroll to current line
watch(() => props.currentLine, async (newLine) => {
  if (newLine !== null && codeViewerRef.value) {
    await nextTick();
    const lineElement = codeViewerRef.value.querySelector(`[data-line="${newLine}"]`);
    if (lineElement) {
      lineElement.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }
});
</script>

<template>
  <div class="container">
    <div class="header">
      <div class="fileInfo">
        <div class="label">File:</div>
        <div class="fileName">{{ fileName }}</div>
      </div>
      <div class="stats" v-if="gcodeContent">
        <span>{{ lineCount }} lines</span>
      </div>
    </div>

    <div class="codeViewer" v-if="gcodeContent" ref="codeViewerRef">
      <div class="codeLine"
           v-for="(line, index) in lines"
           :key="index"
           :data-line="index + 1"
           :class="{ active: currentLine === index + 1 }">
        <span class="lineNumber">{{ index + 1 }}</span>
        <span class="lineContent">{{ line }}</span>
      </div>
    </div>

    <div class="emptyState" v-else>
      <div class="emptyIcon">📄</div>
      <div class="emptyText">No G-code file loaded</div>
      <div class="emptyHint">Load a program to view its G-code</div>
    </div>
  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 600px;
  gap: 12px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: color-mix(in oklab, var(--panel) 50%, transparent);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.fileInfo {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.label {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.fileName {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats {
  font-size: 12px;
  opacity: 0.7;
  white-space: nowrap;
}

.codeViewer {
  flex: 1;
  min-height: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: color-mix(in oklab, var(--panel) 70%, transparent);
  overflow: auto;
  padding: 8px 0;
}

.codeLine {
  display: flex;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  padding: 2px 12px;
  transition: background-color 0.2s ease;
}

.codeLine:hover {
  background: color-mix(in oklab, var(--panel) 90%, var(--fg) 5%);
}

.codeLine.active {
  background: color-mix(in oklab, #ffa500 20%, var(--panel));
  border-left: 3px solid #ffa500;
  padding-left: 9px;
}

.lineNumber {
  display: inline-block;
  min-width: 40px;
  text-align: right;
  margin-right: 16px;
  opacity: 0.5;
  user-select: none;
  flex-shrink: 0;
}

.lineContent {
  color: var(--fg);
  white-space: pre;
  flex: 1;
}

.emptyState {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0.6;
}

.emptyIcon {
  font-size: 48px;
  opacity: 0.5;
}

.emptyText {
  font-size: 16px;
  font-weight: 600;
}

.emptyHint {
  font-size: 13px;
  opacity: 0.7;
}
</style>
