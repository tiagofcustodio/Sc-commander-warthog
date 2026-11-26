"""
ActionMaps Fixer & Star Citizen Thruster / Device Doctor
Deteta, diagnostica e repara automaticamente:
1. Inversão de IDs (js1 vs js2) entre Manche (0402) e Manete (0404).
2. Bloqueio dos Thrusters causado por v_ifcs_speed_limiter_rel no eixo js2_rotz (Manete Direita).
3. Curvas exponenciais extremas na manete (ex: exponent="2.9000001") e falta de inversão (invert="1").
4. Falta de v_pitch (js1_y), v_throttle_abs (js2_rotz), v_speed_range_abs (js2_slider1) e spaceship_weapons.
5. Bloqueio de botões de Cutoff (js2_button29 / js2_button30).
"""

import os
import shutil
import time
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from warthog_constants import (
    WARTHOG_JOYSTICK_GUID_SUBSTR,
    WARTHOG_THROTTLE_GUID_SUBSTR
)

STANDARD_SC_PATHS = [
    r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE",
    r"D:\Roberts Space Industries\StarCitizen\LIVE",
    r"E:\Roberts Space Industries\StarCitizen\LIVE",
    r"C:\Roberts Space Industries\StarCitizen\LIVE"
]


def find_sc_live_dir(custom_path: Optional[str] = None) -> Optional[str]:
    """Localiza o diretório LIVE do Star Citizen."""
    candidates = []
    if custom_path:
        candidates.append(custom_path)
    candidates.extend(STANDARD_SC_PATHS)

    for p in candidates:
        if os.path.exists(p) and os.path.isdir(p):
            if os.path.exists(os.path.join(p, "user")) or os.path.exists(os.path.join(p, "StarCitizen.exe")):
                return p
    return None


def get_actionmaps_path(sc_live_dir: str) -> str:
    """Retorna o caminho do actionmaps.xml ativo do Star Citizen."""
    return os.path.join(sc_live_dir, "user", "client", "0", "Profiles", "default", "actionmaps.xml")


def get_mappings_dir(sc_live_dir: str) -> str:
    """Retorna o caminho da pasta controls/mappings."""
    return os.path.join(sc_live_dir, "user", "client", "0", "controls", "mappings")


def _classify_sc_joystick_product(prod: str) -> tuple[bool, bool, str]:
    """Classifica o atributo Product do Star Citizen (is_stick, is_throttle, kit_id)."""
    p = (prod or "").strip()
    pl = p.lower()
    pu = p.upper()

    # Thrustmaster HOTAS Warthog
    if (WARTHOG_JOYSTICK_GUID_SUBSTR in pu) or ("joystick" in pl and "warthog" in pl):
        return True, False, "warthog"
    if (WARTHOG_THROTTLE_GUID_SUBSTR in pu) or ("throttle" in pl and "warthog" in pl):
        return False, True, "warthog"

    # Logitech G / Saitek X56 & X55 Rhino
    if any(g in pu for g in ("22210738", "222106A3", "C221046D", "2221046D", "22150738")) or (
        any(k in pl for k in ("x56", "x-56", "x55", "x-55", "rhino")) and "throttle" not in pl
    ):
        return True, False, "saitek_x56"
    if any(g in pu for g in ("A2210738", "A22106A3", "A221046D", "A2150738")) or (
        any(k in pl for k in ("x56", "x-56", "x55", "x-55", "rhino")) and "throttle" in pl
    ):
        return False, True, "saitek_x56"

    # Thrustmaster T.16000M / TWCS / TCA / T.Flight
    if "B10A044F" in pu or "t.16000" in pl or "t16000" in pl:
        return True, False, "tm_t16000m"
    if "B687044F" in pu or "twcs" in pl:
        return False, True, "tm_t16000m"
    if "tca" in pl and "quadrant" in pl:
        return False, True, "tm_tca"
    if "tca" in pl or "t.flight" in pl or "t-flight" in pl:
        return True, False, "tm_tca" if "tca" in pl else "tm_tflight"

    # Genérico por nome
    if "throttle" in pl:
        return False, True, "generic"
    if "stick" in pl or "joystick" in pl:
        return True, False, "generic"
    return False, False, "unknown"


