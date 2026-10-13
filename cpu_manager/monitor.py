"""Process and per-core metrics using procps/psutil."""
import os
import re
import platform
import subprocess
import time
import psutil
from dataclasses import dataclass

@dataclass
class ProcessRow:
    pid: int
    name: str
    user: str
    cpu: float
    rss_mb: float
    status: str
    threads: int
    cmdline: str
    is_system_service: bool

class Monitor:
    def __init__(self):
        self._processes = {}
        self._primed = False
        self._cpu_info_static = self._read_cpu_info_static()
        self._throttle_cache = "Nicht verfügbar"
        self._throttle_checked_at = 0.0

    def prime(self):
        # Establish baselines so the first sample isn't misleading.
        psutil.cpu_percent(interval=None, percpu=True)
        for p in psutil.process_iter():
            try:
                p.cpu_percent(None)
                self._processes[p.pid] = p
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self._primed = True


    @staticmethod
    def _read_text(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read().strip().replace("\x00", "")
        except (OSError, PermissionError):
            return ""

    def _read_cpu_info_static(self):
        model = self._read_text("/proc/device-tree/model")
        cpuinfo = self._read_text("/proc/cpuinfo")
        if not model:
            for line in cpuinfo.splitlines():
                key, sep, value = line.partition(":")
                if sep and key.strip().lower() in ("model name", "hardware", "processor") and value.strip():
                    model = value.strip()
                    if key.strip().lower() == "model name":
                        break
        if not model:
            model = platform.processor() or "Unbekanntes CPU-Modell"
        arch = platform.machine() or "Unbekannt"
        logical = psutil.cpu_count(logical=True) or os.cpu_count() or 1
        physical = psutil.cpu_count(logical=False) or logical
        max_khz = self._read_text("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
        try:
            max_mhz = f"{int(max_khz) / 1000:.0f} MHz" if max_khz else "Nicht gemeldet"
        except ValueError:
            max_mhz = "Nicht gemeldet"
        governor = self._read_text("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") or "Nicht gemeldet"
        return {"model": model, "arch": arch, "physical": physical, "logical": logical, "max_mhz": max_mhz, "governor": governor}

    def cpu_info(self):
        """Return lightweight live CPU hardware/thermal information."""
        info = dict(self._cpu_info_static)
        freq = psutil.cpu_freq()
        info["current_mhz"] = f"{freq.current:.0f} MHz" if freq and freq.current else "Nicht gemeldet"
        temp = "Nicht verfügbar"
        # Linux thermal zones are generally available without extra packages on Pi OS.
        for path in ("/sys/class/thermal/thermal_zone0/temp", "/sys/devices/virtual/thermal/thermal_zone0/temp"):
            raw = self._read_text(path)
            if raw:
                try:
                    value = float(raw)
                    temp = f"{value / 1000:.1f} °C" if value > 1000 else f"{value:.1f} °C"
                    break
                except ValueError:
                    pass
        info["temperature"] = temp
        now = time.monotonic()
        if now - self._throttle_checked_at >= 10:
            self._throttle_checked_at = now
            try:
                result = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=1, check=False)
                output = (result.stdout or "").strip()
                match = re.search(r"throttled=0x([0-9a-fA-F]+)", output)
                if result.returncode == 0 and match:
                    bits = int(match.group(1), 16)
                    flags = []
                    if bits & 0x1: flags.append("Unterspannung aktuell")
                    if bits & 0x2: flags.append("Taktbegrenzung aktuell")
                    if bits & 0x4: flags.append("Drosselung aktuell")
                    if bits & 0x8: flags.append("Temperaturlimit aktuell")
                    if bits & 0x10000: flags.append("Unterspannung protokolliert")
                    if bits & 0x20000: flags.append("Taktbegrenzung protokolliert")
                    if bits & 0x40000: flags.append("Drosselung protokolliert")
                    if bits & 0x80000: flags.append("Temperaturlimit protokolliert")
                    self._throttle_cache = ", ".join(flags) if flags else "Keine Flags gemeldet"
                else:
                    self._throttle_cache = "Nicht verfügbar"
            except (OSError, subprocess.SubprocessError):
                self._throttle_cache = "Nicht verfügbar"
        info["throttling"] = self._throttle_cache
        return info

    def snapshot(self):
        per_core = psutil.cpu_percent(interval=None, percpu=True)
        total = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        rows = []
        live = {}
        for proc in psutil.process_iter():
            try:
                pid = proc.pid
                # Keep process objects to maintain per-process CPU sampling baseline.
                old = self._processes.get(pid)
                if old is None or old.create_time() != proc.create_time():
                    proc.cpu_percent(None)
                    cpu = 0.0
                else:
                    cpu = proc.cpu_percent(None)
                live[pid] = proc
                info = proc.as_dict(attrs=["name", "username", "memory_info", "status", "num_threads", "cmdline"], ad_value=None)
                rss = info["memory_info"].rss / (1024 * 1024) if info.get("memory_info") else 0.0
                # Identify processes belonging to systemd system services without invoking systemctl every second.
                try:
                    with open(f"/proc/{pid}/cgroup", "r", encoding="utf-8", errors="replace") as cg:
                        cgroup = cg.read()
                    # Include system services and user-session service units. Desktop
                    # helpers commonly run in user.slice rather than system.slice.
                    is_service = (
                        ("system.slice/" in cgroup and ".service" in cgroup)
                        or ("user@" in cgroup and (".service" in cgroup or ".scope" in cgroup))
                        or ("/app.slice/" in cgroup and (".scope" in cgroup or ".service" in cgroup))
                    )
                except (OSError, PermissionError):
                    cgroup = ""
                    is_service = False
                # Some desktop background agents are launched directly by the
                # session and do not have a .service cgroup. Classify only known
                # service/agent naming patterns, not ordinary user applications.
                pname = (info.get("name") or "").lower()
                service_markers = (
                    "akonadi_", "akonadi-", "polkit-", "tracker-miner", "gvfsd-",
                    "xdg-document-portal", "xdg-permission-store", "pipewire", "wireplumber",
                    "dbus-daemon", "at-spi-bus", "evolution-source-registry", "evolution-calendar-factory",
                    "gnome-keyring-", "pulseaudio", "bluetoothd", "networkmanager",
                    # Desktop session and helper/background processes commonly
                    # visible on Raspberry Pi OS / MATE desktops.
                    "mate-session", "mate-settings-daemon", "mate-screensaver",
                    "mate-panel", "mate-volume-control-status-icon",
                    "blueman-applet", "blueman-tray", "nm-applet", "polkit-mate-authentication-agent",
                    "qtwebengineprocess", "akonadiserver", "kalendarac", "compiz-session-helper",
                    "caja", "compiz", "emerald", "fusion-icon", "pasystray", "notify-osd",
                    # Additional helpers observed on Raspberry Pi OS / MATE / KDE.
                    "mate-power-manager", "kunifiedpush-distributor", "sddm-helper",
                    "xdg-desktop-portal-gtk", "xdg-desktop-portal", "kdedconnectd",
                    "kworker/", "ksoftirqd/", "migration/", "watchdog/", "systemd",
                    "avfsd", "systemd-journald", "systemd-logind", "systemd-udevd",
                    "cron", "rsyslogd", "udisksd", "upowerd", "accounts-daemon",
                    "colord", "cupsd", "avahi-daemon", " ModemManager".strip(),
                )
                if any(marker.lower() in pname for marker in service_markers):
                    is_service = True
                # Kernel worker threads have no user-space command line and names
                # such as kthreadd, rcu_preempt, ksoftirqd/0, kworker/0:1-events,
                # migration/0, watchdog/0, cpuhp/0 and idle_inject/0.
                kernel_thread_patterns = (
                    r"^kthreadd$", r"^kworker(?:/|$)", r"^ksoftirqd(?:/|$)",
                    r"^rcu(?:_|/|$)", r"^migration(?:/|$)", r"^watchdog(?:/|$)",
                    r"^cpuhp(?:/|$)", r"^idle_inject(?:/|$)", r"^kcompactd(?:/|$)",
                    r"^kswapd(?:/|$)", r"^oom_reaper$", r"^writeback$",
                    r"^kblockd$", r"^khugepaged$", r"^kintegrityd$", r"^kcryptd(?:/|$)",
                    r"^scsi_eh_(?:\d+|.*)$", r"^jbd2(?:/|$)", r"^ext4-rsv-conver",
                    r"^irq/", r"^.*-events(?:/|$)",
                )
                cmdline = info.get("cmdline") or []
                if any(re.search(pattern, pname) for pattern in kernel_thread_patterns):
                    is_service = True
                # PID 2+ kernel threads usually expose an empty command line.
                # Restrict this fallback to root-owned processes with no cmdline,
                # and verify that /proc/PID/exe is unavailable to avoid hiding
                # ordinary root-run applications.
                if not cmdline and (info.get("username") or "") == "root":
                    try:
                        os.readlink(f"/proc/{pid}/exe")
                    except (OSError, PermissionError):
                        is_service = True
                # Some desktop-session helpers have names that are not attached to
                # a systemd service unit. Hide these from the default process list,
                # but retain them in the list when "Systemdienste anzeigen" is on.
                rows.append(ProcessRow(
                    pid=pid, name=info.get("name") or "?", user=info.get("username") or "?",
                    cpu=max(0.0, cpu), rss_mb=rss, status=info.get("status") or "?",
                    threads=info.get("num_threads") or 0,
                    cmdline=" ".join(info.get("cmdline") or []),
                    is_system_service=is_service
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
                continue
        self._processes = live
        rows.sort(key=lambda r: (-r.cpu, -r.rss_mb, r.pid))
        return per_core, total, vm, rows

    @staticmethod
    def affinity(pid):
        try:
            return sorted(psutil.Process(pid).cpu_affinity())
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError, OSError):
            return []
