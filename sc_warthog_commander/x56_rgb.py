"""
Logitech G / Saitek X56 Rhino RGB Backlight Controller (DirectOutput.dll Native API)
Controla a cor RGB de 24 bits (0..16777215) e o brilho (0..100%) do Manche e da Manete
Logitech G / Saitek X56 Rhino através da biblioteca oficial DirectOutput.dll do Windows.

Características:
- Deteção automática de DirectOutput.dll via Registo do Windows e caminhos padrão Logitech/Saitek
- Compatível com DirectOutput v8.x (3 argumentos em AddPage — X56) e v7.x legado (4 argumentos)
- Identificação exata de Stick (PID 0x2221) vs Throttle (PID 0xA221) via GUID DirectInput8
- Controlo unificado (Stick + Manete juntos) ou independente (cores distintas por módulo)
- Sincronização automática opcional com Perfis Star Citizen (M1 Combate / M2 Mineração / S1 Carga)
- Falha graciosa (zero crashes) quando o X56 ou o driver DirectOutput não estão presentes
"""

import ctypes
from ctypes import wintypes
import os
import threading
import time
import winreg
from typing import Callable, Optional

# Constantes DirectOutput SDK
FLAG_SET_AS_ACTIVE = 0x00000001
X56_PAGE_ID = 1
X56_LED_IDX_BRIGHTNESS = 0  # 0..100
X56_LED_IDX_COLOR = 1       # (R << 16) | (G << 8) | B (0..16777215)

# GUIDs de dispositivos Saitek que NÃO são X56 (para evitar interferir com X52 Pro / FIP)
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


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
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


# Callbacks DirectOutput (__stdcall via WINFUNCTYPE)
_PFN_DEVICE_CHANGE = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_bool, ctypes.c_void_p)
_PFN_ENUMERATE = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


def _guid_to_key(g: _GUID) -> str:
    """Converte GUID Win32 para o mesmo formato de directinput8_backend._guid_to_key."""
    d4 = "".join(f"{b:02X}" for b in g.Data4)
    return f"{g.Data1:08X}-{g.Data2:04X}-{g.Data3:04X}-{d4}"


