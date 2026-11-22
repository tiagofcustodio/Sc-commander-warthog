"""
Multi-HOTAS Device Registry
Suporte unificado para múltiplos controladores Thrustmaster e Saitek / Logitech X56 Rhino.
Identificação exata por VID/PID USB (DirectInput / WinMM) + fallback inteligente por nome OEM.
"""

from typing import Optional

# Vendor IDs oficiais
VID_THRUSTMASTER = 0x044F
VID_SAITEK_MADCATZ = 0x0738
VID_SAITEK_LOGITECH = 0x06A3

# Tabela de dispositivos suportados por (VID, PID)
KNOWN_USB_DEVICES = {
    # --- THRUSTMASTER WARTHOG ---
    (VID_THRUSTMASTER, 0x0402): {"kit": "warthog", "role": "stick", "brand": "Thrustmaster", "model": "HOTAS Warthog Flight Stick (A-10C)", "buttons": 19, "axes": 2},
    (VID_THRUSTMASTER, 0x0404): {"kit": "warthog", "role": "throttle", "brand": "Thrustmaster", "model": "HOTAS Warthog Dual Throttle", "buttons": 32, "axes": 5},

    # --- THRUSTMASTER T.16000M FCS & TWCS THROTTLE ---
    (VID_THRUSTMASTER, 0xB10A): {"kit": "tm_t16000m", "role": "stick", "brand": "Thrustmaster", "model": "T.16000M FCS Space Sim Stick", "buttons": 16, "axes": 4},
    (VID_THRUSTMASTER, 0xB687): {"kit": "tm_t16000m", "role": "throttle", "brand": "Thrustmaster", "model": "TWCS Throttle", "buttons": 14, "axes": 5},

    # --- THRUSTMASTER T.FLIGHT HOTAS (X / 4 / ONE) ---
    (VID_THRUSTMASTER, 0xB108): {"kit": "tm_tflight", "role": "stick", "brand": "Thrustmaster", "model": "T.Flight HOTAS X", "buttons": 12, "axes": 5},
    (VID_THRUSTMASTER, 0xB67B): {"kit": "tm_tflight", "role": "stick", "brand": "Thrustmaster", "model": "T.Flight HOTAS 4", "buttons": 12, "axes": 5},
    (VID_THRUSTMASTER, 0xB68D): {"kit": "tm_tflight", "role": "stick", "brand": "Thrustmaster", "model": "T.Flight HOTAS One", "buttons": 12, "axes": 5},

    # --- THRUSTMASTER TCA AIRBUS OFFICER PACK ---
    (VID_THRUSTMASTER, 0x0405): {"kit": "tm_tca", "role": "stick", "brand": "Thrustmaster", "model": "TCA Sidestick Airbus Edition", "buttons": 17, "axes": 4},
    (VID_THRUSTMASTER, 0x0406): {"kit": "tm_tca", "role": "stick", "brand": "Thrustmaster", "model": "TCA Sidestick X Airbus Edition", "buttons": 17, "axes": 4},
    (VID_THRUSTMASTER, 0x0407): {"kit": "tm_tca", "role": "throttle", "brand": "Thrustmaster", "model": "TCA Quadrant Airbus Edition", "buttons": 17, "axes": 2},

    # --- THRUSTMASTER VIPER TQS / COUGAR / F-18 ---
    (VID_THRUSTMASTER, 0x0400): {"kit": "warthog", "role": "stick", "brand": "Thrustmaster", "model": "HOTAS Cougar (F-16)", "buttons": 19, "axes": 2},
    (VID_THRUSTMASTER, 0x0412): {"kit": "warthog", "role": "throttle", "brand": "Thrustmaster", "model": "Viper TQS Mission Pack", "buttons": 32, "axes": 5},
    (VID_THRUSTMASTER, 0x0413): {"kit": "warthog", "role": "throttle", "brand": "Thrustmaster", "model": "Viper Panel", "buttons": 32, "axes": 2},

    # --- SAITEK / LOGITECH G X56 RHINO HOTAS ---
    (VID_SAITEK_MADCATZ, 0x2221): {"kit": "saitek_x56", "role": "stick", "brand": "Saitek / Logitech", "model": "Saitek X56 Rhino Stick", "buttons": 17, "axes": 5},
    (VID_SAITEK_MADCATZ, 0xA221): {"kit": "saitek_x56", "role": "throttle", "brand": "Saitek / Logitech", "model": "Saitek X56 Rhino Throttle", "buttons": 32, "axes": 6},
    (VID_SAITEK_LOGITECH, 0x2221): {"kit": "saitek_x56", "role": "stick", "brand": "Logitech G / Saitek", "model": "Logitech G X56 Rhino Stick", "buttons": 17, "axes": 5},
    (VID_SAITEK_LOGITECH, 0xA221): {"kit": "saitek_x56", "role": "throttle", "brand": "Logitech G / Saitek", "model": "Logitech G X56 Rhino Throttle", "buttons": 32, "axes": 6},
}

