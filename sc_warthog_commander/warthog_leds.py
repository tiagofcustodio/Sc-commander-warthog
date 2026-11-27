"""
Warthog LEDs Controller - Official Thrustmaster 36-Byte USB HID Protocol
Controla a Retroiluminação do painel (bit 0x08, intensidade 0-5) e os 5 LEDs verdes da base
da Manete HOTAS Warthog (VID 0x044F, PID 0x0404) usando o protocolo oficial de 36 bytes
de TmHidControl.dll (CTmHidFilter::SetWarthogThrottleLEDValue):
  Buffer de 36 bytes (OutputReportByteLength = 36):
    Byte 0: 0x01 (Report ID 1)
    Byte 1: 0x06 (Comando Set LEDs & Backlight)
    Byte 2: Máscara de Hardware:
      - 0x08: Retroiluminação do Painel (Backlight ON/OFF)
      - 0x04: LED 1 (Topo)
      - 0x02: LED 2
      - 0x10: LED 3 (Centro)
      - 0x01: LED 4
      - 0x40: LED 5 (Base)
    Byte 3: Intensidade PWM (0 a 5)
    Bytes 4..35: 0x00
"""

import ctypes
from ctypes import wintypes
import threading
from typing import Optional, Callable

# Win32 Constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# Máscaras físicas exatas extraídas da tabela 0x273E0 de TmHidControl.dll
HW_BIT_BACKLIGHT = 0x08
HW_LED_BITS = (
    0x04,  # LED 1 (Topo)
    0x02,  # LED 2
    0x10,  # LED 3 (Meio)
    0x01,  # LED 4
    0x40,  # LED 5 (Fundo)
)
WARTHOG_OUTPUT_REPORT_LEN = 36  # 0x24 bytes exigidos pelo descritor HID da Manete 044F:0404

setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
hid = ctypes.WinDLL("hid", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.c_size_t),
    ]


# Configuração explícita de tipos 64-bit para evitar truncamento de ponteiros HDEVINFO / HANDLE no Python 64-bit
hid.HidD_GetHidGuid.argtypes = [ctypes.POINTER(GUID)]
hid.HidD_GetHidGuid.restype = None

hid.HidD_SetOutputReport.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.ULONG]
hid.HidD_SetOutputReport.restype = wintypes.BOOLEAN

setupapi.SetupDiGetClassDevsW.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCWSTR,
    wintypes.HWND,
    wintypes.DWORD,
]
setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p

setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
]
setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL

setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
]
setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL

setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
]
kernel32.CreateFileW.restype = ctypes.c_void_p

kernel32.WriteFile.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
]
kernel32.WriteFile.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = wintypes.BOOL


