"""
Windows System Tray Service for Warthog Commander (Windows 10 & Windows 11 Compatible)
Suporta Windows Terminal (CASCADIA_HOSTING_WINDOW_CLASS), Consola Clássica (ConsoleWindowClass)
e Janela do Dashboard (Edge --app / Chrome / Firefox).
Ao minimizar o Dashboard ou a Consola, oculta automaticamente da barra de tarefas para o System Tray.
"""

import os
import time
import ctypes
import threading
import win32api
import win32con
import win32gui
from typing import Callable, Optional


def _get_legacy_console_hwnd() -> int:
    try:
        return int(ctypes.windll.kernel32.GetConsoleWindow() or 0)
    except Exception:
        return 0


def _is_window_minimized(hwnd: int) -> bool:
    """Deteta de forma fiável se uma janela está minimizada (suporta Windows 11 Terminal e Edge/Chrome)."""
    try:
        if win32gui.IsIconic(hwnd):
            return True
        placement = win32gui.GetWindowPlacement(hwnd)
        if placement and placement[1] == win32con.SW_SHOWMINIMIZED:
            return True
    except Exception:
        pass
    return False


def _find_console_hwnds() -> list[int]:
    """Encontra a janela real da Consola (tanto CMD clássico como Windows 11 Terminal)."""
    hwnds = []
    legacy = _get_legacy_console_hwnd()
    if legacy and win32gui.IsWindow(legacy) and win32gui.IsWindowVisible(legacy):
        hwnds.append(legacy)

    def _enum_cb(hwnd, _):
        try:
            cls = win32gui.GetClassName(hwnd) or ""
            if cls in ("CASCADIA_HOSTING_WINDOW_CLASS", "ConsoleWindowClass"):
                title = (win32gui.GetWindowText(hwnd) or "").lower()
                if any(k in title for k in ("warthog", "main.py", "run.bat", "sc_warthog_commander")):
                    if hwnd not in hwnds:
                        hwnds.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception:
        pass
    return hwnds


def _find_dashboard_hwnds() -> list[int]:
    """Encontra a janela do Dashboard (Edge --app, Chrome ou Browser com Warthog SC Commander)."""
    hwnds = []
    console_set = set(_find_console_hwnds())
    legacy = _get_legacy_console_hwnd()
    if legacy:
        console_set.add(legacy)

    def _enum_cb(hwnd, _):
        try:
            if hwnd in console_set:
                return True
            cls = win32gui.GetClassName(hwnd) or ""
            if cls in ("WarthogSCTrayClass", "CASCADIA_HOSTING_WINDOW_CLASS", "ConsoleWindowClass"):
                return True
            title = (win32gui.GetWindowText(hwnd) or "").lower()
            if any(k in title for k in ("warthog sc commander", "warthog commander", "aegis // warthog", "127.0.0.1:8765")):
                if hwnd not in hwnds:
                    hwnds.append(hwnd)
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception:
        pass
    return hwnds


