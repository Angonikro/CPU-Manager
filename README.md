# CPU Manager 1.1.5

CPU Manager ist ein grafischer Systemmonitor für Raspberry Pi und andere Debian-/Linux-Systeme. Er zeigt die Auslastung der CPU-Kerne, Arbeitsspeicher und laufende Prozesse an. Die Anwendung startet ohne Passwortabfrage und läuft mit den Rechten des angemeldeten Benutzers.

## Funktionen

- Live-Anzeige der Gesamt-CPU-Auslastung und der einzelnen CPU-Kerne
- Übersicht zu RAM, Swap und Load Average (1, 5 und 15 Minuten)
- Prozessliste mit PID, Name, Benutzer, CPU- und RAM-Verbrauch, Status und Thread-Anzahl
- Prozesse filtern und nach CPU, RAM, PID oder Name sortieren
- Option **„Systemdienste anzeigen“** zum Ein- und Ausblenden erkannter Systemdienste und Hintergrundprozesse
- CPU-Informationen wie Modell, Architektur, Kernanzahl, Takt, Temperatur und Governor, soweit das System diese Daten bereitstellt
- Einstellbares Messintervall: **1, 2, 5, 10 oder 30 Sekunden**
- Gespeicherte Einstellungen für Messintervall, Hell-/Dunkelmodus, Anzeige der Systemdienste und Infobereichssymbol (Tray)
- Prozessdetails einschließlich Programmdatei, Kommandozeile und erlaubter CPU-Affinität
- Verwaltungsaktionen wie Prozess beenden und – sofern eindeutig zuordenbar – einen systemd-Dienst neu starten
- System-Tray wie in LunaKalender über GTK 3 `Gtk.StatusIcon`: CPU-Chip-Symbol mit Live-Prozentwert, Aktualisierung beim Messintervall und Warnfarbe ab 80 %; Tooltip zeigt die aktuelle CPU-Auslastung. Linksklick blendet das Fenster ein/aus, Rechtsklick öffnet „CPU Manager anzeigen“ und „Beenden“
- Optionales Infobereichssymbol; bei aktiviertem Tray blendet das Schließen-Kreuz das Fenster nur aus
- Start über das Anwendungsmenü ohne zusätzliches Terminal; Start ohne Passwortabfrage; Verwaltungsaktionen sind durch die Rechte des angemeldeten Benutzers begrenzt

## Voraussetzungen

- Raspberry Pi OS oder ein Debian-basiertes Linux mit grafischer Desktop-Sitzung
- Python 3
- PySide6 Qt Widgets (`python3-pyside6.qtwidgets`)
- psutil (`python3-psutil`)
- GTK 3 Python-Bindings (`python3-gi`, `gir1.2-gtk-3.0`) für das System-Tray

Eine virtuelle Python-Umgebung und `pip` sind für die Debian-Installation nicht erforderlich.

## Installation (empfohlen): Debian-Paket

Lade `cpu-manager_1.1.5_all.deb` aus den Release-Dateien herunter und installiere es im Verzeichnis, in dem die Datei liegt:

```bash
sudo apt install ./cpu-manager_1.1.5_all.deb
```

Danach kannst du **CPU Manager** über das Anwendungsmenü starten. Der Menüeintrag öffnet kein zusätzliches Terminal. Die App startet ohne Passwortabfrage mit den Rechten deines angemeldeten Benutzers. Aktionen an fremden Prozessen oder Systemdiensten können daher vom System abgelehnt werden.

## Start aus dem GitHub-Quellcode

Entpacke das GitHub-ZIP. Es entsteht der Ordner `cpu-manager`. Öffne ein Terminal in diesem Ordner und installiere die benötigten Systempakete:

```bash
chmod +x install_dependencies.sh start_cpu_manager.sh
./install_dependencies.sh
```

Die Abhängigkeiten werden über `apt` installiert; das Skript richtet keine virtuelle Umgebung ein und verwendet kein `pip`.

Der Quellcode kann ohne Administratorrechte gestartet werden:

```bash
/usr/bin/python3 main.py
```

Das Startskript startet CPU Manager direkt ohne Passwortabfrage. Verwaltungsaktionen, für die Root-Rechte erforderlich sind, können weiterhin eingeschränkt sein.

## Einstellungen und Systemdienste

Die Anwendung merkt sich deine Auswahl für den Hell-/Dunkelmodus, das Messintervall und die Checkbox **„Systemdienste anzeigen“**, die Tray-Einstellung und das Messintervall. Diese Einstellungen werden beim nächsten Start wiederhergestellt.

Wenn **„Systemdienste anzeigen“** ausgeschaltet ist, blendet CPU Manager erkannte systemd-Dienste und bekannte Hintergrundprozesse in der Prozessliste aus. Die Gesamtwerte für CPU und Arbeitsspeicher beziehen sich weiterhin auf das gesamte System. Die genaue Erkennung kann je nach Linux-Distribution und Prozess-Cgroup variieren.

## Hinweise zur Bedienung

- Ein Prozess kann mehr als 100 % CPU anzeigen, wenn er mehrere Kerne gleichzeitig nutzt.
- Linux kann Prozesse zwischen CPU-Kernen verschieben. Die angezeigte CPU-Affinität zeigt, auf welchen Kernen ein Prozess laufen darf, nicht auf welchem Kern er dauerhaft läuft.
- **Beenden** sendet ein normales Beendigungssignal. **Sofort beenden** kann ungespeicherte Daten verlieren lassen.
- Das Neustarten eines Dienstes kann davon abhängige Programme kurz unterbrechen. Prüfe die Auswahl vor der Bestätigung.
- Einige Hardwarewerte, etwa Temperatur, Governor oder Drosselungsstatus, sind nicht auf jedem Gerät verfügbar.

## Fehlerbehebung

**Das Programm startet nach der Installation nicht:**

- Stelle sicher, dass du eine grafische Desktop-Sitzung verwendest.
- Installiere fehlende Paketabhängigkeiten erneut:

  ```bash
  sudo apt update
  sudo apt install python3 python3-pyside6.qtwidgets python3-psutil python3-gi gir1.2-gtk-3.0
  ```

**Ein Paketname wird nicht gefunden:**

```bash
apt-cache search pyside6
```

## Projektdateien

- `main.py` – Programmeinstieg
- `cpu_manager/` – Oberfläche, Überwachung und Verwaltungsaktionen
- `install_dependencies.sh` – Installation der Systemabhängigkeiten
- `build_deb.sh` – reproduzierbarer Bau des Debian-Pakets
- `start_cpu_manager.sh` – Startskript
- - `CHANGELOG.md` – Versionshistorie
- `RELEASE_NOTES_v1.1.5.md` – Hinweise zum Release 1.1.5
- `LICENSE` – Lizenzinformationen

## Lizenz

Siehe [`LICENSE`](LICENSE).


### Passwortloser Start über das Anwendungsmenü

Die Desktop-Datei verwendet `Exec=sudo /usr/bin/cpu-manager` wie gewünscht. Das Debian-Paket richtet dafür eine eng begrenzte sudoers-Regel für `/usr/bin/cpu-manager` ein (für Mitglieder der Gruppe `sudo`). Beim vollständigen Entfernen des Pakets wird die Regel entfernt.

73 de DO2QG Andreas
