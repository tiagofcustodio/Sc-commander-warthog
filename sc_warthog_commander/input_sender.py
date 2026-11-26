"""
Input Sender - Hardware Scancode Emulation
Módulo de injeção de teclas em nível de hardware (SendInput com Scancodes) para jogos DirectX como Star Citizen.
"""

import ctypes
from ctypes import wintypes
import time
import threading

user32 = ctypes.windll.user32

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_WHEEL = 0x0800
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002
WHEEL_DELTA = 120
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001

# Mouse button mapping: key_name -> (down_flag, up_flag, mouseData)
MOUSE_BUTTONS = {
    "MOUSE1": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
    "LMB": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
    "MOUSE2": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
    "RMB": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
    "MOUSE3": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
    "MMB": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
    "MOUSE4": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1),
    "MOUSE5": (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2),
}

MAPVK_VK_TO_VSC = 0

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    class _INPUT_UNION(ctypes.Union):
        _fields_ = [
            ('mi', MOUSEINPUT),
            ('ki', KEYBDINPUT),
        ]
    _fields_ = [
        ('type', wintypes.DWORD),
        ('u', _INPUT_UNION)
    ]

# Common VK codes
VK_MODIFIERS = {
    "SHIFT": 0x10,      # VK_SHIFT
    "LSHIFT": 0xA0,     # VK_LSHIFT
    "RSHIFT": 0xA1,
    "CTRL": 0x11,       # VK_CONTROL
    "LCTRL": 0xA2,
    "RCTRL": 0xA3,
    "ALT": 0x12,        # VK_MENU
    "LALT": 0xA4,
    "RALT": 0xA5,
}

# Special key VK map
SPECIAL_KEYS = {
    "SPACE": 0x20,
    "ENTER": 0x0D,
    "ESCAPE": 0x1B,
    "ESC": 0x1B,
    "TAB": 0x09,
    "BACKSPACE": 0x08,
    "CAPSLOCK": 0x14,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "HOME": 0x24,
    "END": 0x23,
    "PGUP": 0x21,
    "PGDN": 0x22,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "NUM0": 0x60, "NUM1": 0x61, "NUM2": 0x62, "NUM3": 0x63, "NUM4": 0x64,
    "NUM5": 0x65, "NUM6": 0x66, "NUM7": 0x67, "NUM8": 0x68, "NUM9": 0x69,
    "NUMPAD0": 0x60, "NUMPAD1": 0x61, "NUMPAD2": 0x62, "NUMPAD3": 0x63, "NUMPAD4": 0x64,
    "NUMPAD5": 0x65, "NUMPAD6": 0x66, "NUMPAD7": 0x67, "NUMPAD8": 0x68, "NUMPAD9": 0x69,
    "NUM_ADD": 0x6B, "NUM_SUB": 0x6D, "NUM_MUL": 0x6A, "NUM_DIV": 0x6F,
}

_input_lock = threading.Lock()

def key_to_scancode(key_name: str) -> tuple[int, bool]:
    """
    Converte um nome de tecla ('R', 'SPACE', 'F1', etc.) no scancode correspondente.
    Retorna (scancode, is_extended).
    """
    k = key_name.strip().upper()
    
    # 1. Checa modificadores
    if k in VK_MODIFIERS:
        vk = VK_MODIFIERS[k]
        sc = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        is_ext = (k in ("RSHIFT", "RCTRL", "RALT"))
        return sc, is_ext

    # 2. Checa teclas especiais
    if k in SPECIAL_KEYS:
        vk = SPECIAL_KEYS[k]
        sc = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        is_ext = (k in ("UP", "DOWN", "LEFT", "RIGHT", "INSERT", "DELETE", "HOME", "END", "PGUP", "PGDN", "NUM_DIV"))
        return sc, is_ext

    # 3. Tecla alfanumérica simples (ex: 'R', 'N', '1')
    if len(k) == 1:
        vk = ord(k)
        sc = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
        return sc, False

    return 0, False


