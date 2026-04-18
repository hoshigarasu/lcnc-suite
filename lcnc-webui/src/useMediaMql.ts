import { onMounted, onUnmounted, ref, type Ref } from "vue";

/**
 * Reactive wrapper around window.matchMedia().
 *
 * Returns a Ref<boolean> that updates whenever the media query match state
 * changes. The MQL listener is attached in onMounted and removed in
 * onUnmounted so callers do not need to manage lifecycle.
 *
 * @param query   MediaQueryList query string (e.g. "(prefers-color-scheme: dark)")
 * @param onChange Optional side-effect callback invoked when the match state flips
 */
export function useMediaMql(
  query: string,
  onChange?: (matches: boolean) => void,
): Ref<boolean> {
  const mql = window.matchMedia(query);
  const matches = ref(mql.matches);
  function handler() {
    matches.value = mql.matches;
    onChange?.(mql.matches);
  }
  onMounted(() => mql.addEventListener("change", handler));
  onUnmounted(() => mql.removeEventListener("change", handler));
  return matches;
}
