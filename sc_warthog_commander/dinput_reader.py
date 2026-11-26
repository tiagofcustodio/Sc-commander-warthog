"""
DirectInput8 & WinMM Hardware Reader (True Dual-Engine)
Motor Primário: DirectInput8 nativo (dinput8.dll) — exatamente a mesma API usada pelo Star Citizen!
Suporta até 128 botões e 8 eixos (incluindo Sliders 0/1, Rx/Ry, Twist Rz), resolvendo 100%
a deteção do Logitech G / Saitek X56 Rhino Throttle (VID_0738&PID_A221 — 36 botões / 8 eixos),
Thrustmaster HOTAS Warthog, Dual T.16000M HOSAS, TWCS, TCA e T.Flight.
Fallback automático para WinMM (joyGetPosEx) sem exigir POV Hat.
"""

import ctypes
from ctypes import wintypes
import time
import threading
import winreg
from typing import Callable, Optional

from warthog_constants import (
    TM_VENDOR_ID,
    WARTHOG_JOYSTICK_PID,
    WARTHOG_THROTTLE_PID,
)
from hotas_devices import (
    identify_usb_device,
    VID_THRUSTMASTER,
    VID_SAITEK_MADCATZ,
    VID_SAITEK_LOGITECH,
    VID_LOGITECH,
)
from directinput8_backend import DirectInput8Manager, DirectInput8Device

winmm = ctypes.windll.winmm

JOY_RETURNX = 0x00000001
JOY_RETURNY = 0x00000002
JOY_RETURNZ = 0x00000004
JOY_RETURNR = 0x00000008
JOY_RETURNU = 0x00000010
JOY_RETURNV = 0x00000020
JOY_RETURNPOV = 0x00000040
JOY_RETURNBUTTONS = 0x00000080

JOY_RETURNALL = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNU | JOY_RETURNV |
    JOY_RETURNPOV | JOY_RETURNBUTTONS
)
JOY_RETURN_NOPOV = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNU | JOY_RETURNV |
    JOY_RETURNBUTTONS
)
JOY_RETURN_BASIC = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNPOV | JOY_RETURNBUTTONS
)
JOY_RETURN_4AXIS_NOPOV = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNBUTTONS
)
JOY_RETURN_XYB = JOY_RETURNX | JOY_RETURNY | JOY_RETURNBUTTONS

JOYERR_NOERROR = 0

# Palavras-chave de periféricos que NÃO são joysticks/manetes HOTAS (ex.: ratos gaming com analógico)
_IGNORED_PERIPHERAL_KEYWORDS = (
    "chakram", "mouse", "keyboard", "teclado", "rato", "headset",
    "wooting", "razer tartarus", "razer orbweaver", "3dconnexion",
    "spacemouse", "stream deck", "touchscreen", "virtual keyboard",
)


