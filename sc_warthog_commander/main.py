"""
Main Entry Point - Star Citizen Warthog Commander
Suporta modo gráfico interativo (GUI) e modo CLI / Daemon para automações.
"""

import os
import sys
import argparse

# Configura saída UTF-8 segura no Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from actionmaps_fixer import (
    find_sc_live_dir,
    get_actionmaps_path,
    get_mappings_dir,
    diagnose_actionmaps,
    fix_actionmaps
)
from profile_generator import write_profile_to_sc
from config import load_config
from dinput_reader import WarthogDeviceWatcher
from switch_engine import SwitchEngine
import time

def parse_args():
    parser = argparse.ArgumentParser(
        description="Star Citizen Warthog Commander - Elimina problemas de inversão de IDs e interruptores contínuos."
    )
    parser.add_argument("--legacy-gui", action="store_true", help="Inicia a interface clássica Tkinter")
    parser.add_argument("--diagnose", action="store_true", help="Executa diagnóstico rápido do Star Citizen na consola")
    parser.add_argument("--fix-ids", action="store_true", help="Corrige a inversão de IDs e eixos no actionmaps.xml")
    parser.add_argument("--install-profile", action="store_true", help="Instala layout_warthog_sc_fixed.xml na pasta mappings do SC")
    parser.add_argument("--generate-3d", action="store_true", help="Gera o diagrama Ultra-HD e os modelos 3D (.STL / .SVG) da Manete Dupla")
    parser.add_argument("--daemon", action="store_true", help="Executa o motor de tradução de interruptores em modo serviço (headless)")
    return parser.parse_args()

def main():
    args = parse_args()
    config = load_config()
    sc_live = find_sc_live_dir(config.get("star_citizen_live_path"))

    if args.diagnose:
        print("\n================ DIAGNÓSTICO STAR CITIZEN ================")
        if not sc_live:
            print("❌ Pasta LIVE do Star Citizen não foi encontrada.")
            sys.exit(1)
        xml_path = get_actionmaps_path(sc_live)
        print(f"Diretório LIVE: {sc_live}")
        print(f"ActionMaps: {xml_path}")
        report = diagnose_actionmaps(xml_path)
        print(f"Status: {report['summary']}")
        for inst, inf in report["instances"].items():
            print(f"  • Dispositivo js{inst}: {inf['product']}")
        if report["anomalies"]:
            print("\nAnomalias Encontradas:")
            for a in report["anomalies"]:
                print(f"  - {a}")
        print("==========================================================\n")
        sys.exit(0)

    if args.fix_ids:
        print("\n[ActionMaps Fixer] A verificar e corrigir actionmaps.xml...")
        if not sc_live:
            print("❌ Pasta LIVE do Star Citizen não encontrada.")
            sys.exit(1)
        xml_path = get_actionmaps_path(sc_live)
        success, msg = fix_actionmaps(xml_path, fix_roll_pitch=True)
        print(f"Resultado: {msg}")
        sys.exit(0 if success else 1)

    if args.install_profile:
        print("\n[Profile Generator] A instalar perfil otimizado...")
        if not sc_live:
            print("❌ Pasta LIVE do Star Citizen não encontrada.")
            sys.exit(1)
        mappings_dir = get_mappings_dir(sc_live)
        success, msg = write_profile_to_sc(mappings_dir)
        print(f"Resultado: {msg}")
        sys.exit(0 if success else 1)

    if args.generate_3d:
        from pathlib import Path
        from print3d_generator import generate_all_warthog_3d_and_diagrams
        out_dir = Path(__file__).resolve().parent / "profiles"
        res = generate_all_warthog_3d_and_diagrams(out_dir)
        print("\n[3D & Diagram Generator] Ficheiros gerados com sucesso:")
        for k, v in res.items():
            print(f"  • {k}: {v}")
        sys.exit(0)

    if args.daemon:
        print("\n[Warthog Commander] A iniciar daemon de interruptores em segundo plano...")
        watcher = WarthogDeviceWatcher()
        engine = SwitchEngine(config.get("mappings", {}), config.get("pulse_hold_ms", 60))
        watcher.on_button_change = engine.handle_button_event
        engine.on_action_triggered = lambda act, key, desc: print(f"[{time.strftime('%X')}] {act} -> {key} ({desc})")
        watcher.start()
        print("Motor ativo! Pressione Ctrl+C para encerrar.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("Encerrado com sucesso.")
        sys.exit(0)

    # Interface Clássica Tkinter se solicitada
    if args.legacy_gui:
        from gui import run_gui
        run_gui()
        sys.exit(0)

    # Por padrão, abre o novo Dashboard Glassmorphism Star Citizen
    from web_app import run_glassmorphism_app
    run_glassmorphism_app()

if __name__ == "__main__":
    main()
