"""
Native DirectInput8 (dinput8.dll) Backend for Windows (64-bit / 32-bit)
Usa exatamente a mesma API DirectInput8 que o Star Citizen usa — deteta controladores
com >32 botões e 8 eixos (como Logitech G / Saitek X56 Rhino Throttle VID_0738&PID_A221)
mesmo quando o antigo WinMM (joyGetPosEx) falha, rejeita flags POV ou esgota os 16 slots.
"""

import ctypes
from ctypes import wintypes
from typing import Optional

# Constants
DIRECTINPUT_VERSION = 0x0800
DI8DEVCLASS_GAMECTRL = 4
DIEDFL_ATTACHEDONLY = 0x00000001
DIENUM_CONTINUE = 1
DIENUM_STOP = 0

DISCL_NONEXCLUSIVE = 0x00000002
DISCL_BACKGROUND = 0x00000008

DIDFT_ALL = 0x00000000
DIDFT_RELAXIS = 0x00000001
DIDFT_ABSAXIS = 0x00000002
DIDFT_AXIS = 0x00000003
DIDFT_PSHBUTTON = 0x00000004
DIDFT_TGLBUTTON = 0x00000008
DIDFT_BUTTON = 0x0000000C
DIDFT_POV = 0x00000010
DIDFT_ANYINSTANCE = 0x00FFFF00
DIDFT_OPTIONAL = 0x80000000
DIDF_ABSAXIS = 0x00000001

DIERR_INPUTLOST = 0x8007001E
DIERR_NOTACQUIRED = 0x8007000C


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


IID_IDirectInput8W = GUID(
    0xBF798031, 0x483A, 0x4DA2,
    (ctypes.c_ubyte * 8)(0xAA, 0x99, 0x5D, 0x64, 0xED, 0x36, 0x97, 0x00),
)

