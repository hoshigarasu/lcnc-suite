import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { fetchSettings, saveSettingsSection } from './lcncApi'
import { initServerDefaults } from './defaults'

const SERVER_SECTIONS = ["macros", "machine", "viewer", "camera", "mdi"];

async function bootstrap() {
  let serverSettings: Record<string, any> = {};
  try {
    serverSettings = await fetchSettings();
  } catch {
    // Gateway unreachable — app still loads with fallback defaults
  }

  // One-time migration: localStorage → server for server sections
  try {
    const raw = localStorage.getItem("lcnc-defaults");
    if (raw) {
      const local = JSON.parse(raw);
      const migrations: Promise<void>[] = [];
      for (const key of SERVER_SECTIONS) {
        if (local[key] && !serverSettings[key]) {
          serverSettings[key] = local[key];
          migrations.push(saveSettingsSection(key, local[key]));
        }
      }
      if (migrations.length) await Promise.all(migrations);
      // Strip server sections from localStorage
      const localOnly: Record<string, any> = {};
      for (const [k, v] of Object.entries(local as Record<string, any>)) {
        if (!SERVER_SECTIONS.includes(k)) localOnly[k] = v;
      }
      localStorage.setItem("lcnc-defaults", JSON.stringify(localOnly));
    }
  } catch { /* ignore corrupt localStorage */ }

  initServerDefaults(serverSettings);
  createApp(App).mount('#app');
}

bootstrap();
