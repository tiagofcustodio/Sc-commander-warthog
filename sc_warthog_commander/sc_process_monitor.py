"""
Star Citizen Process Monitor & Auto-Sync
Monitoriza em segundo plano a execução de 'StarCitizen.exe'.
Quando o jogo arranca, sincroniza automaticamente o perfil e os IDs de hardware.
"""

import time
import threading
from typing import Callable, Optional
import psutil

SC_PROCESS_NAMES = ["StarCitizen.exe", "StarCitizen_Launcher.exe"]

class StarCitizenProcessMonitor:
    def __init__(self):
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._active = False
        self.on_state_change: Optional[Callable[[bool], None]] = None # (is_running)

    def start(self):
        if self._active:
            return
        self._active = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False

    def _loop(self):
        last_state = False
        while self._active:
            found = False
            for p in psutil.process_iter(['name']):
                try:
                    if p.info['name'] in SC_PROCESS_NAMES:
                        found = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if found != last_state:
                last_state = found
                self.is_running = found
                if self.on_state_change:
                    self.on_state_change(found)

            time.sleep(2.0)