def diagnose_actionmaps(xml_path: str) -> dict:
    """
    Analisa profundamente o actionmaps.xml do Star Citizen e deteta todas as causas
    pelas quais os Thrusters (propulsores), a Manete ou o Manche falham no jogo.
    """
    report = {
        "exists": False,
        "path": xml_path,
        "instances": {},
        "is_swapped": False,
        "anomalies": [],
        "healthy": False,
        "summary": ""
    }

    if not os.path.exists(xml_path):
        report["summary"] = f"Ficheiro não encontrado: {xml_path}"
        return report

    report["exists"] = True

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # 1. Analisa opções de joystick
        stick_inst = None
        throttle_inst = None

        for opt in root.findall(".//options[@type='joystick']"):
            inst = opt.get("instance")
            prod = opt.get("Product", "") or ""
            is_stick, is_throttle, dev_kit = _classify_sc_joystick_product(prod)

            report["instances"][inst] = {
                "product": prod,
                "is_stick": is_stick,
                "is_throttle": is_throttle,
                "kit": dev_kit
            }

            if is_stick and stick_inst is None:
                stick_inst = inst
            elif is_throttle and throttle_inst is None:
                throttle_inst = inst
                # Verifica expoente excessivo nos thrusters
                strafe_lon = opt.find("flight_strafe_longitudinal")
                if strafe_lon is not None:
                    exp_str = strafe_lon.get("exponent", "1.0")
                    try:
                        if float(exp_str) > 1.5:
                            report["anomalies"].append(
                                f"THRUSTERS: Expoente demasiado alto ({exp_str}) em flight_strafe_longitudinal na Manete (cria zona morta gigante nos propulsores)."
                            )
                    except ValueError:
                        pass
                    if strafe_lon.get("invert") != "1":
                        report["anomalies"].append(
                            "THRUSTERS: Falta invert='1' em flight_strafe_longitudinal na Manete (eixo Z invertido)."
                        )

        # 2. Avalia alinhamento de instâncias
        if stick_inst == "2" and throttle_inst == "1":
            report["is_swapped"] = True
            report["anomalies"].append("CRÍTICO: O Star Citizen trocou a Manete (js1) com o Manche (js2).")
        elif not stick_inst and not throttle_inst:
            report["anomalies"].append("AVISO: Nenhum joystick HOTAS reconhecido no cabeçalho de opções do Star Citizen.")

        # 3. Analisa conflitos de Thrusters e Eixos em spaceship_movement
        mov_map = root.find(".//actionmap[@name='spaceship_movement']")
        has_pitch = False
        has_roll = False
        has_thruster_axis = False

        if mov_map is not None:
            for action in mov_map.findall("action"):
                name = action.get("name", "")
                for rebind in action.findall("rebind"):
                    inp = (rebind.get("input", "") or "").strip()

                    if name == "v_pitch" and inp == "js1_y":
                        has_pitch = True
                    if name == "v_roll" and inp == "js1_x":
                        has_roll = True
                    if name in ("v_strafe_longitudinal", "v_throttle_abs") and inp in ("js2_z", "js2_rotz"):
                        has_thruster_axis = True

                    # BUG CRÍTICO DOS THRUSTERS: js2_rotz ligado a v_ifcs_speed_limiter_rel!
                    if name == "v_ifcs_speed_limiter_rel" and inp in ("js2_rotz", "js2_z"):
                        report["anomalies"].append(
                            f"BLOQUEIO DE THRUSTERS CRÍTICO: A alavanca principal da Manete ('{inp}') está ligada a 'v_ifcs_speed_limiter_rel' (Limitador Relativo), bloqueando a velocidade da nave em 0 m/s!"
                        )

                    if name == "v_roll" and inp.startswith("js2_"):
                        report["anomalies"].append(f"CONFLITO DE EIXO: v_roll está na Manete ('{inp}') em vez do Manche ('js1_x').")
                    if name == "v_pitch" and inp.startswith("js2_"):
                        report["anomalies"].append(f"CONFLITO DE EIXO: v_pitch está na Manete ('{inp}') em vez do Manche ('js1_y').")

        if not has_pitch:
            report["anomalies"].append("FALTA EIXO PRIMÁRIO: 'v_pitch' (Arfagem) não está mapeado para 'js1_y' (Manche) em spaceship_movement.")
        if not has_roll:
            report["anomalies"].append("FALTA EIXO PRIMÁRIO: 'v_roll' (Rolamento) não está mapeado para 'js1_x' (Manche).")
        if not has_thruster_axis:
            report["anomalies"].append("FALTA PROPULSÃO: Nenhum eixo de manete ('js2_z' / 'js2_rotz') ligado aos propulsores.")

        # 4. Verifica se spaceship_weapons existe
        wpn_map = root.find(".//actionmap[@name='spaceship_weapons']")
        if wpn_map is None:
            report["anomalies"].append("FALTA ARMAMENTO: Secção 'spaceship_weapons' ausente (Gatilhos Etapa 1 e 2 não mapeados).")

        # 5. Verifica se botões 29 ou 30 (Idle Cutoff) foram gravados por acidente
        for rebind in root.findall(".//rebind"):
            inp = (rebind.get("input", "") or "").strip()
            if inp in ("js2_button29", "js2_button30"):
                report["anomalies"].append(
                    f"BLOQUEIO IDLE CUTOFF: O detentor físico '{inp}' está mapeado diretamente no XML, o que bloqueia comandos quando a manete está em OFF."
                )

        if not report["is_swapped"] and not report["anomalies"]:
            report["healthy"] = True
            report["summary"] = "✅ Perfil 100% saudável! Thrusters, Manche (19B) e Manete (32B) sincronizados sem conflitos."
        else:
            report["healthy"] = False
            report["summary"] = f"⚠️ Detetados {len(report['anomalies'])} problemas que afetam os Thrusters / Controlos no Star Citizen."

    except Exception as e:
        report["summary"] = f"Erro ao analisar XML: {e}"

    return report


