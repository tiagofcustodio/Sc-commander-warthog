"""
Switch Engine - Logic & State Transition Engine
Processa todas as transições físicas dos interruptores do Warthog segundo as tabelas oficiais
da Thrustmaster (VID_044F&PID_0402.dev para o Manche de 19 botões e VID_044F&PID_0404.dev
para a Manete de 32 botões), Camada Shift no Pinky Lever (Botão 4), Debounce Inteligente do
Duplo Detentor Idle Cutoff (Botões 29/30), Detetor de Pós-Combustão e Sincronização dos 5 LEDs.
"""

import time
import threading
from typing import Callable, Optional
from warthog_constants import STICK_BUTTONS, THROTTLE_BUTTONS
from input_sender import send_key_pulse, send_key_state
from warthog_leds import WarthogLEDController


class SwitchEngine:
    """Motor de transição, pulsos momentâneos, camada Shift, Macros e Ação Dupla (Tap/Hold)."""

    def __init__(self, mappings: dict, default_hold_ms: int = 60, led_controller: Optional[WarthogLEDController] = None, macros: Optional[dict] = None):
        self.mappings = mappings
        self.default_hold_ms = default_hold_ms
        self.led_controller = led_controller or WarthogLEDController()
        self.macros: dict = macros or {}

        # Dual-Action (Tap Curto vs Pressão Longa)
        self._hold_timers: dict[str, threading.Timer] = {}
        self._hold_fired: dict[str, bool] = {}
        self._hold_lock = threading.Lock()

        # Callbacks
        self.on_action_triggered: Optional[Callable[[str, str, str], None]] = None
        self.on_shift_change: Optional[Callable[[bool], None]] = None
        self.on_afterburner_change: Optional[Callable[[bool], None]] = None
        self.on_profile_cycle_requested: Optional[Callable[[], None]] = None

        # Estado da Camada Shift (Pinky Lever - Botão 4 do Manche)
        self.shift_active = False

        # Estado de Pós-Combustão (Afterburner Detent no eixo Z desativado para evitar LSHIFT preso / Shift+Z)
        self.afterburner_enabled = False
        self.afterburner_active = False
        self.afterburner_threshold = 5500  # Eixo Z/Rz próximo de 0 (avanço > 92%)
        send_key_state("LSHIFT", False)

        # Anti-duplo disparo para quando as duas manetes (Botões 29 e 30) saem/entram no Cutoff unidas
        self._last_cutoff_event_time = 0.0
        self._last_cutoff_state: Optional[bool] = None

        # Estados dos Sistemas de Voo para os 5 LEDs físicos da Manete
        self.flight_state = {
            "nav_mode": False,       # LED 1 (EAC / Master Mode)
            "gear_down": False,      # LED 2 (RDR ALTM - Trem de Aterragem)
            "vtol_on": False,        # LED 3 (Flaps Down - VTOL)
            "lights_on": False,      # LED 4 (Pinky FWD - Faróis)
            "quantum_spool": False,  # LED 5 (Boat FWD - Quantum)
        }

        # Rastreio de estados dos 7 interruptores de 3-posições
        self._3way_states = {
            "speedbrake": None,
            "boat": None,
            "pinky": None,
            "eng_l": None,
            "eng_r": None,
            "flaps": None,
            "ap_mode": None,
        }

    def update_mappings(self, new_mappings: dict, hold_ms: int, afterburner_enabled: bool = False):
        self.mappings = new_mappings
        self.default_hold_ms = hold_ms
        if self.afterburner_active:
            self.afterburner_active = False
            send_key_state("LSHIFT", False)
            if self.on_afterburner_change:
                self.on_afterburner_change(False)
        self.afterburner_enabled = False

    def handle_axis_event(self, device: str, axis_name: str, value: int):
        """Desativado: Não injeta LSHIFT no eixo Z para evitar conflitos Shift+Z."""
        if self.afterburner_active:
            self.afterburner_active = False
            send_key_state("LSHIFT", False)
            if self.on_afterburner_change:
                self.on_afterburner_change(False)
        return

    def handle_hat_event(self, device: str, direction: str):
        """Processa movimentos dos POV Hats (Trim Hat do Manche e Coolie Hat da Manete) usando os mapeamentos editáveis."""
        if direction == "CENTER":
            return

        if device == "stick":
            hat_map = {
                "UP": ("TRIM_HAT_UP", "F6", "Capacitor: Energia Máxima aos Propulsores (F6)"),
                "RIGHT": ("TRIM_HAT_RIGHT", "F7", "Capacitor: Energia Máxima aos Escudos (F7)"),
                "LEFT": ("TRIM_HAT_LEFT", "F5", "Capacitor: Energia Máxima às Armas (F5)"),
                "DOWN": ("TRIM_HAT_DOWN", "F8", "Capacitor: Equilibrar Energia (F8)"),
            }
            if direction in hat_map:
                act_id, default_key, default_desc = hat_map[direction]
                if act_id in self.mappings:
                    self._dispatch_action(act_id, default_desc)
                else:
                    send_key_pulse(default_key, [], self.default_hold_ms)
                    if self.on_action_triggered:
                        self.on_action_triggered(act_id, default_key, default_desc)

        elif device == "throttle":
            coolie_desc = {
                "UP": ("COOLIE_UP", "Strafe Up", "Propulsor Vertical: Subir"),
                "DOWN": ("COOLIE_DOWN", "Strafe Down", "Propulsor Vertical: Descer"),
                "LEFT": ("COOLIE_LEFT", "Yaw Left", "Guiada: Esquerda"),
                "RIGHT": ("COOLIE_RIGHT", "Yaw Right", "Guiada: Direita"),
            }
            if direction in coolie_desc:
                act_id, key_lbl, desc = coolie_desc[direction]
                if act_id in self.mappings and self.mappings[act_id].get("key", "").strip():
                    self._dispatch_action(act_id, desc)
                elif self.on_action_triggered:
                    self.on_action_triggered(act_id, key_lbl, desc)

    def handle_button_event(self, device: str, button: int, is_down: bool):
        """Processa todos os botões do Manche (1 a 19) e da Manete (1 a 32)."""

        # ======================================================================
        # 1. MANCHE A-10C (STICK - Botões 1 a 19 segundo VID_044F&PID_0402.dev)
        # ======================================================================
        if device == "stick":
            if button == 4:
                # S4 (Pinky Lever) = Modificador Shift Global
                self.shift_active = is_down
                if self.on_shift_change:
                    self.on_shift_change(is_down)
                if is_down and self.on_action_triggered:
                    self.on_action_triggered("SHIFT_MODIFIER_ON", "S4 PINKY (HOLD)", "Camada Shift Ativada")
                return

            if self.shift_active and is_down:
                if button == 3:
                    # S4 (Shift) + S3 (BTN 3) = Ciclar Perfil de Atividade (Combate -> Mineração -> Carga -> Terrestre)
                    if self.on_profile_cycle_requested:
                        self.on_profile_cycle_requested()
                    return

                shift_combos = {
                    2: ("S2_SHIFT", "J", ["ALT"], "Ejetar Carga / Jettison Cargo (Alt+J)"),
                    5: ("S1_SHIFT", "K", [], "Alternar Modo VTOL (K)"),
                    7: ("TMS_UP_SHIFT", "8", [], "Sub-Target: Próximo Sub-componente (8)"),
                    8: ("TMS_RIGHT_SHIFT", "6", [], "Selecionar Próximo Aliado (6)"),
                    9: ("TMS_DOWN_SHIFT", "8", ["ALT"], "Reset Sub-componente (Alt+8)"),
                    11: ("DMS_UP_SHIFT", "NUM8", [], "Reforçar Escudo Frontal (Num 8)"),
                    12: ("DMS_RIGHT_SHIFT", "NUM6", [], "Reforçar Escudo Direito (Num 6)"),
                    13: ("DMS_DOWN_SHIFT", "NUM2", [], "Reforçar Escudo Traseiro (Num 2)"),
                    14: ("DMS_LEFT_SHIFT", "NUM4", [], "Reforçar Escudo Esquerdo (Num 4)"),
                    16: ("CMS_RIGHT_SHIFT", "G", [], "Aumentar Mísseis Armados (G)"),
                    18: ("CMS_LEFT_SHIFT", "G", ["ALT"], "Reset Mísseis Armados (Alt+G)"),
                }
                if button in shift_combos:
                    act_id, default_key, default_mods, default_desc = shift_combos[button]
                    if act_id in self.mappings:
                        self._dispatch_action(act_id, f"[SHIFT] {default_desc}")
                    else:
                        send_key_pulse(default_key, default_mods, self.default_hold_ms)
                        if self.on_action_triggered:
                            mod_str = "+".join(default_mods) + "+" if default_mods else ""
                            self.on_action_triggered(act_id, f"{mod_str}{default_key}", f"[SHIFT] {default_desc}")
                    return

            if button in STICK_BUTTONS:
                info = STICK_BUTTONS[button]
                act_id = f"STICK_BTN_{button}"
                self._handle_dual_action(f"stick_{button}", is_down, act_id, info["desc"], fallback_name=info["name"])
            return

        # ======================================================================
        # 2. MANETE DUPLA (THROTTLE - Botões 1 a 32 segundo VID_044F&PID_0404.dev)
        # ======================================================================
        if device != "throttle":
            return

        # --- A. DETENTORES FÍSICOS IDLE CUTOFF (Botão 29 = Dir IDLEROFF, Botão 30 = Esq IDLELOFF) ---
        if button in (29, 30):
            now = time.time()
            if (now - self._last_cutoff_event_time < 0.35) and (self._last_cutoff_state == is_down):
                return
            self._last_cutoff_event_time = now
            self._last_cutoff_state = is_down

            if button == 30:
                action_id = "IDLE_L_OFF" if is_down else "IDLE_L_IDLE"
                label = "Manete Esq. em CUTOFF (Motores OFF)" if is_down else "Manete Esq. em IDLE (Arranque Propulsores)"
            else:
                action_id = "IDLE_R_OFF" if is_down else "IDLE_R_IDLE"
                label = "Manete Dir. em CUTOFF (Motores OFF)" if is_down else "Manete Dir. em IDLE (Arranque Propulsores)"

            self._dispatch_action(action_id, label)
            return

        # --- B. INTERRUPTORES DE 2 POSIÇÕES DA BASE (2-WAY TOGGLES) ---
        if button == 16:  # EFLNORM (Engine Fuel Left NORM)
            action_id = "FUEL_L_ON" if is_down else "FUEL_L_OFF"
            self._dispatch_action(action_id, f"Fuel Left {'NORM (Propulsores ON)' if is_down else 'OVERRIDE (Propulsores OFF)'}")

        elif button == 17:  # EFRNORM (Engine Fuel Right NORM)
            action_id = "FUEL_R_ON" if is_down else "FUEL_R_OFF"
            self._dispatch_action(action_id, f"Fuel Right {'NORM (Armas ON)' if is_down else 'OVERRIDE (Armas OFF)'}")

        elif button == 20:  # APUON (APU Start / Off)
            action_id = "APU_ON" if is_down else "APU_OFF"
            self._dispatch_action(action_id, f"APU Switch {'START (Flight Ready)' if is_down else 'OFF (Power Off)'}")

        elif button == 24:  # EACON (EAC ARM / OFF) -> Controla LED 1!
            action_id = "EAC_ON" if is_down else "EAC_OFF"
            self.flight_state["nav_mode"] = is_down
            self._update_leds()
            self._dispatch_action(action_id, f"EAC {'ARM [LED 1 ON]' if is_down else 'OFF [LED 1 OFF]'}")

        elif button == 25:  # RDRNRM (RDR ALTM NRM / DIS) -> Controla LED 2!
            action_id = "RDR_ALTM_ON" if is_down else "RDR_ALTM_OFF"
            self.flight_state["gear_down"] = not is_down  # DIS (baixo) = Trem descido (LED 2 aceso)
            self._update_leds()
            self._dispatch_action(action_id, f"RDR ALTM {'NRM (Recolher Trem)' if is_down else 'DIS (Baixar Trem) [LED 2 ON]'}")

        elif button == 21:  # LDGH (Landing Gear Horn Silence - Botão Vermelho Base)
            self._handle_dual_action("throttle_21", is_down, "LDGHORN_PRESS", "Chamar Torre ATC / Pedir Aterragem (Alt+N)")

        elif button == 26:  # APENG (Botão Autopilot Engage/Disengage)
            self._handle_dual_action("throttle_26", is_down, "AP_ENGAGE_PRESS", "Autopilot Engage: Chamar ATC / Aterragem (Alt+N)")

        # --- C. INTERRUPTORES DE 3 POSIÇÕES (3-WAY TOGGLES COM CENTRO SINTETIZADO) ---
        elif button in (22, 23):  # FLAPS (FLAPU=22, FLAPD=23, FLAPM=Centro) -> Controla LED 3!
            self.flight_state["vtol_on"] = (button == 23 and is_down)
            self._update_leds()
            self._handle_3way("flaps", button, is_down, btn_a=22, btn_b=23,
                              act_a="FLAPS_UP", act_b="FLAPS_DN", act_mid="FLAPS_MID",
                              name_a="Flaps UP (Cruise)", name_b="Flaps DN (VTOL) [LED 3 ON]", name_mid="Flaps MVR (Voo Normal)")

        elif button in (13, 14):  # PINKY SWITCH (PSF=13, PSB=14, PSM=Centro) -> Controla LED 4!
            self.flight_state["lights_on"] = (button == 13 and is_down)
            self._update_leds()
            self._handle_3way("pinky", button, is_down, btn_a=13, btn_b=14,
                              act_a="PINKY_FWD", act_b="PINKY_AFT", act_mid="PINKY_MID",
                              name_a="Pinky FWD (Faróis ON) [LED 4 ON]", name_b="Pinky AFT (Luzes Cabine)", name_mid="Pinky MID (Faróis OFF)")

        elif button in (9, 10):  # BOAT SWITCH (BSF=9, BSB=10, BSM=Centro) -> Controla LED 5!
            self.flight_state["quantum_spool"] = (button == 9 and is_down)
            self._update_leds()
            self._handle_3way("boat", button, is_down, btn_a=9, btn_b=10,
                              act_a="BOAT_FWD", act_b="BOAT_AFT", act_mid="BOAT_MID",
                              name_a="Boat FWD (Quantum Mode) [LED 5 ON]", name_b="Boat AFT (SCM / Armas)", name_mid="Boat MID (Neutro)")

        elif button in (7, 8):  # SPEED BRAKE (SPDF=7 Fixo, SPDB=8 Mola, SPDM=Centro)
            if button == 8:
                spd_map = self.mappings.get("SPDBRK_AFT", {"key": "X", "modifiers": [], "desc": "Space Brake Ativo (Travão Espacial)"})
                spd_key = spd_map.get("key", "X").strip()
                spd_mods = spd_map.get("modifiers", [])
                spd_desc = spd_map.get("desc", "Space Brake Ativo (Travão Espacial)")

                if not spd_key:
                    if is_down and self.on_action_triggered:
                        self.on_action_triggered("SPDBRK_AFT", "Desativado", spd_desc)
                elif spd_key.upper() in ("MWHEEL_UP", "MWHEEL_DOWN") or spd_mods:
                    if is_down:
                        self._dispatch_action("SPDBRK_AFT", spd_desc)
                else:
                    send_key_state(spd_key, is_down)
                    if is_down and self.on_action_triggered:
                        self.on_action_triggered("SPDBRK_AFT", f"{spd_key} (HOLD)", spd_desc)
                    elif not is_down and self.on_action_triggered:
                        self.on_action_triggered("SPDBRK_RELEASE", f"{spd_key} (RELEASE)", f"{spd_desc} — Libertado")
            else:
                self._handle_3way("speedbrake", button, is_down, btn_a=7, btn_b=8,
                                  act_a="SPDBRK_FWD", act_b="SPDBRK_AFT", act_mid="SPDBRK_MID",
                                  name_a="Speedbrake FWD (Cruise Control)", name_b="Speedbrake AFT (Space Brake)", name_mid="Speedbrake Neutro")

        elif button in (31, 18):  # ENGINE OPER LEFT (EOLIGN=31 Cima Mola, EOLMOTOR=18 Baixo Fixo, EOLNORM=Centro)
            self._handle_3way("eng_l", button, is_down, btn_a=31, btn_b=18,
                              act_a="ENG_L_IGN", act_b="ENG_L_MOTOR", act_mid="ENG_L_NORM",
                              name_a="Eng L IGN (Limpar Visor Alt+X)", name_b="Eng L MOTOR (Motores OFF)", name_mid="Eng L NORM (Motores ON)")

        elif button in (32, 19):  # ENGINE OPER RIGHT (EORIGN=32 Cima Mola, EORMOTOR=19 Baixo Fixo, EORNORM=Centro)
            self._handle_3way("eng_r", button, is_down, btn_a=32, btn_b=19,
                              act_a="ENG_R_IGN", act_b="ENG_R_MOTOR", act_mid="ENG_R_NORM",
                              name_a="Eng R IGN (Armas)", name_b="Eng R MOTOR (Armas OFF)", name_mid="Eng R NORM (Armas ON)")

        elif button in (27, 28):  # AUTOPILOT MODE (APPAT=27 Cima, APALT=28 Baixo, APAH=Centro)
            self._handle_3way("ap_mode", button, is_down, btn_a=27, btn_b=28,
                              act_a="AP_PATH", act_b="AP_ALT", act_mid="AP_MID",
                              name_a="AP PATH (Abrir Portas)", name_b="AP ALT (Trancar Portas)", name_mid="AP ALT/HDG (Fechar Portas)")

        # --- D. BOTÕES MOMENTÂNEOS DAS PEGAS DA MANETE (1..6, 11, 12, 15) ---
        else:
            momentary_map = {
                1: "SLEW_PUSH_PRESS",
                2: "MIC_PUSH_PRESS",
                3: "MIC_UP_PRESS",
                4: "MIC_RIGHT_PRESS",
                5: "MIC_DOWN_PRESS",
                6: "MIC_LEFT_PRESS",
                11: "CHINA_FWD_PRESS",
                12: "CHINA_AFT_PRESS",
                15: "LTB_PRESS",
            }
            if button in momentary_map:
                info = THROTTLE_BUTTONS.get(button, {})
                self._handle_dual_action(
                    f"throttle_{button}",
                    is_down,
                    momentary_map[button],
                    info.get("desc", f"Botão {button}"),
                    fallback_name=info.get("name", f"BTN {button}")
                )
            elif is_down and button in THROTTLE_BUTTONS and self.on_action_triggered:
                info = THROTTLE_BUTTONS[button]
                self.on_action_triggered(f"THROTTLE_BTN_{button}", info["name"], info["desc"])

    def update_macros(self, macros: dict):
        """Atualiza o dicionário de macros ativas."""
        self.macros = macros or {}

    def run_macro(self, macro_id: str, trigger_label: str = ""):
        """Executa uma macro multi-passo em thread separada sem bloquear o polling."""
        macro = self.macros.get(macro_id)
        if not macro:
            return
        steps = macro.get("steps", [])
        name = macro.get("name", macro_id)
        icon = macro.get("icon", "⚡")

        if self.on_action_triggered:
            lbl = f"{icon} MACRO: {name}" + (f" ({trigger_label})" if trigger_label else "")
            self.on_action_triggered(f"MACRO:{macro_id}", f"⚡ {len(steps)} passos", lbl)

        def _exec_steps():
            for step in steps:
                s_key = str(step.get("key", "")).strip().upper()
                s_mods = [str(m).strip().upper() for m in step.get("modifiers", []) if m]
                s_hold = int(step.get("hold_ms", self.default_hold_ms))
                s_delay = int(step.get("delay_after_ms", 150))
                if s_key and s_key != "Z":
                    send_key_pulse(s_key, s_mods, s_hold)
                if s_delay > 0:
                    time.sleep(s_delay / 1000.0)

        threading.Thread(target=_exec_steps, daemon=True).start()

    def _has_long_press(self, action_id: str) -> bool:
        m = self.mappings.get(action_id)
        if not m:
            return False
        return bool((m.get("long_key") or "").strip() or (m.get("long_macro_id") or "").strip())

    def _handle_dual_action(self, btn_key: str, is_down: bool, action_id: str, fallback_desc: str, fallback_name: str = ""):
        """
        Gere Ação Dupla (Toque Curto vs Pressão Longa):
        - Se NÃO existir Pressão Longa configurada -> dispara instantaneamente em is_down (zero latência).
        - Se EXISTIR Pressão Longa -> inicia temporizador; se segurar >= limiar dispara Pressão Longa;
          se soltar antes do limiar dispara Toque Curto.
        """
        if not self._has_long_press(action_id):
            if is_down:
                mapping = self.mappings.get(action_id)
                if mapping and ((mapping.get("key") or "").strip() or (mapping.get("macro_id") or "").strip()):
                    self._dispatch_action(action_id, fallback_desc)
                elif self.on_action_triggered:
                    self.on_action_triggered(action_id, fallback_name or "Nativo XML", fallback_desc)
            return

        mapping = self.mappings.get(action_id, {})
        threshold_ms = max(180, int(mapping.get("long_threshold_ms", 450)))

        with self._hold_lock:
            existing = self._hold_timers.pop(btn_key, None)
            if existing:
                existing.cancel()

            if is_down:
                self._hold_fired[btn_key] = False

                def _on_long_timeout():
                    with self._hold_lock:
                        self._hold_fired[btn_key] = True
                        self._hold_timers.pop(btn_key, None)
                    self._dispatch_long_action(action_id, fallback_desc)

                t = threading.Timer(threshold_ms / 1000.0, _on_long_timeout)
                t.daemon = True
                self._hold_timers[btn_key] = t
                t.start()
            else:
                was_long = self._hold_fired.pop(btn_key, False)
                if not was_long:
                    self._dispatch_action(action_id, f"[CURTO] {fallback_desc}")

    def _dispatch_long_action(self, action_id: str, label: str):
        mapping = self.mappings.get(action_id)
        if not mapping:
            return

        long_macro = (mapping.get("long_macro_id") or "").strip()
        if long_macro and long_macro in self.macros:
            self.run_macro(long_macro, trigger_label="Pressão Longa")
            return

        key = (mapping.get("long_key") or "").strip()
        modifiers = mapping.get("long_modifiers", [])
        hold_ms = int(mapping.get("long_hold_ms", 120))
        desc = mapping.get("desc", label)

        if key.upper() == "Z":
            key = ""

        if key:
            send_key_pulse(key, modifiers, hold_ms)

        if self.on_action_triggered:
            mod_str = "+".join(modifiers) + "+" if modifiers else ""
            key_combo = f"⏱️ HOLD: {mod_str}{key}" if key else "⏱️ HOLD"
            self.on_action_triggered(f"{action_id}_LONG", key_combo, f"[PRESSÃO LONGA] {desc}")

    def _update_leds(self):
        """Atualiza os 5 LEDs verdes físicos da base da manete."""
        if self.led_controller:
            self.led_controller.sync_flight_state(
                self.flight_state["nav_mode"],
                self.flight_state["gear_down"],
                self.flight_state["vtol_on"],
                self.flight_state["lights_on"],
                self.flight_state["quantum_spool"],
            )

    def _handle_3way(self, group: str, button: int, is_down: bool,
                     btn_a: int, btn_b: int,
                     act_a: str, act_b: str, act_mid: str,
                     name_a: str, name_b: str, name_mid: str):
        last = self._3way_states[group]
        if is_down:
            if button == btn_a:
                self._3way_states[group] = btn_a
                self._dispatch_action(act_a, name_a)
            elif button == btn_b:
                self._3way_states[group] = btn_b
                self._dispatch_action(act_b, name_b)
        else:
            if last == button:
                self._3way_states[group] = "MID"
                self._dispatch_action(act_mid, name_mid)

    def _dispatch_action(self, action_id: str, label: str):
        mapping = self.mappings.get(action_id)
        if not mapping:
            return

        macro_id = (mapping.get("macro_id") or "").strip()
        if macro_id and macro_id in self.macros:
            self.run_macro(macro_id, trigger_label=action_id)
            return

        key = mapping.get("key", "").strip()
        modifiers = mapping.get("modifiers", [])
        hold_ms = mapping.get("hold_ms", self.default_hold_ms)
        desc = mapping.get("desc", label)

        # Bloqueio explícito de Z / Shift+Z
        if key.upper() == "Z":
            key = ""

        if key:
            send_key_pulse(key, modifiers, hold_ms)

        if self.on_action_triggered:
            mod_str = "+".join(modifiers) + "+" if modifiers else ""
            key_combo = f"{mod_str}{key}" if key else "Nativo XML"
            self.on_action_triggered(action_id, key_combo, desc)