def _guid_to_standard_str(g: _GUID) -> str:
    """Converte GUID Win32 para formato padrão 8-4-4-4-12 em maiúsculas."""
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

    # 1. Registo do Windows (chave oficial criada pelo instalador Logitech/Saitek)
    reg_paths = [
        r"SOFTWARE\Logitech\DirectOutput",
        r"SOFTWARE\Saitek\DirectOutput",
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

    # 2. Caminhos padrão de instalação Logitech / Saitek / Mad Catz (64-bit)
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
    Controlador RGB nativo para o Logitech G / Saitek X56 Rhino HOTAS via DirectOutput.dll.
    Gerencia cor de 24-bit, brilho 0-100%, ligação/separação Stick+Throttle e Auto-Sync de perfis.
    """

    def __init__(self, initial_settings: Optional[dict] = None):
        self._lock = threading.RLock()
        self._dll = None
        self._dll_path: Optional[str] = None
        self._dll_version: tuple[int, int, int, int] = (0, 0, 0, 0)
        self._dll_dir_handle = None
        self._initialized: bool = False
        self._use_4arg_addpage: bool = False
        self._last_error: str = ""

        # Dispositivos DirectOutput enumerados: {int(hDevice): {handle, role, type_guid, instance_guid, page_added}}
        self._devices: dict[int, dict] = {}
        self._di_devices_cache: list[dict] = []

        # Mantém referências vivas aos callbacks ctypes (impede GC enquanto a DLL os referencia)
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

        # Tenta inicializar automaticamente (sem nunca levantar exceção se o driver não existir)
        self._try_connect()

    def _configure_dll_prototypes(self, dll) -> None:
        """Define argtypes/restype exatos (64-bit safe) das funções exportadas por DirectOutput.dll."""
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

        # v8.x (Logitech G X56): 3 argumentos (hDevice, dwPage, dwFlags)
        # v7.x legado (Saitek SD6): 4 argumentos (hDevice, dwPage, wszDebugName, dwFlags)
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

    def _try_connect(self) -> bool:
        """Carrega DirectOutput.dll, inicializa a sessão e enumera dispositivos X56 ligados."""
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
                    # X56 usa sempre DirectOutput v8+ (3 args); apenas v1..v7 usam 4 args
                    self._use_4arg_addpage = (0 < major <= 7)
                    dll = ctypes.WinDLL(dll_path)
                else:
                    # Última tentativa: DLL diretamente no PATH do sistema
                    self._dll_version = (0, 0, 0, 0)
                    self._use_4arg_addpage = False
                    dll = ctypes.WinDLL("DirectOutput.dll")
                    self._dll_path = "DirectOutput.dll"
            except OSError:
                self._dll = None
                self._initialized = False
                self._last_error = (
                    "DirectOutput.dll não encontrada. Instala o software/driver oficial "
                    "Logitech X56 H.O.T.A.S. para ativar o controlo RGB."
                )
                return False

            try:
                self._configure_dll_prototypes(dll)
                hr = dll.DirectOutput_Initialize("SC_Warthog_Commander")
                if hr != 0:
                    self._last_error = f"DirectOutput_Initialize falhou (HRESULT=0x{hr & 0xFFFFFFFF:08X})"
                    self._dll = None
                    self._initialized = False
                    return False

                self._dll = dll
                self._initialized = True
                self._last_error = ""
                self._devices.clear()

                # Regista callback de ligação/desligação a quente e enumera já ligados
                dll.DirectOutput_RegisterDeviceCallback(self._cb_device_change, None)
                dll.DirectOutput_Enumerate(self._cb_enumerate, None)
                self._reclassify_devices_locked()
                return True
            except Exception as e:
                self._last_error = f"Erro DirectOutput: {e}"
                self._dll = None
                self._initialized = False
                return False

    def _on_device_enumerated(self, h_device, _p_ctxt):
        """Callback síncrono disparado por DirectOutput_Enumerate para cada dispositivo ligado."""
        if not h_device:
            return
        self._register_handle(int(h_device))

    def _on_device_change(self, h_device, b_added, _p_ctxt):
        """Callback assíncrono disparado quando um dispositivo DirectOutput é ligado ou desligado."""
        if not h_device:
            return
        h_int = int(h_device)
        if b_added:
            self._register_handle(h_int)
            with self._lock:
                self._reclassify_devices_locked()
            self.apply_to_hardware()
        else:
            with self._lock:
                self._devices.pop(h_int, None)
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

            # Ignora explicitamente X52 Pro / FIP caso o utilizador também os tenha ligados
            if type_guid_std in _NON_X56_DEVICE_TYPE_GUIDS:
                return

            try:
                if hasattr(self._dll, "DirectOutput_GetDeviceInstance"):
                    g_inst = _GUID()
                    if self._dll.DirectOutput_GetDeviceInstance(ctypes.c_void_p(h_int), ctypes.byref(g_inst)) == 0:
                        inst_guid_key = _guid_to_key(g_inst)
            except Exception:
                pass

            self._devices[h_int] = {
                "handle": h_int,
                "role": "x56",
                "type_guid": type_guid_std,
                "instance_guid": inst_guid_key,
                "page_added": False,
            }
            self._ensure_page_locked(h_int)

    def _ensure_page_locked(self, h_int: int) -> bool:
        """Cria e ativa a página DirectOutput (ID=1) no dispositivo X56."""
        info = self._devices.get(h_int)
        if not info or not self._dll:
            return False
        if info.get("page_added"):
            return True
        try:
            h_ptr = ctypes.c_void_p(h_int)
            if self._use_4arg_addpage:
                hr = self._dll.DirectOutput_AddPage(h_ptr, X56_PAGE_ID, "SC_RGB", FLAG_SET_AS_ACTIVE)
            else:
                hr = self._dll.DirectOutput_AddPage(h_ptr, X56_PAGE_ID, FLAG_SET_AS_ACTIVE)
            # S_OK (0) ou ERROR_ALREADY_EXISTS (0x800700B7) significa que a página 1 está pronta
            if hr == 0 or (hr & 0xFFFFFFFF) == 0x800700B7:
                info["page_added"] = True
                return True
            self._last_error = f"DirectOutput_AddPage retornou 0x{hr & 0xFFFFFFFF:08X}"
        except Exception as e:
            self._last_error = f"Erro AddPage: {e}"
        return False

    def _reclassify_devices_locked(self) -> None:
        """Associa cada handle DirectOutput ao papel 'stick' ou 'throttle' via DirectInput8."""
        if not self._devices:
            return

        di_by_guid: dict[str, dict] = {}
        x56_di_roles: list[str] = []
        for d in self._di_devices_cache or []:
            gkey = str(d.get("guid_key") or d.get("slot") or "").upper()
            if gkey:
                di_by_guid[gkey] = d
            if d.get("kit") == "saitek_x56" or d.get("pid") in (0x2221, 0xA221):
                r = "stick" if d.get("pid") == 0x2221 else ("throttle" if d.get("pid") == 0xA221 else d.get("role", "x56"))
                x56_di_roles.append(r)

        assigned_roles: set[str] = set()
        unmatched: list[dict] = []

        for info in self._devices.values():
            inst = (info.get("instance_guid") or "").upper()
            di = di_by_guid.get(inst) if inst else None
            if di:
                if di.get("pid") == 0x2221 or di.get("role") == "stick":
                    info["role"] = "stick"
                    assigned_roles.add("stick")
                    continue
                if di.get("pid") == 0xA221 or di.get("role") == "throttle":
                    info["role"] = "throttle"
                    assigned_roles.add("throttle")
                    continue
            unmatched.append(info)

        # Fallback limpo caso DirectOutput_GetDeviceInstance não tenha correspondido ao GUID DI8
        if unmatched:
            if len(unmatched) == 1 and len(x56_di_roles) == 1:
                unmatched[0]["role"] = x56_di_roles[0]
            else:
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
        """Atualiza a tabela de GUIDs DirectInput8 para identificar Stick vs Throttle."""
        with self._lock:
            self._di_devices_cache = list(di_devices or [])
            self._reclassify_devices_locked()

    def rescan(self, di_devices: Optional[list[dict]] = None) -> dict:
        """Re-deteta DirectOutput.dll e dispositivos X56 ligados, aplicando a cor atual."""
        with self._lock:
            if di_devices is not None:
                self._di_devices_cache = list(di_devices)
            if not self._initialized or self._dll is None:
                self._try_connect()
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

    def _send_rgb_to_handle_locked(self, h_int: int, hex_color: str, brightness: int) -> bool:
        """Envia brilho (dwIndex=0) e cor 24-bit (dwIndex=1) para um handle X56."""
        if not self._dll or not self._initialized:
            return False
        if not self._ensure_page_locked(h_int):
            return False

        r, g, b, _ = parse_hex_color(hex_color)
        br = max(0, min(100, int(brightness)))
        if r == 0 and g == 0 and b == 0:
            br = 0
        rgb_int = 0 if br == 0 else rgb_to_int24(r, g, b)

        h_ptr = ctypes.c_void_p(h_int)
        try:
            hr_br = self._dll.DirectOutput_SetLed(h_ptr, X56_PAGE_ID, X56_LED_IDX_BRIGHTNESS, br)
            time.sleep(0.004)
            hr_col = self._dll.DirectOutput_SetLed(h_ptr, X56_PAGE_ID, X56_LED_IDX_COLOR, rgb_int)
            if hr_br == 0 and hr_col == 0:
                self._last_error = ""
                return True
            self._last_error = f"SetLed HRESULT br=0x{hr_br & 0xFFFFFFFF:08X} col=0x{hr_col & 0xFFFFFFFF:08X}"
            return False
        except Exception as e:
            self._last_error = f"Erro SetLed: {e}"
            return False

    def apply_to_hardware(self) -> int:
        """Aplica a configuração RGB atual a todos os dispositivos X56 conectados."""
        sent = 0
        with self._lock:
            if not self._initialized or not self._dll or not self._devices:
                return 0
            for h_int, info in list(self._devices.items()):
                role = info.get("role", "x56")
                if self.linked:
                    target_hex = self.throttle_color
                elif role == "stick":
                    target_hex = self.stick_color
                else:
                    target_hex = self.throttle_color
                if self._send_rgb_to_handle_locked(h_int, target_hex, self.brightness):
                    sent += 1
        return sent

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
        """Devolve estado completo para enviar ao Dashboard via WebSocket."""
        with self._lock:
            roles = [d.get("role", "x56") for d in self._devices.values()]
            dev_count = len(self._devices)
            ver_str = ".".join(str(x) for x in self._dll_version) if any(self._dll_version) else ""

            if not self._initialized:
                status_code = "no_driver"
                message = self._last_error or "Driver Logitech DirectOutput não detetado."
            elif dev_count == 0:
                status_code = "waiting_device"
                message = "DirectOutput ativo — liga o Logitech X56 por USB e clica em Re-detetar."
            else:
                status_code = "ready"
                message = f"Logitech DirectOutput ligado ({dev_count} módulo{'s' if dev_count != 1 else ''} RGB pronto{'s' if dev_count != 1 else ''})."

            return {
                "status": status_code,
                "dll_found": bool(self._initialized),
                "dll_path": self._dll_path or "",
                "dll_version": ver_str,
                "devices_count": dev_count,
                "stick_ready": ("stick" in roles) or (dev_count >= 2),
                "throttle_ready": ("throttle" in roles) or (dev_count >= 1),
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
        """Remove páginas DirectOutput e encerra a sessão de forma limpa."""
        with self._lock:
            if self._dll and self._initialized:
                for h_int, info in list(self._devices.items()):
                    if info.get("page_added"):
                        try:
                            self._dll.DirectOutput_RemovePage(ctypes.c_void_p(h_int), X56_PAGE_ID)
                        except Exception:
                            pass
                try:
                    self._dll.DirectOutput_Deinitialize()
                except Exception:
                    pass
            self._devices.clear()
            self._initialized = False
            self._dll = None
            if self._dll_dir_handle is not None:
                try:
                    self._dll_dir_handle.close()
                except Exception:
                    pass
                self._dll_dir_handle = None
