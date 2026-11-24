# CPU Manager 1.1.7

## Prozessaktionen ohne UI-Blockade

Die Aktionen **Beenden**, **Sofort beenden** und **Dienst neu starten** laufen jetzt in separaten Qt-Hintergrundthreads. Langsame Systemaufrufe und systemd-Wartezeiten blockieren dadurch nicht mehr den GUI-Thread. Während eine Aktion läuft, zeigt die Statuszeile den Vorgang an; die Aktionsschaltflächen werden gegen versehentliche Mehrfachausführung deaktiviert. Nach Abschluss aktualisiert CPU Manager die Prozessliste und zeigt gegebenenfalls eine Fehlermeldung.

Die vorhandene Sicherheitslogik bleibt bestehen: PID 1 ist geschützt, und ein Neustart wird weiterhin nur für eindeutig erkannte systemd-Service-Units ausgeführt.
