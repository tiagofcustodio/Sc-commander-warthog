"""
GUI - Star Citizen Warthog Commander
Interface gráfica moderna e intuitiva com tema escuro Star Citizen (Aegis/RSI HUD).
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time

from warthog_constants import (
    THROTTLE_BUTTONS,
    THREE_WAY_GROUPS,
    DEFAULT_SC_MAPPINGS
)
from config import load_config, save_config, DEFAULT_CONFIG
from dinput_reader import WarthogDeviceWatcher
from switch_engine import SwitchEngine
from actionmaps_fixer import (
    find_sc_live_dir,
    get_actionmaps_path,
    get_mappings_dir,
    diagnose_actionmaps,
    fix_actionmaps,
    create_backup,
    list_backups,
    restore_backup
)
from profile_generator import write_profile_to_sc

# Sci-Fi / Star Citizen Color Palette
COLOR_BG_DARK = "#0d1117"
COLOR_BG_PANEL = "#161b22"
COLOR_BG_CARD = "#21262d"
COLOR_ACCENT_CYAN = "#00d2ff"
COLOR_ACCENT_ORANGE = "#ff9900"
COLOR_ACCENT_GREEN = "#2ea043"
COLOR_ACCENT_RED = "#da3633"
COLOR_TEXT_PRIMARY = "#f0f6fc"
COLOR_TEXT_SECONDARY = "#8b949e"
COLOR_BORDER = "#30363d"

class WarthogCommanderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Star Citizen - HOTAS Warthog Commander v1.0")
        self.root.geometry("980x720")
        self.root.minsize(860, 640)
        self.root.configure(bg=COLOR_BG_DARK)

        # Carrega configurações
        self.config = load_config()

        # Componentes do motor de entrada
        self.watcher = WarthogDeviceWatcher()
        self.engine = SwitchEngine(
            self.config.get("mappings", DEFAULT_SC_MAPPINGS),
            self.config.get("pulse_hold_ms", 60)
        )

        # Liga callbacks do hardware ao motor
        self.watcher.on_button_change = self._on_hardware_button_change
        self.watcher.on_device_status_change = self._on_device_status_change
        self.engine.on_action_triggered = self._on_action_triggered

        # Dicionário de indicadores de botões da interface
        self.switch_indicators = {}

        # Configuração do estilo visual ttk
        self._setup_styles()

        # Monta interface
        self._build_header()
        self._build_notebook()
        self._build_footer()

        # Inicializa diagnóstico inicial do Star Citizen
        self._refresh_sc_diagnosis()

        # Inicia watcher em segundo plano
        self.watcher.start()

        # Trata encerramento da janela
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLOR_BG_DARK, foreground=COLOR_TEXT_PRIMARY)
        style.configure("TNotebook", background=COLOR_BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_BG_CARD, foreground=COLOR_TEXT_SECONDARY,
                        padding=[16, 8], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_BG_PANEL)],
                  foreground=[("selected", COLOR_ACCENT_CYAN)])

        style.configure("TFrame", background=COLOR_BG_PANEL)
        style.configure("Card.TFrame", background=COLOR_BG_CARD, relief="flat")

        style.configure("TLabel", background=COLOR_BG_PANEL, foreground=COLOR_TEXT_PRIMARY, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=COLOR_BG_DARK, foreground=COLOR_ACCENT_CYAN, font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background=COLOR_BG_DARK, foreground=COLOR_TEXT_SECONDARY, font=("Segoe UI", 9))

        style.configure("Action.TButton", background=COLOR_ACCENT_CYAN, foreground="#000000",
                        font=("Segoe UI", 9, "bold"), padding=[12, 6], borderwidth=0)
        style.map("Action.TButton",
                  background=[("active", "#33dcff"), ("pressed", "#00b4db")])

        style.configure("Secondary.TButton", background=COLOR_BG_CARD, foreground=COLOR_TEXT_PRIMARY,
                        font=("Segoe UI", 9), padding=[10, 5], borderwidth=1, bordercolor=COLOR_BORDER)
        style.map("Secondary.TButton",
                  background=[("active", "#30363d")])

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=COLOR_BG_DARK, padx=20, pady=12)
        header_frame.pack(fill="x")

        title_box = tk.Frame(header_frame, bg=COLOR_BG_DARK)
        title_box.pack(side="left")

        lbl_title = ttk.Label(title_box, text="⚡ WARTHOG SC COMMANDER", style="Header.TLabel")
        lbl_title.pack(anchor="w")

        lbl_sub = ttk.Label(title_box, text="Ponte Inteligente para Thrustmaster HOTAS Warthog & Star Citizen", style="SubHeader.TLabel")
        lbl_sub.pack(anchor="w")

        # Status Badges
        self.badge_box = tk.Frame(header_frame, bg=COLOR_BG_DARK)
        self.badge_box.pack(side="right")

        self.lbl_stick_status = tk.Label(self.badge_box, text="MANCHE: DESCONECTADO", bg="#2d1515", fg="#ff7b72",
                                         font=("Segoe UI", 8, "bold"), padx=8, pady=4, relief="flat")
        self.lbl_stick_status.pack(side="left", padx=4)

        self.lbl_throttle_status = tk.Label(self.badge_box, text="MANETE: DESCONECTADA", bg="#2d1515", fg="#ff7b72",
                                           font=("Segoe UI", 8, "bold"), padx=8, pady=4, relief="flat")
        self.lbl_throttle_status.pack(side="left", padx=4)

        self.lbl_sc_status = tk.Label(self.badge_box, text="SC: PROCURANDO...", bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY,
                                      font=("Segoe UI", 8, "bold"), padx=8, pady=4, relief="flat")
        self.lbl_sc_status.pack(side="left", padx=4)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Aba 1: Painel ao Vivo
        self.tab_dashboard = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_dashboard, text="  🎛️ Painel de Controlo  ")
        self._build_dashboard_tab()

        # Aba 2: Reparador de IDs
        self.tab_doctor = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_doctor, text="  🩺 Auto-Doctor (Fix IDs)  ")
        self._build_doctor_tab()

        # Aba 3: Mapeamento de Teclas
        self.tab_mappings = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_mappings, text="  ⚙️ Mapeamento de Chaves  ")
        self._build_mappings_tab()

        # Aba 4: Eixos e Slew
        self.tab_axes = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_axes, text="  🎯 Eixos & Deadzone  ")
        self._build_axes_tab()

    def _build_dashboard_tab(self):
        container = tk.Frame(self.tab_dashboard, bg=COLOR_BG_PANEL, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        # Top Control Bar
        top_bar = tk.Frame(container, bg=COLOR_BG_CARD, padx=14, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        top_bar.pack(fill="x", pady=(0, 14))

        self.engine_enabled = tk.BooleanVar(value=True)
        chk_engine = tk.Checkbutton(top_bar, text="Ativar Motor de Transições (Tradutor de Chaves em Background)",
                                    variable=self.engine_enabled, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY,
                                    selectcolor=COLOR_BG_DARK, activebackground=COLOR_BG_CARD, activeforeground=COLOR_ACCENT_CYAN,
                                    font=("Segoe UI", 10, "bold"))
        chk_engine.pack(side="left")

        btn_test_pulse = ttk.Button(top_bar, text="Disparar Teste (Landing Gear 'N')", style="Secondary.TButton",
                                    command=lambda: self.engine.handle_button_event("throttle", 20, True))
        btn_test_pulse.pack(side="right")

        # Switches Visualization Grid
        sw_frame = tk.LabelFrame(container, text=" Monitor de Interruptores Físicos da Manete ",
                                bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"),
                                padx=12, pady=12, highlightthickness=1, highlightbackground=COLOR_BORDER)
        sw_frame.pack(fill="x", pady=(0, 14))

        switches_to_show = [
            ("APU", "APU START (15)", "Flight Ready (R)"),
            ("EAC", "EAC ARM (21)", "Shields Toggle (O)"),
            ("RDR", "RDR ALTM (20)", "Landing Gear (N)"),
            ("FLAPS_UP", "FLAPS UP (22)", "Cruise Mode"),
            ("FLAPS_DN", "FLAPS DN (23)", "VTOL Mode (K)"),
            ("PINKY_FWD", "PINKY FWD (12)", "Luzes ON (L)"),
            ("PINKY_AFT", "PINKY AFT (13)", "Luzes Cabine"),
            ("BOAT_FWD", "BOAT FWD (8)", "Quantum Spool (B)"),
            ("BOAT_AFT", "BOAT AFT (9)", "Quantum Cancel"),
            ("SPDBRK", "SPDBRK EXT (7)", "Space Brake (X)"),
            ("ENG_L", "ENG L IGN (16)", "Motor Esq (I)"),
            ("ENG_R", "ENG R IGN (18)", "Armas (P)"),
            ("LDGHORN", "LDG HORN (32)", "Chamar ATC (Alt+N)")
        ]

        row, col = 0, 0
        for key_id, label_txt, action_txt in switches_to_show:
            card = tk.Frame(sw_frame, bg=COLOR_BG_CARD, padx=8, pady=6, relief="ridge", borderwidth=1)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")

            lbl_name = tk.Label(card, text=label_txt, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 8, "bold"))
            lbl_name.pack(anchor="w")

            lbl_act = tk.Label(card, text=action_txt, bg=COLOR_BG_CARD, fg=COLOR_TEXT_SECONDARY, font=("Segoe UI", 7))
            lbl_act.pack(anchor="w")

            led = tk.Label(card, text="● INATIVO", bg=COLOR_BG_CARD, fg="#555555", font=("Segoe UI", 8, "bold"))
            led.pack(anchor="e")

            self.switch_indicators[key_id] = (led, card)

            col += 1
            if col >= 4:
                col = 0
                row += 1

        for c in range(4):
            sw_frame.grid_columnconfigure(c, weight=1)

        # Real-time Activity Log
        log_frame = tk.LabelFrame(container, text=" Registo de Eventos e Teclas Injetadas ",
                                  bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"),
                                  padx=8, pady=8, highlightthickness=1, highlightbackground=COLOR_BORDER)
        log_frame.pack(fill="both", expand=True)

        self.txt_log = tk.Text(log_frame, bg=COLOR_BG_DARK, fg="#c9d1d9", font=("Consolas", 9),
                               relief="flat", height=8, wrap="word")
        self.txt_log.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=scrollbar.set)

    def _build_doctor_tab(self):
        container = tk.Frame(self.tab_doctor, bg=COLOR_BG_PANEL, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        # Path Card
        path_card = tk.Frame(container, bg=COLOR_BG_CARD, padx=12, pady=10, highlightthickness=1, highlightbackground=COLOR_BORDER)
        path_card.pack(fill="x", pady=(0, 14))

        tk.Label(path_card, text="Diretório LIVE do Star Citizen:", bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 9, "bold")).pack(anchor="w")

        p_box = tk.Frame(path_card, bg=COLOR_BG_CARD)
        p_box.pack(fill="x", pady=(4, 0))

        self.ent_sc_path = tk.Entry(p_box, bg=COLOR_BG_DARK, fg=COLOR_TEXT_PRIMARY, insertbackground="white",
                                    relief="flat", font=("Segoe UI", 9))
        self.ent_sc_path.insert(0, self.config.get("star_citizen_live_path", ""))
        self.ent_sc_path.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        btn_browse = ttk.Button(p_box, text="Procurar...", style="Secondary.TButton", command=self._browse_sc_path)
        btn_browse.pack(side="right")

        # Diagnosis Card
        self.diag_card = tk.LabelFrame(container, text=" Diagnóstico de Conflitos e Inversão de Dispositivos ",
                                       bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"),
                                       padx=14, pady=14, highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.diag_card.pack(fill="both", expand=True, pady=(0, 14))

        self.lbl_diag_status = tk.Label(self.diag_card, text="A analisar actionmaps.xml...",
                                        bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 11, "bold"),
                                        wraplength=800, justify="left")
        self.lbl_diag_status.pack(anchor="w", pady=(0, 8))

        self.lbl_diag_instances = tk.Label(self.diag_card, text="", bg=COLOR_BG_PANEL, fg=COLOR_TEXT_SECONDARY,
                                           font=("Segoe UI", 9), justify="left")
        self.lbl_diag_instances.pack(anchor="w", pady=(0, 8))

        self.txt_anomalies = tk.Text(self.diag_card, bg=COLOR_BG_DARK, fg="#ff7b72", font=("Consolas", 9),
                                     relief="flat", height=6, wrap="word")
        self.txt_anomalies.pack(fill="both", expand=True, pady=(0, 10))

        # Action Buttons
        btn_box = tk.Frame(container, bg=COLOR_BG_PANEL)
        btn_box.pack(fill="x")

        btn_fix_now = ttk.Button(btn_box, text="⚡ Corrigir Inversão de IDs & Eixos no actionmaps.xml",
                                 style="Action.TButton", command=self._apply_actionmaps_fix)
        btn_fix_now.pack(side="left", padx=(0, 8))

        btn_install_profile = ttk.Button(btn_box, text="📥 Instalar Perfil Otimizado (layout_warthog_sc_fixed.xml)",
                                         style="Secondary.TButton", command=self._install_clean_profile)
        btn_install_profile.pack(side="left", padx=(0, 8))

        btn_backup = ttk.Button(btn_box, text="💾 Criar Cópia de Segurança", style="Secondary.TButton",
                                command=self._create_manual_backup)
        btn_backup.pack(side="left", padx=(0, 8))

        btn_refresh_diag = ttk.Button(btn_box, text="🔄 Re-verificar", style="Secondary.TButton",
                                      command=self._refresh_sc_diagnosis)
        btn_refresh_diag.pack(side="right")

    def _build_mappings_tab(self):
        container = tk.Frame(self.tab_mappings, bg=COLOR_BG_PANEL, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="Configure a tecla momentânea injetada para cada transição de interruptor:",
                 bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Tabela com Treeview ou Canvas
        tree_frame = tk.Frame(container, bg=COLOR_BG_CARD, highlightthickness=1, highlightbackground=COLOR_BORDER)
        tree_frame.pack(fill="both", expand=True, pady=(0, 12))

        columns = ("id", "desc", "key", "modifiers", "hold_ms")
        self.tree_maps = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)

        self.tree_maps.heading("id", text="ID da Ação")
        self.tree_maps.heading("desc", text="Descrição / Função no Star Citizen")
        self.tree_maps.heading("key", text="Tecla Principal")
        self.tree_maps.heading("modifiers", text="Modificadores")
        self.tree_maps.heading("hold_ms", text="Duração (ms)")

        self.tree_maps.column("id", width=140)
        self.tree_maps.column("desc", width=340)
        self.tree_maps.column("key", width=120)
        self.tree_maps.column("modifiers", width=120)
        self.tree_maps.column("hold_ms", width=100)

        self.tree_maps.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_maps.yview)
        sb.pack(side="right", fill="y")
        self.tree_maps.configure(yscrollcommand=sb.set)

        self._populate_mappings_tree()

        # Botões inferiores
        btn_frame = tk.Frame(container, bg=COLOR_BG_PANEL)
        btn_frame.pack(fill="x")

        btn_reset = ttk.Button(btn_frame, text="Restaurar Predefinições de Fábrica Star Citizen",
                               style="Secondary.TButton", command=self._reset_mappings_to_default)
        btn_reset.pack(side="left")

        btn_save = ttk.Button(btn_frame, text="Salvar Mapeamentos em Ficheiro",
                              style="Action.TButton", command=self._save_mappings)
        btn_save.pack(side="right")

    def _build_axes_tab(self):
        container = tk.Frame(self.tab_axes, bg=COLOR_BG_PANEL, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        # Slew Deadzone Card
        slew_card = tk.LabelFrame(container, text=" Calibração e Anti-Drift do Microstick (Slew Control) ",
                                  bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"),
                                  padx=14, pady=14, highlightthickness=1, highlightbackground=COLOR_BORDER)
        slew_card.pack(fill="x", pady=(0, 16))

        tk.Label(slew_card, text="Zona Morta Central (Deadzone): Elimina o drift indesejado de strafe e mira em repouso.",
                 bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 8))

        slew_box = tk.Frame(slew_card, bg=COLOR_BG_PANEL)
        slew_box.pack(fill="x")

        self.slew_slider = tk.Scale(slew_box, from_=2, to=30, orient="horizontal",
                                    bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY, activebackground=COLOR_ACCENT_CYAN,
                                    highlightthickness=0, length=400)
        self.slew_slider.set(self.config.get("slew_deadzone_percent", 12))
        self.slew_slider.pack(side="left", padx=(0, 12))

        self.lbl_slew_val = tk.Label(slew_box, text=f"{self.slew_slider.get()}%", bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"))
        self.lbl_slew_val.pack(side="left")
        self.slew_slider.config(command=lambda val: self.lbl_slew_val.config(text=f"{val}%"))

        # Yaw Assist Card
        yaw_card = tk.LabelFrame(container, text=" Assistência de Leme (Yaw) para Pilotos sem Pedais ",
                                 bg=COLOR_BG_PANEL, fg=COLOR_ACCENT_CYAN, font=("Segoe UI", 10, "bold"),
                                 padx=14, pady=14, highlightthickness=1, highlightbackground=COLOR_BORDER)
        yaw_card.pack(fill="x", pady=(0, 16))

        tk.Label(yaw_card, text="O manche Warthog não possui torção (twist). Se não tens pedais de leme físicos, podes:",
                 bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY).pack(anchor="w", pady=(0, 6))

        self.var_yaw_assist = tk.BooleanVar(value=self.config.get("virtual_yaw_assist", False))
        chk_yaw = tk.Checkbutton(yaw_card, text="Ativar Assistência de Yaw no Micro-stick da Manete (Eixo X do Slew)",
                                 variable=self.var_yaw_assist, bg=COLOR_BG_PANEL, fg=COLOR_TEXT_PRIMARY,
                                 selectcolor=COLOR_BG_DARK, activebackground=COLOR_BG_PANEL, activeforeground=COLOR_ACCENT_CYAN,
                                 font=("Segoe UI", 9, "bold"))
        chk_yaw.pack(anchor="w", pady=4)

        tk.Label(yaw_card, text="Dica: No perfil otimizado XML gerado pelo programa, podes também usar o botão Pinky Lever ou alternar Roll/Yaw via tecla de atalho.",
                 bg=COLOR_BG_PANEL, fg=COLOR_TEXT_SECONDARY, font=("Segoe UI", 8, "italic")).pack(anchor="w", pady=(6, 0))

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COLOR_BG_DARK, padx=20, pady=8)
        footer.pack(fill="x", side="bottom")

        lbl_info = tk.Label(footer, text="Star Citizen HOTAS Warthog Bridge • Compatível com SC 3.23 / 4.0 • Zero Drivers Externos",
                            bg=COLOR_BG_DARK, fg=COLOR_TEXT_SECONDARY, font=("Segoe UI", 8))
        lbl_info.pack(side="left")

        lbl_state = tk.Label(footer, text="Status: Pronto", bg=COLOR_BG_DARK, fg=COLOR_ACCENT_GREEN, font=("Segoe UI", 8, "bold"))
        lbl_state.pack(side="right")
        self.lbl_footer_state = lbl_state

    # ================= EVENTOS E ATUALIZAÇÕES =================

    def log_event(self, text: str):
        """Adiciona uma mensagem à consola da interface de forma thread-safe."""
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {text}\n"

        def _append():
            self.txt_log.insert(tk.END, formatted)
            self.txt_log.see(tk.END)

        self.root.after(0, _append)

    def _on_hardware_button_change(self, device: str, button: int, is_down: bool):
        """Chamado pelo leitor quando qualquer botão físico muda de estado."""
        # Se o motor de transições estiver ativado, processa o switch
        if self.engine_enabled.get():
            self.engine.handle_button_event(device, button, is_down)

        # Atualiza o visual dos LEDs na interface
        def _update_ui():
            led_key = None
            if button == 15: led_key = "APU"
            elif button == 20: led_key = "RDR"
            elif button == 21: led_key = "EAC"
            elif button == 22: led_key = "FLAPS_UP"
            elif button == 23: led_key = "FLAPS_DN"
            elif button == 12: led_key = "PINKY_FWD"
            elif button == 13: led_key = "PINKY_AFT"
            elif button == 8: led_key = "BOAT_FWD"
            elif button == 9: led_key = "BOAT_AFT"
            elif button == 7: led_key = "SPDBRK"
            elif button in (16, 17): led_key = "ENG_L"
            elif button in (18, 19): led_key = "ENG_R"
            elif button == 32: led_key = "LDGHORN"

            if led_key and led_key in self.switch_indicators:
                led_lbl, card = self.switch_indicators[led_key]
                if is_down:
                    led_lbl.config(text="● LIGADO", fg=COLOR_ACCENT_GREEN)
                    card.config(highlightthickness=1, highlightbackground=COLOR_ACCENT_GREEN)
                else:
                    led_lbl.config(text="● DESLIGADO", fg=COLOR_TEXT_SECONDARY)
                    card.config(highlightthickness=0)

        self.root.after(0, _update_ui)

    def _on_action_triggered(self, action_id: str, key_combo: str, desc: str):
        """Chamado quando uma tecla física é disparada para o Star Citizen."""
        msg = f"Interruptor '{action_id}' -> Disparou Tecla '{key_combo}' [{desc}]"
        self.log_event(msg)

    def _on_device_status_change(self, stick_conn: bool, throttle_conn: bool):
        """Atualiza os badges de conexão de hardware no cabeçalho."""
        def _update():
            if stick_conn:
                self.lbl_stick_status.config(text="MANCHE: LIGADO", bg="#1b4725", fg="#7ee787")
            else:
                self.lbl_stick_status.config(text="MANCHE: DESCONECTADO", bg="#2d1515", fg="#ff7b72")

            if throttle_conn:
                self.lbl_throttle_status.config(text="MANETE: LIGADA", bg="#1b4725", fg="#7ee787")
            else:
                self.lbl_throttle_status.config(text="MANETE: DESCONECTADA", bg="#2d1515", fg="#ff7b72")

        self.root.after(0, _update)

    def _refresh_sc_diagnosis(self):
        """Atualiza a caixa de diagnóstico do Star Citizen."""
        sc_dir = self.ent_sc_path.get().strip()
        sc_live = find_sc_live_dir(sc_dir)

        if not sc_live:
            self.lbl_sc_status.config(text="SC: NÃO ENCONTRADO", bg="#2d1515", fg="#ff7b72")
            self.lbl_diag_status.config(text="❌ Pasta LIVE do Star Citizen não encontrada.", fg=COLOR_ACCENT_RED)
            self.lbl_diag_instances.config(text="")
            self.txt_anomalies.delete("1.0", tk.END)
            self.txt_anomalies.insert(tk.END, "Por favor selecione o diretório onde o Star Citizen está instalado (ex: C:\\Program Files\\Roberts Space Industries\\StarCitizen\\LIVE).")
            return

        self.lbl_sc_status.config(text="SC: DETETADO (LIVE)", bg="#1b4725", fg="#7ee787")
        xml_path = get_actionmaps_path(sc_live)
        report = diagnose_actionmaps(xml_path)

        # Monta sumário de instâncias
        inst_lines = []
        for inst_num, info in sorted(report["instances"].items()):
            label = "Manche Warthog" if info["is_stick"] else ("Manete Warthog" if info["is_throttle"] else "Outro")
            inst_lines.append(f"• Dispositivo js{inst_num}: {info['product']} [{label}]")
        self.lbl_diag_instances.config(text="\n".join(inst_lines))

        # Sumário de saúde
        if report["healthy"]:
            self.lbl_diag_status.config(text="✅ " + report["summary"], fg=COLOR_ACCENT_GREEN)
            self.txt_anomalies.delete("1.0", tk.END)
            self.txt_anomalies.insert(tk.END, "Nenhum problema detetado! Os eixos e dispositivos estão perfeitamente sincronizados.")
        else:
            self.lbl_diag_status.config(text=report["summary"], fg=COLOR_ACCENT_ORANGE)
            self.txt_anomalies.delete("1.0", tk.END)
            for a in report["anomalies"]:
                self.txt_anomalies.insert(tk.END, f"• {a}\n")

    def _apply_actionmaps_fix(self):
        """Executa a reparação do actionmaps.xml."""
        sc_dir = self.ent_sc_path.get().strip()
        sc_live = find_sc_live_dir(sc_dir)
        if not sc_live:
            messagebox.showerror("Erro", "Diretório do Star Citizen não encontrado.")
            return

        xml_path = get_actionmaps_path(sc_live)
        success, msg = fix_actionmaps(xml_path, fix_roll_pitch=True)
        if success:
            messagebox.showinfo("Sucesso", f"Correção aplicada com sucesso!\n\n{msg}")
            self.log_event("actionmaps.xml corrigido: Inversões e eixos normalizados.")
            self._refresh_sc_diagnosis()
        else:
            messagebox.showerror("Erro", f"Falha ao corrigir actionmaps: {msg}")

    def _install_clean_profile(self):
        """Escreve o perfil otimizado na pasta mappings."""
        sc_dir = self.ent_sc_path.get().strip()
        sc_live = find_sc_live_dir(sc_dir)
        if not sc_live:
            messagebox.showerror("Erro", "Diretório do Star Citizen não encontrado.")
            return

        mappings_dir = get_mappings_dir(sc_live)
        success, msg = write_profile_to_sc(mappings_dir)
        if success:
            messagebox.showinfo("Sucesso", f"Perfil instalado!\n\nPara carregar no jogo, usa o menu Opções > Keybindings > Import Profile > layout_warthog_sc_fixed\nou abre a consola do SC com '~' e escreve:\npp_rebindkeys layout_warthog_sc_fixed")
            self.log_event("Perfil layout_warthog_sc_fixed.xml copiado para a pasta mappings do Star Citizen.")
        else:
            messagebox.showerror("Erro", msg)

    def _create_manual_backup(self):
        """Cria um backup manual."""
        sc_dir = self.ent_sc_path.get().strip()
        sc_live = find_sc_live_dir(sc_dir)
        if not sc_live:
            return
        xml_path = get_actionmaps_path(sc_live)
        b_path = create_backup(xml_path)
        if b_path:
            messagebox.showinfo("Backup Criado", f"Cópia de segurança criada:\n{os.path.basename(b_path)}")
            self.log_event(f"Backup manual criado: {os.path.basename(b_path)}")

    def _browse_sc_path(self):
        folder = filedialog.askdirectory(title="Selecione a pasta LIVE do Star Citizen")
        if folder:
            self.ent_sc_path.delete(0, tk.END)
            self.ent_sc_path.insert(0, folder)
            self.config["star_citizen_live_path"] = folder
            save_config(self.config)
            self._refresh_sc_diagnosis()

    def _populate_mappings_tree(self):
        self.tree_maps.delete(*self.tree_maps.get_children())
        mappings = self.config.get("mappings", DEFAULT_SC_MAPPINGS)
        for action_id, data in mappings.items():
            mods = "+".join(data.get("modifiers", []))
            self.tree_maps.insert("", "end", values=(
                action_id,
                data.get("desc", ""),
                data.get("key", ""),
                mods,
                data.get("hold_ms", 60)
            ))

    def _reset_mappings_to_default(self):
        if messagebox.askyesno("Confirmar", "Deseja restaurar as configurações padrão de fábrica para todos os interruptores?"):
            self.config["mappings"] = DEFAULT_SC_MAPPINGS.copy()
            save_config(self.config)
            self.engine.update_mappings(self.config["mappings"], self.config.get("pulse_hold_ms", 60))
            self._populate_mappings_tree()
            self.log_event("Mapeamentos restaurados para o padrão de fábrica.")

    def _save_mappings(self):
        self.config["slew_deadzone_percent"] = self.slew_slider.get()
        self.config["virtual_yaw_assist"] = self.var_yaw_assist.get()
        self.config["star_citizen_live_path"] = self.ent_sc_path.get().strip()
        save_config(self.config)
        self.engine.update_mappings(self.config["mappings"], self.config.get("pulse_hold_ms", 60))
        messagebox.showinfo("Configurações Salvas", "Configurações gravadas com sucesso em config.json!")
        self.log_event("Configurações atualizadas e salvas em disco.")

    def _on_close(self):
        self.watcher.stop()
        self.root.destroy()

def run_gui():
    root = tk.Tk()
    app = WarthogCommanderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
