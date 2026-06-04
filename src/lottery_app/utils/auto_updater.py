"""
Auto-update helpers for the lottery application.

Downloads the latest GitHub release zip in a background thread, extracts it
to a staging directory, then writes and launches a platform-specific updater
script that replaces the running installation after the app exits.

Only functional when running as a PyInstaller executable.
"""

import os
import platform
import stat
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

import requests

from lottery_app.utils.version_check import GITHUB_API_URL

# Paths relative to the install directory that are never overwritten during update.
_PROTECTED = frozenset([
    ".env",
    "instance_folder",
    os.path.join("lottery_app", "config.json"),
])

_state: dict = {
    "status": "idle",   # idle | downloading | ready | applying | error
    "downloaded": 0,
    "total": 0,
    "error": None,
    "_staging": None,
}
_lock = threading.Lock()


def get_state() -> dict:
    """Return a copy of the public update state (private keys excluded)."""
    with _lock:
        return {k: v for k, v in _state.items() if not k.startswith("_")}


def _set(**kwargs) -> None:
    with _lock:
        _state.update(kwargs)


def _get_install_dir() -> str:
    return os.path.dirname(sys.executable)


def _asset_name() -> str:
    system = platform.system()
    if system == "Windows":
        return "lottery_app-windows.zip"
    if system == "Darwin":
        return "lottery_app-macos.zip"
    raise RuntimeError(f"Auto-update is not supported on {system}.")


def _fetch_asset_url() -> str:
    resp = requests.get(
        GITHUB_API_URL,
        timeout=10,
        headers={"Accept": "application/vnd.github+json"},
    )
    resp.raise_for_status()
    data = resp.json()
    name = _asset_name()
    for asset in data.get("assets", []):
        if asset["name"] == name:
            return asset["browser_download_url"]
    raise RuntimeError(f"Release asset '{name}' not found in the latest GitHub release.")


def start_download() -> None:
    """Start downloading the update zip in a background thread.

    No-op if a download is already running or the update is staged and ready.
    """
    with _lock:
        if _state["status"] in ("downloading", "ready", "applying"):
            return
        _state.update(status="downloading", downloaded=0, total=0, error=None, _staging=None)

    threading.Thread(target=_download_worker, daemon=True, name="update-dl").start()


def _download_worker() -> None:
    try:
        url = _fetch_asset_url()
        staging = tempfile.mkdtemp(prefix="lottery_update_")
        zip_path = os.path.join(staging, "update.zip")

        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        _set(total=total)

        downloaded = 0
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    _set(downloaded=downloaded)

        extract_dir = os.path.join(staging, "contents")
        os.makedirs(extract_dir)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        os.remove(zip_path)

        # The macOS zip wraps all files inside a lottery_app/ subdirectory;
        # the Windows zip places files directly at the root.
        if platform.system() == "Darwin":
            sub = os.path.join(extract_dir, "lottery_app")
            content_dir = sub if os.path.isdir(sub) else extract_dir
        else:
            content_dir = extract_dir

        _set(status="ready", _staging=content_dir)

    except Exception as exc:  # pylint: disable=broad-except
        _set(status="error", error=str(exc))


# ── Updater scripts ──────────────────────────────────────────────────────────

def _write_windows_ps1(staging: str, install: str) -> str:
    """Write a PowerShell script that copies new files while skipping protected paths."""
    ps1_path = os.path.join(tempfile.gettempdir(), "lottery_updater.ps1")
    protected_block = "\n".join(f'  "{p}",' for p in _PROTECTED)
    script = f"""\
$staging = @'
{staging}
'@.Trim()
$install = @'
{install}
'@.Trim()
$protected = @(
{protected_block}
)

Get-ChildItem -Path $staging -Recurse | ForEach-Object {{
    $rel = $_.FullName.Substring($staging.Length).TrimStart('\\')
    $skip = $false
    foreach ($p in $protected) {{
        if ($rel -eq $p -or $rel.StartsWith($p + '\\')) {{
            $skip = $true; break
        }}
    }}
    if (-not $skip -and -not $_.PSIsContainer) {{
        $dest = Join-Path $install $rel
        $dir  = Split-Path $dest
        if (-not (Test-Path $dir)) {{ New-Item -ItemType Directory $dir -Force | Out-Null }}
        Copy-Item $_.FullName $dest -Force
    }}
}}

Start-Process (Join-Path $install "lottery_app.exe")
Remove-Item $staging -Recurse -Force
Remove-Item $PSCommandPath -Force
"""
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(script)
    return ps1_path


def _write_windows_bat(ps1_path: str) -> str:
    """Write a .bat launcher that waits 3 s then runs the PowerShell updater."""
    bat_path = os.path.join(tempfile.gettempdir(), "lottery_updater.bat")
    bat = (
        "@echo off\n"
        "timeout /t 3 /nobreak >nul\n"
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "{ps1_path}"\n'
        "(goto) 2>nul & del \"%~f0\"\n"
    )
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat)
    return bat_path


def _write_macos_sh(staging: str, install: str) -> str:
    """Write a shell script that rsyncs new files while skipping protected paths."""
    sh_path = os.path.join(tempfile.gettempdir(), "lottery_updater.sh")
    excludes = " \\\n  ".join(f"--exclude='{p}'" for p in _PROTECTED)
    exe = os.path.join(install, "lottery_app")
    script = (
        "#!/bin/bash\n"
        "sleep 3\n"
        f'rsync -a \\\n  {excludes} \\\n  "{staging}/" "{install}/"\n'
        f'chmod +x "{exe}"\n'
        f'open "{exe}"\n'
        f'rm -rf "{staging}"\n'
        'rm -f "$0"\n'
    )
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(script)
    os.chmod(sh_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
    return sh_path


def apply_update() -> None:
    """Write and launch the platform updater script, then exit the app.

    Raises RuntimeError if the download is not in the ``ready`` state.
    The app process exits ~0.5 s after this returns so the HTTP response
    can be flushed to the client first.
    """
    with _lock:
        if _state["status"] != "ready":
            raise RuntimeError("Update is not ready to apply.")
        staging = _state["_staging"]
        _state["status"] = "applying"

    install = _get_install_dir()

    if platform.system() == "Windows":
        ps1 = _write_windows_ps1(staging, install)
        bat = _write_windows_bat(ps1)
        subprocess.Popen(
            ["cmd.exe", "/c", bat],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
    else:
        sh = _write_macos_sh(staging, install)
        subprocess.Popen(["/bin/bash", sh], close_fds=True)

    def _exit():
        time.sleep(0.5)
        os._exit(0)  # pylint: disable=protected-access

    threading.Thread(target=_exit, daemon=True, name="update-exit").start()
