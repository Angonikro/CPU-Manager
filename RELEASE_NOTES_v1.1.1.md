# CPU Manager 1.1.1 ADMIN

## Neu und verbessert
- Die Checkbox „Systemdienste anzeigen“ merkt sich ihren Zustand dauerhaft. Die zuletzt gewählte Einstellung wird beim nächsten Start wieder geladen.
- Die Hell-/Dunkel-Auswahl wird ebenfalls dauerhaft gespeichert.
- Das Messintervall bleibt wie in 1.1.0 gespeichert.
- Release-Paket bereinigt; Python-Cache-Dateien und überflüssige Build-Artefakte sind nicht enthalten.

## Installation

Debian-/Raspberry-Pi-OS-Paket:

```bash
sudo apt install ./cpu-manager_1.1.1_all.deb
```

Für den Quellcode siehe `README.md`. Die App verwendet System-Python; eine virtuelle Umgebung ist nicht erforderlich.
