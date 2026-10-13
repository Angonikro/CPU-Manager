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
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
