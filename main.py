#!/usr/bin/env python3
"""CPU Manager for Raspberry Pi / Linux. Uses Qt Widgets only; no Qt WebEngine."""
import sys
from PySide6.QtWidgets import QApplication
from cpu_manager.window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CPU Manager")
    app.setOrganizationName("CPU Manager")
    app.setStyle("Fusion")
    window = MainWindow()
    # If the user enabled the tray, start hidden only when the tray was
    # successfully initialized. Otherwise keep the window visible as a fallback.
    if not (window.tray_enabled and window.tray_icon is not None):
        window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
