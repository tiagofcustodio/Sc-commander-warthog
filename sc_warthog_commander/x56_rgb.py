"""
Logitech G / Saitek X56 Rhino RGB Backlight Controller (True Dual-Engine)
Controla a cor RGB de 24 bits e o brilho (0..100%) do Manche (VID_0738&PID_2221) e da
Manete (VID_0738&PID_A221) Logitech G / Saitek X56 Rhino usando DOIS motores nativos:

1. Motor Direto USB HID (HidD_SetFeature na Interface 2 / MI_02 / UsagePage 0xFF00):
   - Funciona IMEDIATAMENTE no Windows 10/11 SEM precisar do software Logitech nem DirectOutput.dll!
   - Envia os pacotes exatos de 64 bytes verificados no descritor HID do X56:
       • Feature Report ID 0x09: [0x09, 0x00, 0x03, R, G, B, 0x00...] (cor escalada pelo brilho)
       • Feature Report ID 0x01: [0x01, 0x01, 0x00...]                (commit / aplicar no MCU)

2. Motor Oficial DirectOutput.dll (protocolo exato de X56.cs / spreedated):
   - Usa os GUIDs oficiais do X56 (Throttle EE9E44A9-... / Stick 40D17E5E-...).
   - Executa a sequência completa AddPage(1,1) -> SetLed(1,0,brilho) -> SetLed(1,1,cor24) -> RemovePage(1)
     em cada alteração para nunca sofrer E_PAGENOTACTIVE quando o software Logitech está ativo.
"""

import ctypes
from ctypes import wintypes
import os
import threading
import time
import winreg
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Constantes USB HID (Logitech / Saitek / Mad Catz X56 Rhino)
# ---------------------------------------------------------------------------
X56_VIDS = (0x0738, 0x046D)
X56_STICK_PID = 0x2221
X56_THROTTLE_PID = 0xA221
X56_HID_USAGE_PAGE_CTRL = 0xFF00
X56_HID_FEATURE_LEN = 64

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
DIGCF_PRESENT = 0x00000002
DIGCF_DEVICEINTERFACE = 0x00000010
HIDP_STATUS_SUCCESS = 0x00110000

# ---------------------------------------------------------------------------
# Constantes DirectOutput SDK (verificadas de neXn.X56.DirectOutput / X56.cs)
# ---------------------------------------------------------------------------
FLAG_SET_AS_ACTIVE = 0x00000001
X56_PAGE_ID = 1
X56_LED_IDX_BRIGHTNESS = 0  # 0..100
X56_LED_IDX_COLOR = 1       # (R << 16) | (G << 8) | B (0..16777215)

X56_THROTTLE_TYPE_GUID = "EE9E44A9-46CD-470B-B650-9C5859992240"
X56_STICK_TYPE_GUID = "40D17E5E-8091-409F-A2B5-24EF1915A812"

# Dispositivos Saitek que NÃO são X56
_NON_X56_DEVICE_TYPE_GUIDS = {
    "29DAD506-F93B-4F20-85FA-1E02C04FAC17",  # Saitek X52 Pro
    "3E083CD8-6A37-4A58-80A8-3D6A2C07513E",  # Saitek Flight Instrument Panel (FIP)
}

# Cores táticas Star Citizen por perfil (quando profile_sync está ativo)
DEFAULT_PROFILE_RGB_COLORS = {
    "combat": "#FF1E2D",  # Aegis Red (Combate + menor consumo USB)
    "mining": "#FF9900",  # Drake Amber (Mineração / Salvage)
    "cargo":  "#00D2FF",  # UEE Cyan (Carga / Exploração)
    "ground": "#00E676",  # Anvil Green (Veículos Terrestres)
}

DEFAULT_X56_RGB_CONFIG = {
    "linked": True,
    "stick_color": "#00D2FF",
    "throttle_color": "#00D2FF",
    "brightness": 80,
    "profile_sync": False,
    "profile_colors": dict(DEFAULT_PROFILE_RGB_COLORS),
}


# ---------------------------------------------------------------------------
# Estruturas Win32 (64-bit safe)
# ---------------------------------------------------------------------------
class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", _GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.c_size_t),
    ]


class _HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Size", wintypes.ULONG),
        ("VendorID", wintypes.USHORT),
        ("ProductID", wintypes.USHORT),
        ("VersionNumber", wintypes.USHORT),
    ]


class _HIDP_CAPS(ctypes.Structure):
    _fields_ = [
        ("Usage", wintypes.USHORT),
        ("UsagePage", wintypes.USHORT),
        ("InputReportByteLength", wintypes.USHORT),
        ("OutputReportByteLength", wintypes.USHORT),
        ("FeatureReportByteLength", wintypes.USHORT),
        ("Reserved", wintypes.USHORT * 17),
        ("NumberLinkCollectionNodes", wintypes.USHORT),
        ("NumberInputButtonCaps", wintypes.USHORT),
        ("NumberInputValueCaps", wintypes.USHORT),
        ("NumberInputDataIndices", wintypes.USHORT),
        ("NumberOutputButtonCaps", wintypes.USHORT),
        ("NumberOutputValueCaps", wintypes.USHORT),
        ("NumberOutputDataIndices", wintypes.USHORT),
        ("NumberFeatureButtonCaps", wintypes.USHORT),
        ("NumberFeatureValueCaps", wintypes.USHORT),
        ("NumberFeatureDataIndices", wintypes.USHORT),
    ]


