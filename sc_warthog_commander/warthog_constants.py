"""
Warthog Constants & Star Citizen Complete Hardware Mapping
Módulo com constantes oficiais de hardware Thrustmaster HOTAS Warthog extraídas de
VID_044F&PID_0402.dev (Manche 19 botões + POV + 2 Eixos) e VID_044F&PID_0404.dev
(Manete 32 botões + POV + 5 Eixos) para Star Citizen 4.x.
"""

# Hardware Identifiers (VID & PID)
TM_VENDOR_ID = 0x044F
WARTHOG_JOYSTICK_PID = 0x0402
WARTHOG_THROTTLE_PID = 0x0404

WARTHOG_JOYSTICK_GUID_SUBSTR = "0402044F"
WARTHOG_THROTTLE_GUID_SUBSTR = "0404044F"

# ==============================================================================
# 1. MANCHE A-10C (JOYSTICK - js1 - PID 0x0402) - TODOS OS 19 BOTÕES + POV + EIXOS
# ==============================================================================
STICK_AXES = {
    "js1_x": {"name": "Eixo X (Roll)", "sc_action": "v_roll", "desc": "Rolamento da Nave (Roll) / Turret Yaw"},
    "js1_y": {"name": "Eixo Y (Pitch)", "sc_action": "v_pitch", "desc": "Arfagem da Nave (Pitch) / Turret Pitch"},
}

STICK_HATS = {
    "js1_hat1_up": {"name": "TRIM HAT UP (H1U)", "sc_action": "v_capacitor_assignment_engine_combined_increase_max", "key": "F6", "desc": "Energia Capacitor: Máximo nos Propulsores (F6)"},
    "js1_hat1_right": {"name": "TRIM HAT RIGHT (H1R)", "sc_action": "v_capacitor_assignment_shield_combined_increase_max", "key": "F7", "desc": "Energia Capacitor: Máximo nos Escudos (F7)"},
    "js1_hat1_left": {"name": "TRIM HAT LEFT (H1L)", "sc_action": "v_capacitor_assignment_weapon_combined_increase_max", "key": "F5", "desc": "Energia Capacitor: Máximo nas Armas (F5)"},
    "js1_hat1_down": {"name": "TRIM HAT DOWN (H1D)", "sc_action": "v_capacitor_assignment_reset", "key": "F8", "desc": "Energia Capacitor: Equilibrar / Reset (F8)"},
}

# Índices oficiais Thrustmaster VID_044F&PID_0402.dev (B1..B19)
STICK_BUTTONS = {
    1: {"name": "TG1 (Gatilho Etapa 1)", "sc_action": "v_attack1_group1", "desc": "Disparar Armas Grupo 1 / Laser Mineração / Scan", "shift_desc": "Disparo Primário"},
    2: {"name": "S2 (Weapon Release)", "sc_action": "v_weapon_toggle_launch_missile", "desc": "Travar e Disparar Míssil / Alternar Modo Laser", "shift_desc": "Ejetar Carga Volátil (Alt+J)"},
    3: {"name": "S3 (Nosewheel Steering)", "sc_action": "v_weapon_cycle_aimmode", "desc": "Alternar Modo Gimbal / Igualar Velocidade ao Alvo", "shift_desc": "Olhar para Trás (Look Behind)"},
    4: {"name": "S4 (Pinky Lever)", "sc_action": "v_ifcs_toggle_vector_decoupling", "desc": "⚡ MODIFICADOR SHIFT GLOBAL + Alternar Decoupled (Alt+C)", "shift_desc": "Camada Shift Ativa"},
    5: {"name": "S1 (Master Mode Btn)", "sc_action": "v_toggle_quantum_mode", "desc": "Alternar Master Mode SCM / NAV (B)", "shift_desc": "Alternar Modo VTOL (K)"},
    6: {"name": "TG2 (Gatilho Etapa 2)", "sc_action": "v_attack1_group2", "desc": "Disparar Armas Grupo 2 (Fogo Total Grupo 1 + 2)", "shift_desc": "Disparo Secundário"},
    # TMS Hat (H2U=7, H2R=8, H2D=9, H2L=10)
    7: {"name": "TMS UP (H2U)", "sc_action": "v_target_cycle_in_view_reset", "desc": "Selecionar Alvo sob a Mira (T)", "shift_desc": "Próximo Sub-componente Inimigo (8)"},
    8: {"name": "TMS RIGHT (H2R)", "sc_action": "v_target_cycle_hostile_fwd", "desc": "Próximo Alvo Hostil (5)", "shift_desc": "Próximo Alvo Aliado (6)"},
    9: {"name": "TMS DOWN (H2D)", "sc_action": "v_target_cycle_hostile_reset", "desc": "Alvo Hostil Mais Próximo / Atacante (4)", "shift_desc": "Reset Sub-componente (Alt+8)"},
    10: {"name": "TMS LEFT (H2L)", "sc_action": "v_target_cycle_hostile_back", "desc": "Alvo Hostil Anterior", "shift_desc": "Fixar / Pin Alvo Selecionado"},
    # DMS Hat (H3U=11, H3R=12, H3D=13, H3L=14)
    11: {"name": "DMS UP (H3U)", "sc_action": "v_invoke_ping", "desc": "Disparar Ping de Radar (Tab) + Aumentar Foco Scan", "shift_desc": "Reforçar Escudo Frontal (Num 8)"},
    12: {"name": "DMS RIGHT (H3R)", "sc_action": "v_target_cycle_all_fwd", "desc": "Próximo Alvo Geral (7) + Aumentar Ângulo Ping", "shift_desc": "Reforçar Escudo Direito (Num 6)"},
    13: {"name": "DMS DOWN (H3D)", "sc_action": "v_dec_scan_focus_level", "desc": "Diminuir Foco Scan + Equilibrar Escudos (Num 5)", "shift_desc": "Reforçar Escudo Traseiro (Num 2)"},
    14: {"name": "DMS LEFT (H3L)", "sc_action": "v_target_cycle_all_back", "desc": "Alvo Geral Anterior + Diminuir Ângulo Ping", "shift_desc": "Reforçar Escudo Esquerdo (Num 4)"},
    # CMS Hat (H4U=15, H4R=16, H4D=17, H4L=18, H4P=19)
    15: {"name": "CMS UP (H4U)", "sc_action": "v_weapon_countermeasure_noise_launch", "desc": "Lançar Campo de Ruído / Chaff (J)", "shift_desc": "Salva de Pânico"},
    16: {"name": "CMS RIGHT (H4R)", "sc_action": "v_weapon_countermeasure_decoy_burst_increase", "desc": "Aumentar Salva de Decoy + Próximo Míssil", "shift_desc": "Aumentar Mísseis Armados (G)"},
    17: {"name": "CMS DOWN (H4D)", "sc_action": "v_weapon_countermeasure_decoy_launch", "desc": "Lançar Contramedida Decoy / Flare (H)", "shift_desc": "Salva de Pânico"},
    18: {"name": "CMS LEFT (H4L)", "sc_action": "v_weapon_countermeasure_decoy_burst_decrease", "desc": "Diminuir Salva de Decoy + Míssil Anterior", "shift_desc": "Reset Mísseis Armados (Alt+G)"},
    19: {"name": "CMS PUSH (H4P)", "sc_action": "v_weapon_countermeasure_decoy_launch_panic", "desc": "Salva de Pânico de Contramedidas + Armar Míssil Extra", "shift_desc": "Auto-Destruição (Hold Backspace)"},
}

