# Example Sim Config

A minimal LinuxCNC sim configuration for lcnc-suite. Copy to your LinuxCNC configs directory and adjust paths.

## Setup

```bash
cp -r examples/sim_config ~/linuxcnc/configs/lcnc_suite_sim
```

Edit `lcnc_suite_sim.ini`:
- Set `SUBROUTINE_PATH` to your lcnc-suite clone location

Edit `hallib/lcnc_webui.hal`:
- Set path to `hal_watchdog.py`
- Uncomment surface compensation if needed
- Adjust the estop unlinkp if your config uses a different signal name

## Key files

- `lcnc_suite_sim.ini` — INI with all required RS274NGC, HAL, and display settings
- `hallib/lcnc_webui.hal` — HAL wiring for safety watchdog, e-stop chain, tool change, compensation
- Other HAL files — sim-specific (homing, spindle, etc.)
