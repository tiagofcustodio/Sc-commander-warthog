# 🚀 Star Citizen — Warthog Commander PRO (v5.4 UEE MIL-GLASS)

> **☕ If you like this project, buy me a coffee:** [https://paypal.me/tcustodio](https://paypal.me/tcustodio)  
> **📦 GitHub Repository:** [https://github.com/tiagofcustodio/Sc-commander-warthog](https://github.com/tiagofcustodio/Sc-commander-warthog)

Tactical Command Center, intelligent DirectInput hardware bridge, interactive dual-joystick visual mapping studio, and automatic `actionmaps.xml` fixer for **Star Citizen 4.x**, with full **Multi-HOTAS** support:

* **Thrustmaster:** HOTAS Warthog (A-10C 19-Button Stick + 32-Button Dual Throttle + 5 HID Base LEDs), T.16000M FCS + TWCS Throttle, TCA Officer Pack Airbus, T.Flight HOTAS (X / 4 / One), HOTAS Cougar & Viper TQS.
* **Saitek / Logitech G:** X56 Rhino HOTAS (17-Button Stick + 32-Button Dual Throttle).

---

## ✨ Key Features

* **Star Citizen UEE / Aegis Military-Grade Glass UI:** Anodized gunmetal frosted glass panels, 45° chamfered MFD geometry, and high-contrast cockpit cyan & avionics amber readouts.
* **Interactive Dual-Joystick Visual Mapping:** Automatically switches visual schematics to match your physically connected USB stick & throttle (including mixed setups!), featuring an animated **HUD Target-Lock Reticle** that points directly to each physical button on hover or hardware press.
* **Key & Mouse Button Editor (`MOUSE1`–`MOUSE5`, `MWHEEL_UP/DOWN`):** Live key/mouse capture with modifier support (`ALT`, `CTRL`, `SHIFT`), configurable pulse duration, and instant 1-click editing.
* **Dual-Action Buttons (*Short Tap vs Long Press / Hold*):** Assign two independent actions or macros to the same physical button with a customizable hold threshold (`250ms–1200ms`), with zero latency on buttons without a hold action.
* **Multi-Step Macro Studio:** Build custom timed sequences (includes ready-to-use presets: *Full Landing Sequence*, *Combat Ready*, and *Quantum Jump Prep*) and bind them to any button.
* **Ship AI Voice (*Aegis / Anvil Cockpit Computer*):** Real-time voice callouts for ship systems (Landing Gear, VTOL, Master Modes, Flight Ready, Headlights, ATC, Doors, Macros, and Profiles) in English or Portuguese.
* **Auto-Doctor (`actionmaps.xml` Fixer):** Automatically diagnoses and resolves known Star Citizen HOTAS axis conflicts (`js2_rotz` vs Speed Limiter), generates `layout_warthog_sc_fixed.xml`, and creates backups.
* **5 Physical Base LEDs & Backlight Control (Warthog):** Real-time HID synchronization for Master Mode, Landing Gear, VTOL, Headlights, and Quantum Drive.
* **Automatic Updates with Safe Backups:** Background update checks against GitHub with automatic ZIP backups that always preserve your `config.json`.

---

## 🔍 Why Do Warthog Thrusters Often Fail in Star Citizen?

Analysis of Star Citizen's `actionmaps.xml` and Thrustmaster HOTAS Warthog hardware reveals **4 root causes** that this program resolves automatically:

1. **Dual Throttle Axis Conflict (`js2_rotz` vs `js2_z`):**
   - On the Warthog Dual Throttle, the **Right Lever** is `js2_rotz` (`Rz`) and the **Left Lever** is `js2_z` (`Z`). When linked together, moving the throttle moves both axes simultaneously.
   - Default/corrupted `actionmaps.xml` files often bind `js2_rotz` to `v_ifcs_speed_limiter_rel` with an extreme curve, pinning ship speed to `0 m/s`.
   - **Fix:** Unbinds `js2_rotz` from Speed Limiter, maps both levers linearly (`invert="1"`, `exponent="1.0"`) to propulsion, and moves the **Speed Limiter / Mining Laser Power** to the center grey friction wheel (`js2_slider1`).
2. **Physical Idle Cutoff Detents (Buttons 29 & 30):**
   - Pulling the levers behind the physical `OFF` detent holds **Buttons 29 & 30** continuously pressed, which can double-trigger engine power toggles (`I`) or block axis binding.
   - **Fix:** Smart **350ms debounce** sends a single clean pulse when entering/exiting Idle Cutoff.
3. **Windows `winmm` Ghost Slots:**
   - Validates every USB slot with `joyGetPosEx` (ignoring disconnected registry ghosts and gamepads) and reads real `OEMName` + `VID/PID` from the Windows Registry.
4. **Automatic Administrator Elevation (`run.bat`):**
   - Automatically requests UAC elevation so `actionmaps.xml` inside `C:\Program Files\Roberts Space Industries\StarCitizen\LIVE` can be repaired and backed up cleanly.

---

## 🕹️ Default HOTAS Warthog Mapping Reference

### 1. A-10C Flight Stick (`js1` — 19 Buttons + POV Hat + 2 Axes)

| Physical Control | SC Input | Primary Star Citizen Action | Shift Layer (`S4 Pinky Lever` Held) |
| :--- | :--- | :--- | :--- |
| **X Axis** | `js1_x` | **Roll** (Ship Roll / Turret Yaw) | — |
| **Y Axis** | `js1_y` | **Pitch** (Ship Pitch / Turret Pitch) | — |
| **POV1 Hat (Trim Hat)** | `js1_hat1_*` | **Power Triangle:** `Up`=Engines (`F6`), `Right`=Shields (`F7`), `Left`=Weapons (`F5`), `Down`=Reset (`F8`) | — |
| **Button 1 (TG1 — Stage 1)** | `js1_button1` | Fire Weapon Group 1 / Mining Laser / Scan | — |
| **Button 6 (TG2 — Stage 2)** | `js1_button6` | Fire Weapon Group 2 (Full Salvo) | — |
| **Button 2 (S2 — Weapon Release)** | `js1_button2` | Lock / Launch Missile / Toggle Laser Mode | **Alt+J** (Jettison Volatile Cargo) |
| **Button 3 (S3 — Nosewheel)** | `js1_button3` | Cycle Gimbal Mode / Match Target Velocity | Cycle Active Profile |
| **Button 4 (S4 — Pinky Lever)** | `js1_button4` | **GLOBAL SHIFT MODIFIER** + Toggle Decoupled (`Alt+C`) | — |
| **Button 5 (S1 — Master Mode)** | `js1_button5` | Hold: Toggle Master Mode **SCM ↔ NAV** (`B`) | **K** (Toggle VTOL) |
| **Buttons 7–10 (TMS Hat)** | `js1_button7..10` | `7 Up`: Target Under Reticle (`T`) · `8 Right`: Next Hostile (`5`) · `9 Down`: Nearest Hostile (`4`) · `10 Left`: Prev Hostile | `7`: Next Sub-target (`8`) · `8`: Next Friendly (`6`) · `9`: Reset Sub-target (`Alt+8`) |
| **Buttons 11–14 (DMS Hat)** | `js1_button11..14` | `11 Up`: Radar Ping (`Tab`) · `12 Right`: Next Target (`7`) · `13 Down`: Balance Shields (`Num5`) · `14 Left`: Prev Target | Shield Reinforcement (`Num8/6/2/4`) |
| **Buttons 15–19 (CMS Hat + Push)** | `js1_button15..19` | `15 Up`: Noise Field (`J`) · `16 Right`: +Decoy Burst · `17 Down`: Launch Decoy (`H`) · `18 Left`: -Decoy Burst · `19 Push`: Panic Salvo | `16`: Arm More Missiles (`G`) · `18`: Reset Missiles (`Alt+G`) |

### 2. Dual Throttle (`js2` — 32 Buttons + Coolie Hat + 5 Axes)

| Physical Control | SC Input | Star Citizen Function (XML + Pulse Engine) |
| :--- | :--- | :--- |
| **Left Lever (Z Axis)** | `js2_z` | **Longitudinal Propulsion / Main Throttle** (`invert="1"`, linear) |
| **Right Lever (Rz Axis)** | `js2_rotz` | **Synchronized Absolute Throttle** (works linked or split) |
| **Center Grey Wheel (Slider 1)** | `js2_slider1` | **Absolute Speed Limiter** + **Mining Laser Power** |
| **Slew Mini-Stick (X / Y)** | `js2_x` / `js2_y` | **Analog Lateral Strafe** & **Vertical Strafe** |
| **Coolie Hat (POV1)** | `js2_hat1_*` | **Yaw Left/Right** + **Vertical Strafe Up/Down** |
| **Button 1 (Slew Push)** | `js2_button1` | Match Target Speed / Interaction (`F`) |
| **Buttons 2–6 (MIC Switch)** | `js2_button2..6` | `2 Push`: VOIP PTT (`Num+`) · `3 Up`: Scan (`V`) · `4 Right`: 3rd Person Camera (`F4`) · `5 Down`: Mining/Salvage (`M`) |
| **Buttons 7–8 (Speedbrake)** | `js2_button7..8` | `7 FWD`: **Cruise Control (`C`)** · `8 AFT (Spring)`: **Space Brake (`X`)** |
| **Buttons 9–10 (Boat Switch)** | `js2_button9..10` | `9 FWD`: **Quantum / NAV Mode (`B`)** [LED 5] · `10 AFT`: **SCM / Weapons (`B`)** |
| **Buttons 11–12 (China Hat)** | `js2_button11..12` | `11 FWD (Red)`: **Boost / Afterburner (`LShift`)** · `12 AFT`: **Reverse Thrust (`S`)** |
| **Buttons 13–14 (Pinky Switch)** | `js2_button13..14` | `13 FWD`: **Exterior Headlights (`L`)** [LED 4] · `Center`: Lights Off · `14 AFT`: Cabin Lights |
| **Button 15 (Left Throttle Btn)** | `js2_button15` | **Flight Ready (`Alt+R`)** / Autoland (`N`) |
| **Buttons 16–17 (Fuel Flow L/R)** | `js2_button16..17` | `16 Left`: **Thrusters Power ON/OFF (`I`)** · `17 Right`: **Weapons Power ON/OFF (`P`)** |
| **Buttons 18 / 31 (ENG OPER L)** | `js2_button18,31` | `31 IGN`: **Wipe Visor (`Alt+X`)** · `18 MOTOR`: **Thrusters OFF (`I`)** |
| **Buttons 19 / 32 (ENG OPER R)** | `js2_button19,32` | `32 IGN`: **Eject (`Alt+Y`)** · `19 MOTOR`: **Weapons OFF (`P`)** |
| **Button 20 (APU START / OFF)** | `js2_button20` | `START`: **Flight Ready (`Alt+R`)** · `OFF`: **Power Off (`U`)** |
| **Button 21 (LDG HORN Silence)** | `js2_button21` | **Call ATC / Request Landing (`Alt+N`)** |
| **Buttons 22–23 (FLAPS)** | `js2_button22..23` | `22 UP`: **Cruise Control (`C`)** · `23 DOWN`: **VTOL / Hover (`K`)** [LED 3] |
| **Button 24 (EAC ARM / OFF)** | `js2_button24` | **Master Mode / Power Toggle** [LED 1] |
| **Button 25 (RDR ALTM)** | `js2_button25` | `NRM`: **Retract Landing Gear (`N`)** · `DIS`: **Deploy Landing Gear (`N`)** [LED 2] |
| **Button 26 (Autopilot Engage)** | `js2_button26` | **Call ATC (`Alt+N`)** |
| **Buttons 27–28 (AP PATH / ALT)** | `js2_button27..28` | `27 PATH`: **Open All Doors (`Alt+K`)** · `28 ALT`: **Lock All Doors (`Alt+L`)** |
| **Buttons 29–30 (Idle Cutoff)** | `js2_button29..30` | **Physical Engine Cutoff (`I`) with 350ms Debounce** |

---

## ▶️ Quick Start

1. Double-click **`run.bat`** (automatically requests Administrator privileges so it can repair `actionmaps.xml` inside `C:\Program Files\Roberts Space Industries\StarCitizen\LIVE`).
2. The **Warthog Commander PRO** dashboard opens automatically in your browser:
   - Automatically detects your connected Thrustmaster or Saitek X56 joysticks and switches the visual map images.
   - Repairs `actionmaps.xml` and installs `layout_warthog_sc_fixed.xml` into Star Citizen's `controls\mappings` folder.
   - In-game console (`~`): run `pp_rebindkeys layout_warthog_sc_fixed` to load the profile immediately.

---

## ☕ Support

If this tool improves your Star Citizen flights, consider buying me a coffee!  
👉 **[https://paypal.me/tcustodio](https://paypal.me/tcustodio)**