def _send_key_event(scancode: int, flags: int):
    """Dispara um evento de teclado via SendInput."""
    if scancode <= 0:
        return
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki.wVk = 0
    inp.u.ki.wScan = scancode
    inp.u.ki.dwFlags = KEYEVENTF_SCANCODE | flags
    inp.u.ki.time = 0
    inp.u.ki.dwExtraInfo = None
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _send_mouse_wheel(delta: int):
    """Dispara um evento de roda do rato (Mouse Wheel Up/Down) via SendInput."""
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.u.mi.dx = 0
    inp.u.mi.dy = 0
    inp.u.mi.mouseData = ctypes.c_ulong(delta & 0xFFFFFFFF).value
    inp.u.mi.dwFlags = MOUSEEVENTF_WHEEL
    inp.u.mi.time = 0
    inp.u.mi.dwExtraInfo = None
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def _send_mouse_button(key_upper: str, is_down: bool):
    """Dispara um evento de clique de botão do rato (MOUSE1..MOUSE5) via SendInput."""
    spec = MOUSE_BUTTONS.get(key_upper)
    if not spec:
        return
    down_flag, up_flag, mdata = spec
    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.u.mi.dx = 0
    inp.u.mi.dy = 0
    inp.u.mi.mouseData = mdata
    inp.u.mi.dwFlags = down_flag if is_down else up_flag
    inp.u.mi.time = 0
    inp.u.mi.dwExtraInfo = None
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def send_key_state(key: str, is_down: bool):
    """Pressiona ou liberta uma tecla ou botão do rato continuamente (Afterburner / Boost / Disparo)."""
    k = (key or "").strip().upper()
    if k in ("MWHEEL_UP", "MWHEEL_DOWN"):
        if is_down:
            with _input_lock:
                _send_mouse_wheel(WHEEL_DELTA if k == "MWHEEL_UP" else -WHEEL_DELTA)
        return

    if k in MOUSE_BUTTONS:
        with _input_lock:
            _send_mouse_button(k, is_down)
        return

    sc, ext = key_to_scancode(k)
    if sc <= 0:
        return
    flags = (KEYEVENTF_EXTENDEDKEY if ext else 0) | (0 if is_down else KEYEVENTF_KEYUP)
    with _input_lock:
        _send_key_event(sc, flags)


def _precise_sleep(seconds: float):
    """Espera precisa com perf_counter() para respeitar exatamente a duração do impulso (hold_ms)."""
    if seconds <= 0:
        return
    target = time.perf_counter() + seconds
    if seconds > 0.025:
        time.sleep(seconds - 0.015)
    while time.perf_counter() < target:
        rem = target - time.perf_counter()
        if rem > 0.005:
            time.sleep(0.002)
        else:
            time.sleep(0)


def send_key_pulse(key: str, modifiers: list[str] = None, hold_ms: int = 60, blocking: bool = False):
    """
    Envia um pulso limpo da tecla, botão do rato ou roda do rato com eventuais modificadores (ex: LALT + N).
    - Não bloqueia _input_lock durante o sleep (evita congelar outros botões durante impulsos longos!).
    - Usa temporização de alta precisão (_precise_sleep) para respeitar hold_ms exatamente (20ms..10000ms).
    - Com blocking=True (usado em macros), espera pelo fim exato do impulso antes de avançar para o passo seguinte.
    """
    if not key or key.strip().upper() == "Z":
        return

    try:
        hold_ms_int = max(20, int(hold_ms))
    except (TypeError, ValueError):
        hold_ms_int = 60

    def _worker():
        k_upper = key.strip().upper()
        mod_scancodes = []

        # 1. Pressiona modificadores (lock apenas no SendInput, nunca durante o sleep!)
        if modifiers:
            with _input_lock:
                for mod in modifiers:
                    m_sc, m_ext = key_to_scancode(mod)
                    if m_sc > 0:
                        flags = KEYEVENTF_EXTENDEDKEY if m_ext else 0
                        _send_key_event(m_sc, flags)
                        mod_scancodes.append((m_sc, flags))
            if mod_scancodes:
                _precise_sleep(0.020)

        sleep_time = hold_ms_int / 1000.0

        # 2. Executa tecla principal / botão do rato / roda do rato
        if k_upper in ("MWHEEL_UP", "MWHEEL_DOWN"):
            with _input_lock:
                _send_mouse_wheel(WHEEL_DELTA if k_upper == "MWHEEL_UP" else -WHEEL_DELTA)
            _precise_sleep(sleep_time)
        elif k_upper in MOUSE_BUTTONS:
            with _input_lock:
                _send_mouse_button(k_upper, True)
            _precise_sleep(sleep_time)
            with _input_lock:
                _send_mouse_button(k_upper, False)
        else:
            main_sc, main_ext = key_to_scancode(k_upper)
            if main_sc > 0:
                down_flags = KEYEVENTF_EXTENDEDKEY if main_ext else 0
                with _input_lock:
                    _send_key_event(main_sc, down_flags)
                _precise_sleep(sleep_time)
                with _input_lock:
                    _send_key_event(main_sc, down_flags | KEYEVENTF_KEYUP)

        # 3. Solta os modificadores na ordem inversa após pequena margem
        if mod_scancodes:
            _precise_sleep(0.020)
            with _input_lock:
                for m_sc, m_flags in reversed(mod_scancodes):
                    _send_key_event(m_sc, m_flags | KEYEVENTF_KEYUP)

    if blocking:
        _worker()
    else:
        threading.Thread(target=_worker, daemon=True).start()
