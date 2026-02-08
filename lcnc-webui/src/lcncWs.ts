import { ref, shallowRef } from "vue";

export const connected = ref(false);
export const status = shallowRef<any>(null);
export const lastReply = ref<any>(null);
export const lcncError = ref<string | null>(null);

export const viewerInit = ref<any>(null);
export const viewerGcode = ref<any>(null);


let ws: WebSocket | null = null;

export function connectWs() {
  const host = (location.hostname === "localhost") ? "127.0.0.1" : location.hostname;
  const wsUrl = `ws://${host}:8000/ws`;
  ws = new WebSocket(wsUrl);


  ws.onopen = () => (connected.value = true);
  ws.onclose = () => (connected.value = false);

  let _pendingStatus: any = null;
  let _flushScheduled = false;

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);

    if (msg.type === "status") {
      // Buffer status as plain data — flush to reactive ref once per rAF.
      // When messages queue up, only the latest triggers Vue reactivity.
      _pendingStatus = msg;
      lcncError.value = null;
      if (!_flushScheduled) {
        _flushScheduled = true;
        requestAnimationFrame(() => {
          _flushScheduled = false;
          if (_pendingStatus) {
            status.value = _pendingStatus;
            _pendingStatus = null;
          }
        });
      }
    } else if (msg.type === "status_error") {
      lcncError.value = msg.error;
    } else if (msg.type === "reply") {
      lastReply.value = msg;
    } else if (msg.type === "viewer_init") {
      console.log("viewer_init", msg.data);
      viewerInit.value = msg.data;
    } else if (msg.type === "viewer_gcode") {
      viewerGcode.value = msg.data;
    } else {
      console.debug("WS msg", msg);
    }
  };


  ws.onerror = (e) => {
    console.error("WS error", e);
  };
}

export function send(obj: any) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}