# Catálogo de Kits selecionáveis na interface
HOTAS_KITS_META = {
    "warthog": {
        "id": "warthog",
        "name": "Thrustmaster HOTAS Warthog (A-10C)",
        "brand": "Thrustmaster",
        "stick_label": "MANCHE A-10C (PID 0402)",
        "throttle_label": "MANETE DUPLA (PID 0404)",
        "stick_summary": "19 Botões + 8-Way Trim Hat + 2 Eixos",
        "throttle_summary": "32 Botões + Coolie Hat + 5 Eixos + 5 LEDs",
        "has_leds": True,
    },
    "saitek_x56": {
        "id": "saitek_x56",
        "name": "Saitek / Logitech G X56 Rhino HOTAS",
        "brand": "Saitek / Logitech",
        "stick_label": "X56 RHINO STICK (PID 2221)",
        "throttle_label": "X56 RHINO THROTTLE (PID A221)",
        "stick_summary": "17 Botões + C-Stick Analógico + Twist Yaw + 2 Hats",
        "throttle_summary": "32 Botões + 7 Toggles + 4 Rotativos + Modo M1/M2/S1",
        "has_leds": False,
    },
    "tm_t16000m": {
        "id": "tm_t16000m",
        "name": "Thrustmaster T.16000M FCS + TWCS Throttle",
        "brand": "Thrustmaster",
        "stick_label": "T.16000M FCS STICK (PID B10A)",
        "throttle_label": "TWCS THROTTLE (PID B687)",
        "stick_summary": "16 Botões (12 Base + 4 Grip) + POV + Twist Yaw",
        "throttle_summary": "14 Botões + Mini-Stick + 3 Hats + Paddle Rudder",
        "has_leds": False,
    },
    "tm_tca": {
        "id": "tm_tca",
        "name": "Thrustmaster TCA Officer Pack Airbus",
        "brand": "Thrustmaster",
        "stick_label": "TCA SIDESTICK (PID 0405/0406)",
        "throttle_label": "TCA QUADRANT (PID 0407)",
        "stick_summary": "17 Botões + POV 8-Way + Twist Yaw + Slider",
        "throttle_summary": "17 Botões + Dupla Manete com Reversores + Eng Switches",
        "has_leds": False,
    },
    "tm_tflight": {
        "id": "tm_tflight",
        "name": "Thrustmaster T.Flight HOTAS (X / 4 / One)",
        "brand": "Thrustmaster",
        "stick_label": "T.FLIGHT STICK (PID B108/B67B/B68D)",
        "throttle_label": "T.FLIGHT THROTTLE MODULE",
        "stick_summary": "Gatilho + Botões R1/L1/R3 + POV + Twist Yaw",
        "throttle_summary": "Alavanca Principal + Rocker Leme + Botões 5..12",
        "has_leds": False,
    },
}


def identify_usb_device(mid: int, pid: int, oem_name: str = "") -> Optional[dict]:
    """Identifica qualquer controlador suportado (Thrustmaster ou Saitek X56) por VID/PID ou nome OEM."""
    exact = KNOWN_USB_DEVICES.get((mid, pid))
    if exact:
        return dict(exact)

    name_l = (oem_name or "").lower()

    # Fallback por nome OEM para Saitek / Logitech X56
    if "x56" in name_l or "x-56" in name_l or "rhino" in name_l:
        is_thr = "throttle" in name_l
        return {
            "kit": "saitek_x56",
            "role": "throttle" if is_thr else "stick",
            "brand": "Saitek / Logitech",
            "model": oem_name or ("Saitek X56 Throttle" if is_thr else "Saitek X56 Stick"),
            "buttons": 32 if is_thr else 17,
            "axes": 6 if is_thr else 5,
        }

    # Fallback por nome OEM para outros Thrustmaster
    if "t.16000" in name_l or "t16000" in name_l:
        return {"kit": "tm_t16000m", "role": "stick", "brand": "Thrustmaster", "model": oem_name, "buttons": 16, "axes": 4}
    if "twcs" in name_l:
        return {"kit": "tm_t16000m", "role": "throttle", "brand": "Thrustmaster", "model": oem_name, "buttons": 14, "axes": 5}
    if "tca" in name_l and "quadrant" in name_l:
        return {"kit": "tm_tca", "role": "throttle", "brand": "Thrustmaster", "model": oem_name, "buttons": 17, "axes": 2}
    if "tca" in name_l:
        return {"kit": "tm_tca", "role": "stick", "brand": "Thrustmaster", "model": oem_name, "buttons": 17, "axes": 4}
    if "t.flight" in name_l or "t-flight" in name_l:
        return {"kit": "tm_tflight", "role": "stick", "brand": "Thrustmaster", "model": oem_name, "buttons": 12, "axes": 5}
    if "warthog" in name_l or "viper tqs" in name_l:
        is_thr = "throttle" in name_l or "tqs" in name_l
        return {"kit": "warthog", "role": "throttle" if is_thr else "stick", "brand": "Thrustmaster", "model": oem_name, "buttons": 32 if is_thr else 19, "axes": 5 if is_thr else 2}

    return None
