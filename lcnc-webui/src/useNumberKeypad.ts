// Module-level singleton — shared across all components that import this.
// No provide/inject needed: the module itself is the shared instance.
import { reactive } from 'vue';

export interface KeypadOpts {
  value: string | number | null;
  label?: string;
  trigger?: HTMLElement | null;
  onConfirm: (value: number) => void;
  onCancel?: () => void;
}

export const keypadState = reactive({
  open: false,
  label: '',
  initial: '',
  // Incremented on every openKeypad() call so the dialog can re-init even when
  // the new field's value matches the old one (e.g. switching between zeros).
  seq: 0,
  // Source input the keypad currently targets — bound to .keypad-active class
  // so the input shows a focus outline for the lifetime of the dialog.
  trigger: null as HTMLElement | null,
  onConfirm: null as ((v: number) => void) | null,
  onCancel: null as (() => void) | null,
});

export function openKeypad(opts: KeypadOpts): void {
  keypadState.label = opts.label ?? '';
  keypadState.initial = opts.value != null ? String(opts.value) : '';
  keypadState.trigger = opts.trigger ?? null;
  keypadState.onConfirm = opts.onConfirm;
  keypadState.onCancel = opts.onCancel ?? null;
  keypadState.seq++;
  keypadState.open = true;
}

export function closeKeypad(): void {
  keypadState.open = false;
  keypadState.trigger = null;
  keypadState.onConfirm = null;
  keypadState.onCancel = null;
}