def create_backup(xml_path: str) -> Optional[str]:
    """Cria uma cópia de segurança com carimbo temporal antes de qualquer modificação."""
    if not os.path.exists(xml_path):
        return None
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{xml_path}.bak_{timestamp}"
    try:
        shutil.copy2(xml_path, backup_path)
        return backup_path
    except PermissionError:
        from config import get_app_dir
        local_profiles_dir = os.path.join(get_app_dir(), "profiles")
        os.makedirs(local_profiles_dir, exist_ok=True)
        local_backup = os.path.join(local_profiles_dir, f"actionmaps.xml.bak_{timestamp}")
        shutil.copy2(xml_path, local_backup)
        return local_backup
    except Exception as e:
        print(f"[ActionMapsFixer] Erro ao criar backup: {e}")
        return None


def _set_action_rebind(actionmap_elem: ET.Element, action_name: str, input_val: str):
    """Cria ou atualiza uma ação dentro de um <actionmap>."""
    act = actionmap_elem.find(f"action[@name='{action_name}']")
    if act is None:
        act = ET.SubElement(actionmap_elem, "action", {"name": action_name})
    reb = act.find("rebind")
    if reb is None:
        reb = ET.SubElement(act, "rebind", {"input": input_val})
    else:
        reb.set("input", input_val)


def _get_or_create_actionmap(profile_elem: ET.Element, map_name: str) -> ET.Element:
    """Obtém ou cria um bloco <actionmap name='...'>."""
    am = profile_elem.find(f"actionmap[@name='{map_name}']")
    if am is None:
        am = ET.SubElement(profile_elem, "actionmap", {"name": map_name})
    return am