class _VS_FIXEDFILEINFO(ctypes.Structure):
    _fields_ = [
        ("dwSignature", wintypes.DWORD),
        ("dwStrucVersion", wintypes.DWORD),
        ("dwFileVersionMS", wintypes.DWORD),
        ("dwFileVersionLS", wintypes.DWORD),
        ("dwProductVersionMS", wintypes.DWORD),
        ("dwProductVersionLS", wintypes.DWORD),
        ("dwFileFlagsMask", wintypes.DWORD),
        ("dwFileFlags", wintypes.DWORD),
        ("dwFileOS", wintypes.DWORD),
        ("dwFileType", wintypes.DWORD),
        ("dwFileSubtype", wintypes.DWORD),
        ("dwFileDateMS", wintypes.DWORD),
        ("dwFileDateLS", wintypes.DWORD),
    ]


# Configura instâncias privadas WinDLL (evita conflitos de argtypes com warthog_leds.py!)
_setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
_hid = ctypes.WinDLL("hid", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_hid.HidD_GetHidGuid.argtypes = [ctypes.POINTER(_GUID)]
_hid.HidD_GetHidGuid.restype = None

_hid.HidD_GetAttributes.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HIDD_ATTRIBUTES)]
_hid.HidD_GetAttributes.restype = wintypes.BOOLEAN

_hid.HidD_GetPreparsedData.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
_hid.HidD_GetPreparsedData.restype = wintypes.BOOLEAN

_hid.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]
_hid.HidD_FreePreparsedData.restype = wintypes.BOOLEAN

_hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(_HIDP_CAPS)]
_hid.HidP_GetCaps.restype = ctypes.c_long

_hid.HidD_SetFeature.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.ULONG]
_hid.HidD_SetFeature.restype = wintypes.BOOLEAN

_setupapi.SetupDiGetClassDevsW.argtypes = [
    ctypes.POINTER(_GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD
]
_setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p

_setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(_GUID),
    wintypes.DWORD, ctypes.POINTER(_SP_DEVICE_INTERFACE_DATA)
]
_setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL

_setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
    ctypes.c_void_p, ctypes.POINTER(_SP_DEVICE_INTERFACE_DATA),
    ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p
]
_setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL

_setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
_setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

_kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
    ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p
]
_kernel32.CreateFileW.restype = ctypes.c_void_p

_kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
_kernel32.CloseHandle.restype = wintypes.BOOL


# Callbacks DirectOutput (__stdcall via WINFUNCTYPE)
_PFN_DEVICE_CHANGE = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p)
_PFN_ENUMERATE = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


# ---------------------------------------------------------------------------
# Utilitários de cor e pacotes
# ---------------------------------------------------------------------------
def _guid_to_key(g: _GUID) -> str:
    d4 = "".join(f"{b:02X}" for b in g.Data4)
    return f"{g.Data1:08X}-{g.Data2:04X}-{g.Data3:04X}-{d4}"


def _guid_to_standard_str(g: _GUID) -> str:
    d4_hi = "".join(f"{b:02X}" for b in g.Data4[:2])
    d4_lo = "".join(f"{b:02X}" for b in g.Data4[2:])
    return f"{g.Data1:08X}-{g.Data2:04X}-{g.Data3:04X}-{d4_hi}-{d4_lo}"


def parse_hex_color(color_str: str, fallback: str = "#00D2FF") -> tuple[int, int, int, str]:
    """Valida uma cor hexadecimal (#RRGGBB ou #RGB) e devolve (r, g, b, '#RRGGBB')."""
    raw = str(color_str or "").strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        raw = fallback.lstrip("#")
    try:
        r = int(raw[0:2], 16)
        g = int(raw[2:4], 16)
        b = int(raw[4:6], 16)
    except ValueError:
        fb = fallback.lstrip("#")
        r, g, b = int(fb[0:2], 16), int(fb[2:4], 16), int(fb[4:6], 16)
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return r, g, b, f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_int24(r: int, g: int, b: int) -> int:
    """Empacota (R, G, B) num inteiro 24-bit (65536*R + 256*G + B) exigido pelo DirectOutput X56."""
    return ((max(0, min(255, int(r))) & 0xFF) << 16) | \
           ((max(0, min(255, int(g))) & 0xFF) << 8) | \
           (max(0, min(255, int(b))) & 0xFF)


def build_x56_hid_rgb_packets(
    hex_color: str,
    brightness: int,
    report_len: int = X56_HID_FEATURE_LEN,
) -> tuple[bytes, bytes]:
    """
    Constrói os 2 pacotes USB HID Feature Report de 64 bytes para a Interface 2 (MI_02) do X56:
      1) Report ID 0x09: [0x09, 0x00, 0x03, R_scaled, G_scaled, B_scaled, 0x00...]
      2) Report ID 0x01: [0x01, 0x01, 0x00...] (commit / aplicar cor no firmware do X56)
    """
    r, g, b, _ = parse_hex_color(hex_color)
    br = max(0, min(100, int(brightness)))
    scale = br / 100.0
    r_eff = max(0, min(255, int(round(r * scale))))
    g_eff = max(0, min(255, int(round(g * scale))))
    b_eff = max(0, min(255, int(round(b * scale))))

    size = max(64, int(report_len or 64))
    pkt_color = bytearray(size)
    pkt_color[0] = 0x09
    pkt_color[1] = 0x00
    pkt_color[2] = 0x03
    pkt_color[3] = r_eff
    pkt_color[4] = g_eff
    pkt_color[5] = b_eff

    pkt_commit = bytearray(size)
    pkt_commit[0] = 0x01
    pkt_commit[1] = 0x01
    return bytes(pkt_color), bytes(pkt_commit)


