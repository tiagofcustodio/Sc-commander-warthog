"""
Web App Server & Glassmorphism Dashboard Host
Inicia o servidor FastAPI local com WebSockets, gere Perfis de Atividade, LEDs da base,
Camada Shift do Pinky Lever, Detentor de Pós-Combustão, Monitor de Cutoff (Botões 29/30),
Telemetria em Tempo Real de Todos os Eixos e Monitor de Processo do Star Citizen.
"""

import os
import sys
import time
import json
import asyncio
import threading
import subprocess
import webbrowser
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from warthog_constants import (
    DEFAULT_SC_MAPPINGS,
    STICK_BUTTONS,
    STICK_HATS,
    STICK_AXES,
    THROTTLE_BUTTONS,
    THROTTLE_HATS,
    THROTTLE_AXES
)
from config import load_config, save_config, get_resource_dir
from dinput_reader import WarthogDeviceWatcher
from switch_engine import SwitchEngine
from warthog_leds import WarthogLEDController
from profile_manager import ProfileManager
from sc_process_monitor import StarCitizenProcessMonitor
from tray_service import WarthogTrayIcon
from actionmaps_fixer import (
    find_sc_live_dir,
    get_actionmaps_path,
    get_mappings_dir,
    diagnose_actionmaps,
    fix_actionmaps,
    create_backup,
    apply_axis_calibration_to_xml
)
from profile_generator import write_profile_to_sc
from hotas_devices import HOTAS_KITS_META
from updater import APP_VERSION, check_for_updates, apply_update, create_zip_backup

latest_update_info = {
    "status": "idle",
    "update_available": False,
    "current_version": APP_VERSION,
    "latest_version": APP_VERSION,
    "message": f"Versão atual v{APP_VERSION}"
}

WEB_DIR = os.path.join(get_resource_dir(), "web")
HOST = "127.0.0.1"
PORT = 8765

app = FastAPI(title="Star Citizen Warthog Commander Pro")

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/")
async def get_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"), headers={"Cache-Control": "no-store"})


@app.get("/style.css")
async def get_css():
    return FileResponse(os.path.join(WEB_DIR, "style.css"), headers={"Cache-Control": "no-store"})


@app.get("/app.js")
async def get_js():
    return FileResponse(os.path.join(WEB_DIR, "app.js"), headers={"Cache-Control": "no-store"})


