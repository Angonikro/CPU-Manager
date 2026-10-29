# Changelog

## 1.1.5
- Startet bei aktivierter Tray-Option verborgen im System-Tray.
- Desktop-Datei nutzt `Exec=sudo /usr/bin/cpu-manager`.

## 1.1.4
- Tray-Einstellung bleibt beim Beenden über das Tray-Menü erhalten.
- Beenden schließt die Anwendung, ohne die gespeicherte Auswahl zu deaktivieren.
- CPU-Auslastungsanzeige und GTK-3-Tray-Verfahren unverändert.

## 1.1.3
- Tray-Symbol zeigt CPU-Chip und aktuelle Auslastung als Prozentwert.
- Tray-Anzeige wird zusammen mit der CPU-Messung aktualisiert; Warnfarbe ab 80 % und Tooltip mit Live-Wert.
- Bestehende GTK-3-`Gtk.StatusIcon`-Tray-Methode und übrige CPU-Manager-Funktionen beibehalten.

# Changelog

## 1.1.2
- Added optional GTK 3 system-tray icon using the same `Gtk.StatusIcon` method as LunaKalender.
- Left-click toggles the main window; right-click opens the show/quit menu.
- Closing the window hides it to the tray when tray mode is enabled.
- Added GTK 3 Python bindings as Debian package dependencies.

1.1.1 ADMIN — 2026-10-13
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