def _open_hid_handle(path: str) -> Optional[int]:
    """Abre um caminho HID do Windows tentando RW primeiro e depois acesso 0 (permitido para HidD_SetFeature)."""
    for access in (GENERIC_READ | GENERIC_WRITE, 0):
        h = _kernel32.CreateFileW(
            path,
            access,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        if h and h != INVALID_HANDLE_VALUE:
            return int(h)
    return None


def enumerate_x56_hid_rgb_interfaces() -> list[dict]:
    """
    Descobre todas as interfaces USB HID de controlo RGB (MI_02 / UsagePage 0xFF00 / FeatureLen=64)
    do Logitech G / Saitek X56 Stick (PID 0x2221) e Throttle (PID 0xA221) diretamente via SetupAPI.
    Funciona sem qualquer driver Logitech ou DirectOutput.dll!
    """
    found: list[dict] = []
    hid_guid = _GUID()
    _hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

    dev_info = _setupapi.SetupDiGetClassDevsW(
        ctypes.byref(hid_guid), None, None, DIGCF_DEVICEINTERFACE | DIGCF_PRESENT
    )
    if not dev_info or dev_info == INVALID_HANDLE_VALUE:
        return found

    idx = 0
    seen_paths: set[str] = set()
    try:
        while True:
            if_data = _SP_DEVICE_INTERFACE_DATA()
            if_data.cbSize = ctypes.sizeof(_SP_DEVICE_INTERFACE_DATA)
            if not _setupapi.SetupDiEnumDeviceInterfaces(
                dev_info, None, ctypes.byref(hid_guid), idx, ctypes.byref(if_data)
            ):
                break
            idx += 1

            req_size = wintypes.DWORD(0)
            _setupapi.SetupDiGetDeviceInterfaceDetailW(
                dev_info, ctypes.byref(if_data), None, 0, ctypes.byref(req_size), None
            )
            if req_size.value <= 4:
                continue

            buf = ctypes.create_string_buffer(req_size.value)
            ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD))[0] = (
                8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            )
            if not _setupapi.SetupDiGetDeviceInterfaceDetailW(
                dev_info, ctypes.byref(if_data), buf, req_size.value, None, None
            ):
                continue

            path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
            pl = path.lower()
            if pl in seen_paths:
                continue

            # Filtra rapidamente por VID_0738 (ou 046D) + PID_2221 / PID_A221
            if not (("vid_0738" in pl or "vid_046d" in pl) and ("pid_2221" in pl or "pid_a221" in pl)):
                continue

            h = _open_hid_handle(path)
            if not h:
                continue

            try:
                attrs = _HIDD_ATTRIBUTES()
                attrs.Size = ctypes.sizeof(_HIDD_ATTRIBUTES)
                vid = 0x0738 if "vid_0738" in pl else 0x046D
                pid = X56_STICK_PID if "pid_2221" in pl else X56_THROTTLE_PID
                if _hid.HidD_GetAttributes(ctypes.c_void_p(h), ctypes.byref(attrs)):
                    vid = int(attrs.VendorID)
                    pid = int(attrs.ProductID)

                if vid not in X56_VIDS or pid not in (X56_STICK_PID, X56_THROTTLE_PID):
                    continue

                usage_page = 0
                usage = 0
                feat_len = 0
                ppd = ctypes.c_void_p(0)
                if _hid.HidD_GetPreparsedData(ctypes.c_void_p(h), ctypes.byref(ppd)) and ppd.value:
                    try:
                        caps = _HIDP_CAPS()
                        if _hid.HidP_GetCaps(ppd, ctypes.byref(caps)) == HIDP_STATUS_SUCCESS:
                            usage_page = int(caps.UsagePage)
                            usage = int(caps.Usage)
                            feat_len = int(caps.FeatureReportByteLength)
                    finally:
                        _hid.HidD_FreePreparsedData(ppd)

                # Interface 2 (MI_02) de controlo RGB do X56 tem UsagePage 0xFF00 e FeatureReportByteLength == 64
                is_ctrl_if = (
                    (usage_page == X56_HID_USAGE_PAGE_CTRL and feat_len >= 64)
                    or ("mi_02" in pl and feat_len >= 64)
                )
                if not is_ctrl_if:
                    continue

                seen_paths.add(pl)
                found.append({
                    "path": path,
                    "vid": vid,
                    "pid": pid,
                    "role": "stick" if pid == X56_STICK_PID else "throttle",
                    "usage_page": usage_page,
                    "usage": usage,
                    "feature_len": feat_len or X56_HID_FEATURE_LEN,
                })
            finally:
                _kernel32.CloseHandle(ctypes.c_void_p(h))
    finally:
        _setupapi.SetupDiDestroyDeviceInfoList(dev_info)

    return found


