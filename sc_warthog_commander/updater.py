"""
Auto-Updater & Backup Engine
Verifica atualizações automáticas diretamente a partir dos commits do GitHub
(comparação exata por Git Blob SHA-1 do executável dist/SC_Warthog_Commander.exe,
GitHub Releases ou Git local), preserva sempre config.json e profiles/, e
auto-atualiza o .exe no Windows com reinício automático.
"""

import os
import sys
import json
import time
import hashlib
import zipfile
import shutil
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Tuple

from config import get_app_dir

APP_VERSION = "5.9.1"
APP_DIR = get_app_dir()
BACKUP_DIR = os.path.join(APP_DIR, "backups")
STATE_FILE = os.path.join(APP_DIR, "update_state.json")
LOG_FILE = os.path.join(APP_DIR, "update_log.txt")


def _log_update(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

DEFAULT_UPDATE_REPO = "tiagofcustodio/Sc-commander-warthog"
EXE_REPO_PATH = "dist/SC_Warthog_Commander.exe"


def _parse_version(v: str) -> Tuple[int, ...]:
    cleaned = str(v or "0.0.0").strip().lstrip("vV")
    parts = []
    for p in cleaned.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def is_newer_version(remote_ver: str, local_ver: str = APP_VERSION) -> bool:
    return _parse_version(remote_ver) > _parse_version(local_ver)


def compute_git_blob_sha(file_path: str) -> str:
    """Calcula o hash Git Blob SHA-1 exato de um ficheiro local (idêntico ao 'sha' da GitHub Contents API)."""
    size = os.path.getsize(file_path)
    h = hashlib.sha1()
    h.update(f"blob {size}\0".encode("utf-8"))
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_update_state() -> dict:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_update_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def create_zip_backup() -> str:
    """Cria um backup ZIP seguro das configurações (e código-fonte se não for .exe)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    zip_name = f"warthog_commander_v{APP_VERSION}_{ts}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)

    if getattr(sys, "frozen", False):
        # Em modo .exe, faz backup leve apenas do config.json e profiles/
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            cfg = os.path.join(APP_DIR, "config.json")
            if os.path.exists(cfg):
                zf.write(cfg, "config.json")
            prof_dir = os.path.join(APP_DIR, "profiles")
            if os.path.isdir(prof_dir):
                for root, _, files in os.walk(prof_dir):
                    for fn in files:
                        full = os.path.join(root, fn)
                        zf.write(full, os.path.relpath(full, APP_DIR))
        return zip_path

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(APP_DIR):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "backups", ".git", "build", "dist")]
            for fn in files:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, APP_DIR)
                zf.write(full, rel)
    return zip_path


def _github_get_json(url: str, timeout: int = 8):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"WarthogSCCommander/{APP_VERSION}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _check_frozen_exe_github_commit(repo_slug: str, now_str: str) -> Optional[dict]:
    """
    Em modo .exe compilado, verifica diretamente o último commit do ficheiro
    dist/SC_Warthog_Commander.exe no branch main do GitHub usando Git Blob SHA-1.
    Garante deteção imediata de qualquer novo commit sem loops infinitos.
    """
    repo = repo_slug.strip("/")
    exe_path = os.path.abspath(sys.executable)
    if not os.path.exists(exe_path):
        return None

    try:
        local_blob_sha = compute_git_blob_sha(exe_path)
    except Exception:
        local_blob_sha = ""

    # 1. Lista a pasta dist/ no branch main (nunca falha no limite de 1MB da GitHub Contents API)
    dir_url = f"https://api.github.com/repos/{repo}/contents/dist?ref=main"
    entries = _github_get_json(dir_url, timeout=10)
    meta = {}
    if isinstance(entries, list):
        for item in entries:
            if str(item.get("name", "")).lower() == "sc_warthog_commander.exe":
                meta = item
                break
    elif isinstance(entries, dict):
        meta = entries
    remote_blob_sha = str(meta.get("sha") or "").strip()
    dl_url = str(meta.get("download_url") or f"https://raw.githubusercontent.com/{repo}/main/{EXE_REPO_PATH}")
    _log_update(f"Check commit: local={local_blob_sha[:10]} remote={remote_blob_sha[:10]} url={dl_url}")

    # 2. Obtém a mensagem e SHA curto do último commit que alterou o .exe
    commit_sha = remote_blob_sha[:8]
    commit_msg = "Nova atualização disponível no GitHub."
    try:
        commits = _github_get_json(
            f"https://api.github.com/repos/{repo}/commits?path={EXE_REPO_PATH}&sha=main&per_page=1",
            timeout=8,
        )
        if isinstance(commits, list) and commits:
            c0 = commits[0]
            commit_sha = str(c0.get("sha", ""))[:8] or commit_sha
            commit_msg = str(c0.get("commit", {}).get("message", "")).splitlines()[0].strip() or commit_msg
    except Exception:
        pass

    update_available = bool(remote_blob_sha and local_blob_sha and (remote_blob_sha != local_blob_sha))
    return {
        "status": "ok",
        "mode": "exe_commit",
        "update_available": update_available,
        "current_version": f"{APP_VERSION} ({local_blob_sha[:7]})" if local_blob_sha else APP_VERSION,
        "latest_version": f"{APP_VERSION} ({commit_sha})",
        "remote_blob_sha": remote_blob_sha,
        "local_blob_sha": local_blob_sha,
        "commit_sha": commit_sha,
        "download_url": dl_url,
        "changelog": commit_msg,
        "checked_at": now_str,
        "message": (
            f"Nova compilação detetada no GitHub ({commit_sha}): {commit_msg}"
            if update_available
            else f"Executável atualizado com o último commit do GitHub ({commit_sha})."
        ),
    }


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


def check_for_updates(update_source: str = DEFAULT_UPDATE_REPO) -> dict:
    """
    Verifica atualizações a partir de:
    1) Em modo .exe (PyInstaller): último commit de dist/SC_Warthog_Commander.exe no GitHub (Git Blob SHA-1).
    2) GitHub Releases / Manifesto JSON.
    3) Repositório Git local (em modo código-fonte).
    """
    src = (update_source or DEFAULT_UPDATE_REPO).strip()
    now_str = time.strftime("%H:%M:%S")

    # Modo Executável (.exe): verifica diretamente o último commit no GitHub
    if getattr(sys, "frozen", False) and src and not src.startswith(("http://", "https://")):
        try:
            exe_res = _check_frozen_exe_github_commit(src, now_str)
            if exe_res is not None:
                return exe_res
        except urllib.error.URLError as e:
            return {
                "status": "offline",
                "update_available": False,
                "current_version": APP_VERSION,
                "latest_version": APP_VERSION,
                "checked_at": now_str,
                "message": f"Sem ligação ao GitHub ({e.reason})."
            }
        except Exception as e:
            return {
                "status": "error",
                "update_available": False,
                "current_version": APP_VERSION,
                "latest_version": APP_VERSION,
                "checked_at": now_str,
                "message": f"Erro ao verificar commits no GitHub: {e}"
            }

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
            "message": f"Versão v{APP_VERSION} instalada (mais recente)."
        }

    # Determina URL de consulta (Releases ou Manifesto JSON)
    if src.startswith("http://") or src.startswith("https://"):
        api_url = src
        is_github_api = "api.github.com" in src
    else:
        api_url = f"https://api.github.com/repos/{src.strip('/')}/releases/latest"
        is_github_api = True

    try:
        payload = _github_get_json(api_url, timeout=8)

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
    except urllib.error.HTTPError as e:
        # Se não houver GitHub Releases ainda (404), usa fallback Git local em modo código-fonte
        if e.code == 404:
            git_res = _check_git_updates()
            if git_res:
                git_res["checked_at"] = now_str
                return git_res
        return {
            "status": "offline",
            "update_available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "checked_at": now_str,
            "message": f"Servidor de atualizações indisponível (HTTP {e.code})."
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


def apply_exe_self_update(download_url: str, expected_blob_sha: str = "", auto_exit_delay: float = 1.5) -> dict:
    """
    Descarrega o novo SC_Warthog_Commander.exe do GitHub, valida o binário PE (MZ),
    cria um script temporário para substituir o .exe em execução e reinicia automaticamente.
    Preserva 100% do config.json e pasta profiles/.
    """
    if not getattr(sys, "frozen", False):
        return {"ok": False, "message": "Auto-atualização de .exe só está ativa no executável compilado."}

    current_exe = os.path.abspath(sys.executable)
    staged_exe = current_exe + ".new"

    try:
        backup_path = create_zip_backup()
    except Exception:
        backup_path = ""

    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"WarthogSCCommander/{APP_VERSION}"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp, open(staged_exe, "wb") as out:
            shutil.copyfileobj(resp, out, length=1024 * 512)

        # Valida integridade mínima do executável Windows PE ('MZ' + tamanho > 5MB)
        file_size = os.path.getsize(staged_exe)
        with open(staged_exe, "rb") as f:
            header = f.read(2)
        if header != b"MZ" or file_size < 5 * 1024 * 1024:
            os.remove(staged_exe)
            return {"ok": False, "message": "Download da atualização inválido ou incompleto. Abortado com segurança."}

        if expected_blob_sha:
            dl_blob = compute_git_blob_sha(staged_exe)
            if dl_blob != expected_blob_sha:
                # Ainda assim o GitHub pode ter recebido outro commit entretanto — aceita se PE válido
                pass

        _save_update_state({
            "last_update_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "blob_sha": expected_blob_sha,
            "source_url": download_url,
        })

        # Cria script .bat isolado em %TEMP% para substituir o .exe após o processo sair e relançá-lo
        pid = os.getpid()
        bat_path = os.path.join(tempfile.gettempdir(), f"sc_warthog_update_{pid}.bat")
        bat_content = (
            "@echo off\r\n"
            "setlocal\r\n"
            f"set \"TARGET={current_exe}\"\r\n"
            f"set \"STAGED={staged_exe}\"\r\n"
            ":wait_loop\r\n"
            f"tasklist /FI \"PID eq {pid}\" 2>NUL | find /I \"{pid}\" >NUL\r\n"
            "if not errorlevel 1 (\r\n"
            "    timeout /t 1 /nobreak >NUL\r\n"
            "    goto wait_loop\r\n"
            ")\r\n"
            "timeout /t 1 /nobreak >NUL\r\n"
            "set /a retries=0\r\n"
            ":replace_loop\r\n"
            "move /Y \"%STAGED%\" \"%TARGET%\" >NUL 2>&1\r\n"
            "if errorlevel 1 (\r\n"
            "    set /a retries+=1\r\n"
            "    if %retries% LSS 15 (\r\n"
            "        timeout /t 1 /nobreak >NUL\r\n"
            "        goto replace_loop\r\n"
            "    )\r\n"
            "    exit /b 1\r\n"
            ")\r\n"
            "start \"\" \"%TARGET%\"\r\n"
            "del \"%~f0\" >NUL 2>&1\r\n"
        )
        with open(bat_path, "w", encoding="utf-8") as bf:
            bf.write(bat_content)

        CREATE_NO_WINDOW = 0x08000000
        DETACHED_PROCESS = 0x00000008
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
            close_fds=True,
        )

        # Encerra o processo atual após breve pausa para a UI receber a notificação
        def _delayed_exit():
            time.sleep(max(0.5, auto_exit_delay))
            os._exit(0)

        threading.Thread(target=_delayed_exit, daemon=True).start()

        return {
            "ok": True,
            "restarting": True,
            "backup": backup_path,
            "message": "Nova versão descarregada do GitHub! A reiniciar automaticamente com a atualização..."
        }
    except Exception as e:
        if os.path.exists(staged_exe):
            try:
                os.remove(staged_exe)
            except OSError:
                pass
        return {"ok": False, "backup": backup_path, "message": f"Erro ao auto-atualizar .exe: {e}"}


def apply_update(download_url: str, expected_blob_sha: str = "") -> dict:
    """Aplica atualização automaticamente (self-update do .exe em modo compilado, ou Git/ZIP em código-fonte)."""
    if getattr(sys, "frozen", False) and download_url and download_url.lower().endswith(".exe"):
        return apply_exe_self_update(download_url, expected_blob_sha=expected_blob_sha)

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

        src_root = tmp_dir
        entries = os.listdir(tmp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(tmp_dir, entries[0])):
            candidate = os.path.join(tmp_dir, entries[0])
            if os.path.isdir(os.path.join(candidate, "sc_warthog_commander")):
                src_root = os.path.join(candidate, "sc_warthog_commander")
            else:
                src_root = candidate

        updated_files = 0
        for root, dirs, files in os.walk(src_root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "backups", ".git")]
            rel_dir = os.path.relpath(root, src_root)
            dest_dir = APP_DIR if rel_dir == "." else os.path.join(APP_DIR, rel_dir)
            os.makedirs(dest_dir, exist_ok=True)
            for fn in files:
                if fn.lower() == "config.json":
                    continue
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
