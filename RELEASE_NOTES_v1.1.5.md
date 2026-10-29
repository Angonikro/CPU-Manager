# CPU Manager 1.1.5

- Wenn „Infobereichssymbol“ aktiviert und das Tray verfügbar ist, startet die Anwendung direkt im System-Tray und das Hauptfenster bleibt zunächst verborgen.
- Der Desktop-Eintrag verwendet `Exec=/usr/bin/cpu-manager`.
- Der normale Start erfolgt ohne `pkexec` und ohne Passwortabfrage.
- Die Anwendung läuft mit den Rechten des angemeldeten Benutzers; Systemaktionen können deshalb eingeschränkt sein.

- Desktop launcher now uses the requested `Exec=sudo /usr/bin/cpu-manager` command.
- Debian package adds a narrowly scoped sudoers rule for passwordless launch by sudo-group users.
- When tray mode is enabled, the app starts hidden if the tray initializes successfully.
