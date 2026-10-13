"""Careful process actions. No shell interpolation is used."""
import os
import signal
import subprocess
import psutil

def process_details(pid):
    p = psutil.Process(pid)
    return {
        "pid": p.pid,
        "name": p.name(),
        "exe": p.exe() if p.exe() else "",
        "cmdline": p.cmdline(),
        "username": p.username(),
        "status": p.status(),
        "create_time": p.create_time(),
        "ppid": p.ppid(),
        "cwd": p.cwd() if p.is_running() else "",
    }

def terminate_process(pid):
    p = psutil.Process(pid)
    # Graceful request first; UI handles waiting and force-kill separately.
    p.terminate()

def kill_process(pid):
    psutil.Process(pid).kill()

def restart_process(pid):
    """Restart only a recognized systemd service; never guess a GUI process command."""
    p = psutil.Process(pid)
    if p.pid <= 1:
        raise ValueError("PID 1 bzw. ein grundlegender Systemprozess darf nicht neu gestartet werden.")
    # Resolve a systemd unit from cgroup membership.
    try:
        cgroup = open(f"/proc/{pid}/cgroup", "r", encoding="utf-8", errors="replace").read()
    except OSError:
        cgroup = ""
    unit = None
    for line in cgroup.splitlines():
        tail = line.rsplit(":", 1)[-1]
        for part in tail.split("/"):
            if part.endswith(".service") and not part.startswith("user@"):
                unit = part
                break
        if unit:
            break
    if not unit:
        raise ValueError("Für diesen Prozess wurde keine eindeutige systemd-Service-Unit gefunden. Ein normaler Prozess wird nicht automatisch neu gestartet, da sein Startbefehl unbekannt sein kann.")
    if not unit.endswith(".service") or any(ch in unit for ch in " \t\n;|&$`"):
        raise ValueError("Ungültige Service-Unit.")
    result = subprocess.run(
        ["systemctl", "restart", unit],
        capture_output=True, text=True, timeout=30, check=False
    )
    if result.returncode:
        msg = (result.stderr or result.stdout or "systemctl meldete einen Fehler").strip()
        raise RuntimeError(msg)
    return unit

def is_root():
    return os.geteuid() == 0
