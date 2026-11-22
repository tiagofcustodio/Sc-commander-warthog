"""
DirectInput8 & WinMM Hardware Reader (Dual-Engine)
Lê em tempo real o estado de todos os botões (19 no Manche + 32 na Manete), POV Hats e todos os eixos
(X, Y, Z, Rz, Slider) do Thrustmaster HOTAS Warthog sem falsos positivos de slots desligados ou Gamepads.
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
)

winmm = ctypes.windll.winmm

JOY_RETURNX = 0x00000001
JOY_RETURNY = 0x00000002
JOY_RETURNZ = 0x00000004
JOY_RETURNR = 0x00000008
JOY_RETURNU = 0x00000010
JOY_RETURNV = 0x00000020
JOY_RETURNPOV = 0x00000040
JOY_RETURNBUTTONS = 0x00000080
JOY_RETURNRAWDATA = 0x00000100
JOY_RETURNPOVCTS = 0x00000200
JOY_RETURNCENTERED = 0x00000400
JOY_USEDEADZONE = 0x00000800
JOY_RETURNALL = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNU | JOY_RETURNV |
    JOY_RETURNPOV | JOY_RETURNBUTTONS
)
JOY_RETURN_BASIC = (
    JOY_RETURNX | JOY_RETURNY | JOY_RETURNZ |
    JOY_RETURNR | JOY_RETURNPOV | JOY_RETURNBUTTONS
)

JOYERR_NOERROR = 0


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
    """Monitora a conexão e o estado em tempo real do Manche e da Manete Warthog."""

    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # Slots ativos confirmados (0..15)
        self.stick_slot: Optional[int] = None
        self.throttle_slot: Optional[int] = None
        self.stick_name: str = "Desconectado"
        self.throttle_name: str = "Desconectado"
        self.detected_kit: str = "warthog"
        self.detected_stick_kit: Optional[str] = None
        self.detected_throttle_kit: Optional[str] = None
        self.detected_devices: list[dict] = []

        # Estados de botões anteriores (bitmasks de 32 bits)
        self.prev_stick_buttons = 0
        self.prev_throttle_buttons = 0
        self.prev_stick_pov = "CENTER"
        self.prev_throttle_pov = "CENTER"

        # Estado do Detentor Físico IDLE CUTOFF (Botões 29 e 30 da Manete)
        self.cutoff_left = False   # Botão 29 premido = Manete Esq. em OFF
        self.cutoff_right = False  # Botão 30 premido = Manete Dir. em OFF

        # Eixos atuais (0..65535)
        self.stick_axes = {"x": 32767, "y": 32767}
        self.throttle_axes = {
            "z": 65535,      # Manete Esquerda (0=Máx Frente, 65535=Idle Trás)
            "rz": 65535,     # Manete Direita Principal (0=Máx Frente, 65535=Idle Trás)
            "slider": 32767, # Roda de Fricção Cinzenta Central (Slider 1)
            "slew_x": 32767, # Mini-stick Slew X
            "slew_y": 32767  # Mini-stick Slew Y
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
            print(f"[WarthogWatcher] {message}")

    def _poll_slot(self, slot: int, jie: JOYINFOEX) -> bool:
        """Lê o estado de um slot winmm garantindo fallback de flags."""
        jie.dwSize = ctypes.sizeof(JOYINFOEX)
        jie.dwFlags = JOY_RETURNALL
        res = winmm.joyGetPosEx(slot, ctypes.byref(jie))
        if res == JOYERR_NOERROR:
            return True
        jie.dwSize = ctypes.sizeof(JOYINFOEX)
        jie.dwFlags = JOY_RETURN_BASIC
        res = winmm.joyGetPosEx(slot, ctypes.byref(jie))
        return res == JOYERR_NOERROR

    def scan_devices(self) -> tuple[Optional[int], Optional[int]]:
        """
        Varre todos os slots de joystick do Windows, verificando fisicamente com joyGetPosEx
        quais estão REALMENTE ligados (ignorando slots fantasma ou desligados) e identificando
        o Manche Warthog (PID 0x0402, 19 botões) e a Manete Warthog (PID 0x0404, 32 botões).
        """
        num_devs = winmm.joyGetNumDevs()
        stick_found = None
        throttle_found = None
        stick_kit = None
        throttle_kit = None

        caps = JOYCAPSW()
        caps_size = ctypes.sizeof(JOYCAPSW)
        test_jie = JOYINFOEX()

        connected_slots = []

        for slot in range(num_devs):
            res_caps = winmm.joyGetDevCapsW(slot, ctypes.byref(caps), caps_size)
            if res_caps != JOYERR_NOERROR:
                continue

            # CRÍTICO: Verifica se o dispositivo está FISICAMENTE conectado agora!
            # No Windows, joyGetDevCapsW retorna 0 para controladores antigos no registo mesmo desligados.
            if not self._poll_slot(slot, test_jie):
                continue

            mid = caps.wMid
            pid = caps.wPid
            btns = caps.wNumButtons
            axes = caps.wNumAxes
            oem_name = _get_oem_device_name(mid, pid) or caps.szPname
            pname_lower = oem_name.lower()

            matched = identify_usb_device(mid, pid, oem_name)

            connected_slots.append({
                "slot": slot,
                "mid": mid,
                "pid": pid,
                "vid_hex": f"{mid:04X}",
                "pid_hex": f"{pid:04X}",
                "btns": btns,
                "axes": axes,
                "name": oem_name,
                "kit": matched["kit"] if matched else "generic",
                "role": matched["role"] if matched else ("throttle" if btns >= 24 else "stick"),
                "brand": matched["brand"] if matched else "USB HID",
                "model": matched["model"] if matched else oem_name,
            })

            # 1. Identificação unificada Multi-HOTAS (Thrustmaster Warthog / T.16000M / TWCS / TCA / T.Flight / Viper + Saitek/Logitech X56 Rhino)
            if matched:
                if matched["role"] == "throttle" and throttle_found is None:
                    throttle_found = slot
                    self.throttle_name = matched["model"]
                    throttle_kit = matched["kit"]
                    continue
                elif matched["role"] == "stick" and stick_found is None:
                    stick_found = slot
                    self.stick_name = matched["model"]
                    stick_kit = matched["kit"]
                    continue

            # 2. Identificação por PID ou nome OEM no Registo
            if pid == WARTHOG_THROTTLE_PID or "throttle" in pname_lower or "0404" in pname_lower:
                throttle_found = slot
                self.throttle_name = oem_name or f"HOTAS Throttle (Slot {slot})"
                continue
            elif pid == WARTHOG_JOYSTICK_PID or ("joystick" in pname_lower and "warthog" in pname_lower):
                stick_found = slot
                self.stick_name = oem_name or f"HOTAS Stick (Slot {slot})"
                continue

            # 3. Identificação por assinatura de botões (32 botões = Manete, 16-19 botões = Manche)
            if btns == 32 and throttle_found is None:
                throttle_found = slot
                self.throttle_name = oem_name or f"HOTAS Throttle 32-Btn (Slot {slot})"
            elif btns in (16, 17, 19) and stick_found is None:
                stick_found = slot
                self.stick_name = oem_name or f"HOTAS Stick {btns}-Btn (Slot {slot})"

        # 4. Fallback para controladores Thrustmaster / Saitek / Logitech secundários
        supported_vids = (VID_THRUSTMASTER, VID_SAITEK_MADCATZ, VID_SAITEK_LOGITECH)
        if throttle_found is None:
            for dev in connected_slots:
                if dev["slot"] != stick_found and (dev["btns"] >= 24 or dev["mid"] in supported_vids):
                    throttle_found = dev["slot"]
                    self.throttle_name = dev["name"]
                    break

        if stick_found is None:
            for dev in connected_slots:
                if dev["slot"] != throttle_found and (dev["btns"] >= 12 or dev["mid"] in supported_vids):
                    stick_found = dev["slot"]
                    self.stick_name = dev["name"]
                    break

        self.detected_stick_kit = stick_kit
        self.detected_throttle_kit = throttle_kit
        if stick_kit or throttle_kit:
            self.detected_kit = stick_kit or throttle_kit
        self.detected_devices = connected_slots
        return stick_found, throttle_found

    def start(self):
        """Inicia a thread de monitorização a 50Hz."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log("Monitorização de dispositivos Warthog iniciada.")

    def stop(self):
        """Para a monitorização."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.log("Monitorização de dispositivos parada.")

    def _sync_initial_throttle_switches(self, buttons_mask: int):
        """Sincroniza o estado físico inicial dos interruptores da Manete na interface."""
        for b in (6, 7, 8, 9, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 29, 30):
            is_down = bool(buttons_mask & (1 << (b - 1)))
            if is_down and self.on_button_change:
                self.on_button_change("throttle", b, True)

    def _loop(self):
        jie_stick = JOYINFOEX()
        jie_throttle = JOYINFOEX()

        last_scan_time = 0.0
        last_stick_status = False
        last_throttle_status = False

        while self.running:
            now = time.time()
            # Re-escaneia slots a cada 1.5s se algum dos dois dispositivos não estiver atribuído
            if (self.stick_slot is None or self.throttle_slot is None) and (now - last_scan_time > 1.5):
                new_stick, new_throttle = self.scan_devices()
                if new_stick != self.stick_slot:
                    self.stick_slot = new_stick
                    if new_stick is not None:
                        self.log(f"Manche detetado no Slot {new_stick}: {self.stick_name}")
                if new_throttle != self.throttle_slot:
                    self.throttle_slot = new_throttle
                    if new_throttle is not None:
                        self.log(f"Manete detetada no Slot {new_throttle}: {self.throttle_name}")
                        if self._poll_slot(new_throttle, jie_throttle):
                            self.prev_throttle_buttons = jie_throttle.dwButtons
                            self._sync_initial_throttle_switches(jie_throttle.dwButtons)
                last_scan_time = now

            stick_connected = False
            throttle_connected = False

            # 1. Leitura do Manche (Stick - 19 Botões + POV Hat + Eixos X/Y)
            if self.stick_slot is not None:
                if self._poll_slot(self.stick_slot, jie_stick):
                    stick_connected = True
                    curr_buttons = jie_stick.dwButtons
                    diff = curr_buttons ^ self.prev_stick_buttons
                    if diff:
                        for b in range(1, 20):
                            mask = 1 << (b - 1)
                            if diff & mask:
                                is_down = bool(curr_buttons & mask)
                                if self.on_button_change:
                                    self.on_button_change("stick", b, is_down)
                        self.prev_stick_buttons = curr_buttons

                    # POV Hat do Manche (Trim Hat)
                    pov_dir = _pov_to_dir(jie_stick.dwPOV)
                    if pov_dir != self.prev_stick_pov:
                        self.prev_stick_pov = pov_dir
                        if self.on_hat_change:
                            self.on_hat_change("stick", pov_dir)

                    self.stick_axes["x"] = jie_stick.dwXpos
                    self.stick_axes["y"] = jie_stick.dwYpos
                    if self.on_axis_change:
                        self.on_axis_change("stick", "x", jie_stick.dwXpos)
                        self.on_axis_change("stick", "y", jie_stick.dwYpos)
                else:
                    self.stick_slot = None
                    self.stick_name = "Desconectado"

            # 2. Leitura da Manete (Throttle - 32 Botões + Coolie Hat + 5 Eixos)
            if self.throttle_slot is not None:
                if self._poll_slot(self.throttle_slot, jie_throttle):
                    throttle_connected = True
                    curr_buttons = jie_throttle.dwButtons

                    # Deteta estado de bloqueio IDLE CUTOFF (Botão 29 = Esq, Botão 30 = Dir)
                    cut_l = bool(curr_buttons & (1 << 28))
                    cut_r = bool(curr_buttons & (1 << 29))
                    if (cut_l != self.cutoff_left) or (cut_r != self.cutoff_right):
                        self.cutoff_left = cut_l
                        self.cutoff_right = cut_r
                        if self.on_cutoff_change:
                            self.on_cutoff_change(cut_l, cut_r)

                    diff = curr_buttons ^ self.prev_throttle_buttons
                    if diff:
                        for b in range(1, 33):
                            mask = 1 << (b - 1)
                            if diff & mask:
                                is_down = bool(curr_buttons & mask)
                                if self.on_button_change:
                                    self.on_button_change("throttle", b, is_down)
                        self.prev_throttle_buttons = curr_buttons

                    # POV Hat da Manete (Coolie Hat)
                    pov_dir = _pov_to_dir(jie_throttle.dwPOV)
                    if pov_dir != self.prev_throttle_pov:
                        self.prev_throttle_pov = pov_dir
                        if self.on_hat_change:
                            self.on_hat_change("throttle", pov_dir)

                    # Todos os 5 Eixos da Manete:
                    # dwZpos = Manete Esquerda (Z)
                    # dwRpos = Manete Direita Principal (Rz)
                    # dwUpos = Roda Cinzenta de Fricção (Slider 1)
                    # dwXpos / dwYpos = Mini-stick Slew
                    self.throttle_axes["z"] = jie_throttle.dwZpos
                    self.throttle_axes["rz"] = jie_throttle.dwRpos
                    self.throttle_axes["slider"] = jie_throttle.dwUpos
                    self.throttle_axes["slew_x"] = jie_throttle.dwXpos
                    self.throttle_axes["slew_y"] = jie_throttle.dwYpos

                    if self.on_axis_change:
                        self.on_axis_change("throttle", "z", jie_throttle.dwZpos)
                        self.on_axis_change("throttle", "rz", jie_throttle.dwRpos)
                        self.on_axis_change("throttle", "slider", jie_throttle.dwUpos)
                else:
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
