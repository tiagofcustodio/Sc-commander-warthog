"""
Configuration Manager
Gerencia a persistência das configurações do Warthog Commander em JSON.
"""

import os
import json
from warthog_constants import DEFAULT_SC_MAPPINGS

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

GITHUB_REPO_URL = "https://github.com/tiagofcustodio/Sc-commander-warthog"
DONATE_URL = "https://paypal.me/tcustodio"

DEFAULT_SC_PATH = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"

DEFAULT_MACROS = {
    "macro_full_landing": {
        "id": "macro_full_landing",
        "name": "Aterragem Completa (ATC + Trem + VTOL + Faróis)",
        "icon": "🛬",
        "steps": [
            {"key": "N", "modifiers": ["ALT"], "hold_ms": 80, "delay_after_ms": 450, "note": "Chamar Torre ATC"},
            {"key": "N", "modifiers": [], "hold_ms": 80, "delay_after_ms": 350, "note": "Baixar Trem de Aterragem"},
            {"key": "K", "modifiers": [], "hold_ms": 80, "delay_after_ms": 350, "note": "Ativar VTOL / Hover"},
            {"key": "L", "modifiers": [], "hold_ms": 80, "delay_after_ms": 0, "note": "Ligar Faróis Exteriores"}
        ]
    },
    "macro_combat_ready": {
        "id": "macro_combat_ready",
        "name": "Pronto para Combate (Flight Ready + Ping + Capacitores)",
        "icon": "⚔️",
        "steps": [
            {"key": "R", "modifiers": ["ALT"], "hold_ms": 80, "delay_after_ms": 600, "note": "Flight Ready (Ligar Tudo)"},
            {"key": "TAB", "modifiers": [], "hold_ms": 100, "delay_after_ms": 300, "note": "Ping de Radar"},
            {"key": "F8", "modifiers": [], "hold_ms": 60, "delay_after_ms": 0, "note": "Equilibrar Capacitores"}
        ]
    },
    "macro_quantum_prep": {
        "id": "macro_quantum_prep",
        "name": "Preparação Salto Quantum (NAV + Propulsores)",
        "icon": "🌌",
        "steps": [
            {"key": "B", "modifiers": [], "hold_ms": 350, "delay_after_ms": 500, "note": "Master Mode NAV / Spool"},
            {"key": "F6", "modifiers": [], "hold_ms": 80, "delay_after_ms": 0, "note": "Energia Máxima Propulsores"}
        ]
    }
}

DEFAULT_VOICE_SETTINGS = {
    "enabled": True,
    "lang": "en",
    "rate": 1.05,
    "pitch": 0.85,
    "volume": 0.85
}

DEFAULT_CONFIG = {
    "star_citizen_live_path": DEFAULT_SC_PATH,
    "pulse_hold_ms": 60,
    "slew_deadzone_percent": 12,
    "virtual_yaw_assist": False,
    "virtual_yaw_source": "slew_x", # ou 'coolie'
    "auto_fix_ids_on_start": True,
    "active_profile": "combat",
    "afterburner_auto_boost": False,
    "throttle_led_brightness": 3,
    "curve_type": "expo",
    "curve_exponent": 1.8,
    "split_throttle_mode": "speed_limiter",
    "mappings": DEFAULT_SC_MAPPINGS,
    "custom_profile_mappings": {},
    "macros": DEFAULT_MACROS,
    "voice_settings": DEFAULT_VOICE_SETTINGS,
    "selected_hotas_kit": "warthog",
    "auto_check_updates": True,
    "update_source": "tiagofcustodio/Sc-commander-warthog"
}

def load_config() -> dict:
    """Carrega a configuração existente ou retorna a padrão."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Garante que chaves novas presentes no padrão existam
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception as e:
            print(f"[Config] Erro ao ler {CONFIG_FILE}: {e}")

    # Salva configuração padrão
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(config_data: dict) -> bool:
    """Salva os dados de configuração em JSON."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[Config] Erro ao gravar {CONFIG_FILE}: {e}")
        return False