class WarthogLEDController:
    """Controlador de Retroiluminação e dos 5 LEDs verdes da base da manete HOTAS Warthog."""

    def __init__(self, initial_brightness: int = 3):
        self.device_handle: Optional[int] = None
        self.device_path: Optional[str] = None
        self.brightness = max(0, min(5, int(initial_brightness)))  # 0 (Off) a 5 (Máx)
        self.led_states = [False, False, False, False, False]       # LED 1 a 5
        self._lock = threading.Lock()
        self._is_connected = False
        self.on_state_change: Optional[Callable[[list[bool], int], None]] = None

        # Inicializa imediatamente o estado físico da manete ao arrancar
        self._push_state_to_hardware(sync=True)

    def find_and_open_device(self) -> bool:
        """Localiza e abre o handle USB HID de 64-bits da Manete Warthog (VID_044F&PID_0404)."""
        if self.device_handle and self.device_handle != INVALID_HANDLE_VALUE:
            return True

        hid_guid = GUID()
        hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

        dev_info = setupapi.SetupDiGetClassDevsW(
            ctypes.byref(hid_guid),
            None,
            None,
            0x00000010 | 0x00000002,  # DIGCF_DEVICEINTERFACE | DIGCF_PRESENT
        )

        if not dev_info or dev_info == INVALID_HANDLE_VALUE:
            return False

        idx = 0
        opened = False
        try:
            while True:
                if_data = SP_DEVICE_INTERFACE_DATA()
                if_data.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
                if not setupapi.SetupDiEnumDeviceInterfaces(
                    dev_info, None, ctypes.byref(hid_guid), idx, ctypes.byref(if_data)
                ):
                    break

                req_size = wintypes.DWORD(0)
                setupapi.SetupDiGetDeviceInterfaceDetailW(
                    dev_info, ctypes.byref(if_data), None, 0, ctypes.byref(req_size), None
                )

                if req_size.value > 0:
                    buf = ctypes.create_string_buffer(req_size.value)
                    # cbSize em Windows 64-bit é 8; em 32-bit é 6
                    ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD))[0] = (
                        8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
                    )
                    if setupapi.SetupDiGetDeviceInterfaceDetailW(
                        dev_info, ctypes.byref(if_data), buf, req_size.value, None, None
                    ):
                        path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
                        if "vid_044f" in path.lower() and "pid_0404" in path.lower():
                            h_file = kernel32.CreateFileW(
                                path,
                                GENERIC_READ | GENERIC_WRITE,
                                FILE_SHARE_READ | FILE_SHARE_WRITE,
                                None,
                                OPEN_EXISTING,
                                0,
                                None,
                            )
                            if h_file and h_file != INVALID_HANDLE_VALUE:
                                self.device_handle = h_file
                                self.device_path = path
                                self._is_connected = True
                                opened = True
                                break
                idx += 1
        finally:
            setupapi.SetupDiDestroyDeviceInfoList(dev_info)

        return opened

    def _build_hardware_packet(self) -> ctypes.Array:
        """
        Constrói o pacote oficial de 36 bytes para o Warthog Throttle:
        [0x01, 0x06, hw_mask, pwm_intensity, 0x00 * 32]
        """
        hw_mask = 0
        if self.brightness > 0:
            hw_mask |= HW_BIT_BACKLIGHT

        for i in range(5):
            if self.led_states[i]:
                hw_mask |= HW_LED_BITS[i]

        # Se a retroiluminação estiver em 0 mas algum dos 5 LEDs estiver ativo,
        # usamos intensidade PWM 3 para que os LEDs individuais continuem visíveis
        # com a retroiluminação do painel (0x08) desligada!
        if self.brightness > 0:
            pwm_level = self.brightness & 0x07
        elif any(self.led_states):
            pwm_level = 3
        else:
            pwm_level = 0

        packet = (ctypes.c_ubyte * WARTHOG_OUTPUT_REPORT_LEN)()
        packet[0] = 0x01
        packet[1] = 0x06
        packet[2] = hw_mask & 0xFF
        packet[3] = pwm_level & 0x07
        return packet

    def set_brightness(self, level: int):
        """Define o brilho da retroiluminação (0 = desligado, 1 a 5 = nível de brilho)."""
        self.brightness = max(0, min(5, int(level)))
        self._push_state_to_hardware()
        if self.on_state_change:
            self.on_state_change(list(self.led_states), self.brightness)

    def set_led(self, led_index: int, state: bool):
        """Define o estado de um dos 5 LEDs (led_index: 1 a 5)."""
        if 1 <= led_index <= 5:
            self.led_states[led_index - 1] = bool(state)
            self._push_state_to_hardware()
            if self.on_state_change:
                self.on_state_change(list(self.led_states), self.brightness)

    def set_all_leds(self, states: list[bool]):
        """Define todos os 5 LEDs de uma vez."""
        for i in range(min(5, len(states))):
            self.led_states[i] = bool(states[i])
        self._push_state_to_hardware()
        if self.on_state_change:
            self.on_state_change(list(self.led_states), self.brightness)

    def sync_flight_state(
        self,
        is_nav_mode: bool,
        gear_down: bool,
        vtol_on: bool,
        lights_on: bool,
        quantum_spool: bool,
    ):
        """Sincroniza os 5 LEDs físicos da base com os sistemas do Star Citizen."""
        self.led_states[0] = bool(is_nav_mode)     # LED 1: Master Mode NAV / EAC
        self.led_states[1] = bool(gear_down)       # LED 2: Trem de Aterragem (RDR ALTM)
        self.led_states[2] = bool(vtol_on)         # LED 3: Modo VTOL (Flaps Down)
        self.led_states[3] = bool(lights_on)       # LED 4: Faróis Exteriores (Pinky FWD)
        self.led_states[4] = bool(quantum_spool)   # LED 5: Quantum Mode (Boat FWD)
        self._push_state_to_hardware()
        if self.on_state_change:
            self.on_state_change(list(self.led_states), self.brightness)

    def _send_now(self) -> bool:
        with self._lock:
            if not self._is_connected or not self.device_handle:
                if not self.find_and_open_device():
                    return False

            packet = self._build_hardware_packet()
            written = wintypes.DWORD(0)

            # Método primário oficial Thrustmaster (WriteFile de 36 bytes)
            ok = bool(
                kernel32.WriteFile(
                    self.device_handle,
                    ctypes.byref(packet),
                    WARTHOG_OUTPUT_REPORT_LEN,
                    ctypes.byref(written),
                    None,
                )
            )
            if not ok:
                # Fallback via HidD_SetOutputReport (36 bytes)
                ok = bool(
                    hid.HidD_SetOutputReport(
                        self.device_handle,
                        ctypes.byref(packet),
                        WARTHOG_OUTPUT_REPORT_LEN,
                    )
                )

            if not ok:
                try:
                    kernel32.CloseHandle(self.device_handle)
                except Exception:
                    pass
                self.device_handle = None
                self._is_connected = False
            return ok

    def _push_state_to_hardware(self, sync: bool = False):
        """Envia o pacote de 36 bytes USB HID para a manete física."""
        if sync:
            self._send_now()
        else:
            threading.Thread(target=self._send_now, daemon=True).start()

    def close(self):
        """Fecha o handle USB."""
        with self._lock:
            if self.device_handle and self.device_handle != INVALID_HANDLE_VALUE:
                try:
                    kernel32.CloseHandle(self.device_handle)
                except Exception:
                    pass
                self.device_handle = None
                self._is_connected = False