def fix_actionmaps(xml_path: str, fix_roll_pitch: bool = True) -> Tuple[bool, str]:
    """
    Repara completamente o actionmaps.xml do Star Citizen:
    1. Garante js1 = Manche (0402) e js2 = Manete (0404).
    2. Elimina o conflito de js2_rotz em v_ifcs_speed_limiter_rel que impedia os thrusters de acelerar.
    3. Configura os propulsores (v_strafe_longitudinal em js2_z e v_throttle_abs em js2_rotz) com invert='1' e exponent='1.0'.
    4. Configura o Limitador de Velocidade absoluto (v_speed_range_abs) na Roda Cinzenta Central (js2_slider1).
    5. Injeta o mapeamento completo de todas as teclas, hats e eixos do Manche e da Manete.
    """
    if not os.path.exists(xml_path):
        return False, f"Ficheiro não existe: {xml_path}"

    backup_file = create_backup(xml_path)
    if not backup_file:
        return False, (
            "Permissão de Administrador necessária para modificar o ficheiro do Star Citizen em 'C:\\Program Files\\...'.\n"
            "Execute o 'run.bat' (que agora solicita elevação UAC automaticamente) ou clique com o botão direito > 'Executar como Administrador'."
        )

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        profile = root.find("ActionProfiles")
        if profile is None:
            profile = root

        # 1. Corrige <options type="joystick"> para Manche (instance 1) e Manete (instance 2)
        opt_stick = None
        opt_throttle = None
        detected_xml_kit = "warthog"
        for opt in profile.findall("options[@type='joystick']"):
            prod = opt.get("Product", "") or ""
            is_stick, is_throttle, dev_kit = _classify_sc_joystick_product(prod)
            if is_stick and opt_stick is None:
                opt_stick = opt
                if dev_kit not in ("unknown", "generic"):
                    detected_xml_kit = dev_kit
            elif is_throttle and opt_throttle is None:
                opt_throttle = opt
                if dev_kit not in ("unknown", "generic"):
                    detected_xml_kit = dev_kit

        is_x56 = (detected_xml_kit == "saitek_x56")

        if opt_stick is not None:
            opt_stick.set("instance", "1")

        if opt_throttle is not None:
            opt_throttle.set("instance", "2")
            # Corrige opções de inversão e expoente dos Thrusters na Manete
            strafe_lon = opt_throttle.find("flight_strafe_longitudinal")
            if strafe_lon is None:
                strafe_lon = ET.SubElement(opt_throttle, "flight_strafe_longitudinal")
            strafe_lon.set("invert", "1")
            strafe_lon.set("exponent", "1.0")

            thr_abs = opt_throttle.find("flight_throttle_abs")
            if thr_abs is None:
                thr_abs = ET.SubElement(opt_throttle, "flight_throttle_abs")
            thr_abs.set("invert", "1")
            thr_abs.set("exponent", "1.0")

            spd_abs = opt_throttle.find("flight_move_speed_range_abs")
            if spd_abs is None:
                spd_abs = ET.SubElement(opt_throttle, "flight_move_speed_range_abs")
            spd_abs.set("invert", "1")

        # 2. Remove bindings acidentais nos botões de Cutoff (29 e 30) APENAS no Warthog
        # (No Logitech X56, os botões 29 e 30 são interruptores normais da base)
        if not is_x56:
            for rebind in profile.findall(".//rebind"):
                inp = (rebind.get("input", "") or "").strip()
                if inp in ("js2_button29", "js2_button30"):
                    rebind.set("input", "js2_ ")

        # 3. Aplica o Mapeamento Completo e Corrigido em todas as categorias do Star Citizen
        # 3.1 Movimento e Propulsores (spaceship_movement)
        am_mov = _get_or_create_actionmap(profile, "spaceship_movement")
        _set_action_rebind(am_mov, "v_pitch", "js1_y")
        _set_action_rebind(am_mov, "v_roll", "js1_x")
        if is_x56:
            # Logitech G / Saitek X56 Rhino:
            # Stick possui Twist Yaw (js1_rotz); Throttle usa X/Y para as duas alavancas,
            # slider1 para o rotativo F no polegar (Speed Limiter) e rotx/roty para o mini-stick do polegar!
            _set_action_rebind(am_mov, "v_yaw", "js1_rotz")
            _set_action_rebind(am_mov, "v_strafe_longitudinal", "js2_x")
            _set_action_rebind(am_mov, "v_throttle_abs", "js2_y")
            _set_action_rebind(am_mov, "v_speed_range_abs", "js2_slider1")
            _set_action_rebind(am_mov, "v_strafe_lateral", "js2_rotx")
            _set_action_rebind(am_mov, "v_strafe_vertical", "js2_roty")
        else:
            _set_action_rebind(am_mov, "v_strafe_lateral", "js2_x")
            _set_action_rebind(am_mov, "v_strafe_vertical", "js2_y")
            _set_action_rebind(am_mov, "v_strafe_longitudinal", "js2_z")
            _set_action_rebind(am_mov, "v_throttle_abs", "js2_rotz")
            _set_action_rebind(am_mov, "v_speed_range_abs", "js2_slider1")
        _set_action_rebind(am_mov, "v_strafe_longitudinal_invert", "js2_button12")
        _set_action_rebind(am_mov, "v_strafe_back", "js2_button12")
        _set_action_rebind(am_mov, "v_ifcs_speed_limiter_rel", "js2_ ")  # Liberta eixo da manete!
        _set_action_rebind(am_mov, "v_accel_range_rel", "js2_ ")
        _set_action_rebind(am_mov, "v_strafe_up", "js2_hat1_up")
        _set_action_rebind(am_mov, "v_strafe_down", "js2_hat1_down")
        _set_action_rebind(am_mov, "v_yaw_left", "js2_hat1_left")
        _set_action_rebind(am_mov, "v_yaw_right", "js2_hat1_right")
        _set_action_rebind(am_mov, "v_afterburner", "js2_button11")
        _set_action_rebind(am_mov, "v_space_brake", "js2_button8")
        _set_action_rebind(am_mov, "v_ifcs_toggle_cruise_control", "js2_button7")
        _set_action_rebind(am_mov, "v_ifcs_toggle_vector_decoupling", "js1_button4")
        _set_action_rebind(am_mov, "v_target_match_vel", "js2_button1")
        _set_action_rebind(am_mov, "v_toggle_landing_system", "js2_button25")
        _set_action_rebind(am_mov, "v_retract_landing_system", "js2_button22")
        _set_action_rebind(am_mov, "v_deploy_landing_system", "js2_ ")
        _set_action_rebind(am_mov, "v_vtol_toggle", "js2_button23")
        _set_action_rebind(am_mov, "v_toggle_vtol", "js2_button23")
        _set_action_rebind(am_mov, "v_atc_request", "js2_button21")

        # 3.2 Modos de Assento (seat_general)
        am_seat = _get_or_create_actionmap(profile, "seat_general")
        _set_action_rebind(am_seat, "v_toggle_quantum_mode", "js1_button5")
        _set_action_rebind(am_seat, "v_toggle_guns_mode", "js2_button10")
        _set_action_rebind(am_seat, "v_toggle_missile_mode", "js2_button26")
        _set_action_rebind(am_seat, "v_toggle_scan_mode", "js2_button3")
        _set_action_rebind(am_seat, "v_toggle_mining_mode", "js2_button5")
        _set_action_rebind(am_seat, "v_eject", "js2_button32")

        # 3.3 Geral da Nave (spaceship_general)
        am_gen = _get_or_create_actionmap(profile, "spaceship_general")
        _set_action_rebind(am_gen, "v_flightready", "js2_button20")
        _set_action_rebind(am_gen, "v_open_all_doors", "js2_button27")
        _set_action_rebind(am_gen, "v_close_all_doors", "js2_button15")
        _set_action_rebind(am_gen, "v_lock_all_doors", "js2_button28")

        # 3.4 Câmara (spaceship_view)
        am_view = _get_or_create_actionmap(profile, "spaceship_view")
        _set_action_rebind(am_view, "v_view_cycle_fwd", "js2_button4")
        _set_action_rebind(am_view, "v_view_freelook_mode", "js2_ ")

        # 3.5 Quantum Drive (spaceship_quantum)
        am_qd = _get_or_create_actionmap(profile, "spaceship_quantum")
        _set_action_rebind(am_qd, "v_toggle_qdrive_engagement", "js2_button9")

        # 3.6 Armas (spaceship_weapons)
        am_wpn = _get_or_create_actionmap(profile, "spaceship_weapons")
        _set_action_rebind(am_wpn, "v_attack1_group1", "js1_button1")
        _set_action_rebind(am_wpn, "v_attack1_group2", "js1_button6")
        _set_action_rebind(am_wpn, "v_weapon_cycle_aimmode", "js1_button3")

        # 3.7 Mísseis (spaceship_missiles)
        am_mis = _get_or_create_actionmap(profile, "spaceship_missiles")
        _set_action_rebind(am_mis, "v_weapon_toggle_launch_missile", "js1_button2")
        _set_action_rebind(am_mis, "v_weapon_cycle_missile_fwd", "js1_button16")
        _set_action_rebind(am_mis, "v_weapon_cycle_missile_back", "js1_button18")
        _set_action_rebind(am_mis, "v_weapon_increase_max_missiles", "js1_button19")
        _set_action_rebind(am_mis, "v_weapon_bombing_toggle_desired_impact_point_hold", "js2_button14")

        # 3.8 Contramedidas e Defesa (spaceship_defensive)
        am_def = _get_or_create_actionmap(profile, "spaceship_defensive")
        _set_action_rebind(am_def, "v_weapon_countermeasure_noise_launch", "js1_button15")
        _set_action_rebind(am_def, "v_weapon_countermeasure_decoy_burst_increase", "js1_button16")
        _set_action_rebind(am_def, "v_weapon_countermeasure_decoy_launch", "js1_button17")
        _set_action_rebind(am_def, "v_weapon_countermeasure_decoy_burst_decrease", "js1_button18")
        _set_action_rebind(am_def, "v_weapon_countermeasure_decoy_launch_panic", "js1_button19")
        _set_action_rebind(am_def, "v_shield_reset_level", "js1_button13")

        # 3.9 Targeting & Radar (spaceship_targeting, spaceship_targeting_advanced, spaceship_radar, spaceship_scanning)
        am_tgt = _get_or_create_actionmap(profile, "spaceship_targeting")
        _set_action_rebind(am_tgt, "v_target_lock_selected", "js1_button7")
        _set_action_rebind(am_tgt, "v_target_pin_selected", "js1_button10")

        am_tgta = _get_or_create_actionmap(profile, "spaceship_targeting_advanced")
        _set_action_rebind(am_tgta, "v_target_cycle_in_view_fwd", "js1_button7")
        _set_action_rebind(am_tgta, "v_target_cycle_in_view_reset", "js1_button7")
        _set_action_rebind(am_tgta, "v_target_cycle_hostile_fwd", "js1_button8")
        _set_action_rebind(am_tgta, "v_target_cycle_hostile_reset", "js1_button9")
        _set_action_rebind(am_tgta, "v_target_cycle_hostile_back", "js1_button10")
        _set_action_rebind(am_tgta, "v_target_cycle_all_fwd", "js1_button12")
        _set_action_rebind(am_tgta, "v_target_cycle_all_back", "js1_button14")

        am_rad = _get_or_create_actionmap(profile, "spaceship_radar")
        _set_action_rebind(am_rad, "v_invoke_ping", "js1_button11")
        _set_action_rebind(am_rad, "v_inc_ping_focus_angle", "js1_button12")
        _set_action_rebind(am_rad, "v_dec_ping_focus_angle", "js1_button14")

        am_scan = _get_or_create_actionmap(profile, "spaceship_scanning")
        _set_action_rebind(am_scan, "v_scanning_trigger_scan", "js1_button1")
        _set_action_rebind(am_scan, "v_inc_scan_focus_level", "js1_button11")
        _set_action_rebind(am_scan, "v_dec_scan_focus_level", "js1_button13")

        # 3.10 Mineração, Capacitor e Energia
        am_min = _get_or_create_actionmap(profile, "spaceship_mining")
        _set_action_rebind(am_min, "v_toggle_mining_laser_fire", "js1_button1")
        _set_action_rebind(am_min, "v_toggle_mining_laser_type", "js1_button2")
        _set_action_rebind(am_min, "v_mining_throttle", "js2_slider1")

        am_cap = _get_or_create_actionmap(profile, "vehicle_capacitor_assignment")
        _set_action_rebind(am_cap, "v_capacitor_assignment_engine_combined_increase_max", "js1_hat1_up")
        _set_action_rebind(am_cap, "v_capacitor_assignment_shield_combined_increase_max", "js1_hat1_right")
        _set_action_rebind(am_cap, "v_capacitor_assignment_weapon_combined_increase_max", "js1_hat1_left")
        _set_action_rebind(am_cap, "v_capacitor_assignment_reset", "js1_hat1_down")

        am_pwr = _get_or_create_actionmap(profile, "spaceship_power")
        _set_action_rebind(am_pwr, "v_power_toggle_thrusters", "js2_button16")
        _set_action_rebind(am_pwr, "v_power_set_thrusters_off", "js2_button18")
        _set_action_rebind(am_pwr, "v_power_toggle_weapons", "js2_button17")
        _set_action_rebind(am_pwr, "v_power_set_weapons_off", "js2_button19")
        _set_action_rebind(am_pwr, "v_power_toggle_shields", "js2_button24")

        am_lgt = _get_or_create_actionmap(profile, "lights_controller")
        _set_action_rebind(am_lgt, "v_lights", "js2_button13")
        _set_action_rebind(am_lgt, "v_toggle_cabin_lights", "js2_button14")
        _set_action_rebind(am_lgt, "v_lights_on", "js2_ ")
        _set_action_rebind(am_lgt, "v_lights_off", "js2_ ")

        am_hud = _get_or_create_actionmap(profile, "spaceship_hud")
        _set_action_rebind(am_hud, "visor_wipe", "js2_button31")

        am_voip = _get_or_create_actionmap(profile, "player_input_optical_tracking")
        _set_action_rebind(am_voip, "foip_pushtotalk", "js2_button2")

        # Guarda sempre uma cópia local reparada em profiles/actionmaps_REPARADO.xml
        from config import get_app_dir
        local_profiles_dir = os.path.join(get_app_dir(), "profiles")
        os.makedirs(local_profiles_dir, exist_ok=True)
        local_repaired = os.path.join(local_profiles_dir, "actionmaps_REPARADO.xml")
        tree.write(local_repaired, encoding="utf-8", xml_declaration=True)

        # Salva o ficheiro XML corrigido diretamente no Star Citizen
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)
        return True, (
            f"✅ Reparado com sucesso! Backup salvo em {os.path.basename(backup_file)}.\n"
            "• Conflito de Thrusters (js2_rotz vs Speed Limiter) eliminado!\n"
            "• Propulsores (Z e Rz), Limitador (Slider 1), Manche (19B) e Manete (32B) 100% mapeados!"
        )

    except PermissionError:
        return False, (
            "Permissão de Administrador necessária para gravar diretamente em 'C:\\Program Files\\...'.\n"
            f"✅ Uma cópia 100% reparada do teu actionmaps.xml foi guardada em:\n{local_repaired}\n"
            "Executa o 'run.bat' (que solicita automaticamente privilégios de Administrador) para aplicar diretamente no Star Citizen!"
        )
    except Exception as e:
        return False, f"Erro ao aplicar correções: {e}"