@app.get("/favicon.ico")
async def get_favicon():
    ico_path = os.path.join(WEB_DIR, "app_icon.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path, media_type="image/x-icon")
    return FileResponse(os.path.join(WEB_DIR, "app_icon.png"), media_type="image/png")


@app.get("/{filename}.png")
async def get_png(filename: str):
    file_path = os.path.join(WEB_DIR, f"{filename}.png")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png")
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


class WebSocketHub:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


hub = WebSocketHub()

# Global state instances
config = load_config()
led_controller = WarthogLEDController(initial_brightness=config.get("throttle_led_brightness", 3))
profile_mgr = ProfileManager(
    config.get("active_profile", "combat"),
    config.get("custom_profile_mappings", {})
)
sc_monitor = StarCitizenProcessMonitor()

active_profile_data = profile_mgr.get_active_profile()

watcher = WarthogDeviceWatcher()
engine = SwitchEngine(
    active_profile_data.get("mappings", DEFAULT_SC_MAPPINGS),
    config.get("pulse_hold_ms", 60),
    led_controller=led_controller,
    macros=config.get("macros", {})
)
engine.afterburner_enabled = False

main_event_loop: asyncio.AbstractEventLoop = None
tray_icon_ref = None


def broadcast_threadsafe(message: dict):
    global main_event_loop
    if main_event_loop and main_event_loop.is_running():
        asyncio.run_coroutine_threadsafe(hub.broadcast(message), main_event_loop)


# Hardware Callbacks
def on_hardware_button(device: str, button: int, is_down: bool):
    engine.handle_button_event(device, button, is_down)
    broadcast_threadsafe({
        "type": "switch_event",
        "device": device,
        "button": button,
        "is_down": is_down
    })


def on_hardware_hat(device: str, direction: str):
    engine.handle_hat_event(device, direction)
    broadcast_threadsafe({
        "type": "hat_event",
        "device": device,
        "direction": direction
    })


def on_hardware_axis(device: str, axis_name: str, value: int):
    engine.handle_axis_event(device, axis_name, value)


def on_cutoff_change(cut_left: bool, cut_right: bool):
    broadcast_threadsafe({
        "type": "cutoff_event",
        "left": cut_left,
        "right": cut_right
    })


def on_action_triggered(action_id: str, key_combo: str, desc: str):
    timestamp = time.strftime("%H:%M:%S")
    broadcast_threadsafe({
        "type": "log",
        "timestamp": timestamp,
        "action_id": action_id,
        "desc": desc,
        "text": f"Ação [{action_id}]",
        "key_hit": f"{key_combo} ({desc})"
    })


def on_shift_change(shift_active: bool):
    broadcast_threadsafe({
        "type": "shift_event",
        "active": shift_active
    })


def on_afterburner_change(afterburner_active: bool):
    broadcast_threadsafe({
        "type": "afterburner_event",
        "active": afterburner_active
    })


def on_led_state_change(leds: list[bool], brightness: int):
    broadcast_threadsafe({
        "type": "led_status",
        "leds": leds,
        "brightness": brightness
    })


def _build_hotas_info_payload(auto_switch: bool = False) -> dict:
    has_hw = (watcher.stick_slot is not None) or (watcher.throttle_slot is not None)
    selected = watcher.detected_kit if (auto_switch and has_hw and watcher.detected_kit in HOTAS_KITS_META) else config.get("selected_hotas_kit", watcher.detected_kit or "warthog")
    return {
        "type": "hotas_info",
        "kits": HOTAS_KITS_META,
        "selected_kit": selected,
        "detected_kit": watcher.detected_kit if has_hw else None,
        "detected_stick_kit": watcher.detected_stick_kit,
        "detected_throttle_kit": watcher.detected_throttle_kit,
        "left_device_role": watcher.left_device_role,
        "stick_connected": watcher.stick_slot is not None,
        "throttle_connected": watcher.throttle_slot is not None,
        "detected_devices": watcher.detected_devices,
        "auto_switch": bool(auto_switch and has_hw),
    }


def on_device_status(stick_conn: bool, throttle_conn: bool):
    if throttle_conn and (watcher.detected_throttle_kit == "warthog" or watcher.detected_kit == "warthog"):
        led_controller._push_state_to_hardware()
    sc_live = find_sc_live_dir(config.get("star_citizen_live_path"))
    broadcast_threadsafe({
        "type": "device_status",
        "stick": stick_conn,
        "throttle": throttle_conn,
        "stick_name": watcher.stick_name,
        "throttle_name": watcher.throttle_name,
        "sc_live": bool(sc_live),
        "sc_running": sc_monitor.is_running
    })
    if stick_conn or throttle_conn:
        if watcher.detected_kit in HOTAS_KITS_META:
            config["selected_hotas_kit"] = watcher.detected_kit
            save_config(config)
        broadcast_threadsafe(_build_hotas_info_payload(auto_switch=True))


def on_sc_process_change(is_running: bool):
    broadcast_threadsafe({
        "type": "device_status",
        "stick": watcher.stick_slot is not None,
        "throttle": watcher.throttle_slot is not None,
        "stick_name": watcher.stick_name,
        "throttle_name": watcher.throttle_name,
        "sc_live": bool(find_sc_live_dir(config.get("star_citizen_live_path"))),
        "sc_running": is_running
    })
    broadcast_threadsafe({
        "type": "log",
        "timestamp": time.strftime("%H:%M:%S"),
        "text": f"Processo StarCitizen.exe: {'DETETADO EM EXECUÇÃO' if is_running else 'FINALIZADO'}",
        "key_hit": "AUTO-SYNC"
    })


def apply_and_persist_profile(pid: str) -> dict:
    """Aplica o perfil selecionado ao SwitchEngine, guarda no config.json e retorna os dados do perfil."""
    pdata = profile_mgr.set_active_profile(pid)
    actual_pid = profile_mgr.active_profile_id
    engine.update_mappings(
        pdata.get("mappings", DEFAULT_SC_MAPPINGS),
        config.get("pulse_hold_ms", 60),
        afterburner_enabled=False
    )
    config["active_profile"] = actual_pid
    config["afterburner_auto_boost"] = False
    config["split_throttle_mode"] = pdata.get("split_throttle_mode", "speed_limiter")
    config["curve_type"] = pdata.get("curve_type", "expo")
    config["curve_exponent"] = pdata.get("curve_exponent", 1.8)
    config["mappings"] = pdata.get("mappings", DEFAULT_SC_MAPPINGS)
    save_config(config)
    return pdata


def on_profile_cycle_requested():
    """Cicla para o próximo perfil quando o utilizador prime S4 (Shift) + S3 (BTN 3) no Manche."""
    next_id, pdata = profile_mgr.cycle_next_profile()
    apply_and_persist_profile(next_id)
    broadcast_threadsafe({
        "type": "profile_changed",
        "profile_id": next_id,
        "profile_data": pdata
    })
    broadcast_threadsafe({
        "type": "log",
        "timestamp": time.strftime("%H:%M:%S"),
        "text": f"[HOTAS S4+S3] Perfil alternado para: {pdata['name']}",
        "key_hit": f"{pdata['icon']} {pdata.get('highlights', '')}"
    })


watcher.on_button_change = on_hardware_button
watcher.on_hat_change = on_hardware_hat
watcher.on_axis_change = on_hardware_axis
watcher.on_cutoff_change = on_cutoff_change
watcher.on_device_status_change = on_device_status
engine.on_action_triggered = on_action_triggered
engine.on_shift_change = on_shift_change
engine.on_afterburner_change = on_afterburner_change
engine.on_profile_cycle_requested = on_profile_cycle_requested
led_controller.on_state_change = on_led_state_change
sc_monitor.on_state_change = on_sc_process_change


# Background axis streamer (Slew Radar + Throttle Z / Rz / Slider + Stick X / Y)
def start_axis_streamer():
    def _loop():
        prev_state = {}
        while True:
            cur = {
                "slew_x": watcher.throttle_axes.get("slew_x", 32767),
                "slew_y": watcher.throttle_axes.get("slew_y", 32767),
                "z": watcher.throttle_axes.get("z", 65535),
                "rz": watcher.throttle_axes.get("rz", 65535),
                "slider": watcher.throttle_axes.get("slider", 32767),
                "stick_x": watcher.stick_axes.get("x", 32767),
                "stick_y": watcher.stick_axes.get("y", 32767),
            }
            changed = False
            for k, v in cur.items():
                if abs(v - prev_state.get(k, -9999)) > 250:
                    changed = True
                    break
            if changed:
                prev_state = dict(cur)
                broadcast_threadsafe({
                    "type": "axis_event",
                    **cur
                })
            time.sleep(0.05)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
    await hub.connect(websocket)

    sc_live = find_sc_live_dir(config.get("star_citizen_live_path"))
    diag = {}
    if sc_live:
        xml_p = get_actionmaps_path(sc_live)
        diag = diagnose_actionmaps(xml_p)

    # Envia estados iniciais completos
    await websocket.send_text(json.dumps({
        "type": "device_status",
        "stick": watcher.stick_slot is not None,
        "throttle": watcher.throttle_slot is not None,
        "stick_name": watcher.stick_name,
        "throttle_name": watcher.throttle_name,
        "sc_live": bool(sc_live),
        "sc_running": sc_monitor.is_running
    }))

    await websocket.send_text(json.dumps({
        "type": "cutoff_event",
        "left": watcher.cutoff_left,
        "right": watcher.cutoff_right
    }))

    await websocket.send_text(json.dumps({
        "type": "led_status",
        "leds": led_controller.led_states,
        "brightness": led_controller.brightness
    }))

    await websocket.send_text(json.dumps({
        "type": "hardware_catalog",
        "stick_buttons": STICK_BUTTONS,
        "stick_hats": STICK_HATS,
        "stick_axes": STICK_AXES,
        "throttle_buttons": THROTTLE_BUTTONS,
        "throttle_hats": THROTTLE_HATS,
        "throttle_axes": THROTTLE_AXES
    }))

    await websocket.send_text(json.dumps({
        "type": "initial_throttle_state",
        "buttons_mask": watcher.prev_throttle_buttons,
        "pov": watcher.prev_throttle_pov,
        "stick_buttons_mask": watcher.prev_stick_buttons,
        "stick_pov": watcher.prev_stick_pov
    }))

    await websocket.send_text(json.dumps({
        "type": "profile_changed",
        "profile_id": profile_mgr.active_profile_id,
        "profile_data": profile_mgr.get_active_profile()
    }))

    await websocket.send_text(json.dumps({
        "type": "config",
        "config": {
            **config,
            "active_profile": profile_mgr.active_profile_id,
            "mappings": engine.mappings
        }
    }))

    await websocket.send_text(json.dumps(_build_hotas_info_payload(auto_switch=True)))

    await websocket.send_text(json.dumps({
        "type": "update_status",
        **latest_update_info,
        "auto_check_updates": config.get("auto_check_updates", True),
        "update_source": config.get("update_source", "")
    }))

    if diag:
        await websocket.send_text(json.dumps({
            "type": "diagnosis",
            **diag
        }))

    try:
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type == "set_profile":
                pid = data.get("profile", "combat")
                pdata = apply_and_persist_profile(pid)
                actual_pid = profile_mgr.active_profile_id

                await hub.broadcast({
                    "type": "profile_changed",
                    "profile_id": actual_pid,
                    "profile_data": pdata
                })
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Perfil alterado para: {pdata['name']}",
                    "key_hit": f"{pdata['icon']} {pdata.get('highlights', '')}"
                })

            elif msg_type == "set_led":
                idx = data.get("led", 1)
                st = data.get("state", False)
                led_controller.set_led(idx, st)
                await hub.broadcast({
                    "type": "led_status",
                    "leds": led_controller.led_states,
                    "brightness": led_controller.brightness
                })

            elif msg_type == "set_brightness":
                br = data.get("brightness", 3)
                led_controller.set_brightness(br)
                config["throttle_led_brightness"] = br
                save_config(config)
                await hub.broadcast({
                    "type": "led_status",
                    "leds": led_controller.led_states,
                    "brightness": led_controller.brightness
                })

            elif msg_type == "set_auto_boost":
                en = data.get("enabled", True)
                engine.afterburner_enabled = en
                config["afterburner_auto_boost"] = en
                save_config(config)

            elif msg_type == "trigger_action":
                act_id = data.get("action_id")
                engine._dispatch_action(act_id, f"Teste Manual {act_id}")

            elif msg_type == "update_mapping":
                act_id = data.get("action_id")
                if act_id:
                    active_pid = profile_mgr.active_profile_id
                    updated_entry = profile_mgr.update_single_mapping(act_id, data, active_pid)
                    pdata = profile_mgr.get_active_profile()
                    engine.mappings = pdata["mappings"]

                    custom_all = config.setdefault("custom_profile_mappings", {})
                    custom_prof = custom_all.setdefault(active_pid, {})
                    custom_prof[act_id] = updated_entry
                    config["mappings"] = pdata["mappings"]
                    save_config(config)

                    mod_str = "+".join(updated_entry["modifiers"]) + "+" if updated_entry["modifiers"] else ""
                    combo_lbl = f"{mod_str}{updated_entry['key']}" if updated_entry["key"] else "Desativado / Nativo XML"
                    await hub.broadcast({
                        "type": "mapping_updated",
                        "profile_id": active_pid,
                        "action_id": act_id,
                        "mapping": updated_entry,
                        "mappings": pdata["mappings"]
                    })
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Tecla Guardada [{act_id}]: {updated_entry['desc']}",
                        "key_hit": combo_lbl
                    })

            elif msg_type == "save_all_mappings":
                new_maps = data.get("mappings", {})
                active_pid = profile_mgr.active_profile_id
                pdata = profile_mgr.update_bulk_mappings(new_maps, active_pid)
                engine.mappings = pdata["mappings"]

                custom_all = config.setdefault("custom_profile_mappings", {})
                custom_all[active_pid] = dict(pdata["mappings"])
                config["mappings"] = pdata["mappings"]
                save_config(config)

                await hub.broadcast({
                    "type": "profile_changed",
                    "profile_id": active_pid,
                    "profile_data": pdata
                })
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Todos os mapeamentos guardados no perfil {pdata['name']}",
                    "key_hit": "💾 CONFIG GUARDADA"
                })

            elif msg_type == "reset_profile_mappings":
                active_pid = data.get("profile") or profile_mgr.active_profile_id
                pdata = profile_mgr.reset_profile_mappings(active_pid)
                engine.mappings = pdata["mappings"]

                custom_all = config.setdefault("custom_profile_mappings", {})
                custom_all.pop(active_pid, None)
                config["mappings"] = pdata["mappings"]
                save_config(config)

                await hub.broadcast({
                    "type": "profile_changed",
                    "profile_id": active_pid,
                    "profile_data": pdata
                })
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Mapeamentos de fábrica restaurados para {pdata['name']}",
                    "key_hit": "🔄 PADRÃO RESTAURADO"
                })

            elif msg_type == "save_macro":
                macro = data.get("macro", {})
                mid = str(macro.get("id", "")).strip()
                if mid:
                    macros_dict = config.setdefault("macros", {})
                    macros_dict[mid] = {
                        "id": mid,
                        "name": str(macro.get("name", mid)).strip(),
                        "icon": str(macro.get("icon", "⚡")).strip() or "⚡",
                        "voice_text": str(macro.get("voice_text", "")).strip(),
                        "steps": macro.get("steps", [])
                    }
                    engine.update_macros(macros_dict)
                    save_config(config)
                    await hub.broadcast({"type": "macros_updated", "macros": macros_dict})
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Macro guardada: {macros_dict[mid]['name']}",
                        "key_hit": f"⚡ {len(macros_dict[mid]['steps'])} passos"
                    })

            elif msg_type == "delete_macro":
                mid = str(data.get("macro_id", "")).strip()
                macros_dict = config.setdefault("macros", {})
                if mid in macros_dict:
                    removed_name = macros_dict[mid].get("name", mid)
                    macros_dict.pop(mid, None)
                    engine.update_macros(macros_dict)
                    save_config(config)
                    await hub.broadcast({"type": "macros_updated", "macros": macros_dict})
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Macro eliminada: {removed_name}",
                        "key_hit": "🗑️ REMOVIDA"
                    })

            elif msg_type == "run_macro":
                mid = str(data.get("macro_id", "")).strip()
                if mid:
                    engine.run_macro(mid, trigger_label="Execução Manual")

            elif msg_type == "save_voice_settings":
                vs = data.get("voice_settings", {})
                prev_vs = config.get("voice_settings", {})
                custom_map = vs.get("custom_callouts", prev_vs.get("custom_callouts", {}))
                muted_list = vs.get("muted_callouts", prev_vs.get("muted_callouts", []))
                config["voice_settings"] = {
                    "enabled": bool(vs.get("enabled", True)),
                    "lang": str(vs.get("lang", "en")),
                    "rate": float(vs.get("rate", 1.05)),
                    "pitch": float(vs.get("pitch", 0.85)),
                    "volume": float(vs.get("volume", 0.85)),
                    "custom_callouts": custom_map if isinstance(custom_map, dict) else {},
                    "muted_callouts": muted_list if isinstance(muted_list, list) else [],
                }
                save_config(config)
                await hub.broadcast({"type": "voice_settings_updated", "voice_settings": config["voice_settings"]})

            elif msg_type == "set_hotas_kit":
                kit_id = str(data.get("kit_id", "warthog")).strip()
                if kit_id in HOTAS_KITS_META:
                    config["selected_hotas_kit"] = kit_id
                    save_config(config)
                    await hub.broadcast({
                        "type": "hotas_info",
                        "kits": HOTAS_KITS_META,
                        "selected_kit": kit_id,
                        "detected_kit": watcher.detected_kit,
                        "detected_devices": watcher.detected_devices
                    })
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Kit HOTAS ativo alterado para: {HOTAS_KITS_META[kit_id]['name']}",
                        "key_hit": f"🕹️ {HOTAS_KITS_META[kit_id]['brand']}"
                    })

            elif msg_type == "save_update_settings":
                config["auto_check_updates"] = bool(data.get("auto_check_updates", True))
                config["update_source"] = str(data.get("update_source", "")).strip()
                save_config(config)
                await hub.broadcast({
                    "type": "update_status",
                    **latest_update_info,
                    "auto_check_updates": config["auto_check_updates"],
                    "update_source": config["update_source"]
                })

            elif msg_type == "check_updates":
                src = str(data.get("update_source", config.get("update_source", ""))).strip()
                if src != config.get("update_source", ""):
                    config["update_source"] = src
                    save_config(config)
                res = await asyncio.to_thread(check_for_updates, src)
                latest_update_info.clear()
                latest_update_info.update(res)
                await hub.broadcast({
                    "type": "update_status",
                    **latest_update_info,
                    "auto_check_updates": config.get("auto_check_updates", True),
                    "update_source": config.get("update_source", "")
                })

            elif msg_type == "apply_update":
                dl_url = str(data.get("download_url") or latest_update_info.get("download_url", "")).strip()
                res = await asyncio.to_thread(apply_update, dl_url)
                await hub.broadcast({
                    "type": "update_applied",
                    **res
                })
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Updater: {res.get('message', '')}",
                    "key_hit": "✅ ATUALIZADO" if res.get("ok") else "⚠️ AVISO"
                })

            elif msg_type == "create_app_backup":
                bpath = await asyncio.to_thread(create_zip_backup)
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Backup ZIP criado: {os.path.basename(bpath)}",
                    "key_hit": "📦 BACKUP OK"
                })
                await hub.broadcast({
                    "type": "update_status",
                    **latest_update_info,
                    "auto_check_updates": config.get("auto_check_updates", True),
                    "update_source": config.get("update_source", ""),
                    "message": f"Backup completo guardado em backups/{os.path.basename(bpath)}"
                })

            elif msg_type == "fix_actionmaps":
                if sc_live:
                    xml_p = get_actionmaps_path(sc_live)
                    success, msg = fix_actionmaps(xml_p, fix_roll_pitch=True)
                    new_diag = diagnose_actionmaps(xml_p)
                    await hub.broadcast({"type": "diagnosis", **new_diag})
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Auto-Doctor: {msg}",
                        "key_hit": "CORREÇÃO CONCLUÍDA" if success else "AVISO PERMISSÃO"
                    })

            elif msg_type == "install_profile":
                if sc_live:
                    m_dir = get_mappings_dir(sc_live)
                    success, msg = write_profile_to_sc(m_dir)
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Instalação de Perfil: {msg}",
                        "key_hit": "PERFIL COMPLETO" if success else "CÓPIA LOCAL SALVA"
                    })

            elif msg_type == "create_backup":
                if sc_live:
                    xml_p = get_actionmaps_path(sc_live)
                    b_file = create_backup(xml_p)
                    await hub.broadcast({
                        "type": "log",
                        "timestamp": time.strftime("%H:%M:%S"),
                        "text": f"Backup Criado: {os.path.basename(b_file) if b_file else 'Requer Admin'}",
                        "key_hit": "BACKUP SALVO"
                    })

            elif msg_type == "request_diagnosis":
                if sc_live:
                    xml_p = get_actionmaps_path(sc_live)
                    new_diag = diagnose_actionmaps(xml_p)
                    await hub.broadcast({"type": "diagnosis", **new_diag})

            elif msg_type == "rescan_hardware":
                watcher.stick_slot, watcher.throttle_slot = watcher.scan_devices()
                await hub.broadcast({
                    "type": "device_status",
                    "stick": watcher.stick_slot is not None,
                    "throttle": watcher.throttle_slot is not None,
                    "stick_name": watcher.stick_name,
                    "throttle_name": watcher.throttle_name,
                    "sc_live": bool(sc_live),
                    "sc_running": sc_monitor.is_running
                })
                await hub.broadcast(_build_hotas_info_payload(auto_switch=True))

            elif msg_type == "set_deadzone":
                dz = data.get("value", 12)
                config["slew_deadzone_percent"] = dz
                save_config(config)

            elif msg_type == "set_yaw_assist":
                ya = data.get("value", False)
                config["virtual_yaw_assist"] = ya
                save_config(config)

            elif msg_type == "set_curve_type":
                ct = data.get("curve_type", "expo")
                config["curve_type"] = ct
                save_config(config)

            elif msg_type == "set_curve_exponent":
                ce = data.get("exponent", 1.8)
                config["curve_exponent"] = ce
                save_config(config)

            elif msg_type == "save_axis_calibration":
                cal = data.get("axis_calibration")
                if isinstance(cal, dict):
                    config["axis_calibration"] = cal
                    save_config(config)
                    await hub.broadcast({"type": "axis_calibration_updated", "axis_calibration": cal})

            elif msg_type == "minimize_to_tray":
                if tray_icon_ref is not None:
                    tray_icon_ref.minimize_all_to_tray()

            elif msg_type == "apply_axis_calibration_xml":
                cal = data.get("axis_calibration") or config.get("axis_calibration", {})
                if isinstance(cal, dict):
                    config["axis_calibration"] = cal
                    save_config(config)
                if sc_live:
                    xml_p = get_actionmaps_path(sc_live)
                    ok, msg = apply_axis_calibration_to_xml(xml_p, cal)
                else:
                    ok, msg = False, "Pasta StarCitizen LIVE não encontrada — calibração guardada no config.json."
                await hub.broadcast({
                    "type": "log",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "text": f"Calibração X/Y/Z: {msg}",
                    "key_hit": "✅ ANTI-DRIFT XML" if ok else "💾 GUARDADO LOCAL"
                })

    except WebSocketDisconnect:
        hub.disconnect(websocket)
    except Exception:
        hub.disconnect(websocket)