class JOYINFOEX(ctypes.Structure):
    _fields_ = [
        ('dwSize', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('dwXpos', wintypes.DWORD),
        ('dwYpos', wintypes.DWORD),
        ('dwZpos', wintypes.DWORD),
        ('dwRpos', wintypes.DWORD),
        ('dwUpos', wintypes.DWORD),
        ('dwVpos', wintypes.DWORD),
        ('dwButtons', wintypes.DWORD),
        ('dwButtonNumber', wintypes.DWORD),
        ('dwPOV', wintypes.DWORD),
        ('dwReserved1', wintypes.DWORD),
        ('dwReserved2', wintypes.DWORD)
    ]


class JOYCAPSW(ctypes.Structure):
    _fields_ = [
        ('wMid', wintypes.WORD),
        ('wPid', wintypes.WORD),
        ('szPname', wintypes.WCHAR * 32),
        ('wXmin', wintypes.UINT),
        ('wXmax', wintypes.UINT),
        ('wYmin', wintypes.UINT),
        ('wYmax', wintypes.UINT),
        ('wZmin', wintypes.UINT),
        ('wZmax', wintypes.UINT),
        ('wNumButtons', wintypes.UINT),
        ('wPeriodMin', wintypes.UINT),
        ('wPeriodMax', wintypes.UINT),
        ('wRmin', wintypes.UINT),
        ('wRmax', wintypes.UINT),
        ('wUmin', wintypes.UINT),
        ('wUmax', wintypes.UINT),
        ('wVmin', wintypes.UINT),
        ('wVmax', wintypes.UINT),
        ('wCaps', wintypes.UINT),
        ('wMaxAxes', wintypes.UINT),
        ('wNumAxes', wintypes.UINT),
        ('wMaxButtons', wintypes.UINT),
        ('szRegKey', wintypes.WCHAR * 32),
        ('szOEMVxD', wintypes.WCHAR * 260),
    ]


def _get_oem_device_name(mid: int, pid: int) -> str:
    """Obtém o nome real do dispositivo OEM no Registo do Windows (ex: 'Throttle - HOTAS Warthog')."""
    try:
        key_path = f"SYSTEM\\CurrentControlSet\\Control\\MediaProperties\\PrivateProperties\\Joystick\\OEM\\VID_{mid:04X}&PID_{pid:04X}"
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                with winreg.OpenKey(root, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, "OEMName")
                    if val:
                        return str(val)
            except OSError:
                continue
    except Exception:
        pass
    return ""


def _is_ignored_peripheral(name: str, btns: int, axes: int) -> bool:
    """Ignora interfaces HID vazias (0 botões e 0 eixos) e ratos/teclados gaming (ex: ROG Chakram)."""
    if btns == 0 and axes == 0:
        return True
    nl = (name or "").lower()
    return any(k in nl for k in _IGNORED_PERIPHERAL_KEYWORDS)


def _pov_to_dir(pov: int) -> str:
    """Converte valor de ângulo POV (centésimos de grau) em direção cardinal."""
    if pov == 0xFFFF or pov > 36000:
        return "CENTER"
    if pov >= 31500 or pov < 4500:
        return "UP"
    if 4500 <= pov < 13500:
        return "RIGHT"
    if 13500 <= pov < 22500:
        return "DOWN"
    if 22500 <= pov < 31500:
        return "LEFT"
    return "CENTER"


class WarthogDeviceWatcher:
    """
    Monitora em tempo real controladores HOTAS / HOSAS via DirectInput8 (primário)
    e WinMM (fallback), suportando Thrustmaster Warthog, Logitech G / Saitek X56 Rhino,
    Dual T.16000M HOSAS, TWCS, TCA e T.Flight.
    """

    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # Backend DirectInput8 nativo (detecta >32 botões, 8 eixos, X56 Throttle sem falhas WinMM)
        self._di8 = DirectInput8Manager()
        self._di_stick_dev: Optional[DirectInput8Device] = None
        self._di_throttle_dev: Optional[DirectInput8Device] = None
        self._di_stick_info: Optional[dict] = None
        self._di_throttle_info: Optional[dict] = None
        self._backend_mode: str = "dinput8" if self._di8.available() else "winmm"
        self._winmm_slot_flags: dict[int, int] = {}

        # Slots/identificadores ativos confirmados (int WinMM ou guid_key DirectInput8)
        self.stick_slot = None
        self.throttle_slot = None
        self.stick_name: str = "Desconectado"
        self.throttle_name: str = "Desconectado"
        self.detected_kit: str = "warthog"
        self.detected_stick_kit: Optional[str] = None
        self.detected_throttle_kit: Optional[str] = None
        self.left_device_role: str = "throttle"  # 'throttle' (HOTAS), 'stick' (HOSAS 2 Joysticks), ou 'none' (1 Stick)
        self.detected_devices: list[dict] = []

        # Estados de botões anteriores (bitmasks arbitrárias até 64 bits)
        self.prev_stick_buttons = 0
        self.prev_throttle_buttons = 0
        self.prev_stick_pov = "CENTER"
        self.prev_throttle_pov = "CENTER"

        # Estado do Detentor Físico IDLE CUTOFF (Apenas Warthog: Botões 29 e 30 da Manete)
        self.cutoff_left = False
        self.cutoff_right = False

        # Eixos atuais (0..65535)
        self.stick_axes = {"x": 32767, "y": 32767, "rz": 32767}
        self.throttle_axes = {
            "z": 65535,      # Manete Esquerda (0=Máx Frente, 65535=Idle Trás)
            "rz": 65535,     # Manete Direita Principal (0=Máx Frente, 65535=Idle Trás)
            "slider": 32767, # Roda Fricção / Rotativo F (Speed Limiter)
            "slew_x": 32767, # Mini-stick Slew / Polegar X
            "slew_y": 32767  # Mini-stick Slew / Polegar Y
        }

        # Callbacks
        self.on_button_change: Optional[Callable[[str, int, bool], None]] = None
        self.on_hat_change: Optional[Callable[[str, str], None]] = None
        self.on_axis_change: Optional[Callable[[str, str, int], None]] = None
        self.on_device_status_change: Optional[Callable[[bool, bool], None]] = None
        self.on_cutoff_change: Optional[Callable[[bool, bool], None]] = None
        self.on_log: Optional[Callable[[str], None]] = None

    def log(self, message: str):
        if self.on_log:
            self.on_log(message)
        else:
            print(f"[HOTASWatcher] {message}")

    def _poll_winmm_slot(self, slot: int, jie: JOYINFOEX) -> bool:
        """Lê um slot WinMM com fallback progressivo (inclui modo sem POV para X56 Throttle!)."""
        preferred = self._winmm_slot_flags.get(slot)
        flag_sequence = (
            [preferred] if preferred else []
        ) + [
            JOY_RETURNALL,
            JOY_RETURN_NOPOV,
            JOY_RETURN_BASIC,
            JOY_RETURN_4AXIS_NOPOV,
            JOY_RETURN_XYB,
            JOY_RETURNBUTTONS,
        ]
        seen = set()
        for fl in flag_sequence:
            if not fl or fl in seen:
                continue
            seen.add(fl)
            jie.dwSize = ctypes.sizeof(JOYINFOEX)
            jie.dwFlags = fl
            if winmm.joyGetPosEx(slot, ctypes.byref(jie)) == JOYERR_NOERROR:
                self._winmm_slot_flags[slot] = fl
                return True
        return False

    def _collect_raw_devices(self) -> tuple[str, list[dict]]:
        """
        Recolhe todos os dispositivos fisicamente ligados usando DirectInput8 (primário)
        e faz fallback automático para WinMM caso DI8 não encontre nenhum controlador.
        """
        # 1. Tenta DirectInput8 nativo (vê TODOS os dispositivos do Star Citizen: X56 36B/8E, Warthog, T.16000M...)
        if self._di8.available():
            di_devs = self._di8.enumerate_devices()
            enriched = []
            for d in di_devs:
                mid, pid = d["mid"], d["pid"]
                btns, axes = d["btns"], d["axes"]
                oem_name = d["name"] or _get_oem_device_name(mid, pid)
                if _is_ignored_peripheral(oem_name, btns, axes):
                    continue
                matched = identify_usb_device(mid, pid, oem_name)
                enriched.append({
                    **d,
                    "slot": d["guid_key"],
                    "backend": "dinput8",
                    "name": oem_name,
                    "matched": matched,
                    "kit": matched["kit"] if matched else "generic",
                    "role": matched["role"] if matched else ("throttle" if ("throttle" in oem_name.lower() or btns >= 20) else "stick"),
                    "brand": matched["brand"] if matched else "USB HID",
                    "model": matched["model"] if matched else oem_name,
                })
            if enriched:
                return "dinput8", enriched

        # 2. Fallback WinMM (joyGetDevCapsW + joyGetPosEx sem obrigar POV)
        num_devs = winmm.joyGetNumDevs()
        caps = JOYCAPSW()
        caps_size = ctypes.sizeof(JOYCAPSW)
        test_jie = JOYINFOEX()
        winmm_devs = []

        for slot in range(num_devs):
            if winmm.joyGetDevCapsW(slot, ctypes.byref(caps), caps_size) != JOYERR_NOERROR:
                continue
            if not self._poll_winmm_slot(slot, test_jie):
                continue

            mid = caps.wMid
            pid = caps.wPid
            btns = caps.wNumButtons
            axes = caps.wNumAxes
            oem_name = _get_oem_device_name(mid, pid) or caps.szPname
            if _is_ignored_peripheral(oem_name, btns, axes):
                continue
            matched = identify_usb_device(mid, pid, oem_name)
            winmm_devs.append({
                "slot": slot,
                "backend": "winmm",
                "mid": mid,
                "pid": pid,
                "vid_hex": f"{mid:04X}",
                "pid_hex": f"{pid:04X}",
                "btns": btns,
                "axes": axes,
                "name": oem_name,
                "matched": matched,
                "kit": matched["kit"] if matched else "generic",
                "role": matched["role"] if matched else ("throttle" if ("throttle" in oem_name.lower() or btns >= 20) else "stick"),
                "brand": matched["brand"] if matched else "USB HID",
                "model": matched["model"] if matched else oem_name,
            })

        return "winmm", winmm_devs

    def scan_devices(self):
        """
        Varre todos os controladores USB ligados em 2 passagens prioritárias:
        - Passagem 1: Atribui manetes dedicadas (Throttle) e o Manche principal (Stick) —
          impedindo que interfaces compostas ou 2º stick roubem o slot da manete!
        - Passagem 2: Só se NÃO houver manete dedicada, atribui um 2º stick real como HOSAS (Dual Stick).
        """
        backend, devs = self._collect_raw_devices()
        self._backend_mode = backend

        stick_dev = None
        throttle_dev = None
        left_role = "none"

        # PASSAGEM 1: Dispositivos conhecidos (matched) — Throttle dedicado + 1º Stick
        for d in devs:
            m = d.get("matched")
            if not m:
                continue
            if m["role"] == "throttle" and throttle_dev is None:
                throttle_dev = d
                left_role = "throttle"
            elif m["role"] == "stick" and stick_dev is None:
                stick_dev = d

        # PASSAGEM 2: Deteção por nome / assinatura de botões para controladores não tabelados
        for d in devs:
            if d is stick_dev or d is throttle_dev:
                continue
            nl = d["name"].lower()
            is_thr_hint = any(k in nl for k in ("throttle", "quadrant", "twcs", "tqs")) or d["btns"] >= 24
            if is_thr_hint and throttle_dev is None:
                throttle_dev = d
                left_role = "throttle"
            elif stick_dev is None and d["btns"] >= 8:
                stick_dev = d

        # PASSAGEM 3: Modo HOSAS (2º Joystick ligado simultaneamente quando NÃO há manete dedicada!)
        if throttle_dev is None:
            for d in devs:
                if d is stick_dev:
                    continue
                if d["btns"] >= 8 and d["axes"] >= 2:
                    throttle_dev = d
                    left_role = "stick"
                    break

        # PASSAGEM 4: Fallback para VIDs suportados (Thrustmaster / Saitek / Logitech)
        supported_vids = (VID_THRUSTMASTER, VID_SAITEK_MADCATZ, VID_SAITEK_LOGITECH, VID_LOGITECH)
        if stick_dev is None:
            for d in devs:
                if d is not throttle_dev and d["mid"] in supported_vids:
                    stick_dev = d
                    break
        if throttle_dev is None:
            for d in devs:
                if d is not stick_dev and d["mid"] in supported_vids:
                    throttle_dev = d
                    left_role = "throttle" if d["role"] == "throttle" else "stick"
                    break

        # Atualiza nomes, kits e info para abertura DirectInput8
        stick_found = stick_dev["slot"] if stick_dev else None
        throttle_found = throttle_dev["slot"] if throttle_dev else None
        self._di_stick_info = stick_dev if (stick_dev and backend == "dinput8") else None
        self._di_throttle_info = throttle_dev if (throttle_dev and backend == "dinput8") else None

        self.stick_name = stick_dev["model"] if stick_dev else "Desconectado"
        if throttle_dev:
            self.throttle_name = (
                f"{throttle_dev['model']} (Esq. / HOSAS)"
                if left_role == "stick"
                else throttle_dev["model"]
            )
        else:
            self.throttle_name = "Desconectado"

        stick_kit = stick_dev["kit"] if (stick_dev and stick_dev["kit"] != "generic") else None
        throttle_kit = throttle_dev["kit"] if (throttle_dev and throttle_dev["kit"] != "generic") else None

        self.detected_stick_kit = stick_kit
        self.detected_throttle_kit = throttle_kit
        self.left_device_role = left_role if throttle_found is not None else "none"

        if stick_kit == "tm_t16000m" and throttle_kit == "tm_t16000m" and left_role == "stick":
            self.detected_kit = "tm_t16000m_hosas"
        elif stick_kit == "tm_t16000m" and throttle_found is None:
            self.detected_kit = "tm_t16000m_single"
        elif stick_kit or throttle_kit:
            self.detected_kit = stick_kit or throttle_kit

        # Guarda lista limpa (serializável em JSON para o WebSocket)
        self.detected_devices = [
            {
                "slot": str(d["slot"])[:12] if backend == "dinput8" else d["slot"],
                "backend": d["backend"],
                "mid": d["mid"],
                "pid": d["pid"],
                "vid_hex": d["vid_hex"],
                "pid_hex": d["pid_hex"],
                "btns": d["btns"],
                "axes": d["axes"],
                "name": d["name"],
                "kit": d["kit"],
                "role": d["role"],
                "brand": d["brand"],
                "model": d["model"],
            }
            for d in devs
        ]
        return stick_found, throttle_found

    def _close_di_stick(self):
        if self._di_stick_dev:
            self._di_stick_dev.close()
            self._di_stick_dev = None

    def _close_di_throttle(self):
        if self._di_throttle_dev:
            self._di_throttle_dev.close()
            self._di_throttle_dev = None

    def rescan_now(self):
        """Força re-scan imediato e reabre handles DirectInput8 (usado pelo botão Re-escanear USB)."""
        new_stick, new_throttle = self.scan_devices()
        self._close_di_stick()
        self._close_di_throttle()
        self.stick_slot = new_stick
        self.throttle_slot = new_throttle
        if self._backend_mode == "dinput8":
            if new_stick is not None and self._di_stick_info:
                self._di_stick_dev = self._di8.open_device(self._di_stick_info)
                if self._di_stick_dev:
                    self.prev_stick_buttons = self._di_stick_dev.get_buttons_mask()
            if new_throttle is not None and self._di_throttle_info:
                self._di_throttle_dev = self._di8.open_device(self._di_throttle_info)
                if self._di_throttle_dev:
                    self.prev_throttle_buttons = self._di_throttle_dev.get_buttons_mask()
        return new_stick, new_throttle

    def start(self):
        """Inicia a thread de monitorização a 50Hz."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log(f"Monitorização HOTAS iniciada (Motor: {self._backend_mode.upper()}).")

    def stop(self):
        """Para a monitorização e liberta handles DirectInput8."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._close_di_stick()
        self._close_di_throttle()
        self.log("Monitorização de dispositivos parada.")

    def _sync_initial_throttle_switches(self, buttons_mask: int):
        """Sincroniza o estado físico inicial dos interruptores fixos da Manete Warthog."""
        for b in (6, 7, 8, 9, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 29, 30):
            is_down = bool(buttons_mask & (1 << (b - 1)))
            if is_down and self.on_button_change:
                self.on_button_change("throttle", b, True)

    def _read_stick_state(self, jie_stick: JOYINFOEX) -> Optional[tuple[int, int, dict]]:
        """Devolve (buttons_mask, pov, axes_dict) ou None se desconectado."""
        if self._backend_mode == "dinput8":
            if self._di_stick_dev and self._di_stick_dev.poll():
                return (
                    self._di_stick_dev.get_buttons_mask(),
                    self._di_stick_dev.get_pov(),
                    self._di_stick_dev.get_axes(),
                )
            return None
        else:
            if isinstance(self.stick_slot, int) and self._poll_winmm_slot(self.stick_slot, jie_stick):
                return (
                    jie_stick.dwButtons,
                    jie_stick.dwPOV,
                    {
                        "x": jie_stick.dwXpos,
                        "y": jie_stick.dwYpos,
                        "z": jie_stick.dwZpos,
                        "rx": jie_stick.dwUpos,
                        "ry": jie_stick.dwVpos,
                        "rz": jie_stick.dwRpos,
                        "slider0": jie_stick.dwUpos,
                        "slider1": jie_stick.dwVpos,
                    },
                )
            return None

    def _read_throttle_state(self, jie_throttle: JOYINFOEX) -> Optional[tuple[int, int, dict]]:
        """Devolve (buttons_mask, pov, axes_dict) ou None se desconectado."""
        if self._backend_mode == "dinput8":
            if self._di_throttle_dev and self._di_throttle_dev.poll():
                return (
                    self._di_throttle_dev.get_buttons_mask(),
                    self._di_throttle_dev.get_pov(),
                    self._di_throttle_dev.get_axes(),
                )
            return None
        else:
            if isinstance(self.throttle_slot, int) and self._poll_winmm_slot(self.throttle_slot, jie_throttle):
                return (
                    jie_throttle.dwButtons,
                    jie_throttle.dwPOV,
                    {
                        "x": jie_throttle.dwXpos,
                        "y": jie_throttle.dwYpos,
                        "z": jie_throttle.dwZpos,
                        "rx": jie_throttle.dwUpos,
                        "ry": jie_throttle.dwVpos,
                        "rz": jie_throttle.dwRpos,
                        "slider0": jie_throttle.dwUpos,
                        "slider1": jie_throttle.dwVpos,
                    },
                )
            return None

    def _loop(self):
        jie_stick = JOYINFOEX()
        jie_throttle = JOYINFOEX()

        last_scan_time = 0.0
        last_stick_status = False
        last_throttle_status = False

        while self.running:
            now = time.time()
            # Re-escaneia dispositivos a cada 1.5s se faltar stick ou manete
            if (self.stick_slot is None or self.throttle_slot is None) and (now - last_scan_time > 1.5):
                new_stick, new_throttle = self.scan_devices()

                if new_stick != self.stick_slot:
                    self._close_di_stick()
                    self.stick_slot = new_stick
                    if new_stick is not None:
                        if self._backend_mode == "dinput8" and self._di_stick_info:
                            self._di_stick_dev = self._di8.open_device(self._di_stick_info)
                            if self._di_stick_dev:
                                self.prev_stick_buttons = self._di_stick_dev.get_buttons_mask()
                        self.log(f"Manche detetado ({self._backend_mode}): {self.stick_name}")

                if new_throttle != self.throttle_slot:
                    self._close_di_throttle()
                    self.throttle_slot = new_throttle
                    if new_throttle is not None:
                        if self._backend_mode == "dinput8" and self._di_throttle_info:
                            self._di_throttle_dev = self._di8.open_device(self._di_throttle_info)
                            if self._di_throttle_dev:
                                init_mask = self._di_throttle_dev.get_buttons_mask()
                                self.prev_throttle_buttons = init_mask
                                if self.detected_throttle_kit == "warthog":
                                    self._sync_initial_throttle_switches(init_mask)
                        elif isinstance(new_throttle, int) and self._poll_winmm_slot(new_throttle, jie_throttle):
                            self.prev_throttle_buttons = jie_throttle.dwButtons
                            if self.detected_throttle_kit == "warthog":
                                self._sync_initial_throttle_switches(jie_throttle.dwButtons)
                        self.log(f"Manete detetada ({self._backend_mode}): {self.throttle_name}")

                last_scan_time = now

            stick_connected = False
            throttle_connected = False

            # 1. Leitura do Manche (Stick)
            if self.stick_slot is not None:
                st = self._read_stick_state(jie_stick)
                if st is not None:
                    stick_connected = True
                    curr_buttons, pov_raw, ax = st
                    diff = curr_buttons ^ self.prev_stick_buttons
                    if diff:
                        for b in range(1, 33):
                            mask = 1 << (b - 1)
                            if diff & mask:
                                is_down = bool(curr_buttons & mask)
                                if self.on_button_change:
                                    self.on_button_change("stick", b, is_down)
                        self.prev_stick_buttons = curr_buttons

                    pov_dir = _pov_to_dir(pov_raw)
                    if pov_dir != self.prev_stick_pov:
                        self.prev_stick_pov = pov_dir
                        if self.on_hat_change:
                            self.on_hat_change("stick", pov_dir)

                    self.stick_axes["x"] = ax["x"]
                    self.stick_axes["y"] = ax["y"]
                    self.stick_axes["rz"] = ax["rz"]
                    if self.on_axis_change:
                        self.on_axis_change("stick", "x", ax["x"])
                        self.on_axis_change("stick", "y", ax["y"])
                        self.on_axis_change("stick", "rz", ax["rz"])
                else:
                    self._close_di_stick()
                    self.stick_slot = None
                    self.stick_name = "Desconectado"

            # 2. Leitura da Manete (Throttle / 2º Stick HOSAS)
            if self.throttle_slot is not None:
                th = self._read_throttle_state(jie_throttle)
                if th is not None:
                    throttle_connected = True
                    curr_buttons, pov_raw, ax = th

                    # Idle Cutoff apenas no Thrustmaster Warthog (Botões 29/30)
                    if self.detected_throttle_kit == "warthog":
                        cut_l = bool(curr_buttons & (1 << 28))
                        cut_r = bool(curr_buttons & (1 << 29))
                    else:
                        cut_l = False
                        cut_r = False
                    if (cut_l != self.cutoff_left) or (cut_r != self.cutoff_right):
                        self.cutoff_left = cut_l
                        self.cutoff_right = cut_r
                        if self.on_cutoff_change:
                            self.on_cutoff_change(cut_l, cut_r)

                    diff = curr_buttons ^ self.prev_throttle_buttons
                    if diff:
                        # Lê até 40 botões (Logitech X56 Throttle possui até 36 botões incluindo M1/M2/S1!)
                        for b in range(1, 41):
                            mask = 1 << (b - 1)
                            if diff & mask:
                                is_down = bool(curr_buttons & mask)
                                if self.on_button_change:
                                    self.on_button_change("throttle", b, is_down)
                        self.prev_throttle_buttons = curr_buttons

                    pov_dir = _pov_to_dir(pov_raw)
                    if pov_dir != self.prev_throttle_pov:
                        self.prev_throttle_pov = pov_dir
                        if self.on_hat_change:
                            self.on_hat_change("throttle", pov_dir)

                    # Mapeamento de Eixos da Manete consoante o hardware ligado:
                    # - Logitech / Saitek X56 Throttle:
                    #   x = Alavanca Esq., y = Alavanca Dir., slider0 = Rotativo F (Speed Limiter),
                    #   rx/ry = Mini-Stick do Polegar
                    # - Thrustmaster Warthog / outros:
                    #   z = Alavanca Esq., rz = Alavanca Dir., slider0 = Roda Cinzenta (Slider 1),
                    #   x/y = Mini-Stick Slew
                    if self.detected_throttle_kit == "saitek_x56":
                        self.throttle_axes["z"] = ax["x"]
                        self.throttle_axes["rz"] = ax["y"]
                        self.throttle_axes["slider"] = ax["slider0"] if self._backend_mode == "dinput8" else ax["z"]
                        self.throttle_axes["slew_x"] = ax["rx"]
                        self.throttle_axes["slew_y"] = ax["ry"]
                    else:
                        self.throttle_axes["z"] = ax["z"]
                        self.throttle_axes["rz"] = ax["rz"]
                        self.throttle_axes["slider"] = ax["slider0"]
                        self.throttle_axes["slew_x"] = ax["x"]
                        self.throttle_axes["slew_y"] = ax["y"]

                    if self.on_axis_change:
                        self.on_axis_change("throttle", "z", self.throttle_axes["z"])
                        self.on_axis_change("throttle", "rz", self.throttle_axes["rz"])
                        self.on_axis_change("throttle", "slider", self.throttle_axes["slider"])
                else:
                    self._close_di_throttle()
                    self.throttle_slot = None
                    self.throttle_name = "Desconectado"

            # Notifica mudança de status de conexão
            if (stick_connected != last_stick_status) or (throttle_connected != last_throttle_status):
                last_stick_status = stick_connected
                last_throttle_status = throttle_connected
                if self.on_device_status_change:
                    self.on_device_status_change(stick_connected, throttle_connected)

            # Polling a 50Hz (~20ms)
            time.sleep(0.02)