def send_x56_hid_rgb(path: str, hex_color: str, brightness: int, feature_len: int = 64) -> tuple[bool, str]:
    """Envia os 2 Feature Reports USB HID (0x09 cor + 0x01 commit) diretamente para a interface MI_02 do X56."""
    h = _open_hid_handle(path)
    if not h:
        err = ctypes.get_last_error()
        return False, f"CreateFileW falhou (Win32={err})"

    try:
        pkt_color, pkt_commit = build_x56_hid_rgb_packets(hex_color, brightness, feature_len)
        buf_c = (ctypes.c_ubyte * len(pkt_color)).from_buffer_copy(pkt_color)
        ok1 = bool(_hid.HidD_SetFeature(ctypes.c_void_p(h), ctypes.byref(buf_c), len(pkt_color)))
        if not ok1:
            err1 = ctypes.get_last_error()
            return False, f"HidD_SetFeature(0x09) falhou (Win32={err1})"

        time.sleep(0.010)

        buf_k = (ctypes.c_ubyte * len(pkt_commit)).from_buffer_copy(pkt_commit)
        ok2 = bool(_hid.HidD_SetFeature(ctypes.c_void_p(h), ctypes.byref(buf_k), len(pkt_commit)))
        if not ok2:
            # Em alguns firmwares o pacote 0x09 já aplica a cor mesmo se 0x01 retornar erro
            err2 = ctypes.get_last_error()
            return True, f"HidD_SetFeature(0x09 OK; 0x01 Win32={err2})"

        return True, ""
    except Exception as e:
        return False, f"Erro HID SetFeature: {e}"
    finally:
        _kernel32.CloseHandle(ctypes.c_void_p(h))


def _get_file_version(dll_path: str) -> tuple[int, int, int, int]:
    """Lê a versão de ficheiro Win32 (ex.: 8.0.213.0) de DirectOutput.dll."""
    if not dll_path or not os.path.isfile(dll_path):
        return (0, 0, 0, 0)
    try:
        ver = ctypes.WinDLL("version.dll")
        ver.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
        ver.GetFileVersionInfoSizeW.restype = wintypes.DWORD
        ver.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
        ver.GetFileVersionInfoW.restype = wintypes.BOOL
        ver.VerQueryValueW.argtypes = [
            ctypes.c_void_p, wintypes.LPCWSTR,
            ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT),
        ]
        ver.VerQueryValueW.restype = wintypes.BOOL

        dummy = wintypes.DWORD(0)
        size = ver.GetFileVersionInfoSizeW(dll_path, ctypes.byref(dummy))
        if not size:
            return (0, 0, 0, 0)
        buf = ctypes.create_string_buffer(size)
        if not ver.GetFileVersionInfoW(dll_path, 0, size, buf):
            return (0, 0, 0, 0)
        ptr = ctypes.c_void_p(0)
        length = wintypes.UINT(0)
        if not ver.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(length)):
            return (0, 0, 0, 0)
        if not ptr.value or length.value < ctypes.sizeof(_VS_FIXEDFILEINFO):
            return (0, 0, 0, 0)
        info = ctypes.cast(ptr, ctypes.POINTER(_VS_FIXEDFILEINFO)).contents
        return (
            (info.dwFileVersionMS >> 16) & 0xFFFF,
            info.dwFileVersionMS & 0xFFFF,
            (info.dwFileVersionLS >> 16) & 0xFFFF,
            info.dwFileVersionLS & 0xFFFF,
        )
    except Exception:
        return (0, 0, 0, 0)


