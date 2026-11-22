"""
Windows System Tray Service for Warthog Commander
Cria um ícone discreto no tabuleiro do sistema (junto ao relógio do Windows) com menu de contexto rápido.
"""

import os
import sys
import threading
import win32api
import win32con
import win32gui
from typing import Callable, Optional

class WarthogTrayIcon:
    def __init__(self, on_open_dashboard: Optional[Callable] = None, on_exit: Optional[Callable] = None):
        self.on_open_dashboard = on_open_dashboard
        self.on_exit = on_exit
        self.hwnd = None
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run_tray_loop, daemon=True)
        self._thread.start()

    def _run_tray_loop(self):
        msg_taskbar = win32gui.RegisterWindowMessage("TaskbarCreated")
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "WarthogSCTrayClass"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = self._wnd_proc

        try:
            class_atom = win32gui.RegisterClass(wc)
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

        # Usa ícone padrão de jogo/joystick do sistema
        hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "Star Citizen - Warthog Commander Pro")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        win32gui.PumpMessages()

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_USER + 20:
            if lparam == win32con.WM_LBUTTONDBLCLK:
                if self.on_open_dashboard:
                    self.on_open_dashboard()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu()
        elif msg == win32con.WM_DESTROY:
            nid = (self.hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1001, "Abrir Dashboard (Web HUD)")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1002, "Sair")

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        cmd = win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN | win32con.TPM_RETURNCMD, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

        if cmd == 1001:
            if self.on_open_dashboard:
                self.on_open_dashboard()
        elif cmd == 1002:
            if self.on_exit:
                self.on_exit()
            else:
                os._exit(0)