# ==============================================================================
# 2. MANETE DUPLA (THROTTLE - js2 - PID 0x0404) - TODOS OS 32 BOTÕES + POV + 5 EIXOS
# ==============================================================================
THROTTLE_AXES = {
    "js2_z": {"name": "Eixo Z (THR_LEFT - Manete Esq.)", "sc_action": "v_strafe_longitudinal", "desc": "Propulsão Principal dos Thrusters (Frente/Trás Invertido)"},
    "js2_rotz": {"name": "Eixo Rz (THR_RIGHT - Manete Dir.)", "sc_action": "v_throttle_abs", "desc": "Aceleração Principal Sincronizada (Sem conflito com Limitador)"},
    "js2_slider1": {"name": "Slider 1 (THR_FC - Roda Cinzenta)", "sc_action": "v_speed_range_abs", "desc": "Limitador de Velocidade Absoluto + Potência Laser Mineração"},
    "js2_x": {"name": "Eixo X (SCX - Mini-Stick Slew Horiz.)", "sc_action": "v_strafe_lateral", "desc": "Strafe Lateral Analógico (Esquerda / Direita)"},
    "js2_y": {"name": "Eixo Y (SCY - Mini-Stick Slew Vert.)", "sc_action": "v_strafe_vertical", "desc": "Strafe Vertical Analógico (Subir / Descer Suave)"},
}

THROTTLE_HATS = {
    "js2_hat1_up": {"name": "COOLIE HAT UP (CSU)", "sc_action": "v_strafe_up", "key": "SPACE", "desc": "Propulsor Vertical: Subir (Strafe Up)"},
    "js2_hat1_down": {"name": "COOLIE HAT DOWN (CSD)", "sc_action": "v_strafe_down", "key": "LCTRL", "desc": "Propulsor Vertical: Descer (Strafe Down)"},
    "js2_hat1_left": {"name": "COOLIE HAT LEFT (CSL)", "sc_action": "v_yaw_left", "key": "A", "desc": "Guiada Esquerda (Yaw Left)"},
    "js2_hat1_right": {"name": "COOLIE HAT RIGHT (CSR)", "sc_action": "v_yaw_right", "key": "D", "desc": "Guiada Direita (Yaw Right)"},
}

