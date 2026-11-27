"""
Profile Manager - Star Citizen Multi-Activity Specialized Profiles
Gere perfis dedicados para Combate, Mineração, Carga e Veículos Terrestres,
com comutação instantânea no Dashboard ou via atalho no cockpit (S4 Shift + S3).
"""

import copy
from warthog_constants import DEFAULT_SC_MAPPINGS

PROFILE_ORDER = ["combat", "mining", "cargo", "ground"]

# Ações físicas globais do seletor rotativo MODE (M1/M2/S1) do X56:
# Quando editadas, propagam-se por TODOS os perfis para não desaparecerem ao rodar o seletor!
GLOBAL_MODE_ACTION_IDS = ("X56_THR_34", "X56_THR_35", "X56_THR_36")

PROFILES = {
    "combat": {
        "id": "combat",
        "name": "⚔️ Combate / Dogfight",
        "description": "Otimizado para Master Modes (SCM/NAV), seleção rápida de alvos e contramedidas em pânico.",
        "icon": "⚔️",
        "afterburner_auto_boost": False,
        "split_throttle_mode": "speed_limiter",
        "slider_label": "LIMITADOR VELOC. (Slider 1):",
        "curve_type": "expo",
        "curve_exponent": 2.0,
        "highlights": "EAC: Master Mode (B) • SPDBRK: Cruise(C)/Travão(X) • BOAT: Quantum(B)/SCM • Boost: China FWD (B11)",
        "ui_cards": {
            "eac_sub": "Master Mode SCM / NAV",
            "eac_tag": "ARM/OFF: Alternar SCM/NAV (B)",
            "spdbrk_sub": "Cruise (07) / Space Brake (08)",
            "spdbrk_tag_a": "07: Cruise (C)",
            "spdbrk_tag_b": "08: Travão (X)",
            "boat_sub": "Quantum NAV (09) / SCM (10)",
            "boat_tag_a": "09: Quantum (B)",
            "boat_tag_b": "10: Armas SCM",
            "china_sub": "Boost (11) / Recuar (12)",
            "china_tag_a": "11: Boost (LShift)",
            "china_tag_b": "12: Recuar (S)",
            "flaps_sub": "UP (Cruise) / MVR / DN (VTOL)",
            "flaps_tag_a": "22: Cruise (C)",
            "flaps_tag_b": "23: VTOL (K)",
        },
        "mappings": {
            **DEFAULT_SC_MAPPINGS,
            "EAC_ON": {"key": "B", "modifiers": [], "desc": "Alternar Master Mode (SCM / NAV - B)", "hold_ms": 300},
            "EAC_OFF": {"key": "B", "modifiers": [], "desc": "Regressar a Modo Combate SCM (B)", "hold_ms": 300},
            "SPDBRK_FWD": {"key": "C", "modifiers": [], "desc": "Cruise Control ON/OFF (C)", "hold_ms": 60},
            "SPDBRK_AFT": {"key": "X", "modifiers": [], "desc": "Space Brake / Travão de Emergência (X)", "hold_ms": 80},
            "BOAT_FWD": {"key": "B", "modifiers": [], "desc": "Quantum Spool / Salto (B)", "hold_ms": 60},
            "BOAT_AFT": {"key": "B", "modifiers": [], "desc": "Cancelar Quantum / SCM (B)", "hold_ms": 60},
            "CHINA_FWD_PRESS": {"key": "LSHIFT", "modifiers": [], "desc": "Boost / Pós-Combustão (Left Shift)", "hold_ms": 100},
            "CHINA_AFT_PRESS": {"key": "S", "modifiers": [], "desc": "Inverter Propulsão / Recuar (S)", "hold_ms": 80},
        }
    },
    "mining": {
        "id": "mining",
        "name": "⛏️ Mineração & Salvage",
        "description": "Manete esquerda e Slider dedicados à potência do laser de mineração, ajuste de raio trator, scanner de rochas e consumíveis.",
        "icon": "⛏️",
        "afterburner_auto_boost": False,
        "split_throttle_mode": "mining_laser",
        "slider_label": "POTÊNCIA LASER (Slider 1):",
        "curve_type": "linear",
        "curve_exponent": 1.0,
        "highlights": "EAC: Modo Mineração(M) • SPDBRK: Potência/Trator(Wheel) • BOAT: Módulos(Alt+1/2) • CHINA: Ping(Tab)/Jettison",
        "ui_cards": {
            "eac_sub": "Modo Mineração / Salvage",
            "eac_tag": "ARM/OFF: Laser Mineração (M)",
            "spdbrk_sub": "Potência Laser / Raio Trator",
            "spdbrk_tag_a": "07: +Laser (WheelUp)",
            "spdbrk_tag_b": "08: -Laser (WheelDn)",
            "boat_sub": "Consumíveis Mineração 1 & 2",
            "boat_tag_a": "09: Módulo 1 (Alt+1)",
            "boat_tag_b": "10: Módulo 2 (Alt+2)",
            "china_sub": "Scanner Ping (11) / Ejetar (12)",
            "china_tag_a": "11: Ping Rochas (Tab)",
            "china_tag_b": "12: Ejetar Carga (Alt+J)",
            "flaps_sub": "Cruise (22) / Hover Estável (23)",
            "flaps_tag_a": "22: Cruise (C)",
            "flaps_tag_b": "23: Hover VTOL (K)",
        },
        "mappings": {
            **DEFAULT_SC_MAPPINGS,
            "EAC_ON": {"key": "M", "modifiers": [], "desc": "Ativar Modo Mineração / Salvage (M)", "hold_ms": 60},
            "EAC_OFF": {"key": "M", "modifiers": [], "desc": "Sair do Modo Mineração (M)", "hold_ms": 60},
            "BOAT_FWD": {"key": "1", "modifiers": ["ALT"], "desc": "Ativar Consumível de Mineração 1 (Alt+1)", "hold_ms": 60},
            "BOAT_AFT": {"key": "2", "modifiers": ["ALT"], "desc": "Ativar Consumível de Mineração 2 (Alt+2)", "hold_ms": 60},
            "SPDBRK_FWD": {"key": "MWHEEL_UP", "modifiers": [], "desc": "Aumentar Potência Laser / Distância Trator (Wheel Up)", "hold_ms": 60},
            "SPDBRK_AFT": {"key": "MWHEEL_DOWN", "modifiers": [], "desc": "Diminuir Potência Laser / Distância Trator (Wheel Down)", "hold_ms": 60},
            "CHINA_FWD_PRESS": {"key": "TAB", "modifiers": [], "desc": "Disparar Ping de Scanner de Rochas (Tab)", "hold_ms": 80},
            "CHINA_AFT_PRESS": {"key": "J", "modifiers": ["ALT"], "desc": "Ejetar Carga Instável Quantanium (Alt+J)", "hold_ms": 80},
        }
    },
    "cargo": {
        "id": "cargo",
        "name": "📦 Carga & Transporte",
        "description": "Manobras suaves em hangar sem boost acidental, chamada rápida a torres ATC, controlo de portas/rampas e VTOL pesado.",
        "icon": "📦",
        "afterburner_auto_boost": False,
        "split_throttle_mode": "speed_limiter",
        "slider_label": "LIMITADOR DOCAGEM (Slider 1):",
        "curve_type": "expo",
        "curve_exponent": 1.6,
        "highlights": "EAC: Portas/Rampas(Alt+K) • BOAT: Quantum(B)/Torre ATC(Alt+N) • B15: AutoLand(N) • Auto-Boost: OFF",
        "ui_cards": {
            "eac_sub": "Rampas & Portas Exteriores",
            "eac_tag": "ARM/OFF: Abrir/Fechar (Alt+K)",
            "spdbrk_sub": "Cruise Rota (07) / Travão (08)",
            "spdbrk_tag_a": "07: Cruise (C)",
            "spdbrk_tag_b": "08: Travão (X)",
            "boat_sub": "Quantum (09) / Chamar ATC (10)",
            "boat_tag_a": "09: Quantum (B)",
            "boat_tag_b": "10: Torre ATC (Alt+N)",
            "china_sub": "Boost Suave (11) / Recuar (12)",
            "china_tag_a": "11: Boost (LShift)",
            "china_tag_b": "12: Recuar (S)",
            "flaps_sub": "Cruise (22) / VTOL Carga (23)",
            "flaps_tag_a": "22: Cruise (C)",
            "flaps_tag_b": "23: VTOL Pesado (K)",
        },
        "mappings": {
            **DEFAULT_SC_MAPPINGS,
            "EAC_ON": {"key": "K", "modifiers": ["ALT"], "desc": "Abrir/Fechar Rampas e Portas Exteriores (Alt+K)", "hold_ms": 60},
            "EAC_OFF": {"key": "K", "modifiers": ["ALT"], "desc": "Fechar Rampas e Portas Exteriores (Alt+K)", "hold_ms": 60},
            "BOAT_FWD": {"key": "B", "modifiers": [], "desc": "Modo Quantum / Spool de Rota (B)", "hold_ms": 60},
            "BOAT_AFT": {"key": "N", "modifiers": ["ALT"], "desc": "Chamar Torre ATC / Hangar (Alt+N)", "hold_ms": 80},
            "LDGHORN_PRESS": {"key": "N", "modifiers": ["ALT"], "desc": "Pedir Autorização de Aterragem ATC (Alt+N)", "hold_ms": 80},
            "FLAPS_UP": {"key": "C", "modifiers": [], "desc": "Cruise Control de Rota (C)", "hold_ms": 60},
            "FLAPS_DN": {"key": "K", "modifiers": [], "desc": "VTOL / Propulsores de Carga Pesada (K)", "hold_ms": 60},
            "LTB_PRESS": {"key": "N", "modifiers": [], "desc": "AutoLand / Aterragem Automática no Pad (Hold N)", "hold_ms": 1200},
        }
    },
    "ground": {
        "id": "ground",
        "name": "🚜 Veículos Terrestres",
        "description": "Controlo dedicado para Rovers e Tanques (Ursa, Nova Tonk, Spartan, Cyclone) com travão de mão (Space), faróis e torre.",
        "icon": "🚜",
        "afterburner_auto_boost": False,
        "split_throttle_mode": "speed_limiter",
        "slider_label": "LIMITADOR TERRESTRE (Slider 1):",
        "curve_type": "expo",
        "curve_exponent": 1.5,
        "highlights": "EAC: Faróis Veículo(L) • SPDBRK AFT: Travão de Mão(Space) • BOAT: Centrar Torre(R)/Scan(V) • CHINA: Boost/Ré",
        "ui_cards": {
            "eac_sub": "Faróis do Veículo Terrestre",
            "eac_tag": "ARM/OFF: Faróis ON/OFF (L)",
            "spdbrk_sub": "Cruise (07) / Travão de Mão (08)",
            "spdbrk_tag_a": "07: Cruise (C)",
            "spdbrk_tag_b": "08: Travão Mão (Space)",
            "boat_sub": "Centrar Torre (09) / Scan (10)",
            "boat_tag_a": "09: Centrar Torre (R)",
            "boat_tag_b": "10: Modo Scan (V)",
            "china_sub": "Boost Rover (11) / Marcha-Atrás (12)",
            "china_tag_a": "11: Turbo (LShift)",
            "china_tag_b": "12: Marcha-Atrás (S)",
            "flaps_sub": "Motor ON (22) / Sistemas OFF (23)",
            "flaps_tag_a": "22: Motor ON (I)",
            "flaps_tag_b": "23: Power OFF (U)",
        },
        "mappings": {
            **DEFAULT_SC_MAPPINGS,
            "SPDBRK_FWD": {"key": "C", "modifiers": [], "desc": "Cruise / Marcha Constante Terrestre (C)", "hold_ms": 60},
            "SPDBRK_AFT": {"key": "SPACE", "modifiers": [], "desc": "Travão de Mão Terrestre / Paragem (Space)", "hold_ms": 80},
            "EAC_ON": {"key": "L", "modifiers": [], "desc": "Ligar Faróis do Veículo Terrestre (L)", "hold_ms": 60},
            "EAC_OFF": {"key": "L", "modifiers": [], "desc": "Desligar Faróis do Veículo Terrestre (L)", "hold_ms": 60},
            "BOAT_FWD": {"key": "R", "modifiers": [], "desc": "Centrar Torre do Tanque / Gimbal Lock (R)", "hold_ms": 60},
            "BOAT_AFT": {"key": "V", "modifiers": [], "desc": "Modo Scan Terrestre (V)", "hold_ms": 60},
            "FLAPS_UP": {"key": "I", "modifiers": [], "desc": "Ligar Motor do Veículo (I)", "hold_ms": 60},
            "FLAPS_DN": {"key": "U", "modifiers": [], "desc": "Desligar Sistemas do Veículo (U)", "hold_ms": 60},
        }
    }
}