class WarthogTrayIcon:
    def __init__(
        self,
        on_open_dashboard: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        auto_hide_console: bool = True,
    ):
        self.on_open_dashboard = on_open_dashboard
        self.on_exit = on_exit
        self.auto_hide_console = auto_hide_console
        self.hwnd = None
        self.running = False
        self._thread = None
        self._monitor_thread = None
        self._hidden_dash_hwnds: list[int] = []
        self._hidden_console_hwnds: list[int] = []

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run_tray_loop, daemon=True)
        self._thread.start()
        self._monitor_thread = threading.Thread(target=self._monitor_minimize_loop, daemon=True)
        self._monitor_thread.start()

    def hide_console(self):
        for h in _find_console_hwnds():
            if win32gui.IsWindow(h):
                win32gui.ShowWindow(h, win32con.SW_HIDE)
                if h not in self._hidden_console_hwnds:
                    self._hidden_console_hwnds.append(h)

    def show_console(self):
        targets = [h for h in self._hidden_console_hwnds if win32gui.IsWindow(h)]
        if not targets:
            targets = _find_console_hwnds()
        for h in targets:
            win32gui.ShowWindow(h, win32con.SW_SHOW)
            win32gui.ShowWindow(h, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(h)
            except Exception:
                pass
        self._hidden_console_hwnds.clear()

    def toggle_console(self):
        vis = [h for h in _find_console_hwnds() if win32gui.IsWindowVisible(h)]
        if vis:
            self.hide_console()
        else:
            self.show_console()

    def hide_dashboard(self):
        for h in _find_dashboard_hwnds():
            if win32gui.IsWindow(h):
                win32gui.ShowWindow(h, win32con.SW_HIDE)
                if h not in self._hidden_dash_hwnds:
                    self._hidden_dash_hwnds.append(h)

    def restore_or_open_dashboard(self):
        targets = [h for h in self._hidden_dash_hwnds if win32gui.IsWindow(h)]
        if not targets:
            targets = _find_dashboard_hwnds()
        if targets:
            for h in targets:
                win32gui.ShowWindow(h, win32con.SW_SHOW)
                win32gui.ShowWindow(h, win32con.SW_RESTORE)
                try:
                    win32gui.SetForegroundWindow(h)
                except Exception:
                    pass
            self._hidden_dash_hwnds.clear()
        elif self.on_open_dashboard:
            threading.Thread(target=self.on_open_dashboard, daemon=True).start()

    def minimize_all_to_tray(self):
        self.hide_dashboard()
        self.hide_console()

    def _monitor_minimize_loop(self):
        """
        Monitoriza continuamente Dashboard + Consola (CMD / Windows 11 Terminal).
        Quando qualquer uma é minimizada, oculta-a imediatamente para o System Tray.
        """
        if self.auto_hide_console:
            time.sleep(2.2)
            self.hide_console()

        while self.running:
            try:
                # 1. Verifica Consola / Windows Terminal
                for c_hwnd in _find_console_hwnds():
                    if win32gui.IsWindowVisible(c_hwnd) and _is_window_minimized(c_hwnd):
                        win32gui.ShowWindow(c_hwnd, win32con.SW_HIDE)
                        if c_hwnd not in self._hidden_console_hwnds:
                            self._hidden_console_hwnds.append(c_hwnd)

                # 2. Verifica Dashboard (Edge --app / Browser)
                for d_hwnd in _find_dashboard_hwnds():
                    if win32gui.IsWindowVisible(d_hwnd) and _is_window_minimized(d_hwnd):
                        win32gui.ShowWindow(d_hwnd, win32con.SW_HIDE)
                        if d_hwnd not in self._hidden_dash_hwnds:
                            self._hidden_dash_hwnds.append(d_hwnd)
                        # Oculta também a consola se ainda estiver visível
                        self.hide_console()
            except Exception:
                pass
            time.sleep(0.18)

    def _run_tray_loop(self):
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "WarthogSCTrayClass"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = self._wnd_proc

        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass

        self.hwnd = win32gui.CreateWindow(
            wc.lpszClassName,
            "WarthogSCTray",
            win32con.WS_OVERLAPPED | win32con.WS_SYSMENU,
            0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0, hinst, None
        )
        win32gui.UpdateWindow(self.hwnd)

        hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "Warthog SC Commander PRO (Clique para abrir)")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        win32gui.PumpMessages()

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_USER + 20:
            if lparam in (win32con.WM_LBUTTONDBLCLK, win32con.WM_LBUTTONUP):
                self.restore_or_open_dashboard()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu()
        elif msg == win32con.WM_DESTROY:
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
            except Exception:
                pass
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = win32gui.CreatePopupMenu()
        console_vis = any(win32gui.IsWindowVisible(h) for h in _find_console_hwnds())

        win32gui.AppendMenu(menu, win32con.MF_STRING, 1001, "Abrir / Restaurar Dashboard")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1003, "Esconder Consola (CMD)" if console_vis else "Mostrar Consola (CMD)")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1004, "Minimizar Tudo para o Tray")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1002, "Sair")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        cmd = win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

        if cmd == 1001:
            self.restore_or_open_dashboard()
        elif cmd == 1003:
            self.toggle_console()
        elif cmd == 1004:
            self.minimize_all_to_tray()
        elif cmd == 1002:
            self.running = False
            try:
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
            except Exception:
                pass
            if self.on_exit:
                self.on_exit()
            else:
                os._exit(0)