def list_backups(xml_path: str) -> list[str]:
    """Retorna lista de cópias de segurança existentes para o actionmaps."""
    folder = os.path.dirname(xml_path)
    base_name = os.path.basename(xml_path)
    if not os.path.exists(folder):
        return []
    backups = []
    for f in os.listdir(folder):
        if f.startswith(f"{base_name}.bak_"):
            backups.append(os.path.join(folder, f))
    backups.sort(reverse=True)
    return backups


def restore_backup(backup_path: str, target_xml_path: str) -> Tuple[bool, str]:
    """Restaura uma cópia de segurança selecionada."""
    if not os.path.exists(backup_path):
        return False, "Ficheiro de backup não encontrado."
    try:
        shutil.copy2(backup_path, target_xml_path)
        return True, f"Backup restaurado com sucesso a partir de {os.path.basename(backup_path)}"
    except Exception as e:
        return False, f"Falha ao restaurar backup: {e}"



def apply_axis_calibration_to_xml(xml_path: str, axis_cal: dict) -> tuple[bool, str]:
    """
    Aplica as curvas individuais (exponent) e zonas mortas anti-drift (deadzone)
    dos eixos X (Roll), Y (Pitch) e Z (Yaw) diretamente no actionmaps.xml do Star Citizen.
    """
    if not xml_path or not os.path.exists(xml_path):
        return False, "Ficheiro actionmaps.xml do Star Citizen não encontrado."

    try:
        create_backup(xml_path)
        tree = ET.parse(xml_path)
        root = tree.getroot()
        profile = root.find(".//ActionProfiles") or root

        # Encontra <options type="joystick" instance="1"> (Stick)
        opt_stick = None
        for opt in profile.findall("options[@type='joystick']"):
            if opt.get("instance") == "1":
                opt_stick = opt
                break
        if opt_stick is None:
            opt_stick = ET.SubElement(profile, "options", {"type": "joystick", "instance": "1"})

        axis_tag_map = {
            "x": "flight_move_roll",
            "y": "flight_move_pitch",
            "z": "flight_move_yaw",
        }

        for ax_key, xml_tag in axis_tag_map.items():
            cfg = axis_cal.get(ax_key)
            if not isinstance(cfg, dict):
                continue
            el = opt_stick.find(xml_tag)
            if el is None:
                el = ET.SubElement(opt_stick, xml_tag)

            ctype = str(cfg.get("curve_type", "expo"))
            exp_val = 1.0 if ctype == "linear" else max(1.0, min(3.5, float(cfg.get("exponent", 1.8))))
            dz_val = max(0.0, min(0.50, float(cfg.get("deadzone", 3)) / 100.0))
            inv_val = "1" if cfg.get("invert", False) else "0"

            el.set("exponent", f"{exp_val:.2f}")
            el.set("deadzone", f"{dz_val:.3f}")
            el.set("invert", inv_val)

        # Também aplica deadzone de hardware em <deviceoptions> para o Stick (x, y, rotz)
        stick_prod = (opt_stick.get("Product") or "").strip()
        if stick_prod:
            dev_opt = None
            for dopt in profile.findall("deviceoptions"):
                if (dopt.get("name") or "").strip() == stick_prod:
                    dev_opt = dopt
                    break
            if dev_opt is None:
                dev_opt = ET.SubElement(profile, "deviceoptions", {"name": stick_prod})
            hw_map = {"x": "x", "y": "y", "z": "rotz"}
            for ax_key, hw_input in hw_map.items():
                cfg = axis_cal.get(ax_key)
                if not isinstance(cfg, dict):
                    continue
                dz_val = max(0.0, min(0.50, float(cfg.get("deadzone", 3)) / 100.0))
                opt_el = None
                for o in dev_opt.findall("option"):
                    if o.get("input") == hw_input:
                        opt_el = o
                        break
                if opt_el is None:
                    opt_el = ET.SubElement(dev_opt, "option", {"input": hw_input})
                opt_el.set("deadzone", f"{dz_val:.3f}")

        tree.write(xml_path, encoding="utf-8", xml_declaration=False)
        return True, (
            f"Curvas e Anti-Drift aplicados ao Star Citizen XML "
            f"(X:{axis_cal.get('x',{}).get('deadzone',3)}% | Y:{axis_cal.get('y',{}).get('deadzone',3)}% | Z:{axis_cal.get('z',{}).get('deadzone',4)}%)."
        )
    except PermissionError:
        return False, "Sem permissão de escrita em actionmaps.xml (executa o run.bat como Administrador)."
    except Exception as e:
        return False, f"Erro ao aplicar curvas ao XML: {e}"