# Índices oficiais Thrustmaster VID_044F&PID_0404.dev (B1..B32)
THROTTLE_BUTTONS = {
    1: {"name": "SC (Slew Push)", "desc": "Premir Mini-Stick Slew: Igualar Velocidade Alvo / Interação (F)", "type": "momentary", "sc_action": "v_target_match_vel"},
    2: {"name": "MSP (Mic Push)", "desc": "Mic Switch Push: Push-to-Talk VOIP (Num +)", "type": "momentary", "sc_action": "foip_pushtotalk"},
    3: {"name": "MSU (Mic Up)", "desc": "Mic Switch Cima: Alternar Modo Scan (V)", "type": "momentary", "sc_action": "v_toggle_scan_mode"},
    4: {"name": "MSR (Mic Right)", "desc": "Mic Switch Direita: Alternar Câmara 3ª Pessoa (F4)", "type": "momentary", "sc_action": "v_view_cycle_fwd"},
    5: {"name": "MSD (Mic Down)", "desc": "Mic Switch Baixo: Alternar Modo Mineração / Salvage (M)", "type": "momentary", "sc_action": "v_toggle_mining_mode"},
    6: {"name": "MSL (Mic Left)", "desc": "Mic Switch Esquerda: Desativado (Sem Z / Shift+Z)", "type": "momentary", "sc_action": ""},
    7: {"name": "SPDF (Speedbrake FWD)", "desc": "Speed Brake Frente (Fixo): Cruise Control ON/OFF (C)", "type": "toggle_3way", "group": "speedbrake", "sc_action": "v_ifcs_toggle_cruise_control"},
    8: {"name": "SPDB (Speedbrake AFT)", "desc": "Speed Brake Trás (Mola): Travão Espacial (Space Brake - X)", "type": "toggle_3way", "group": "speedbrake", "sc_action": "v_space_brake"},
    9: {"name": "BSF (Boat FWD)", "desc": "Boat Switch Frente: Quantum Mode / NAV (B) [LED 5]", "type": "toggle_3way", "group": "boat", "sc_action": "v_toggle_qdrive_engagement"},
    10: {"name": "BSB (Boat AFT)", "desc": "Boat Switch Trás: Regressar Modo SCM / Armas (B)", "type": "toggle_3way", "group": "boat", "sc_action": "v_toggle_guns_mode"},
    11: {"name": "CHF (China Hat FWD)", "desc": "China Hat Frente (Vermelho): Boost / Pós-Combustão (Left Shift)", "type": "momentary", "sc_action": "v_afterburner"},
    12: {"name": "CHB (China Hat AFT)", "desc": "China Hat Trás (Vermelho): Inverter Propulsão / Recuar (S)", "type": "momentary", "sc_action": "v_strafe_back"},
    13: {"name": "PSF (Pinky FWD)", "desc": "Pinky Switch Frente: Ligar Faróis da Nave (L) [LED 4]", "type": "toggle_3way", "group": "pinky", "sc_action": "v_lights"},
    14: {"name": "PSB (Pinky AFT)", "desc": "Pinky Switch Trás: Luzes de Cabine / Bombing", "type": "toggle_3way", "group": "pinky", "sc_action": "v_toggle_cabin_lights"},
    15: {"name": "LTB (Left Throttle Btn)", "desc": "Botão Vermelho Manete Esq.: Flight Ready (Alt+R) / Autoland (N)", "type": "momentary", "sc_action": "v_flightready"},
    16: {"name": "EFLNORM (Fuel Left)", "desc": "Engine Fuel Flow Left NORM: Energia dos Propulsores ON/OFF (I)", "type": "toggle_2way", "sc_action": "v_power_toggle_thrusters"},
    17: {"name": "EFRNORM (Fuel Right)", "desc": "Engine Fuel Flow Right NORM: Energia das Armas ON/OFF (P)", "type": "toggle_2way", "sc_action": "v_power_toggle_weapons"},
    18: {"name": "EOLMOTOR (Eng L Motor)", "desc": "Engine Oper Left MOTOR (Trás): Desligar Propulsores OFF (I)", "type": "toggle_3way", "group": "eng_l", "sc_action": "v_power_set_thrusters_off"},
    19: {"name": "EORMOTOR (Eng R Motor)", "desc": "Engine Oper Right MOTOR (Trás): Desligar Armas OFF (P)", "type": "toggle_3way", "group": "eng_r", "sc_action": "v_power_set_weapons_off"},
    20: {"name": "APUON (APU Start)", "desc": "APU Start/Off: Flight Ready (Alt+R) / Desligar Energia Geral (U)", "type": "toggle_2way", "sc_action": "v_flightready"},
    21: {"name": "LDGH (Horn / ATC)", "desc": "Botão Vermelho Base: Chamar Torre ATC / Aterragem (Alt+N)", "type": "momentary", "sc_action": "v_atc_request"},
    22: {"name": "FLAPU (Flaps UP)", "desc": "Flaps Up: Cruise Control (C) / Retrair Trem", "type": "toggle_3way", "group": "flaps", "sc_action": "v_ifcs_toggle_cruise_control"},
    23: {"name": "FLAPD (Flaps DOWN)", "desc": "Flaps Down: Modo VTOL / Hover (K) [LED 3]", "type": "toggle_3way", "group": "flaps", "sc_action": "v_toggle_vtol"},
    24: {"name": "EACON (EAC ARM)", "desc": "EAC Arm/Off: Energia Geral / Escudos ON/OFF (U) [LED 1]", "type": "toggle_2way", "sc_action": "v_power_toggle"},
    25: {"name": "RDRNRM (RDR ALTM)", "desc": "Radar Altimeter: NRM = Recolher Trem (N) | DIS = Baixar Trem (N) [LED 2]", "type": "toggle_2way", "sc_action": "v_toggle_landing_system"},
    26: {"name": "APENG (Autopilot Btn)", "desc": "Botão Autopilot Engage: Chamar ATC (Alt+N) /fechar Portas", "type": "momentary", "sc_action": "v_atc_request"},
    27: {"name": "APPAT (AP PATH)", "desc": "Autopilot Path (Cima): Abrir Todas as Portas Exteriores (Alt+K)", "type": "toggle_3way", "group": "ap_mode", "sc_action": "v_open_all_doors"},
    28: {"name": "APALT (AP ALT)", "desc": "Autopilot Alt (Baixo): Trancar Todas as Portas (Alt+L)", "type": "toggle_3way", "group": "ap_mode", "sc_action": "v_lock_all_doors"},
    29: {"name": "IDLEROFF (Cutoff Dir.)", "desc": "Detentor Físico OFF Manete Dir. (Corte Motor c/ Debounce 350ms)", "type": "toggle_2way", "sc_action": "SAFE_IDLE_R"},
    30: {"name": "IDLELOFF (Cutoff Esq.)", "desc": "Detentor Físico OFF Manete Esq. (Corte Motor c/ Debounce 350ms)", "type": "toggle_2way", "sc_action": "SAFE_IDLE_L"},
    31: {"name": "EOLIGN (Eng L IGN)", "desc": "Engine Oper Left IGN (Cima): Limpar Visor Capacete (Alt+X) / Ignição Esq.", "type": "toggle_3way", "group": "eng_l", "sc_action": "visor_wipe"},
    32: {"name": "EORIGN (Eng R IGN)", "desc": "Engine Oper Right IGN (Cima): Ignição Armas / Ejetar (Alt+Y)", "type": "toggle_3way", "group": "eng_r", "sc_action": "v_eject"},
}

# 3-Way Switch Group definitions (identifies the middle/neutral state when neither button is active)
THREE_WAY_GROUPS = {
    "speedbrake": {"buttons": (7, 8), "neutral_name": "SPDM (Speedbrake Center)"},
    "boat": {"buttons": (9, 10), "neutral_name": "BSM (Boat Center)"},
    "pinky": {"buttons": (13, 14), "neutral_name": "PSM (Pinky Center - Lights Off)"},
    "eng_l": {"buttons": (31, 18), "neutral_name": "EOLNORM (Eng Left Normal)"},
    "eng_r": {"buttons": (32, 19), "neutral_name": "EORNORM (Eng Right Normal)"},
    "flaps": {"buttons": (22, 23), "neutral_name": "FLAPM (Flaps MVR Normal)"},
    "ap_mode": {"buttons": (27, 28), "neutral_name": "APAH (Autopilot ALT/HDG Center)"},
}