def open_desktop_window():
    """Abre o Edge em modo de janela PWA autónoma (--app) ou navegador predefinido."""
    url = f"http://{HOST}:{PORT}"
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    edge_bin = None
    for p in edge_paths:
        if os.path.exists(p):
            edge_bin = p
            break

    time.sleep(0.8)
    if edge_bin:
        subprocess.Popen([
            edge_bin,
            f"--app={url}",
            "--window-size=1360,920",
            "--window-position=60,30"
        ])
    else:
        webbrowser.open(url)


def run_glassmorphism_app():
    """Inicia os subsistemas, gera o perfil XML atualizado e abre o Dashboard."""
    sc_live = find_sc_live_dir(config.get("star_citizen_live_path"))
    if sc_live:
        write_profile_to_sc(get_mappings_dir(sc_live))
        # Tenta aplicar reparação automática se tiver permissões de escrita
        xml_p = get_actionmaps_path(sc_live)
        diag = diagnose_actionmaps(xml_p)
        if not diag.get("healthy", False):
            fix_actionmaps(xml_p, fix_roll_pitch=True)

    watcher.start()
    sc_monitor.start()
    start_axis_streamer()

    global tray_icon_ref
    tray = WarthogTrayIcon(on_open_dashboard=open_desktop_window)
    tray_icon_ref = tray
    tray.start()

    def _bg_update_check():
        if config.get("auto_check_updates", True):
            time.sleep(2.0)
            res = check_for_updates(config.get("update_source", ""))
            latest_update_info.clear()
            latest_update_info.update(res)
            broadcast_threadsafe({
                "type": "update_status",
                **latest_update_info,
                "auto_check_updates": config.get("auto_check_updates", True),
                "update_source": config.get("update_source", "")
            })

    threading.Thread(target=_bg_update_check, daemon=True).start()
    threading.Thread(target=open_desktop_window, daemon=True).start()

    print(f"\n⚡ [Warthog SC Commander Pro] Servidor ativo em http://{HOST}:{PORT}")
    uvicorn_kwargs = {"host": HOST, "port": PORT, "log_level": "warning"}
    if getattr(sys, "frozen", False) and (sys.stdout is None or not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty()):
        uvicorn_kwargs["log_config"] = None
    uvicorn.run(app, **uvicorn_kwargs)


if __name__ == "__main__":
    run_glassmorphism_app()
