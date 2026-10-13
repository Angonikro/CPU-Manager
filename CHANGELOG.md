# Changelog

## 1.1.1 ADMIN — 2026-10-13
- Die Auswahl „Systemdienste anzeigen“ wird dauerhaft gespeichert und beim nächsten Start wiederhergestellt.
- Die zuletzt gewählte Hell-/Dunkel-Darstellung bleibt erhalten.
- GitHub-Paket bereinigt: generierte Python-Cache-Dateien und alte/unnötige Release-Artefakte entfernt.
- README und Release Notes für 1.1.1 aktualisiert; Debian-Paket bleibt Architektur `all`.

## 1.1.0 ADMIN
- Messintervall (1/2/5/10/30 Sekunden) auswählbar und dauerhaft gespeichert.
- Übersicht zeigt zusätzlich Swap-Auslastung und Load Average für 1, 5 und 15 Minuten.
- CPU-Informationen, Prozessfilter, Sortierung, Dark Mode und Administratorstart beibehalten.

## 1.0.9 ADMIN
- CPU-Informationsbereich mit Modell, Architektur, physischen/logischen Kernen, Takt, Temperatur und Governor.
- Raspberry-Pi-Drosselungs-/Unterspannungsstatus über `vcgencmd get_throttled`, sofern verfügbar.

## 1.0.8 ADMIN
- Versionsnummer dauerhaft im Fenstertitel und in der Hauptüberschrift.
- CPU-Kern-Panel vergrößert und Filtererkennung für typische Kernel-Worker erweitert.

## 1.0.7 ADMIN
- Dark Mode mit kontrastreichen Tabellenfarben.
- Erkennung typischer Desktop-/Benutzer-Hintergrunddienste erweitert.

## 1.0.6 ADMIN
- Tabellenfarben beim Umschalten des Themes aktualisiert.
- Dienstfilter für System-/Desktop-Hintergrunddienste erweitert.

## 1.0.4 ADMIN
- Systemd-Systemdienste, Benutzerdienste und bekannte Desktop-Hintergrundprozesse filterbar.
- Dark-Mode-Checkbox und grafische PolicyKit-Authentifizierung.

## 1.0.3 ADMIN
- Grafische Sitzungsvariablen beim Start über `pkexec` weitergereicht.
- Fehlerausgaben in `~/.cache/cpu-manager-admin.log` protokolliert.

## 1.0.2 ADMIN
- Systemdienste ein- und ausblendbar.
- Grafische Administratorfreigabe über PolicyKit.
