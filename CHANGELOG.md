## 1.1.8 – Deutsche Oberfläche
- Bestätigungsfenster verwenden ausdrücklich die Schaltflächen „Ja“ und „Nein“, auch ohne deutsche Qt-Sprachpakete.
- Englische sichtbare Beschriftungen und Prozessstatus ins Deutsche übersetzt.
- Hintergrundaktionen aus 1.1.7 beibehalten.

# Changelog

## 1.1.7 – Prozessaktionen im Hintergrund
- Beenden, Sofort beenden und systemd-Neustart werden in eigenen Qt-Hintergrundthreads ausgeführt.
- Die Oberfläche bleibt während laufender Prozessaktionen reaktionsfähig; Status und Fehlermeldungen erscheinen nach Abschluss.
- Aktionsschaltflächen werden während einer laufenden Verwaltungsaktion gegen doppelte Aufrufe gesperrt.
- Bestehende Prozessschutz- und Berechtigungslogik bleibt erhalten.

## 1.1.6 – Native Qt-System-Tray
- GTK-3-StatusIcon und GTK-Hintergrundthread durch Qt `QSystemTrayIcon` ersetzt.
- CPU-Chip-Symbol mit Live-Prozentwert, Warnfarbe ab 80 %, Tooltip und Tray-Menü bleiben erhalten.
- GTK-3-Python-Bindings aus den Paketabhängigkeiten entfernt.
- Versionsnummer bewusst bei 1.1.6 belassen.

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
- Übersicht zeigt zusätzlich Swap-Auslastung und Systemlast für 1, 5 und 15 Minuten.
- CPU-Informationen, Prozessfilter, Sortierung, dunkles Erscheinungsbild und Administratorstart beibehalten.

## 1.0.9 ADMIN
- CPU-Informationsbereich mit Modell, Architektur, physischen/logischen Kernen, Takt, Temperatur und Taktregler.
- Raspberry-Pi-Drosselungs-/Unterspannungsstatus über `vcgencmd get_throttled`, sofern verfügbar.

## 1.0.8 ADMIN
- Versionsnummer dauerhaft im Fenstertitel und in der Hauptüberschrift.
- CPU-Kern-Panel vergrößert und Filtererkennung für typische Kernel-Worker erweitert.

## 1.0.7 ADMIN
- dunkles Erscheinungsbild mit kontrastreichen Tabellenfarben.
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