FACTORY_PROFILES = copy.deepcopy(PROFILES)


class ProfileManager:
    """Gerencia a seleção, personalização e aplicação de perfis especializados."""

    def __init__(self, initial_profile: str = "combat", custom_overrides: dict = None):
        self.active_profile_id = initial_profile if initial_profile in PROFILES else "combat"
        if custom_overrides and isinstance(custom_overrides, dict):
            self.load_custom_overrides(custom_overrides)

    def load_custom_overrides(self, custom_overrides: dict):
        """Aplica mapeamentos personalizados guardados pelo utilizador em cada perfil (preservando hold_ms, macros e pressão longa)."""
        global_mode_overrides = {}
        for pid, p_maps in custom_overrides.items():
            if pid in PROFILES and isinstance(p_maps, dict):
                for act_id, m_val in p_maps.items():
                    if isinstance(m_val, dict):
                        cur = PROFILES[pid]["mappings"].get(act_id, {})
                        entry = {
                            "key": str(m_val.get("key", cur.get("key", ""))).strip().upper(),
                            "modifiers": [str(mod).strip().upper() for mod in m_val.get("modifiers", cur.get("modifiers", [])) if mod],
                            "desc": str(m_val.get("desc", cur.get("desc", act_id))),
                            "hold_ms": max(20, int(m_val.get("hold_ms") or cur.get("hold_ms", 60))),
                            "macro_id": str(m_val.get("macro_id", cur.get("macro_id", ""))).strip(),
                            "long_key": str(m_val.get("long_key", cur.get("long_key", ""))).strip().upper(),
                            "long_modifiers": [str(mod).strip().upper() for mod in m_val.get("long_modifiers", cur.get("long_modifiers", [])) if mod],
                            "long_hold_ms": max(20, int(m_val.get("long_hold_ms") or cur.get("long_hold_ms", 120))),
                            "long_macro_id": str(m_val.get("long_macro_id", cur.get("long_macro_id", ""))).strip(),
                            "long_threshold_ms": max(180, int(m_val.get("long_threshold_ms") or cur.get("long_threshold_ms", 450))),
                        }
                        PROFILES[pid]["mappings"][act_id] = entry
                        if act_id in GLOBAL_MODE_ACTION_IDS and (entry["key"] or entry["macro_id"]):
                            global_mode_overrides[act_id] = dict(entry)

        # Propaga teclas/macros personalizadas de M1/M2/S1 para todos os perfis
        for act_id, entry in global_mode_overrides.items():
            for pid in PROFILES:
                PROFILES[pid]["mappings"][act_id] = dict(entry)

    def update_single_mapping(self, action_id: str, mapping_data: dict, profile_id: str = None) -> dict:
        """Atualiza uma única tecla/ação (incluindo Macro e Pressão Longa) no perfil especificado."""
        pid = profile_id if (profile_id and profile_id in PROFILES) else self.active_profile_id
        current = PROFILES[pid]["mappings"].get(action_id, {})
        entry = {
            "key": str(mapping_data.get("key", current.get("key", ""))).strip().upper(),
            "modifiers": [str(mod).strip().upper() for mod in mapping_data.get("modifiers", current.get("modifiers", [])) if mod],
            "desc": str(mapping_data.get("desc", current.get("desc", action_id))),
            "hold_ms": max(20, int(mapping_data.get("hold_ms") or current.get("hold_ms", 60))),
            "macro_id": str(mapping_data.get("macro_id", current.get("macro_id", ""))).strip(),
            "long_key": str(mapping_data.get("long_key", current.get("long_key", ""))).strip().upper(),
            "long_modifiers": [str(mod).strip().upper() for mod in mapping_data.get("long_modifiers", current.get("long_modifiers", [])) if mod],
            "long_hold_ms": max(20, int(mapping_data.get("long_hold_ms") or current.get("long_hold_ms", 120))),
            "long_macro_id": str(mapping_data.get("long_macro_id", current.get("long_macro_id", ""))).strip(),
            "long_threshold_ms": max(180, int(mapping_data.get("long_threshold_ms") or current.get("long_threshold_ms", 450))),
        }
        if action_id in GLOBAL_MODE_ACTION_IDS:
            for p in PROFILES:
                PROFILES[p]["mappings"][action_id] = dict(entry)
        else:
            PROFILES[pid]["mappings"][action_id] = entry
        return entry

    def update_bulk_mappings(self, mappings_dict: dict, profile_id: str = None) -> dict:
        """Atualiza múltiplos mapeamentos de uma só vez no perfil ativo."""
        pid = profile_id if (profile_id and profile_id in PROFILES) else self.active_profile_id
        if isinstance(mappings_dict, dict):
            for act_id, m_val in mappings_dict.items():
                if isinstance(m_val, dict):
                    self.update_single_mapping(act_id, m_val, pid)
        return self.get_active_profile()

    def reset_profile_mappings(self, profile_id: str = None) -> dict:
        """Restaura os mapeamentos de fábrica de um perfil."""
        pid = profile_id if (profile_id and profile_id in PROFILES) else self.active_profile_id
        PROFILES[pid]["mappings"] = copy.deepcopy(FACTORY_PROFILES[pid]["mappings"])
        return PROFILES[pid]

    def get_active_profile(self) -> dict:
        return PROFILES[self.active_profile_id]

    def set_active_profile(self, profile_id: str) -> dict:
        if profile_id in PROFILES:
            self.active_profile_id = profile_id
        return self.get_active_profile()

    def cycle_next_profile(self) -> tuple[str, dict]:
        """Avança para o próximo perfil na ordem (combat -> mining -> cargo -> ground)."""
        try:
            idx = PROFILE_ORDER.index(self.active_profile_id)
        except ValueError:
            idx = 0
        next_id = PROFILE_ORDER[(idx + 1) % len(PROFILE_ORDER)]
        self.active_profile_id = next_id
        return next_id, self.get_active_profile()

    def get_all_profiles_summary(self) -> list[dict]:
        summary = []
        for pid in PROFILE_ORDER:
            pdata = PROFILES[pid]
            summary.append({
                "id": pid,
                "name": pdata["name"],
                "description": pdata["description"],
                "icon": pdata["icon"],
                "afterburner_auto_boost": pdata["afterburner_auto_boost"],
                "split_throttle_mode": pdata["split_throttle_mode"],
                "curve_type": pdata["curve_type"],
                "curve_exponent": pdata["curve_exponent"],
                "highlights": pdata.get("highlights", ""),
                "is_active": (pid == self.active_profile_id)
            })
        return summary

