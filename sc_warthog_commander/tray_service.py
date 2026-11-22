"""
Windows System Tray Service for Warthog Commander
Cria um ícone discreto no tabuleiro do sistema (junto ao relógio do Windows).
Quando o utilizador minimiza a janela do Dashboard ou a Consola (linha de comandos),
ambas são ocultadas automaticamente da barra de tarefas e enviadas para o System Tray.
"""

import os
import time
import ctypes
import threading
import win32api
import win32con
import win32gui
from typing import Callable, Optional


def _get_console_hwnd() -> int:
    try:
        return int(ctypes.windll.kernel32.GetConsoleWindow() or 0)
    except Exception:
        return 0


def _find_dashboard_hwnd() -> int:
    """Encontra o HWND da janela do Dashboard (Edge --app ou browser com título Warthog SC Commander)."""
    found = [0]

    def _enum_cb(hwnd, _):
        if found[0]:
            return True
        try:
            title = win32gui.GetWindowText(hwnd) or ""
            if "Warthog SC Commander" in title or "Warthog Commander" in title:
                cls = win32gui.GetClassName(hwnd) or ""
                # Ignora a janela oculta do próprio tray e a janela de consola
                if cls != "WarthogSCTrayClass" and hwnd != _get_console_hwnd():
                    found[0] = hwnd
                    return False
        except Exception:
            pass
        return True

    try:
        win32gui.EnumWindows(_enum_cb, None)
    except Exception:
        pass
    return found[0]


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
        self._hidden_dash_hwnd = 0
        self._console_hidden = False

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run_tray_loop, daemon=True)
        self._thread.start()
        self._monitor_thread = threading.Thread(target=self._monitor_minimize_loop, daemon=True)
        self._monitor_thread.start()

    def hide_console(self):
        c_hwnd = _get_console_hwnd()
        if c_hwnd and win32gui.IsWindow(c_hwnd):
            win32gui.ShowWindow(c_hwnd, win32con.SW_HIDE)
            self._console_hidden = True

    def show_console(self):
        c_hwnd = _get_console_hwnd()
        if c_hwnd and win32gui.IsWindow(c_hwnd):
            win32gui.ShowWindow(c_hwnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(c_hwnd)
            except Exception:
                pass
            self._console_hidden = False

    def toggle_console(self):
        c_hwnd = _get_console_hwnd()
        if not c_hwnd:
            return
        if win32gui.IsWindowVisible(c_hwnd):
            self.hide_console()
        else:
            self.show_console()

    def hide_dashboard(self):
        d_hwnd = self._hidden_dash_hwnd if (self._hidden_dash_hwnd and win32gui.IsWindow(self._hidden_dash_hwnd)) else _find_dashboard_hwnd()
        if d_hwnd and win32gui.IsWindow(d_hwnd):
            self._hidden_dash_hwnd = d_hwnd
            win32gui.ShowWindow(d_hwnd, win32con.SW_HIDE)

    def restore_or_open_dashboard(self):
        d_hwnd = self._hidden_dash_hwnd if (self._hidden_dash_hwnd and win32gui.IsWindow(self._hidden_dash_hwnd)) else _find_dashboard_hwnd()
        if d_hwnd and win32gui.IsWindow(d_hwnd):
            win32gui.ShowWindow(d_hwnd, win32con.SW_RESTORE)
            win32gui.ShowWindow(d_hwnd, win32con.SW_SHOW)
            try:
                win32gui.SetForegroundWindow(d_hwnd)
            except Exception:
                pass
            self._hidden_dash_hwnd = d_hwnd
        elif self.on_open_dashboard:
            threading.Thread(target=self.on_open_dashboard, daemon=True).start()

    def minimize_all_to_tray(self):
        self.hide_dashboard()
        self.hide_console()

    def _monitor_minimize_loop(self):
        """
        Monitoriza continuamente a janela do Dashboard e a janela da Consola (CMD):
        assim que qualquer uma for minimizada, oculta-a da barra de tarefas para o System Tray.
        """
        # Opcionalmente oculta a consola automaticamente após o arranque estar concluído
        if self.auto_hide_console:
            time.sleep(2.5)
            self.hide_console()

        while self.running:
            try:
                # 1. Monitoriza Consola (linha de comandos)
                c_hwnd = _get_console_hwnd()
                if c_hwnd and win32gui.IsWindowVisible(c_hwnd) and win32gui.IsIconic(c_hwnd):
                    win32gui.ShowWindow(c_hwnd, win32con.SW_HIDE)
                    self._console_hidden = True

                # 2. Monitoriza Dashboard (Edge --app / Browser)
                d_hwnd = self._hidden_dash_hwnd if (self._hidden_dash_hwnd and win32gui.IsWindow(self._hidden_dash_hwnd)) else _find_dashboard_hwnd()
                if d_hwnd and win32gui.IsWindow(d_hwnd):
                    self._hidden_dash_hwnd = d_hwnd
                    if win32gui.IsWindowVisible(d_hwnd) and win32gui.IsIconic(d_hwnd):
                        win32gui.ShowWindow(d_hwnd, win32con.SW_HIDE)
                        # Garante que a consola também vai para o tray
                        if c_hwnd and win32gui.IsWindowVisible(c_hwnd):
                            win32gui.ShowWindow(c_hwnd, win32con.SW_HIDE)
                            self._console_hidden = True
            except Exception:
                pass
            time.sleep(0.20)

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
        c_hwnd = _get_console_hwnd()
        console_vis = bool(c_hwnd and win32gui.IsWindowVisible(c_hwnd))

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
