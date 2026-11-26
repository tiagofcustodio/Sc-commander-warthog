"""
Profile Generator - Complete Star Citizen 4.x XML Exporter
Gera o ficheiro de perfil XML 100% completo para o Thrustmaster HOTAS Warthog:
- Manche A-10C (js1 - VID_044F&PID_0402.dev): Todos os 19 botões + POV1 Hat (4 direções) + 2 Eixos (X, Y)
- Manete Dupla (js2 - VID_044F&PID_0404.dev): Todos os 32 botões + POV1 Coolie Hat (4 direções) + 5 Eixos (Z, Rz, Slider1, X, Y)
"""

import os


def generate_warthog_xml_content() -> str:
    """Retorna a string XML completa para o Star Citizen 4.10+."""
    return """<ActionMaps version="1" optionsVersion="2" rebindVersion="2" profileName="Warthog_SC_Commander_Pro">
  <CustomisationUIHeader label="Warthog_SC_Commander_Pro" description="Perfil Completo 100% HOTAS Warthog (Manche 19B + Manete 32B + Thrusters Fix)" image="">
    <devices>
      <keyboard instance="1"/>
      <mouse instance="1"/>
      <joystick instance="1"/>
      <joystick instance="2"/>
    </devices>
    <categories>
      <category label="@ui_CCSeatGeneral"/>
      <category label="@ui_CCSpaceFlight"/>
      <category label="@ui_CCTurrets"/>
      <category label="@ui_CCLightControllerDesc"/>
      <category label="@ui_CCVehicle"/>
      <category label="@ui_CCEA_Interactive"/>
    </categories>
  </CustomisationUIHeader>

  <!-- Joystick 1 = Manche A-10C (PID 0402) | Joystick 2 = Manete Dupla (PID 0404) -->
  <deviceoptions name="Joystick - HOTAS Warthog  {0402044F-0000-0000-0000-504944564944}">
    <option input="x" deadzone="0.015"/>
    <option input="y" deadzone="0.015"/>
  </deviceoptions>
  <deviceoptions name="Throttle - HOTAS Warthog  {0404044F-0000-0000-0000-504944564944}">
    <option input="x" deadzone="0.049499996"/>
    <option input="y" deadzone="0.049499996"/>
  </deviceoptions>

  <options type="keyboard" instance="1" Product="Keyboard  {6F1D2B61-D5A0-11CF-BFC7-444553540000}"/>
  <options type="ouse" instance="1" Product="Mouse  {6F1D2B60-D5A0-11CF-BFC7-444553540000}"/>
  <options type="joystick" instance="1" Product="Joystick - HOTAS Warthog  {0402044F-0000-0000-0000-504944564944}">
    <flight_move_pitch exponent="1.2"/>
    <flight_move_roll exponent="1.2"/>
  </options>
  <options type="joystick" instance="2" Product="Throttle - HOTAS Warthog  {0404044F-0000-0000-0000-504944564944}">
    <flight_move_strafe_vertical invert="1" exponent="1.5"/>
    <flight_move_strafe_lateral exponent="1.5"/>
    <flight_strafe_longitudinal invert="1" exponent="1.0"/>
    <flight_throttle_abs invert="1" exponent="1.0"/>
  </options>

  <modifiers />

  <!-- ================= 1. ASSENTO E MODOS DE OPERAÇÃO (MASTER MODES) ================= -->
  <actionmap name="seat_general">
    <!-- B5 Manche = S1 (Master Mode Control Button) -->
    <action name="v_toggle_quantum_mode">
      <rebind input="js1_button5" activationMode="hold"/>
    </action>
    <!-- B10 Manete = BSB (Boat Switch AFT) -->
    <action name="v_toggle_guns_mode">
      <rebind input="js2_button10"/>
    </action>
    <!-- B26 Manete = APENG (Autopilot Engage Button) -->
    <action name="v_toggle_missile_mode">
      <rebind input="js2_button26"/>
    </action>
    <!-- B3 Manete = MSU (Mic Switch Up) -->
    <action name="v_toggle_scan_mode">
      <rebind input="js2_button3"/>
    </action>
    <!-- B5 Manete = MSD (Mic Switch Down) -->
    <action name="v_toggle_mining_mode">
      <rebind input="js2_button5"/>
    </action>
    <!-- B32 Manete = EORIGN (Eng Oper Right IGN) -->
    <action name="v_eject">
      <rebind input="js2_button32"/>
    </action>
  </actionmap>

  <!-- ================= 2. SISTEMAS GERAIS DA NAVE (PORTAS E FLIGHT READY) ================= -->
  <actionmap name="spaceship_general">
    <!-- B15 Manete = LTB (Left Throttle Button) & B20 = APUON -->
    <action name="v_flightready">
      <rebind input="js2_button20"/>
    </action>
    <!-- B27 Manete = APPAT (Autopilot PATH Up) -->
    <action name="v_open_all_doors">
      <rebind input="js2_button27"/>
    </action>
    <!-- B15 Manete = LTB (Left Throttle Button) -->
    <action name="v_close_all_doors">
      <rebind input="js2_button15"/>
    </action>
    <!-- B28 Manete = APALT (Autopilot ALT Down) -->
    <action name="v_lock_all_doors">
      <rebind input="js2_button28"/>
    </action>
  </actionmap>

  <!-- ================= 3. CÂMARA E VISÃO DE COCKPIT ================= -->
  <actionmap name="spaceship_view">
    <!-- B4 Manete = MSR (Mic Switch Right) -->
    <action name="v_view_cycle_fwd">
      <rebind input="js2_button4"/>
    </action>
    <!-- B6 Manete = MSL (Mic Switch Left) - Freelook/Z Desativado -->
    <action name="v_view_freelook_mode">
      <rebind input="js2_ "/>
    </action>
  </actionmap>

  <!-- ================= 4. MOVIMENTO E PROPULSORES (THRUSTERS CORRIGIDOS) ================= -->
  <actionmap name="spaceship_movement">
    <!-- Manche (js1): Pitch e Roll -->
    <action name="v_pitch">
      <rebind input="js1_y"/>
    </action>
    <action name="v_roll">
      <rebind input="js1_x"/>
    </action>

    <!-- Mini-Stick Slew da Manete (js2_x / js2_y): Strafe Lateral e Vertical Analógico -->
    <action name="v_strafe_lateral">
      <rebind input="js2_x"/>
    </action>
    <action name="v_strafe_vertical">
      <rebind input="js2_y"/>
    </action>

    <!-- Propulsores Principais (Manete Esquerda/Unida = js2_z | Manete Direita = js2_rotz) -->
    <action name="v_strafe_longitudinal">
      <rebind input="js2_z"/>
    </action>
    <action name="v_throttle_abs">
      <rebind input="js2_rotz"/>
    </action>
    <!-- B12 Manete = CHB (China Hat AFT): Inverter Propulsão / Recuar -->
    <action name="v_strafe_longitudinal_invert">
      <rebind input="js2_button12"/>
    </action>
    <action name="v_strafe_back">
      <rebind input="js2_button12"/>
    </action>

    <!-- Limitador de Velocidade na Roda Cinzenta Central (js2_slider1) - SEM CONFLITO COM Rz! -->
    <action name="v_speed_range_abs">
      <rebind input="js2_slider1"/>
    </action>
    <action name="v_ifcs_speed_limiter_rel">
      <rebind input="js2_ "/>
    </action>
    <action name="v_accel_range_rel">
      <rebind input="js2_ "/>
    </action>

    <!-- Coolie Hat da Manete (js2_hat1): Strafe Vertical + Guiada (Yaw) -->
    <action name="v_strafe_up">
      <rebind input="js2_hat1_up"/>
    </action>
    <action name="v_strafe_down">
      <rebind input="js2_hat1_down"/>
    </action>
    <action name="v_yaw_left">
      <rebind input="js2_hat1_left"/>
    </action>
    <action name="v_yaw_right">
      <rebind input="js2_hat1_right"/>
    </action>

    <!-- Boost / Pós-Combustão (B11 = CHF China Hat FWD), Space Brake (B8 = SPDB), Cruise (B7 = SPDF) e Decoupled (B4 Stick = S4) -->
    <action name="v_afterburner">
      <rebind input="js2_button11"/>
    </action>
    <action name="v_space_brake">
      <rebind input="js2_button8"/>
    </action>
    <action name="v_ifcs_toggle_cruise_control">
      <rebind input="js2_button7"/>
    </action>
    <action name="v_ifcs_toggle_vector_decoupling">
      <rebind input="js1_button4"/>
    </action>
    <!-- B1 Manete = SC (Slew Push) -->
    <action name="v_target_match_vel">
      <rebind input="js2_button1"/>
    </action>

    <!-- Trem de Aterragem (B25 = RDRNRM, B22 = FLAPU), VTOL (B23 = FLAPD) e Chamada ATC (B21 = LDGH) -->
    <action name="v_toggle_landing_system">
      <rebind input="js2_button25"/>
    </action>
    <action name="v_retract_landing_system">
      <rebind input="js2_button22"/>
    </action>
    <action name="v_deploy_landing_system">
      <rebind input="js2_ "/>
    </action>
    <action name="v_vtol_toggle">
      <rebind input="js2_button23"/>
    </action>
    <action name="v_toggle_vtol">
      <rebind input="js2_button23"/>
    </action>
    <action name="v_atc_request">
      <rebind input="js2_button21"/>
    </action>
  </actionmap>

  <!-- ================= 5. MOTOR QUÂNTICO (QUANTUM DRIVE) ================= -->
  <actionmap name="spaceship_quantum">
    <!-- B9 Manete = BSF (Boat Switch FWD) -->
    <action name="v_toggle_qdrive_engagement">
      <rebind input="js2_button9"/>
    </action>
  </actionmap>

  <!-- ================= 6. ARMAMENTO E GATILHO DUPLO (MANCHE js1) ================= -->
  <actionmap name="spaceship_weapons">
    <!-- B1 Manche = TG1 (Gatilho Etapa 1) -->
    <action name="v_attack1_group1">
      <rebind input="js1_button1"/>
    </action>
    <!-- B6 Manche = TG2 (Gatilho Etapa 2 Oficial VID_044F&PID_0402.dev) -->
    <action name="v_attack1_group2">
      <rebind input="js1_button6"/>
    </action>
    <!-- B3 Manche = S3 (Nosewheel Steering) -->
    <action name="v_weapon_cycle_aimmode">
      <rebind input="js1_button3"/>
    </action>
  </actionmap>

  <!-- ================= 7. MÍSSEIS E BOMBAS ================= -->
  <actionmap name="spaceship_missiles">
    <!-- B2 Manche = S2 (Weapon Release) -->
    <action name="v_weapon_toggle_launch_missile">
      <rebind input="js1_button2"/>
    </action>
    <action name="v_weapon_cycle_missile_fwd">
      <rebind input="js1_button16"/>
    </action>
    <action name="v_weapon_cycle_missile_back">
      <rebind input="js1_button18"/>
    </action>
    <action name="v_weapon_increase_max_missiles">
      <rebind input="js1_button19"/>
    </action>
    <action name="v_weapon_bombing_toggle_desired_impact_point_hold">
      <rebind input="js2_button14"/>
    </action>
  </actionmap>

  <!-- ================= 8. CONTRAMEDIDAS E ESCUDOS (CMS HAT B15..B19) ================= -->
  <actionmap name="spaceship_defensive">
    <action name="v_weapon_countermeasure_noise_launch">
      <rebind input="js1_button15"/>
    </action>
    <action name="v_weapon_countermeasure_decoy_burst_increase">
      <rebind input="js1_button16"/>
    </action>
    <action name="v_weapon_countermeasure_decoy_launch">
      <rebind input="js1_button17"/>
    </action>
    <action name="v_weapon_countermeasure_decoy_burst_decrease">
      <rebind input="js1_button18"/>
    </action>
    <action name="v_weapon_countermeasure_decoy_launch_panic">
      <rebind input="js1_button19"/>
    </action>
    <action name="v_shield_reset_level">
      <rebind input="js1_button13"/>
    </action>
  </actionmap>

  <!-- ================= 9. SELEÇÃO DE ALVOS (TMS B7..B10 & DMS B11..B14) ================= -->
  <actionmap name="spaceship_targeting">
    <action name="v_target_lock_selected">
      <rebind input="js1_button7"/>
    </action>
    <action name="v_target_pin_selected">
      <rebind input="js1_button10"/>
    </action>
  </actionmap>

  <actionmap name="spaceship_targeting_advanced">
    <action name="v_target_cycle_in_view_fwd">
      <rebind input="js1_button7"/>
    </action>
    <action name="v_target_cycle_in_view_reset">
      <rebind input="js1_button7"/>
    </action>
    <action name="v_target_cycle_hostile_fwd">
      <rebind input="js1_button8"/>
    </action>
    <action name="v_target_cycle_hostile_reset">
      <rebind input="js1_button9"/>
    </action>
    <action name="v_target_cycle_hostile_back">
      <rebind input="js1_button10"/>
    </action>
    <action name="v_target_cycle_all_fwd">
      <rebind input="js1_button12"/>
    </action>
    <action name="v_target_cycle_all_back">
      <rebind input="js1_button14"/>
    </action>
  </actionmap>

  <!-- ================= 10. RADAR, PING E SCANNING (DMS HAT B11..B14) ================= -->
  <actionmap name="spaceship_radar">
    <action name="v_invoke_ping">
      <rebind input="js1_button11"/>
    </action>
    <action name="v_inc_ping_focus_angle">
      <rebind input="js1_button12"/>
    </action>
    <action name="v_dec_ping_focus_angle">
      <rebind input="js1_button14"/>
    </action>
  </actionmap>

  <actionmap name="spaceship_scanning">
    <action name="v_scanning_trigger_scan">
      <rebind input="js1_button1"/>
    </action>
    <action name="v_inc_scan_focus_level">
      <rebind input="js1_button11"/>
    </action>
    <action name="v_dec_scan_focus_level">
      <rebind input="js1_button13"/>
    </action>
  </actionmap>

  <!-- ================= 11. MINERAÇÃO (MINING) ================= -->
  <actionmap name="spaceship_mining">
    <action name="v_toggle_mining_laser_fire">
      <rebind input="js1_button1"/>
    </action>
    <action name="v_toggle_mining_laser_type">
      <rebind input="js1_button2"/>
    </action>
    <action name="v_mining_throttle">
      <rebind input="js2_slider1"/>
    </action>
  </actionmap>

  <!-- ================= 12. CAPACITOR DE ENERGIA (TRIM HAT DO MANCHE) ================= -->
  <actionmap name="vehicle_capacitor_assignment">
    <action name="v_capacitor_assignment_engine_combined_increase_max">
      <rebind input="js1_hat1_up"/>
    </action>
    <action name="v_capacitor_assignment_shield_combined_increase_max">
      <rebind input="js1_hat1_right"/>
    </action>
    <action name="v_capacitor_assignment_weapon_combined_increase_max">
      <rebind input="js1_hat1_left"/>
    </action>
    <action name="v_capacitor_assignment_reset">
      <rebind input="js1_hat1_down"/>
    </action>
  </actionmap>

  <!-- ================= 13. ENERGIA DE MOTORES, ARMAS E ESCUDOS (B16..B19, B24) ================= -->
  <actionmap name="spaceship_power">
    <!-- B16 = EFLNORM, B18 = EOLMOTOR -->
    <action name="v_power_toggle_thrusters">
      <rebind input="js2_button16"/>
    </action>
    <action name="v_power_set_thrusters_off">
      <rebind input="js2_button18"/>
    </action>
    <!-- B17 = EFRNORM, B19 = EORMOTOR -->
    <action name="v_power_toggle_weapons">
      <rebind input="js2_button17"/>
    </action>
    <action name="v_power_set_weapons_off">
      <rebind input="js2_button19"/>
    </action>
    <!-- B24 = EACON -->
    <action name="v_power_toggle_shields">
      <rebind input="js2_button24"/>
    </action>
  </actionmap>

  <!-- ================= 14. ILUMINAÇÃO E HUD (B13, B14, B31) ================= -->
  <actionmap name="lights_controller">
    <!-- B13 = PSF (Pinky Switch FWD) -->
    <action name="v_lights">
      <rebind input="js2_button13"/>
    </action>
    <!-- B14 = PSB (Pinky Switch AFT) -->
    <action name="v_toggle_cabin_lights">
      <rebind input="js2_button14"/>
    </action>
  </actionmap>

  <actionmap name="spaceship_hud">
    <!-- B31 = EOLIGN (Eng Oper Left IGN) -->
    <action name="visor_wipe">
      <rebind input="js2_button31"/>
    </action>
  </actionmap>

  <!-- ================= 15. COMUNICAÇÕES VOIP / FOIP (B2 = MSP) ================= -->
  <actionmap name="player_input_optical_tracking">
    <action name="foip_pushtotalk">
      <rebind input="js2_button2"/>
    </action>
  </actionmap>

  <!-- ================= 16. TORRES (TURRETS) ================= -->
  <actionmap name="turret_movement">
    <action name="turret_pitch">
      <rebind input="js1_y"/>
    </action>
    <action name="turret_yaw">
      <rebind input="js1_x"/>
    </action>
  </actionmap>

  <actionmap name="turret_advanced">
    <action name="turret_limiter_abs">
      <rebind input="js2_slider1"/>
    </action>
    <action name="turret_limiter_toggle">
      <rebind input="js2_button7"/>
    </action>
    <action name="turret_recenter">
      <rebind input="js2_button4"/>
    </action>
  </actionmap>

  <!-- ================= 17. VEÍCULOS TERRESTRES ================= -->
  <actionmap name="vehicle_general">
    <action name="v_attack1_group1">
      <rebind input="js1_button1"/>
    </action>
    <action name="v_attack1_group2">
      <rebind input="js1_button6"/>
    </action>
    <action name="v_horn">
      <rebind input="js2_button21"/>
    </action>
  </actionmap>

  <actionmap name="vehicle_driver">
    <action name="v_move_forward">
      <rebind input="js2_z"/>
    </action>
    <action name="v_move_back">
      <rebind input="js2_button12"/>
    </action>
    <action name="v_boost">
      <rebind input="js2_button11"/>
    </action>
    <action name="v_brake">
      <rebind input="js2_button8"/>
    </action>
    <action name="v_mgv_switch_brake_on_idle">
      <rebind input="js2_button7"/>
    </action>
  </actionmap>

  <!-- ================= 18. MODO DE INTERAÇÃO (INNER THOUGHT) ================= -->
  <actionmap name="player_choice">
    <action name="pc_interaction_mode">
      <rebind input="js2_button1"/>
    </action>
    <action name="pc_select">
      <rebind input="js1_button1"/>
    </action>
  </actionmap>
</ActionMaps>
"""