# Default Pulse Key Mappings for Star Citizen 4.x
DEFAULT_SC_MAPPINGS = {
    # Interruptores de 2 Posições da Base da Manete
    "APU_ON": {"key": "R", "modifiers": ["ALT"], "desc": "Flight Ready - Ligar Tudo (Alt+R)", "hold_ms": 60},
    "APU_OFF": {"key": "U", "modifiers": [], "desc": "Power Off - Desligar Sistemas (U)", "hold_ms": 60},

    "EAC_ON": {"key": "O", "modifiers": [], "desc": "Ligar Escudos / Sistemas (O)", "hold_ms": 60},
    "EAC_OFF": {"key": "O", "modifiers": [], "desc": "Desligar Escudos (O)", "hold_ms": 60},

    "RDR_ALTM_ON": {"key": "N", "modifiers": [], "desc": "Recolher Trem de Aterragem (N)", "hold_ms": 60},
    "RDR_ALTM_OFF": {"key": "N", "modifiers": [], "desc": "Baixar Trem de Aterragem (N)", "hold_ms": 60},

    "FUEL_L_ON": {"key": "I", "modifiers": [], "desc": "Ligar Propulsores (I)", "hold_ms": 60},
    "FUEL_L_OFF": {"key": "I", "modifiers": [], "desc": "Desligar Propulsores (I)", "hold_ms": 60},

    "FUEL_R_ON": {"key": "P", "modifiers": [], "desc": "Ligar Energia das Armas (P)", "hold_ms": 60},
    "FUEL_R_OFF": {"key": "P", "modifiers": [], "desc": "Desligar Energia das Armas (P)", "hold_ms": 60},

    "LDGHORN_PRESS": {"key": "N", "modifiers": ["ALT"], "desc": "Chamar ATC / Pedir Aterragem (Alt+N)", "hold_ms": 80},
    "AP_ENGAGE_PRESS": {"key": "N", "modifiers": ["ALT"], "desc": "Chamar ATC / Aterragem (Alt+N)", "hold_ms": 80},

    # Interruptores de 3 Posições (com Estado Central Sintetizado)
    "FLAPS_UP": {"key": "C", "modifiers": [], "desc": "Cruise Control ON/OFF (C)", "hold_ms": 60},
    "FLAPS_MID": {"key": "K", "modifiers": [], "desc": "Sair de VTOL -> Voo Normal (K)", "hold_ms": 60},
    "FLAPS_DN": {"key": "K", "modifiers": [], "desc": "Ativar Modo VTOL / Hover (K)", "hold_ms": 60},

    "PINKY_FWD": {"key": "L", "modifiers": [], "desc": "Faróis Exteriores ON (L)", "hold_ms": 60},
    "PINKY_MID": {"key": "L", "modifiers": [], "desc": "Faróis Exteriores OFF (L)", "hold_ms": 60},
    "PINKY_AFT": {"key": "L", "modifiers": [], "desc": "Alternar Luzes / Cabine (L)", "hold_ms": 60},

    "BOAT_FWD": {"key": "B", "modifiers": [], "desc": "Quantum Mode / Spool (B)", "hold_ms": 60},
    "BOAT_MID": {"key": "", "modifiers": [], "desc": "Boat Centro (Neutro)", "hold_ms": 0},
    "BOAT_AFT": {"key": "B", "modifiers": [], "desc": "Regressar SCM / Cancelar Quantum (B)", "hold_ms": 60},

    "SPDBRK_FWD": {"key": "C", "modifiers": [], "desc": "Cruise Control Toggle (C)", "hold_ms": 60},
    "SPDBRK_MID": {"key": "", "modifiers": [], "desc": "Speed Brake Neutro", "hold_ms": 0},
    "SPDBRK_AFT": {"key": "X", "modifiers": [], "desc": "Space Brake / Travão Espacial (X)", "hold_ms": 80},

    "ENG_L_IGN": {"key": "X", "modifiers": ["ALT"], "desc": "Limpar Visor do Capacete (Alt+X)", "hold_ms": 60},
    "ENG_L_NORM": {"key": "I", "modifiers": [], "desc": "Propulsores Normais ON (I)", "hold_ms": 60},
    "ENG_L_MOTOR": {"key": "I", "modifiers": [], "desc": "Cortar Propulsores OFF (I)", "hold_ms": 60},

    "ENG_R_IGN": {"key": "P", "modifiers": [], "desc": "Alternar Energia das Armas (P)", "hold_ms": 60},
    "ENG_R_NORM": {"key": "P", "modifiers": [], "desc": "Armas Normais ON (P)", "hold_ms": 60},
    "ENG_R_MOTOR": {"key": "P", "modifiers": [], "desc": "Cortar Energia das Armas OFF (P)", "hold_ms": 60},

    "AP_PATH": {"key": "K", "modifiers": ["ALT"], "desc": "Abrir Todas as Portas / Rampas (Alt+K)", "hold_ms": 60},
    "AP_MID": {"key": "O", "modifiers": ["ALT"], "desc": "Fechar Todas as Portas (Alt+O)", "hold_ms": 60},
    "AP_ALT": {"key": "L", "modifiers": ["ALT"], "desc": "Trancar Todas as Portas (Alt+L)", "hold_ms": 60},

    "IDLE_L_OFF": {"key": "I", "modifiers": [], "desc": "Corte Físico Motor Esq. (Cutoff OFF -> I)", "hold_ms": 60},
    "IDLE_L_IDLE": {"key": "I", "modifiers": [], "desc": "Arranque Motor Esq. (Saída de Cutoff -> I)", "hold_ms": 60},
    "IDLE_R_OFF": {"key": "I", "modifiers": [], "desc": "Corte Físico Motor Dir. (Cutoff OFF -> I)", "hold_ms": 60},
    "IDLE_R_IDLE": {"key": "I", "modifiers": [], "desc": "Arranque Motor Dir. (Saída de Cutoff -> I)", "hold_ms": 60},

    # Botões Momentâneos Adicionais da Manete
    "CHINA_FWD_PRESS": {"key": "LSHIFT", "modifiers": [], "desc": "Boost / Pós-Combustão (Left Shift)", "hold_ms": 100},
    "CHINA_AFT_PRESS": {"key": "S", "modifiers": [], "desc": "Inverter Propulsão / Recuar (S)", "hold_ms": 80},
    "MIC_PUSH_PRESS": {"key": "NUM_ADD", "modifiers": [], "desc": "Push-to-Talk VOIP (Num +)", "hold_ms": 60},
    "MIC_UP_PRESS": {"key": "V", "modifiers": [], "desc": "Modo Scan (V)", "hold_ms": 60},
    "MIC_RIGHT_PRESS": {"key": "F4", "modifiers": [], "desc": "Câmara Externa 3ª Pessoa (F4)", "hold_ms": 60},
    "MIC_DOWN_PRESS": {"key": "M", "modifiers": [], "desc": "Modo Mineração / Salvage (M)", "hold_ms": 60},
    "MIC_LEFT_PRESS": {"key": "", "modifiers": [], "desc": "Desativado (Sem Z / Shift+Z)", "hold_ms": 0},
    "SLEW_PUSH_PRESS": {"key": "F", "modifiers": [], "desc": "Interação Rápida / Match Vel (F)", "hold_ms": 60},
    "LTB_PRESS": {"key": "R", "modifiers": ["ALT"], "desc": "Flight Ready Rápido (Alt+R)", "hold_ms": 60},
    "VISOR_WIPE_PRESS": {"key": "X", "modifiers": ["ALT"], "desc": "Limpar Visor do Capacete (Alt+X)", "hold_ms": 60},

    # Coolie Hat da Manete (POV 1)
    "COOLIE_UP": {"key": "", "modifiers": [], "desc": "Coolie Hat Cima: Strafe Up (Nativo XML)", "hold_ms": 60},
    "COOLIE_DOWN": {"key": "", "modifiers": [], "desc": "Coolie Hat Baixo: Strafe Down (Nativo XML)", "hold_ms": 60},
    "COOLIE_LEFT": {"key": "", "modifiers": [], "desc": "Coolie Hat Esq.: Strafe Left (Nativo XML)", "hold_ms": 60},
    "COOLIE_RIGHT": {"key": "", "modifiers": [], "desc": "Coolie Hat Dir.: Strafe Right (Nativo XML)", "hold_ms": 60},

    # Trim Hat do Manche (POV 1 - Capacitores de Energia)
    "TRIM_HAT_UP": {"key": "F6", "modifiers": [], "desc": "Capacitor: Energia Máxima aos Propulsores (F6)", "hold_ms": 60},
    "TRIM_HAT_RIGHT": {"key": "F7", "modifiers": [], "desc": "Capacitor: Energia Máxima aos Escudos (F7)", "hold_ms": 60},
    "TRIM_HAT_LEFT": {"key": "F5", "modifiers": [], "desc": "Capacitor: Energia Máxima às Armas (F5)", "hold_ms": 60},
    "TRIM_HAT_DOWN": {"key": "F8", "modifiers": [], "desc": "Capacitor: Equilibrar Energia (F8)", "hold_ms": 60},

    # Botões Físicos do Manche A-10C (BTN 01 a BTN 19)
    "STICK_BTN_1": {"key": "", "modifiers": [], "desc": "TG1 Gatilho Etapa 1: Armas Grupo 1 (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_2": {"key": "", "modifiers": [], "desc": "S2 Weapon Release: Lançar Míssil / Laser (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_3": {"key": "", "modifiers": [], "desc": "S3 Nosewheel Steering: Modo Gimbal / Match Vel (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_5": {"key": "B", "modifiers": [], "desc": "S1 Master Mode: Alternar SCM / NAV (B)", "hold_ms": 60},
    "STICK_BTN_6": {"key": "", "modifiers": [], "desc": "TG2 Gatilho Etapa 2: Armas Grupo 2 (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_7": {"key": "T", "modifiers": [], "desc": "TMS Cima (BTN 07): Selecionar Alvo na Mira (T)", "hold_ms": 60},
    "STICK_BTN_8": {"key": "5", "modifiers": [], "desc": "TMS Direita (BTN 08): Próximo Alvo Hostil (5)", "hold_ms": 60},
    "STICK_BTN_9": {"key": "4", "modifiers": [], "desc": "TMS Baixo (BTN 09): Alvo Hostil Mais Próximo (4)", "hold_ms": 60},
    "STICK_BTN_10": {"key": "", "modifiers": [], "desc": "TMS Esquerda (BTN 10): Fixar Alvo / Hostil Ant. (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_11": {"key": "TAB", "modifiers": [], "desc": "DMS Cima (BTN 11): Disparar Ping Radar (Tab)", "hold_ms": 60},
    "STICK_BTN_12": {"key": "7", "modifiers": [], "desc": "DMS Direita (BTN 12): Próximo Todos os Alvos (7)", "hold_ms": 60},
    "STICK_BTN_13": {"key": "NUM5", "modifiers": [], "desc": "DMS Baixo (BTN 13): Equilibrar Escudos (Num 5)", "hold_ms": 60},
    "STICK_BTN_14": {"key": "", "modifiers": [], "desc": "DMS Esquerda (BTN 14): Alvo Anterior (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_15": {"key": "J", "modifiers": [], "desc": "CMS Cima (BTN 15): Lançar Ruído / Chaff (J)", "hold_ms": 60},
    "STICK_BTN_16": {"key": "", "modifiers": [], "desc": "CMS Direita (BTN 16): +Salva Decoy / Próx. Míssil (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_17": {"key": "H", "modifiers": [], "desc": "CMS Baixo (BTN 17): Lançar Decoy / Flare (H)", "hold_ms": 60},
    "STICK_BTN_18": {"key": "", "modifiers": [], "desc": "CMS Esquerda (BTN 18): -Salva Decoy / Míssil Ant. (Nativo XML)", "hold_ms": 60},
    "STICK_BTN_19": {"key": "", "modifiers": [], "desc": "CMS Push (BTN 19): Salva de Pânico / +Mísseis (Nativo XML)", "hold_ms": 60},

    # Camada Shift do Manche (S4 Pinky Lever BTN 04 + Botão)
    "S2_SHIFT": {"key": "J", "modifiers": ["ALT"], "desc": "[S4+BTN 02] Ejetar Carga Volátil (Alt+J)", "hold_ms": 80},
    "S1_SHIFT": {"key": "K", "modifiers": [], "desc": "[S4+BTN 05] Alternar Modo VTOL (K)", "hold_ms": 60},
    "TMS_UP_SHIFT": {"key": "8", "modifiers": [], "desc": "[S4+BTN 07] Sub-Target: Próximo Sub-componente (8)", "hold_ms": 60},
    "TMS_RIGHT_SHIFT": {"key": "6", "modifiers": [], "desc": "[S4+BTN 08] Selecionar Próximo Aliado (6)", "hold_ms": 60},
    "TMS_DOWN_SHIFT": {"key": "8", "modifiers": ["ALT"], "desc": "[S4+BTN 09] Reset Sub-componente (Alt+8)", "hold_ms": 60},
    "DMS_UP_SHIFT": {"key": "NUM8", "modifiers": [], "desc": "[S4+BTN 11] Reforçar Escudo Frontal (Num 8)", "hold_ms": 60},
    "DMS_RIGHT_SHIFT": {"key": "NUM6", "modifiers": [], "desc": "[S4+BTN 12] Reforçar Escudo Direito (Num 6)", "hold_ms": 60},
    "DMS_DOWN_SHIFT": {"key": "NUM2", "modifiers": [], "desc": "[S4+BTN 13] Reforçar Escudo Traseiro (Num 2)", "hold_ms": 60},
    "DMS_LEFT_SHIFT": {"key": "NUM4", "modifiers": [], "desc": "[S4+BTN 14] Reforçar Escudo Esquerdo (Num 4)", "hold_ms": 60},
    "CMS_RIGHT_SHIFT": {"key": "G", "modifiers": [], "desc": "[S4+BTN 16] Aumentar Mísseis Armados (G)", "hold_ms": 60},
    "CMS_LEFT_SHIFT": {"key": "G", "modifiers": ["ALT"], "desc": "[S4+BTN 18] Reset Mísseis Armados (Alt+G)", "hold_ms": 60},

    # ==========================================================================
    # LOGITECH G / SAITEK X56 RHINO — MAPEAMENTO NATIVO COMPLETO (STICK + THROTTLE)
    # ==========================================================================
    # X56 Stick (PID 2221 — BTN 01..17; BTN 06 = Pinky Lever Shift)
    "X56_STK_1":  {"key": "", "modifiers": [], "desc": "Trigger (BTN 01): Disparo Primário Armas 1 (Nativo SC)", "hold_ms": 60},
    "X56_STK_2":  {"key": "", "modifiers": [], "desc": "Botão A (BTN 02): Travar / Lançar Míssil (Nativo SC)", "hold_ms": 60},
    "X56_STK_3":  {"key": "", "modifiers": [], "desc": "Botão B (BTN 03): Alternar Gimbal / Armas 2 (Nativo SC)", "hold_ms": 60},
    "X56_STK_4":  {"key": "B", "modifiers": [], "desc": "Botão C / C-Stick Push (BTN 04): Master Mode SCM/NAV (B)", "hold_ms": 60},
    "X56_STK_5":  {"key": "C", "modifiers": ["ALT"], "desc": "Botão D (BTN 05): Alternar Voo Decoupled (Alt+C)", "hold_ms": 60},
    "X56_STK_7":  {"key": "T", "modifiers": [], "desc": "H1 Cima (BTN 07): Selecionar Alvo na Mira (T)", "hold_ms": 60},
    "X56_STK_8":  {"key": "5", "modifiers": [], "desc": "H1 Direita (BTN 08): Próximo Alvo Hostil (5)", "hold_ms": 60},
    "X56_STK_9":  {"key": "4", "modifiers": [], "desc": "H1 Baixo (BTN 09): Alvo Hostil Mais Próximo (4)", "hold_ms": 60},
    "X56_STK_10": {"key": "7", "modifiers": [], "desc": "H1 Esquerda (BTN 10): Próximo Alvo Geral (7)", "hold_ms": 60},
    "X56_STK_11": {"key": "TAB", "modifiers": [], "desc": "H2 Cima (BTN 11): Ping de Radar (Tab)", "hold_ms": 60},
    "X56_STK_12": {"key": "J", "modifiers": [], "desc": "H2 Direita (BTN 12): Campo de Ruído / Chaff (J)", "hold_ms": 60},
    "X56_STK_13": {"key": "H", "modifiers": [], "desc": "H2 Baixo (BTN 13): Lançar Flare / Decoy (H)", "hold_ms": 60},
    "X56_STK_14": {"key": "NUM5", "modifiers": [], "desc": "H2 Esquerda (BTN 14): Equilibrar Escudos (Num 5)", "hold_ms": 60},
    "X56_STK_15": {"key": "", "modifiers": [], "desc": "Stick BTN 15 (Auxiliar)", "hold_ms": 60},
    "X56_STK_16": {"key": "", "modifiers": [], "desc": "Stick BTN 16 (Auxiliar)", "hold_ms": 60},
    "X56_STK_17": {"key": "", "modifiers": [], "desc": "Stick BTN 17 (Auxiliar)", "hold_ms": 60},

    # X56 Throttle (PID A221 — BTN 01..32; Toggles SW 1-6 e TGL 1-4 são momentâneos com retorno por mola!)
    "X56_THR_1":  {"key": "LSHIFT", "modifiers": [], "desc": "Botão E (BTN 01): Boost / Pós-Combustão (Hold LShift)", "hold_ms": 80},
    "X56_THR_2":  {"key": "C", "modifiers": [], "desc": "Botão F — Press Rotativo Topo (BTN 02): Cruise Control (C)", "hold_ms": 60},
    "X56_THR_3":  {"key": "X", "modifiers": [], "desc": "Botão G — Press Rotativo Inf. (BTN 03): Space Brake (Hold X)", "hold_ms": 80},
    "X56_THR_4":  {"key": "S", "modifiers": [], "desc": "Botão I (BTN 04): Inverter Propulsão / Recuar (S)", "hold_ms": 80},
    "X56_THR_5":  {"key": "B", "modifiers": [], "desc": "Botão H (BTN 05): Quantum Drive / Master Mode (B)", "hold_ms": 60},
    "X56_THR_6":  {"key": "R", "modifiers": ["ALT"], "desc": "SW 1 Cima (BTN 06): Flight Ready — Ligar Nave (Alt+R)", "hold_ms": 60},
    "X56_THR_7":  {"key": "U", "modifiers": [], "desc": "SW 2 Baixo (BTN 07): Power Off — Desligar Energia (U)", "hold_ms": 60},
    "X56_THR_8":  {"key": "I", "modifiers": [], "desc": "SW 3 Cima (BTN 08): Propulsores ON/OFF (I)", "hold_ms": 60},
    "X56_THR_9":  {"key": "P", "modifiers": [], "desc": "SW 4 Baixo (BTN 09): Armas ON/OFF (P)", "hold_ms": 60},
    "X56_THR_10": {"key": "O", "modifiers": [], "desc": "SW 5 Cima (BTN 10): Escudos ON/OFF (O)", "hold_ms": 60},
    "X56_THR_11": {"key": "N", "modifiers": ["ALT"], "desc": "SW 6 Baixo (BTN 11): Chamar Torre ATC / Aterragem (Alt+N)", "hold_ms": 80},
    "X56_THR_12": {"key": "N", "modifiers": [], "desc": "TGL 1 Cima (BTN 12): Trem de Aterragem (N)", "hold_ms": 60},
    "X56_THR_13": {"key": "N", "modifiers": ["ALT"], "desc": "TGL 1 Baixo (BTN 13): Pedir Aterragem ATC (Alt+N)", "hold_ms": 80},
    "X56_THR_14": {"key": "K", "modifiers": [], "desc": "TGL 2 Cima (BTN 14): Alternar Modo VTOL / Hover (K)", "hold_ms": 60},
    "X56_THR_15": {"key": "L", "modifiers": [], "desc": "TGL 2 Baixo (BTN 15): Faróis Exteriores da Nave (L)", "hold_ms": 60},
    "X56_THR_16": {"key": "K", "modifiers": ["ALT"], "desc": "TGL 3 Cima (BTN 16): Abrir Todas as Portas (Alt+K)", "hold_ms": 60},
    "X56_THR_17": {"key": "O", "modifiers": ["ALT"], "desc": "TGL 3 Baixo (BTN 17): Fechar Todas as Portas (Alt+O)", "hold_ms": 60},
    "X56_THR_18": {"key": "L", "modifiers": ["ALT"], "desc": "TGL 4 Cima (BTN 18): Trancar Todas as Portas (Alt+L)", "hold_ms": 60},
    "X56_THR_19": {"key": "X", "modifiers": ["ALT"], "desc": "TGL 4 Baixo (BTN 19): Limpar Visor do Capacete (Alt+X)", "hold_ms": 60},
    "X56_THR_20": {"key": "V", "modifiers": [], "desc": "H3 Cima (BTN 20): Alternar Modo Scan (V)", "hold_ms": 60},
    "X56_THR_21": {"key": "F4", "modifiers": [], "desc": "H3 Direita (BTN 21): Câmara Externa 3ª Pessoa (F4)", "hold_ms": 60},
    "X56_THR_22": {"key": "M", "modifiers": [], "desc": "H3 Baixo (BTN 22): Modo Mineração / Salvage (M)", "hold_ms": 60},
    "X56_THR_23": {"key": "F", "modifiers": [], "desc": "H3 Esquerda (BTN 23): Interação / Match Speed (F)", "hold_ms": 60},
    "X56_THR_24": {"key": "SPACE", "modifiers": [], "desc": "H4 Cima (BTN 24): Strafe Vertical Subir (Space)", "hold_ms": 60},
    "X56_THR_25": {"key": "D", "modifiers": [], "desc": "H4 Direita (BTN 25): Strafe Direita (D)", "hold_ms": 60},
    "X56_THR_26": {"key": "LCTRL", "modifiers": [], "desc": "H4 Baixo (BTN 26): Strafe Vertical Descer (LCtrl)", "hold_ms": 60},
    "X56_THR_27": {"key": "A", "modifiers": [], "desc": "H4 Esquerda (BTN 27): Strafe Esquerda (A)", "hold_ms": 60},
    "X56_THR_28": {"key": "G", "modifiers": [], "desc": "K1 Cima (BTN 28): Armar Mais Mísseis (G)", "hold_ms": 60},
    "X56_THR_29": {"key": "G", "modifiers": ["ALT"], "desc": "K1 Baixo (BTN 29): Reset Salva de Mísseis (Alt+G)", "hold_ms": 60},
    "X56_THR_30": {"key": "MWHEEL_UP", "modifiers": [], "desc": "Scroll Frente (BTN 30): Aumentar Limite Veloc./Laser", "hold_ms": 40},
    "X56_THR_31": {"key": "MWHEEL_DOWN", "modifiers": [], "desc": "Scroll Trás (BTN 31): Diminuir Limite Veloc./Laser", "hold_ms": 40},
    "X56_THR_32": {"key": "NUM_ADD", "modifiers": [], "desc": "Mini-Stick Push (BTN 32): VOIP Push-to-Talk (Num +)", "hold_ms": 60},
    "X56_THR_33": {"key": "B", "modifiers": [], "desc": "SLD Slide Switch (BTN 33): Alternar Quantum / NAV (B)", "hold_ms": 80},
    "X56_THR_34": {"key": "", "modifiers": [], "desc": "MODE M1 (BTN 34): Perfil ⚔️ Combate (ou tecla/macro personalizada)", "hold_ms": 60},
    "X56_THR_35": {"key": "", "modifiers": [], "desc": "MODE M2 (BTN 35): Perfil ⛏️ Mineração (ou tecla/macro personalizada)", "hold_ms": 60},
    "X56_THR_36": {"key": "", "modifiers": [], "desc": "MODE S1 (BTN 36): Perfil 📦 Carga (ou tecla/macro personalizada)", "hold_ms": 60},
}

# Catálogo descritivo de hardware para Logitech G / Saitek X56 Rhino
X56_STICK_BUTTONS = {
    1: {"name": "Trigger (Gatilho)", "desc": "Disparo Primário Armas Grupo 1"},
    2: {"name": "Botão A (Topo)", "desc": "Travar / Lançar Míssil"},
    3: {"name": "Botão B (Lateral)", "desc": "Modo Gimbal / Armas Grupo 2"},
    4: {"name": "Botão C (C-Stick Push)", "desc": "Master Mode SCM / NAV (B)"},
    5: {"name": "Botão D (Polegar Inf.)", "desc": "Alternar Voo Decoupled (Alt+C)"},
    6: {"name": "Pinky Lever (Shift)", "desc": "⚡ MODIFICADOR SHIFT GLOBAL (Segurar)"},
    7: {"name": "H1 Cima", "desc": "Alvo sob a Mira (T)"},
    8: {"name": "H1 Direita", "desc": "Próximo Hostil (5)"},
    9: {"name": "H1 Baixo", "desc": "Hostil Mais Próximo (4)"},
    10: {"name": "H1 Esquerda", "desc": "Próximo Alvo Geral (7)"},
    11: {"name": "H2 Cima", "desc": "Ping de Radar (Tab)"},
    12: {"name": "H2 Direita", "desc": "Campo de Ruído / Chaff (J)"},
    13: {"name": "H2 Baixo", "desc": "Lançar Flare / Decoy (H)"},
    14: {"name": "H2 Esquerda", "desc": "Equilibrar Escudos (Num 5)"},
    15: {"name": "Stick BTN 15", "desc": "Auxiliar 15"},
    16: {"name": "Stick BTN 16", "desc": "Auxiliar 16"},
    17: {"name": "Stick BTN 17", "desc": "Auxiliar 17"},
}

X56_THROTTLE_BUTTONS = {
    1: {"name": "Botão E (Punho Sup.)", "desc": "Boost / Pós-Combustão (Hold LShift)"},
    2: {"name": "Botão F (Rotativo Topo)", "desc": "Cruise Control (C)"},
    3: {"name": "Botão G (Rotativo Inf.)", "desc": "Space Brake / Travão (Hold X)"},
    4: {"name": "Botão I (Punho Inf.)", "desc": "Inverter Propulsão / Recuar (S)"},
    5: {"name": "Botão H (Indicador)", "desc": "Quantum Drive / Master Mode (B)"},
    6: {"name": "SW 1 (Toggle Base Esq. ▲)", "desc": "Flight Ready — Ligar Tudo (Alt+R)"},
    7: {"name": "SW 2 (Toggle Base Esq. ▼)", "desc": "Power Off — Desligar Energia (U)"},
    8: {"name": "SW 3 (Toggle Base Meio ▲)", "desc": "Energia Propulsores ON/OFF (I)"},
    9: {"name": "SW 4 (Toggle Base Meio ▼)", "desc": "Energia Armas ON/OFF (P)"},
    10: {"name": "SW 5 (Toggle Base Dir. ▲)", "desc": "Energia Escudos ON/OFF (O)"},
    11: {"name": "SW 6 (Toggle Base Dir. ▼)", "desc": "Chamar Torre ATC / Aterragem (Alt+N)"},
    12: {"name": "TGL 1 ▲ (Col. Dir. Inf.)", "desc": "Trem de Aterragem (N)"},
    13: {"name": "TGL 1 ▼ (Col. Dir. Inf.)", "desc": "Pedir Aterragem ATC (Alt+N)"},
    14: {"name": "TGL 2 ▲ (Col. Dir.)", "desc": "Modo VTOL / Hover (K)"},
    15: {"name": "TGL 2 ▼ (Col. Dir.)", "desc": "Faróis Exteriores (L)"},
    16: {"name": "TGL 3 ▲ (Col. Dir.)", "desc": "Abrir Todas as Portas (Alt+K)"},
    17: {"name": "TGL 3 ▼ (Col. Dir.)", "desc": "Fechar Todas as Portas (Alt+O)"},
    18: {"name": "TGL 4 ▲ (Col. Dir. Topo)", "desc": "Trancar Todas as Portas (Alt+L)"},
    19: {"name": "TGL 4 ▼ (Col. Dir. Topo)", "desc": "Limpar Visor Capacete (Alt+X)"},
    20: {"name": "H3 Cima (Hat Polegar 3)", "desc": "Modo Scan (V)"},
    21: {"name": "H3 Direita (Hat Polegar 3)", "desc": "Câmara 3ª Pessoa (F4)"},
    22: {"name": "H3 Baixo (Hat Polegar 3)", "desc": "Modo Mineração / Salvage (M)"},
    23: {"name": "H3 Esquerda (Hat Polegar 3)", "desc": "Interação / Match Vel (F)"},
    24: {"name": "H4 Cima (Hat Polegar 4)", "desc": "Strafe Vertical Subir (Space)"},
    25: {"name": "H4 Direita (Hat Polegar 4)", "desc": "Strafe Direita (D)"},
    26: {"name": "H4 Baixo (Hat Polegar 4)", "desc": "Strafe Vertical Descer (LCtrl)"},
    27: {"name": "H4 Esquerda (Hat Polegar 4)", "desc": "Strafe Esquerda (A)"},
    28: {"name": "K1 Cima (Rocker Punho)", "desc": "Armar Mais Mísseis (G)"},
    29: {"name": "K1 Baixo (Rocker Punho)", "desc": "Reset Salva de Mísseis (Alt+G)"},
    30: {"name": "Scroll Frente (Roda)", "desc": "Aumentar Limite Veloc./Laser"},
    31: {"name": "Scroll Trás (Roda)", "desc": "Diminuir Limite Veloc./Laser"},
    32: {"name": "Mini-Stick Push", "desc": "VOIP Push-to-Talk (Num +)"},
    33: {"name": "SLD (Slide Switch)", "desc": "Interruptor Deslizante Cinzento"},
    34: {"name": "MODE M1 (Seletor Modo 1)", "desc": "Selecionar Modo 1 / Perfil ⚔️ Combate"},
    35: {"name": "MODE M2 (Seletor Modo 2)", "desc": "Selecionar Modo 2 / Perfil ⛏️ Mineração"},
    36: {"name": "MODE S1 (Seletor Modo 3)", "desc": "Selecionar Modo S1 / Perfil 📦 Carga"},
}