GUID_XAxis  = GUID(0xA36D02E0, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_YAxis  = GUID(0xA36D02E1, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_ZAxis  = GUID(0xA36D02E2, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_RxAxis = GUID(0xA36D02F4, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_RyAxis = GUID(0xA36D02F5, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_RzAxis = GUID(0xA36D02E3, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_Slider = GUID(0xA36D02E4, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))
GUID_POV    = GUID(0xA36D02F2, 0xC9F3, 0x11CF, (ctypes.c_ubyte * 8)(0xBF, 0xC7, 0x44, 0x45, 0x53, 0x54, 0x00, 0x00))


class DIDEVICEINSTANCEW(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("guidInstance", GUID),
        ("guidProduct", GUID),
        ("dwDevType", wintypes.DWORD),
        ("tszInstanceName", wintypes.WCHAR * 260),
        ("tszProductName", wintypes.WCHAR * 260),
        ("guidFFDriver", GUID),
        ("wUsagePage", wintypes.WORD),
        ("wUsage", wintypes.WORD),
    ]


class DIDEVCAPS(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("dwDevType", wintypes.DWORD),
        ("dwAxes", wintypes.DWORD),
        ("dwButtons", wintypes.DWORD),
        ("dwPOVs", wintypes.DWORD),
        ("dwFFSamplePeriod", wintypes.DWORD),
        ("dwFFMinTimeResolution", wintypes.DWORD),
        ("dwFirmwareRevision", wintypes.DWORD),
        ("dwHardwareRevision", wintypes.DWORD),
        ("dwFFDriverVersion", wintypes.DWORD),
    ]


class DIOBJECTDATAFORMAT(ctypes.Structure):
    _fields_ = [
        ("pguid", ctypes.POINTER(GUID)),
        ("dwOfs", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
    ]


class DIDATAFORMAT(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("dwObjSize", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("dwDataSize", wintypes.DWORD),
        ("dwNumObjs", wintypes.DWORD),
        ("rgodf", ctypes.POINTER(DIOBJECTDATAFORMAT)),
    ]


class DIJOYSTATE2(ctypes.Structure):
    _fields_ = [
        ("lX", wintypes.LONG),
        ("lY", wintypes.LONG),
        ("lZ", wintypes.LONG),
        ("lRx", wintypes.LONG),
        ("lRy", wintypes.LONG),
        ("lRz", wintypes.LONG),
        ("rglSlider", wintypes.LONG * 2),
        ("rgdwPOV", wintypes.DWORD * 4),
        ("rgbButtons", ctypes.c_ubyte * 128),
        ("lVX", wintypes.LONG),
        ("lVY", wintypes.LONG),
        ("lVZ", wintypes.LONG),
        ("lVRx", wintypes.LONG),
        ("lVRy", wintypes.LONG),
        ("lVRz", wintypes.LONG),
        ("rglVSlider", wintypes.LONG * 2),
        ("lAX", wintypes.LONG),
        ("lAY", wintypes.LONG),
        ("lAZ", wintypes.LONG),
        ("lARx", wintypes.LONG),
        ("lARy", wintypes.LONG),
        ("lARz", wintypes.LONG),
        ("rglASlider", wintypes.LONG * 2),
        ("lFX", wintypes.LONG),
        ("lFY", wintypes.LONG),
        ("lFZ", wintypes.LONG),
        ("lFRx", wintypes.LONG),
        ("lFRy", wintypes.LONG),
        ("lFRz", wintypes.LONG),
        ("rglFSlider", wintypes.LONG * 2),
    ]


def _build_joystick2_dataformat():
    """Constrói a tabela oficial c_dfDIJoystick2 (8 eixos + 4 POVs + 128 botões)."""
    objs = []
    axis_defs = [
        (GUID_XAxis,  DIJOYSTATE2.lX.offset),
        (GUID_YAxis,  DIJOYSTATE2.lY.offset),
        (GUID_ZAxis,  DIJOYSTATE2.lZ.offset),
        (GUID_RxAxis, DIJOYSTATE2.lRx.offset),
        (GUID_RyAxis, DIJOYSTATE2.lRy.offset),
        (GUID_RzAxis, DIJOYSTATE2.lRz.offset),
        (GUID_Slider, DIJOYSTATE2.rglSlider.offset),
        (GUID_Slider, DIJOYSTATE2.rglSlider.offset + 4),
    ]
    for g, ofs in axis_defs:
        objs.append(DIOBJECTDATAFORMAT(
            ctypes.pointer(g), ofs,
            DIDFT_AXIS | DIDFT_ANYINSTANCE | DIDFT_OPTIONAL, 0
        ))
    for i in range(4):
        objs.append(DIOBJECTDATAFORMAT(
            ctypes.pointer(GUID_POV), DIJOYSTATE2.rgdwPOV.offset + i * 4,
            DIDFT_POV | DIDFT_ANYINSTANCE | DIDFT_OPTIONAL, 0
        ))
    for i in range(128):
        objs.append(DIOBJECTDATAFORMAT(
            None, DIJOYSTATE2.rgbButtons.offset + i,
            DIDFT_BUTTON | DIDFT_ANYINSTANCE | DIDFT_OPTIONAL, 0
        ))

    arr_type = DIOBJECTDATAFORMAT * len(objs)
    arr = arr_type(*objs)
    fmt = DIDATAFORMAT(
        ctypes.sizeof(DIDATAFORMAT),
        ctypes.sizeof(DIOBJECTDATAFORMAT),
        DIDF_ABSAXIS,
        ctypes.sizeof(DIJOYSTATE2),
        len(objs),
        arr,
    )
    return fmt, arr


_DF_JOY2, _DF_JOY2_ARR = _build_joystick2_dataformat()

# COM vtable call helper
def _com_call(obj_ptr: ctypes.c_void_p, vtable_index: int, restype, argtypes, *args):
    vtable = ctypes.cast(obj_ptr, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    fn_ptr = vtable[vtable_index]
    fn_type = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return fn_type(fn_ptr)(obj_ptr, *args)


ENUM_DEVICES_CB = ctypes.WINFUNCTYPE(
    wintypes.BOOL, ctypes.POINTER(DIDEVICEINSTANCEW), ctypes.c_void_p
)


def _guid_to_key(g: GUID) -> str:
    d4 = "".join(f"{b:02X}" for b in g.Data4)
    return f"{g.Data1:08X}-{g.Data2:04X}-{g.Data3:04X}-{d4}"


class DirectInput8Device:
    """Wrapper para um dispositivo IDirectInputDevice8W aberto (lê até 128 botões e 8 eixos)."""

    def __init__(self, dev_ptr: ctypes.c_void_p, info: dict):
        self.ptr = dev_ptr
        self.info = info
        self.state = DIJOYSTATE2()
        self.closed = False

    def poll(self) -> bool:
        if self.closed or not self.ptr:
            return False
        try:
            # IDirectInputDevice8W::Poll = vtable index 25
            hr = _com_call(self.ptr, 25, ctypes.c_ulong, [])
            if hr in (DIERR_INPUTLOST, DIERR_NOTACQUIRED) or (hr & 0x80000000):
                # IDirectInputDevice8W::Acquire = vtable index 7
                _com_call(self.ptr, 7, ctypes.c_ulong, [])
                _com_call(self.ptr, 25, ctypes.c_ulong, [])

            # IDirectInputDevice8W::GetDeviceState = vtable index 9
            hr = _com_call(
                self.ptr, 9, ctypes.c_ulong,
                [wintypes.DWORD, ctypes.c_void_p],
                ctypes.sizeof(DIJOYSTATE2), ctypes.byref(self.state)
            )
            if hr in (DIERR_INPUTLOST, DIERR_NOTACQUIRED):
                _com_call(self.ptr, 7, ctypes.c_ulong, [])
                hr = _com_call(
                    self.ptr, 9, ctypes.c_ulong,
                    [wintypes.DWORD, ctypes.c_void_p],
                    ctypes.sizeof(DIJOYSTATE2), ctypes.byref(self.state)
                )
            return (hr & 0x80000000) == 0
        except Exception:
            return False

    def get_buttons_mask(self) -> int:
        """Retorna bitmask inteira com todos os botões premidos (suporta até 128 botões!)."""
        mask = 0
        btns = self.state.rgbButtons
        # Lê os primeiros 64 botões (X56 Throttle usa até ~36)
        for i in range(64):
            if btns[i] & 0x80:
                mask |= (1 << i)
        return mask

    def get_pov(self) -> int:
        val = int(self.state.rgdwPOV[0])
        if val == 0xFFFFFFFF or val > 36000:
            return 0xFFFF
        return val

    def get_axes(self) -> dict:
        s = self.state
        return {
            "x": max(0, min(65535, int(s.lX))),
            "y": max(0, min(65535, int(s.lY))),
            "z": max(0, min(65535, int(s.lZ))),
            "rx": max(0, min(65535, int(s.lRx))),
            "ry": max(0, min(65535, int(s.lRy))),
            "rz": max(0, min(65535, int(s.lRz))),
            "slider0": max(0, min(65535, int(s.rglSlider[0]))),
            "slider1": max(0, min(65535, int(s.rglSlider[1]))),
        }

    def close(self):
        if self.ptr and not self.closed:
            self.closed = True
            try:
                # Unacquire = 8, Release = 2
                _com_call(self.ptr, 8, ctypes.c_ulong, [])
                _com_call(self.ptr, 2, ctypes.c_ulong, [])
            except Exception:
                pass
            self.ptr = None


class DirectInput8Manager:
    """Gestor DirectInput8 nativo (dinput8.dll) sem dependências externas."""

    def __init__(self):
        self.di_ptr: Optional[ctypes.c_void_p] = None
        self._init_dinput()

    def _init_dinput(self):
        try:
            dinput8 = ctypes.windll.dinput8
            kernel32 = ctypes.windll.kernel32
            kernel32.GetModuleHandleW.restype = ctypes.c_void_p
            hinst = kernel32.GetModuleHandleW(None)

            di_ptr = ctypes.c_void_p()
            dinput8.DirectInput8Create.argtypes = [
                ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(GUID),
                ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p
            ]
            dinput8.DirectInput8Create.restype = ctypes.c_ulong
            hr = dinput8.DirectInput8Create(
                hinst, DIRECTINPUT_VERSION, ctypes.byref(IID_IDirectInput8W),
                ctypes.byref(di_ptr), None
            )
            if (hr & 0x80000000) == 0 and di_ptr.value:
                self.di_ptr = di_ptr
        except Exception:
            self.di_ptr = None

    def available(self) -> bool:
        return bool(self.di_ptr and self.di_ptr.value)

    def enumerate_devices(self) -> list[dict]:
        """Enumera todos os controladores DirectInput8 fisicamente ligados."""
        if not self.available():
            return []

        found = []

        def _cb(lpddi, pvref):
            inst = lpddi.contents
            data1 = int(inst.guidProduct.Data1)
            vid = data1 & 0xFFFF
            pid = (data1 >> 16) & 0xFFFF
            name = (inst.tszProductName or inst.tszInstanceName or "").strip()

            # Obtém contagem real de botões e eixos via CreateDevice + GetCapabilities
            btns = 0
            axes = 0
            povs = 0
            dev_ptr = ctypes.c_void_p()
            # IDirectInput8W::CreateDevice = vtable index 3
            hr = _com_call(
                self.di_ptr, 3, ctypes.c_ulong,
                [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p],
                ctypes.byref(inst.guidInstance), ctypes.byref(dev_ptr), None
            )
            if (hr & 0x80000000) == 0 and dev_ptr.value:
                caps = DIDEVCAPS()
                caps.dwSize = ctypes.sizeof(DIDEVCAPS)
                # IDirectInputDevice8W::GetCapabilities = vtable index 3
                hr_c = _com_call(
                    dev_ptr, 3, ctypes.c_ulong,
                    [ctypes.POINTER(DIDEVCAPS)],
                    ctypes.byref(caps)
                )
                if (hr_c & 0x80000000) == 0:
                    btns = int(caps.dwButtons)
                    axes = int(caps.dwAxes)
                    povs = int(caps.dwPOVs)
                # Release = index 2
                _com_call(dev_ptr, 2, ctypes.c_ulong, [])

            g_copy = GUID()
            ctypes.memmove(ctypes.byref(g_copy), ctypes.byref(inst.guidInstance), ctypes.sizeof(GUID))

            found.append({
                "guid_key": _guid_to_key(g_copy),
                "guid_instance": g_copy,
                "mid": vid,
                "pid": pid,
                "vid_hex": f"{vid:04X}",
                "pid_hex": f"{pid:04X}",
                "btns": btns,
                "axes": axes,
                "povs": povs,
                "name": name,
            })
            return DIENUM_CONTINUE

        cb_fn = ENUM_DEVICES_CB(_cb)
        # IDirectInput8W::EnumDevices = vtable index 4
        _com_call(
            self.di_ptr, 4, ctypes.c_ulong,
            [wintypes.DWORD, ENUM_DEVICES_CB, ctypes.c_void_p, wintypes.DWORD],
            DI8DEVCLASS_GAMECTRL, cb_fn, None, DIEDFL_ATTACHEDONLY
        )
        return found

    def open_device(self, dev_info: dict) -> Optional[DirectInput8Device]:
        """Abre um dispositivo DirectInput8 em modo BACKGROUND + NONEXCLUSIVE para leitura contínua."""
        if not self.available():
            return None
        dev_ptr = ctypes.c_void_p()
        hr = _com_call(
            self.di_ptr, 3, ctypes.c_ulong,
            [ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p],
            ctypes.byref(dev_info["guid_instance"]), ctypes.byref(dev_ptr), None
        )
        if (hr & 0x80000000) != 0 or not dev_ptr.value:
            return None

        # SetDataFormat = index 11
        hr_df = _com_call(
            dev_ptr, 11, ctypes.c_ulong,
            [ctypes.POINTER(DIDATAFORMAT)],
            ctypes.byref(_DF_JOY2)
        )
        if (hr_df & 0x80000000) != 0:
            _com_call(dev_ptr, 2, ctypes.c_ulong, [])
            return None

        # SetCooperativeLevel = index 13 (hwnd=None + DISCL_BACKGROUND | DISCL_NONEXCLUSIVE funciona em background!)
        hr_cl = _com_call(
            dev_ptr, 13, ctypes.c_ulong,
            [wintypes.HWND, wintypes.DWORD],
            None, DISCL_BACKGROUND | DISCL_NONEXCLUSIVE
        )
        if (hr_cl & 0x80000000) != 0:
            # Fallback usando GetDesktopWindow() caso algum driver exija HWND válido
            hwnd_desk = ctypes.windll.user32.GetDesktopWindow()
            _com_call(
                dev_ptr, 13, ctypes.c_ulong,
                [wintypes.HWND, wintypes.DWORD],
                hwnd_desk, DISCL_BACKGROUND | DISCL_NONEXCLUSIVE
            )

        # Acquire = index 7
        _com_call(dev_ptr, 7, ctypes.c_ulong, [])
        d = DirectInput8Device(dev_ptr, dev_info)
        d.poll()
        return d