def write_profile_to_sc(mappings_dir: str) -> tuple[bool, str]:
    """Escreve o perfil completo na pasta mappings do Star Citizen e mantém uma cópia local."""
    content = generate_warthog_xml_content()

    from config import get_app_dir
    local_profiles_dir = os.path.join(get_app_dir(), "profiles")
    os.makedirs(local_profiles_dir, exist_ok=True)
    local_file = os.path.join(local_profiles_dir, "layout_warthog_sc_fixed.xml")
    try:
        with open(local_file, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"[ProfileGenerator] Aviso ao salvar cópia local: {e}")

    try:
        if not os.path.exists(mappings_dir):
            os.makedirs(mappings_dir, exist_ok=True)
        target_file = os.path.join(mappings_dir, "layout_warthog_sc_fixed.xml")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return True, (
            f"✅ Perfil Completo gravado diretamente no Star Citizen:\n{target_file}\n\n"
            "No jogo, também podes carregar via consola (~):\npp_rebindkeys layout_warthog_sc_fixed"
        )
    except PermissionError:
        return False, (
            "Permissão de Administrador necessária para gravar em 'C:\\Program Files\\...'.\n\n"
            "✅ Uma cópia atualizada foi gerada em:\n"
            f"'{local_file}'\n\n"
            "O run.bat pede agora automaticamente privilégios de Administrador ao iniciar!"
        )
    except Exception as e:
        return False, f"Erro ao gravar perfil: {e}"
