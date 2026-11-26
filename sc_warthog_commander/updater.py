"""
Auto-Updater & Backup Engine
Verifica atualizações automáticas (GitHub Releases / Manifesto JSON / Git),
cria backups ZIP seguros preservando config.json e aplica atualizações com 1 clique.
"""

import os
import json
import time
import zipfile
import shutil
import subprocess
import urllib.request
import urllib.error
from typing import Tuple

from config import get_app_dir

APP_VERSION = "5.6.0"
APP_DIR = get_app_dir()
BACKUP_DIR = os.path.join(APP_DIR, "backups")


def _parse_version(v: str) -> Tuple[int, ...]:
    cleaned = str(v or "0.0.0").strip().lstrip("vV")
    parts = []
    for p in cleaned.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def is_newer_version(remote_ver: str, local_ver: str = APP_VERSION) -> bool:
    return _parse_version(remote_ver) > _parse_version(local_ver)


def create_zip_backup() -> str:
    """Cria um backup ZIP completo da aplicação em backups/ antes de atualizar."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    zip_name = f"warthog_commander_v{APP_VERSION}_{ts}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(APP_DIR):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "backups", ".git")]
            for fn in files:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, APP_DIR)
                zf.write(full, rel)
    return zip_path


def _check_git_updates() -> dict:
    """Tenta verificar atualizações via git se a pasta for um repositório Git."""
    git_dir = os.path.join(APP_DIR, ".git")
    parent_git = os.path.join(os.path.dirname(APP_DIR), ".git")
    repo_root = APP_DIR if os.path.isdir(git_dir) else (os.path.dirname(APP_DIR) if os.path.isdir(parent_git) else None)
    if not repo_root:
        return {}
    try:
        subprocess.run(["git", "-C", repo_root, "fetch", "--quiet"], timeout=8, check=False, capture_output=True)
        res = subprocess.run(["git", "-C", repo_root, "rev-list", "--count", "HEAD..@{u}"], timeout=5, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip().isdigit():
            behind = int(res.stdout.strip())
            if behind > 0:
                return {
                    "update_available": True,
                    "source": "git",
                    "current_version": APP_VERSION,
                    "latest_version": f"{APP_VERSION}+{behind} commits",
                    "changelog": f"Existem {behind} novas atualizações disponíveis no repositório Git.",
                    "download_url": "git://pull"
                }
            return {
                "update_available": False,
                "source": "git",
                "current_version": APP_VERSION,
                "latest_version": APP_VERSION,
                "message": "Repositório Git está 100% atualizado."
            }
    except Exception:
        pass
    return {}


DEFAULT_UPDATE_REPO = "tiagofcustodio/Sc-commander-warthog"


def check_for_updates(update_source: str = DEFAULT_UPDATE_REPO) -> dict:
    """
    Verifica atualizações a partir de:
    1) URL de manifesto JSON (ex: https://.../version.json)
    2) Repositório GitHub (ex: utilizador/repositorio)
    3) Repositório Git local (se existir)
    """
    src = (update_source or DEFAULT_UPDATE_REPO).strip()
    now_str = time.strftime("%H:%M:%S")

    if not src:
        git_res = _check_git_updates()
        if git_res:
            git_res["checked_at"] = now_str
            return git_res
        return {
            "status": "ok",
            "update_available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "checked_at": now_str,
            "message": f"Versão v{APP_VERSION} instalada (mais recente). Configura um repositório GitHub ou URL de manifesto JSON para receber atualizações remotas automáticas."
        }

    # Determina URL de consulta
    if src.startswith("http://") or src.startswith("https://"):
        api_url = src
        is_github_api = "api.github.com" in src
    else:
        # Formato owner/repo do GitHub
        api_url = f"https://api.github.com/repos/{src.strip('/')}/releases/latest"
        is_github_api = True

    try:
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": f"WarthogSCCommander/{APP_VERSION}", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        if is_github_api:
            latest = str(payload.get("tag_name") or payload.get("name") or APP_VERSION).lstrip("vV")
            changelog = payload.get("body") or "Nova versão disponível no GitHub."
            dl_url = payload.get("zipball_url") or ""
            for asset in payload.get("assets", []):
                if str(asset.get("name", "")).endswith(".zip"):
                    dl_url = asset.get("browser_download_url", dl_url)
                    break
        else:
            latest = str(payload.get("version") or APP_VERSION).lstrip("vV")
            changelog = payload.get("changelog") or "Atualização disponível."
            dl_url = payload.get("download_url") or ""

        newer = is_newer_version(latest, APP_VERSION)
        return {
            "status": "ok",
            "update_available": newer,
            "current_version": APP_VERSION,
            "latest_version": latest,
            "download_url": dl_url,
            "changelog": changelog,
            "checked_at": now_str,
            "message": f"Nova versão v{latest} disponível!" if newer else f"Já estás na versão mais recente (v{APP_VERSION})."
        }
    except urllib.error.URLError as e:
        return {
            "status": "offline",
            "update_available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "checked_at": now_str,
            "message": f"Não foi possível contactar o servidor de atualizações ({e.reason})."
        }
    except Exception as e:
        return {
            "status": "error",
            "update_available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "checked_at": now_str,
            "message": f"Erro ao verificar atualizações: {e}"
        }


def apply_update(download_url: str) -> dict:
    """Cria backup ZIP seguro e aplica a atualização (via Git pull ou download ZIP)."""
    try:
        backup_path = create_zip_backup()
    except Exception as e:
        return {"ok": False, "message": f"Falha ao criar backup de segurança: {e}"}

    if download_url == "git://pull":
        repo_root = APP_DIR if os.path.isdir(os.path.join(APP_DIR, ".git")) else os.path.dirname(APP_DIR)
        try:
            res = subprocess.run(["git", "-C", repo_root, "pull", "--ff-only"], timeout=20, capture_output=True, text=True)
            if res.returncode == 0:
                return {"ok": True, "backup": backup_path, "message": "Atualização Git aplicada com sucesso! Reinicia o programa para carregar a nova versão."}
            return {"ok": False, "backup": backup_path, "message": f"Erro no git pull: {res.stderr.strip()}"}
        except Exception as e:
            return {"ok": False, "backup": backup_path, "message": f"Erro ao executar git pull: {e}"}

    if not download_url or not (download_url.startswith("http://") or download_url.startswith("https://")):
        return {"ok": False, "backup": backup_path, "message": "URL de download de atualização inválido ou não configurado."}

    tmp_zip = os.path.join(BACKUP_DIR, f"incoming_update_{int(time.time())}.zip")
    tmp_dir = os.path.join(BACKUP_DIR, f"extracted_{int(time.time())}")
    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": f"WarthogSCCommander/{APP_VERSION}"})
        with urllib.request.urlopen(req, timeout=25) as resp, open(tmp_zip, "wb") as out:
            shutil.copyfileobj(resp, out)

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(tmp_dir)

        # Localiza raiz dos ficheiros (suporta zipball do GitHub com pasta única)
        src_root = tmp_dir
        entries = os.listdir(tmp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
            candidate = os.path.join(tmp_dir, entries[0])
            if os.path.isdir(os.path.join(candidate, "sc_warthog_commander")):
                src_root = os.path.join(candidate, "sc_warthog_commander")
            else:
                src_root = candidate

        # Copia ficheiros preservando config.json do utilizador
        updated_files = 0
        for root, dirs, files in os.walk(src_root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "backups", ".git")]
            rel_dir = os.path.relpath(root, src_root)
            dest_dir = APP_DIR if rel_dir == "." else os.path.join(APP_DIR, rel_dir)
            os.makedirs(dest_dir, exist_ok=True)
            for fn in files:
                if fn.lower() == "config.json":
                    continue  # Nunca sobrescreve as teclas/perfis do utilizador!
                shutil.copy2(os.path.join(root, fn), os.path.join(dest_dir, fn))
                updated_files += 1

        return {
            "ok": True,
            "backup": backup_path,
            "message": f"Atualização aplicada ({updated_files} ficheiros atualizados, config.json preservado)! Reinicia o programa para aplicar."
        }
    except Exception as e:
        return {"ok": False, "backup": backup_path, "message": f"Erro ao aplicar atualização: {e}"}
    finally:
        if os.path.exists(tmp_zip):
            try: os.remove(tmp_zip)
            except OSError: pass
        if os.path.exists(tmp_dir):
            try: shutil.rmtree(tmp_dir, ignore_errors=True)
            except OSError: pass