def find_directoutput_dll() -> Optional[str]:
    """Localiza o ficheiro oficial DirectOutput.dll dos drivers Logitech / Saitek X56."""
    candidates: list[str] = []

    # 1. Registo do Windows (Saitek\DirectOutput é a chave usada pelo X56 mesmo em drivers Logitech!)
    reg_paths = [
        r"SOFTWARE\Saitek\DirectOutput",
        r"SOFTWARE\Logitech\DirectOutput",
        r"SOFTWARE\Mad Catz\DirectOutput",
    ]
    access_flags = [
        winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0),
        winreg.KEY_READ,
    ]
    for rp in reg_paths:
        for flags in access_flags:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rp, 0, flags) as key:
                    val, _ = winreg.QueryValueEx(key, "DirectOutput")
                    if val:
                        p = str(val).strip().strip('"')
                        if p and p not in candidates:
                            candidates.append(p)
            except OSError:
                continue

    # 2. Caminhos padrão Logitech / Saitek / Mad Catz (64-bit)
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    windir = os.environ.get("WINDIR", r"C:\Windows")
    static_paths = [
        os.path.join(prog_files, "Logitech", "DirectOutput", "DirectOutput.dll"),
        os.path.join(prog_files, "Saitek", "DirectOutput", "DirectOutput.dll"),
        os.path.join(prog_files, "Mad Catz", "DirectOutput", "DirectOutput.dll"),
        os.path.join(prog_files, "Logitech", "X56", "DirectOutput.dll"),
        os.path.join(prog_files, "Logitech", "SD6", "DirectOutput.dll"),
        os.path.join(windir, "System32", "DirectOutput.dll"),
    ]
    for sp in static_paths:
        if sp not in candidates:
            candidates.append(sp)

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class X56RGBController:
    """
    Controlador Dual-Engine RGB para o Logitech G / Saitek X56 Rhino HOTAS:
      - Motor 1 (Direto, zero drivers): USB HID Feature Reports na Interface 2 (MI_02 / 0xFF00)
      - Motor 2 (Oficial Logitech/Saitek): DirectOutput.dll com ciclo AddPage -> SetLed -> RemovePage
    """

    def __init__(self, initial_settings: Optional[dict] = None):
        self._lock = threading.RLock()

        # Estado Motor DirectOutput.dll
        self._dll = None
        self._dll_path: Optional[str] = None
        self._dll_version: tuple[int, int, int, int] = (0, 0, 0, 0)
        self._dll_dir_handle = None
        self._initialized: bool = False
        self._use_4arg_addpage: bool = False
        self._devices: dict[int, dict] = {}
        self._di_devices_cache: list[dict] = []

        # Estado Motor USB HID Direto (MI_02)
        self._hid_devices: list[dict] = []

        # Diagnóstico
        self._last_error: str = ""
        self._last_backend_used: str = ""

        # Mantém referências vivas aos callbacks ctypes DirectOutput
        self._cb_device_change = _PFN_DEVICE_CHANGE(self._on_device_change)
        self._cb_enumerate = _PFN_ENUMERATE(self._on_device_enumerated)

        # Estado RGB persistível
        cfg = dict(DEFAULT_X56_RGB_CONFIG)
        if isinstance(initial_settings, dict):
            cfg.update(initial_settings)

        self.linked: bool = bool(cfg.get("linked", True))
        _, _, _, self.stick_color = parse_hex_color(cfg.get("stick_color", "#00D2FF"))
        _, _, _, self.throttle_color = parse_hex_color(cfg.get("throttle_color", "#00D2FF"))
        self.brightness: int = max(0, min(100, int(cfg.get("brightness", 80))))
        self.profile_sync: bool = bool(cfg.get("profile_sync", False))

        p_colors = dict(DEFAULT_PROFILE_RGB_COLORS)
        if isinstance(cfg.get("profile_colors"), dict):
            for k, v in cfg["profile_colors"].items():
                _, _, _, hex_v = parse_hex_color(v, fallback=p_colors.get(k, "#00D2FF"))
                p_colors[k] = hex_v
        self.profile_colors: dict[str, str] = p_colors

        self.on_state_change: Optional[Callable[[dict], None]] = None

        # Deteta ambos os motores ao arrancar (nunca levanta exceção se o X56 não estiver ligado)
        self._scan_hid_devices_locked()
        self._try_connect_directoutput()

    def _scan_hid_devices_locked(self) -> list[dict]:
        try:
            self._hid_devices = enumerate_x56_hid_rgb_interfaces()
        except Exception:
            self._hid_devices = []
        return self._hid_devices

    def _configure_dll_prototypes(self, dll) -> None:
        dll.DirectOutput_Initialize.argtypes = [wintypes.LPCWSTR]
        dll.DirectOutput_Initialize.restype = ctypes.c_long

        dll.DirectOutput_Deinitialize.argtypes = []
        dll.DirectOutput_Deinitialize.restype = ctypes.c_long

        dll.DirectOutput_RegisterDeviceCallback.argtypes = [_PFN_DEVICE_CHANGE, ctypes.c_void_p]
        dll.DirectOutput_RegisterDeviceCallback.restype = ctypes.c_long

        dll.DirectOutput_Enumerate.argtypes = [_PFN_ENUMERATE, ctypes.c_void_p]
        dll.DirectOutput_Enumerate.restype = ctypes.c_long

        dll.DirectOutput_GetDeviceType.argtypes = [ctypes.c_void_p, ctypes.POINTER(_GUID)]
        dll.DirectOutput_GetDeviceType.restype = ctypes.c_long

        if hasattr(dll, "DirectOutput_GetDeviceInstance"):
            dll.DirectOutput_GetDeviceInstance.argtypes = [ctypes.c_void_p, ctypes.POINTER(_GUID)]
            dll.DirectOutput_GetDeviceInstance.restype = ctypes.c_long

        if self._use_4arg_addpage:
            dll.DirectOutput_AddPage.argtypes = [
                ctypes.c_void_p, wintypes.DWORD, wintypes.LPCWSTR, wintypes.DWORD
            ]
        else:
            dll.DirectOutput_AddPage.argtypes = [
                ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD
            ]
        dll.DirectOutput_AddPage.restype = ctypes.c_long

        dll.DirectOutput_RemovePage.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        dll.DirectOutput_RemovePage.restype = ctypes.c_long

        dll.DirectOutput_SetLed.argtypes = [
            ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD
        ]
        dll.DirectOutput_SetLed.restype = ctypes.c_long

    def _try_connect_directoutput(self) -> bool:
        """Inicializa DirectOutput.dll seguindo a ordem exata de X56.cs (Initialize -> Enumerate -> RegisterCallback)."""
        with self._lock:
            if self._initialized and self._dll is not None:
                return True

            dll_path = find_directoutput_dll()
            self._dll_path = dll_path

            try:
                if dll_path:
                    dll_dir = os.path.dirname(dll_path)
                    if dll_dir and os.path.isdir(dll_dir) and hasattr(os, "add_dll_directory"):
                        try:
                            self._dll_dir_handle = os.add_dll_directory(dll_dir)
                        except OSError:
                            pass
                    self._dll_version = _get_file_version(dll_path)
                    major = self._dll_version[0]
                    self._use_4arg_addpage = (0 < major <= 7)
                    dll = ctypes.WinDLL(dll_path)
                else:
                    self._dll_version = (0, 0, 0, 0)
                    self._use_4arg_addpage = False
                    dll = ctypes.WinDLL("DirectOutput.dll")
                    self._dll_path = "DirectOutput.dll"
            except OSError:
                self._dll = None
                self._initialized = False
                return False

            try:
                self._configure_dll_prototypes(dll)
                hr = dll.DirectOutput_Initialize("SC_Warthog_Commander")
                if hr != 0:
                    self._last_error = f"DirectOutput_Initialize falhou (0x{hr & 0xFFFFFFFF:08X})"
                    self._dll = None
                    self._initialized = False
                    return False

                self._dll = dll
                self._initialized = True
                self._devices.clear()

                # Ordem exata verificada em X56.cs: Enumerate primeiro, depois RegisterDeviceCallback
                dll.DirectOutput_Enumerate(self._cb_enumerate, None)
                dll.DirectOutput_RegisterDeviceCallback(self._cb_device_change, None)
                self._reclassify_devices_locked()
                return True
            except Exception as e:
                self._last_error = f"Erro DirectOutput: {e}"
                self._dll = None
                self._initialized = False
                return False

    def _on_device_enumerated(self, h_device, _p_ctxt):
        if not h_device:
            return
        self._register_handle(int(h_device))

    def _on_device_change(self, h_device, b_added, _p_ctxt):
        if not h_device:
            return
        h_int = int(h_device)
        if b_added:
            self._register_handle(h_int)
            with self._lock:
                self._reclassify_devices_locked()
                self._scan_hid_devices_locked()
            self.apply_to_hardware()
        else:
            with self._lock:
                self._devices.pop(h_int, None)
                self._scan_hid_devices_locked()
        self._emit_state()

    def _register_handle(self, h_int: int) -> None:
        with self._lock:
            if not self._dll or h_int in self._devices:
                return

            type_guid_std = ""
            inst_guid_key = ""
            try:
                g_type = _GUID()
                if self._dll.DirectOutput_GetDeviceType(ctypes.c_void_p(h_int), ctypes.byref(g_type)) == 0:
                    type_guid_std = _guid_to_standard_str(g_type)
            except Exception:
                pass

            if type_guid_std in _NON_X56_DEVICE_TYPE_GUIDS:
                return

            try:
                if hasattr(self._dll, "DirectOutput_GetDeviceInstance"):
                    g_inst = _GUID()
                    if self._dll.DirectOutput_GetDeviceInstance(ctypes.c_void_p(h_int), ctypes.byref(g_inst)) == 0:
                        inst_guid_key = _guid_to_key(g_inst)
            except Exception:
                pass

            # Identifica diretamente pelos GUIDs oficiais do X56 (de X56.cs)
            role = "x56"
            if type_guid_std == X56_THROTTLE_TYPE_GUID:
                role = "throttle"
            elif type_guid_std == X56_STICK_TYPE_GUID:
                role = "stick"

            self._devices[h_int] = {
                "handle": h_int,
                "role": role,
                "type_guid": type_guid_std,
                "instance_guid": inst_guid_key,
            }

    def _reclassify_devices_locked(self) -> None:
        """Refina a classificação Stick vs Throttle usando GUID oficial DirectOutput + GUID DirectInput8."""
        if not self._devices:
            return

        di_by_guid: dict[str, dict] = {}
        for d in self._di_devices_cache or []:
            gkey = str(d.get("guid_key") or d.get("slot") or "").upper()
            if gkey:
                di_by_guid[gkey] = d

        assigned_roles: set[str] = set()
        unmatched: list[dict] = []

        for info in self._devices.values():
            if info.get("type_guid") == X56_THROTTLE_TYPE_GUID:
                info["role"] = "throttle"
                assigned_roles.add("throttle")
                continue
            if info.get("type_guid") == X56_STICK_TYPE_GUID:
                info["role"] = "stick"
                assigned_roles.add("stick")
                continue

            inst = (info.get("instance_guid") or "").upper()
            di = di_by_guid.get(inst) if inst else None
            if di:
                if di.get("pid") == X56_STICK_PID or di.get("role") == "stick":
                    info["role"] = "stick"
                    assigned_roles.add("stick")
                    continue
                if di.get("pid") == X56_THROTTLE_PID or di.get("role") == "throttle":
                    info["role"] = "throttle"
                    assigned_roles.add("throttle")
                    continue
            unmatched.append(info)

        for info in unmatched:
            if "throttle" not in assigned_roles:
                info["role"] = "throttle"
                assigned_roles.add("throttle")
            elif "stick" not in assigned_roles:
                info["role"] = "stick"
                assigned_roles.add("stick")
            else:
                info["role"] = "x56"

    def sync_di_devices(self, di_devices: Optional[list[dict]]) -> None:
        with self._lock:
            self._di_devices_cache = list(di_devices or [])
            self._reclassify_devices_locked()

    def rescan(self, di_devices: Optional[list[dict]] = None) -> dict:
        """Re-deteta interfaces USB HID MI_02 e dispositivos DirectOutput.dll do X56 e aplica a cor."""
        with self._lock:
            if di_devices is not None:
                self._di_devices_cache = list(di_devices)
            self._scan_hid_devices_locked()
            if not self._initialized or self._dll is None:
                self._try_connect_directoutput()
            else:
                try:
                    self._devices.clear()
                    self._dll.DirectOutput_Enumerate(self._cb_enumerate, None)
                    self._reclassify_devices_locked()
                except Exception as e:
                    self._last_error = f"Erro ao re-enumerar DirectOutput: {e}"
        self.apply_to_hardware()
        status = self.get_status()
        self._emit_state()
        return status

    def _add_page_locked(self, h_ptr) -> int:
        if self._use_4arg_addpage:
            return self._dll.DirectOutput_AddPage(h_ptr, X56_PAGE_ID, "SC_RGB", FLAG_SET_AS_ACTIVE)
        return self._dll.DirectOutput_AddPage(h_ptr, X56_PAGE_ID, FLAG_SET_AS_ACTIVE)

    def _send_directoutput_to_handle_locked(self, h_int: int, hex_color: str, brightness: int) -> tuple[bool, str]:
        """
        Executa a transação exata de X56.cs (SetLedObject):
          AddPage(h, 1, 1) -> SetLed(h, 1, 0, brightness) -> SetLed(h, 1, 1, rgb24) -> RemovePage(h, 1)
        """
        if not self._dll or not self._initialized:
            return False, "DirectOutput não inicializado"

        r, g, b, _ = parse_hex_color(hex_color)
        br = max(0, min(100, int(brightness)))
        if r == 0 and g == 0 and b == 0:
            br = 0
        rgb_int = 0 if br == 0 else rgb_to_int24(r, g, b)

        h_ptr = ctypes.c_void_p(h_int)
        try:
            hr_add = self._add_page_locked(h_ptr)
            # Se a página 1 já existia (E_INVALIDARG 0x80070057), remove e volta a adicionar ativa!
            if hr_add != 0:
                self._dll.DirectOutput_RemovePage(h_ptr, X56_PAGE_ID)
                hr_add = self._add_page_locked(h_ptr)

            hr_br = self._dll.DirectOutput_SetLed(h_ptr, X56_PAGE_ID, X56_LED_IDX_BRIGHTNESS, br)
            hr_col = self._dll.DirectOutput_SetLed(h_ptr, X56_PAGE_ID, X56_LED_IDX_COLOR, rgb_int)
            self._dll.DirectOutput_RemovePage(h_ptr, X56_PAGE_ID)

            if hr_br == 0 and hr_col == 0:
                return True, ""
            return False, (
                f"DirectOutput SetLed add=0x{hr_add & 0xFFFFFFFF:08X} "
                f"br=0x{hr_br & 0xFFFFFFFF:08X} col=0x{hr_col & 0xFFFFFFFF:08X}"
            )
        except Exception as e:
            return False, f"Erro DirectOutput SetLed: {e}"

    def _target_color_for_role(self, role: str) -> str:
        if self.linked:
            return self.throttle_color
        return self.stick_color if role == "stick" else self.throttle_color

    def apply_to_hardware(self) -> int:
        """
        Aplica a cor e brilho atuais ao X56 usando AMBOS os motores disponíveis:
          1) DirectOutput.dll (transação AddPage -> SetLed -> RemovePage) se presente
          2) USB HID Feature Report direto (MI_02: 0x09 cor + 0x01 commit) — funciona SEM drivers!
        """
        sent_do = 0
        sent_hid = 0
        errors: list[str] = []

        with self._lock:
            # Motor 1: DirectOutput.dll (atualiza serviço Logitech se ativo)
            if self._initialized and self._dll and self._devices:
                for h_int, info in list(self._devices.items()):
                    target_hex = self._target_color_for_role(info.get("role", "x56"))
                    ok, err = self._send_directoutput_to_handle_locked(h_int, target_hex, self.brightness)
                    if ok:
                        sent_do += 1
                    elif err:
                        errors.append(err)

            # Motor 2: Direct USB HID Feature Reports (MI_02 / UsagePage 0xFF00)
            if not self._hid_devices:
                self._scan_hid_devices_locked()

            if self._hid_devices:
                failed_hid = False
                for dev in list(self._hid_devices):
                    target_hex = self._target_color_for_role(dev.get("role", "x56"))
                    ok, err = send_x56_hid_rgb(
                        dev["path"], target_hex, self.brightness, dev.get("feature_len", 64)
                    )
                    if ok:
                        sent_hid += 1
                    else:
                        failed_hid = True
                        if err:
                            errors.append(err)

                # Se algum handle USB ficou obsoleto (replug), re-escaneia uma vez e reenvia
                if failed_hid and sent_hid == 0:
                    self._scan_hid_devices_locked()
                    for dev in list(self._hid_devices):
                        target_hex = self._target_color_for_role(dev.get("role", "x56"))
                        ok, err = send_x56_hid_rgb(
                            dev["path"], target_hex, self.brightness, dev.get("feature_len", 64)
                        )
                        if ok:
                            sent_hid += 1
                        elif err:
                            errors.append(err)

            if sent_hid > 0 and sent_do > 0:
                self._last_backend_used = "hid+directoutput"
                self._last_error = ""
            elif sent_hid > 0:
                self._last_backend_used = "usb_hid"
                self._last_error = ""
            elif sent_do > 0:
                self._last_backend_used = "directoutput"
                self._last_error = ""
            elif errors:
                self._last_error = errors[-1]

        return max(sent_hid, sent_do)

    def update_settings(
        self,
        linked: Optional[bool] = None,
        stick_color: Optional[str] = None,
        throttle_color: Optional[str] = None,
        color: Optional[str] = None,
        brightness: Optional[int] = None,
        profile_sync: Optional[bool] = None,
        profile_colors: Optional[dict] = None,
        push: bool = True,
    ) -> dict:
        """Atualiza cor, brilho, modo sincronizado e/ou sync por perfil e envia ao X56."""
        with self._lock:
            if linked is not None:
                self.linked = bool(linked)

            if color is not None:
                _, _, _, norm_hex = parse_hex_color(color, fallback=self.throttle_color)
                self.throttle_color = norm_hex
                self.stick_color = norm_hex
            else:
                if throttle_color is not None:
                    _, _, _, self.throttle_color = parse_hex_color(throttle_color, fallback=self.throttle_color)
                if stick_color is not None:
                    _, _, _, self.stick_color = parse_hex_color(stick_color, fallback=self.stick_color)
                if self.linked:
                    self.stick_color = self.throttle_color

            if brightness is not None:
                try:
                    self.brightness = max(0, min(100, int(brightness)))
                except (ValueError, TypeError):
                    pass

            if profile_sync is not None:
                self.profile_sync = bool(profile_sync)

            if isinstance(profile_colors, dict):
                for k, v in profile_colors.items():
                    _, _, _, norm_v = parse_hex_color(v, fallback=DEFAULT_PROFILE_RGB_COLORS.get(k, "#00D2FF"))
                    self.profile_colors[str(k)] = norm_v

        if push:
            self.apply_to_hardware()
        status = self.get_status()
        self._emit_state()
        return status

    def apply_profile_color(self, profile_id: str) -> bool:
        """Se profile_sync estiver ativo, muda automaticamente a cor do X56 para a cor do perfil."""
        if not self.profile_sync:
            return False
        target = self.profile_colors.get(profile_id) or DEFAULT_PROFILE_RGB_COLORS.get(profile_id)
        if not target:
            return False
        with self._lock:
            _, _, _, norm_hex = parse_hex_color(target)
            self.throttle_color = norm_hex
            self.stick_color = norm_hex
        self.apply_to_hardware()
        self._emit_state()
        return True

    def export_config(self) -> dict:
        """Devolve o dicionário limpo para persistir em config.json."""
        with self._lock:
            return {
                "linked": self.linked,
                "stick_color": self.stick_color,
                "throttle_color": self.throttle_color,
                "brightness": self.brightness,
                "profile_sync": self.profile_sync,
                "profile_colors": dict(self.profile_colors),
            }

    def get_status(self) -> dict:
        """Devolve estado completo dos dois motores RGB (USB HID Direto + DirectOutput) para o Dashboard."""
        with self._lock:
            hid_roles = [d.get("role", "x56") for d in self._hid_devices]
            do_roles = [d.get("role", "x56") for d in self._devices.values()]
            hid_count = len(self._hid_devices)
            do_count = len(self._devices)
            dev_count = max(hid_count, do_count)
            ver_str = ".".join(str(x) for x in self._dll_version) if any(self._dll_version) else ""

            stick_ready = ("stick" in hid_roles) or ("stick" in do_roles) or (dev_count >= 2)
            throttle_ready = ("throttle" in hid_roles) or ("throttle" in do_roles) or (dev_count >= 1)

            mods = []
            if stick_ready:
                mods.append("Manche")
            if throttle_ready:
                mods.append("Manete")
            mods_txt = " + ".join(mods) if mods else f"{dev_count} módulo(s)"

            if hid_count > 0 and do_count > 0:
                status_code = "ready"
                backend_label = "USB HID + DIRECTOUTPUT"
                message = f"RGB Dual-Engine ativo ({mods_txt}) — USB HID MI_02 + DirectOutput"
            elif hid_count > 0:
                status_code = "ready"
                backend_label = "USB HID DIRETO"
                message = f"USB HID Direto ativo ({mods_txt}) — controlo nativo sem drivers Logitech!"
            elif do_count > 0:
                status_code = "ready"
                backend_label = "DIRECTOUTPUT"
                message = f"Logitech DirectOutput ativo ({mods_txt})."
            else:
                status_code = "waiting_device"
                backend_label = "AGUARDANDO X56"
                message = "Liga o Logitech X56 por USB e clica em 🔄 (funciona via USB HID direto ou DirectOutput)."

            if self._last_error and status_code == "ready":
                message = f"{message} • Nota: {self._last_error}"

            return {
                "status": status_code,
                "backend": backend_label,
                "hid_count": hid_count,
                "directoutput_count": do_count,
                "dll_found": bool(self._initialized),
                "dll_path": self._dll_path or "",
                "dll_version": ver_str,
                "devices_count": dev_count,
                "stick_ready": stick_ready,
                "throttle_ready": throttle_ready,
                "linked": self.linked,
                "color": self.throttle_color,
                "stick_color": self.stick_color,
                "throttle_color": self.throttle_color,
                "brightness": self.brightness,
                "profile_sync": self.profile_sync,
                "profile_colors": dict(self.profile_colors),
                "message": message,
                "last_error": self._last_error,
            }

    def _emit_state(self) -> None:
        cb = self.on_state_change
        if cb:
            try:
                cb(self.get_status())
            except Exception:
                pass

    def close(self) -> None:
        """Encerra a sessão DirectOutput de forma limpa."""
        with self._lock:
            if self._dll and self._initialized:
                try:
                    self._dll.DirectOutput_Deinitialize()
                except Exception:
                    pass
            self._devices.clear()
            self._hid_devices.clear()
            self._initialized = False
            self._dll = None
            if self._dll_dir_handle is not None:
                try:
                    self._dll_dir_handle.close()
                except Exception:
                    pass
                self._dll_dir_handle = None
