import psutil
import os
import subprocess
import sys
from PySide6.QtCore import Qt, QTimer, QSettings, QObject, Signal, QThread
from PySide6.QtGui import QAction, QColor, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QPushButton, QMessageBox, QSplitter, QGroupBox, QComboBox, QAbstractItemView, QCheckBox
)
from .monitor import Monitor
from .actions import terminate_process, kill_process, restart_process, process_details, is_root
import struct
import zlib


class _TrayBridge(QObject):
    action = Signal(str)


class _ProcessActionThread(QThread):
    """Run potentially slow process operations without blocking the Qt UI."""
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, operation, parent=None):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            result = self.operation()
            self.succeeded.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


# Dependency-free PNG renderer for the native Qt system tray icon.
_GLYPHS = {
    "0": ("01110","10001","10011","10101","11001","10001","01110"),
    "1": ("00100","01100","00100","00100","00100","00100","01110"),
    "2": ("01110","10001","00001","00010","00100","01000","11111"),
    "3": ("11110","00001","00001","01110","00001","00001","11110"),
    "4": ("00010","00110","01010","10010","11111","00010","00010"),
    "5": ("11111","10000","10000","11110","00001","00001","11110"),
    "6": ("01110","10000","10000","11110","10001","10001","01110"),
    "7": ("11111","00001","00010","00100","01000","01000","01000"),
    "8": ("01110","10001","10001","01110","10001","10001","01110"),
    "9": ("01110","10001","10001","01111","00001","00001","01110"),
    "%": ("11001","11010","00100","01000","10110","00110","00000"),
}

def _tray_png(percent):
    """Render the final slightly larger, bold CPU percentage for XFCE panels."""
    width, height = 96, 48
    transparent = (0, 0, 0, 0)
    pixels = [[transparent for _ in range(width)] for _ in range(height)]
    accent = (255, 82, 82, 255) if percent >= 80 else (112, 238, 166, 255)

    def rect(x0, y0, x1, y1, color):
        for yy in range(max(0, y0), min(height, y1)):
            for xx in range(max(0, x1)):
                if xx >= max(0, x0):
                    pixels[yy][xx] = color

    label = f"{max(0, min(100, int(round(percent))))}%"
    scale = 4 if len(label) == 4 else 6
    char_w, char_h = 5 * scale, 7 * scale
    total_w = len(label) * char_w
    xstart = (width - total_w) // 2
    ystart = (height - char_h) // 2

    for ci, char in enumerate(label):
        glyph = _GLYPHS.get(char)
        if glyph is None:
            continue
        for gy, line in enumerate(glyph):
            for gx, bit in enumerate(line):
                if bit == "1":
                    x = xstart + ci * char_w + gx * scale
                    y = ystart + gy * scale
                    rect(x, y, x + scale + 1, y + scale + 1, accent)

    raw = b"".join(
        b"\x00" + bytes(channel for pixel in row for channel in pixel)
        for row in pixels
    )

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Manager 1.1.8 – Raspberry Pi")
        self.resize(1180, 760)
        self.monitor = Monitor()
        self.settings = QSettings("CPUManager", "CPUManagerADMIN")
        self._rows_by_pid = {}
        self._action_threads = set()
        self._action_running = False
        self.tray_enabled = self.settings.value("tray_enabled", False, type=bool)
        self.tray_icon = None
        self._really_quit = False
        self._build_ui()
        if self.tray_enabled:
            self._start_tray()
        self.monitor.prime()
        self.timer = QTimer(self)
        self.timer.setInterval(int(self.settings.value("measurement_interval_ms", 2000)))
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        top = QHBoxLayout()
        title = QLabel("CPU Manager 1.1.8")
        title.setStyleSheet("font-size: 23px; font-weight: 700;")
        self.root_badge = QLabel("Administratorrechte" if is_root() else "Benutzerrechte")
        self.root_badge.setStyleSheet("padding: 5px 10px; border-radius: 8px; background: #e6f4ea; color: #176534;" if is_root() else "padding: 5px 10px; border-radius: 8px; background: #fff4d6; color: #785600;")
        self.status_label = QLabel("Initialisiere …")
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(self.status_label)
        top.addWidget(self.root_badge)
        root.addLayout(top)

        self.core_box = QGroupBox("CPU-Auslastung je Kern")
        self.core_box.setMinimumHeight(84)
        self.core_grid = QGridLayout(self.core_box)
        self.core_grid.setContentsMargins(8, 22, 8, 10)
        self.core_grid.setVerticalSpacing(5)
        self.core_bars = []
        root.addWidget(self.core_box)

        self.hardware_box = QGroupBox("CPU-Informationen")
        hardware_layout = QVBoxLayout(self.hardware_box)
        self.hardware_label = QLabel("Lese CPU-Hardwaredaten …")
        self.hardware_label.setWordWrap(True)
        self.hardware_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        hardware_layout.addWidget(self.hardware_label)
        root.addWidget(self.hardware_box)

        self.summary = QLabel("Gesamt-CPU: –    RAM: –")
        self.summary.setStyleSheet("font-size: 14px; font-weight: 600;")
        root.addWidget(self.summary)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Messintervall:"))
        self.interval_box = QComboBox()
        self.interval_box.setMinimumWidth(100)
        self.interval_box.setMaximumWidth(110)
        self.interval_box.view().setMinimumWidth(110)
        for seconds in (1, 2, 5, 10, 30):
            self.interval_box.addItem(f"{seconds} s", seconds)
        saved_interval = int(self.settings.value("measurement_interval_ms", 2000)) // 1000
        idx = self.interval_box.findData(saved_interval)
        self.interval_box.setCurrentIndex(idx if idx >= 0 else 1)
        self.interval_box.currentIndexChanged.connect(self.change_interval)
        controls.addWidget(self.interval_box)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filtern nach Prozess, PID oder Benutzer …")
        self.search.textChanged.connect(self.refresh_table_filter)
        self.sort_box = QComboBox()
        self.sort_box.addItems(["CPU-Last (hoch → niedrig)", "RAM (hoch → niedrig)", "PID (aufsteigend)", "Name (A → Z)"])
        self.sort_box.currentIndexChanged.connect(self.refresh)
        self.services_toggle = QCheckBox("Systemdienste anzeigen")
        saved_show_services = self.settings.value("show_system_services", False, type=bool)
        self.services_toggle.setChecked(saved_show_services)
        self.services_toggle.toggled.connect(self.change_services_visibility)
        self.dark_toggle = QCheckBox("Dunkles Erscheinungsbild")
        self.dark_toggle.toggled.connect(self.apply_theme)
        controls.addWidget(self.search, 1)
        controls.addWidget(QLabel("Sortierung:"))
        controls.addWidget(self.sort_box)
        controls.addWidget(self.services_toggle)
        controls.addWidget(self.dark_toggle)
        root.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["PID", "Prozess", "Benutzer", "CPU %", "Arbeitsspeicher (MB)", "Status", "Ausführungsfäden"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col, mode in [(0,QHeaderView.ResizeMode.ResizeToContents),(2,QHeaderView.ResizeMode.ResizeToContents),(3,QHeaderView.ResizeMode.ResizeToContents),(4,QHeaderView.ResizeMode.ResizeToContents),(5,QHeaderView.ResizeMode.ResizeToContents),(6,QHeaderView.ResizeMode.ResizeToContents)]:
            self.table.horizontalHeader().setSectionResizeMode(col, mode)
        self.table.setSortingEnabled(False)
        splitter.addWidget(self.table)

        bottom = QWidget()
        b = QVBoxLayout(bottom)
        self.details_label = QLabel("Wähle einen Prozess aus, um Details anzuzeigen.")
        self.details_label.setWordWrap(True)
        b.addWidget(self.details_label)
        buttons = QHBoxLayout()
        self.details_btn = QPushButton("Details")
        self.stop_btn = QPushButton("Beenden")
        self.kill_btn = QPushButton("Sofort beenden")
        self.restart_btn = QPushButton("Dienst neu starten")
        self.refresh_btn = QPushButton("Jetzt aktualisieren")
        self.tray_toggle = QCheckBox("Infobereichssymbol")
        self.tray_toggle.setToolTip("CPU Manager im Infobereich anzeigen; Schließen blendet das Fenster dann nur aus.")
        self.tray_toggle.setChecked(self.tray_enabled)
        self.tray_toggle.toggled.connect(self._toggle_tray)
        self.details_btn.clicked.connect(self.show_details)
        self.stop_btn.clicked.connect(self.stop_selected)
        self.kill_btn.clicked.connect(self.kill_selected)
        self.restart_btn.clicked.connect(self.restart_selected)
        self.refresh_btn.clicked.connect(self.refresh)
        for btn in [self.details_btn, self.stop_btn, self.kill_btn, self.restart_btn, self.refresh_btn]:
            buttons.addWidget(btn)
        buttons.addWidget(self.tray_toggle)
        b.addLayout(buttons)
        splitter.addWidget(bottom)
        splitter.setSizes([490, 150])
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)
        # Restore the user's preferred theme after all widgets exist.
        saved_dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.dark_toggle.setChecked(saved_dark_mode)
        self.apply_theme(saved_dark_mode)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self._set_action_enabled(False)

        note = QLabel("Hinweis: CPU-Werte sind Prozesswerte seit der letzten Messung und können über 100 % liegen, wenn mehrere Kerne genutzt werden. Kernzuordnung ist dynamisch; Linux kann Prozesse zwischen Kernen verschieben.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #666; font-size: 11px;")
        root.addWidget(note)


    def _toggle_tray(self, enabled):
        """Enable/disable the GTK 3 StatusIcon tray using LunaKalender's method."""
        self.tray_enabled = bool(enabled)
        self.settings.setValue("tray_enabled", self.tray_enabled)
        if self.tray_enabled:
            if not self._start_tray():
                self.tray_enabled = False
                self.settings.setValue("tray_enabled", False)
                self.tray_toggle.blockSignals(True)
                self.tray_toggle.setChecked(False)
                self.tray_toggle.blockSignals(False)
        else:
            self._stop_tray()

    def _start_tray(self):
        if self.tray_icon is not None:
            return True
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(
                self, "Infobereichssymbol nicht verfügbar",
                "Die Desktop-Umgebung stellt momentan keinen Infobereich bereit."
            )
            return False
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setToolTip("CPU Manager – CPU-Auslastung wird gemessen")
            self._tray_menu = QMenu(self)
            show_action = QAction("CPU Manager öffnen", self._tray_menu)
            show_action.triggered.connect(lambda: self._handle_tray_action("show"))
            self._tray_menu.addAction(show_action)
            self._tray_menu.addSeparator()
            quit_action = QAction("Beenden", self._tray_menu)
            quit_action.triggered.connect(lambda: self._handle_tray_action("quit"))
            self._tray_menu.addAction(quit_action)
            self.tray_icon.setContextMenu(self._tray_menu)
            self.tray_icon.activated.connect(self._on_tray_activated)
            self._set_tray_visual(0.0)
            self.tray_icon.show()
            return True
        except Exception as exc:
            if self.tray_icon is not None:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
                self.tray_icon = None
            QMessageBox.warning(self, "Infobereichssymbol nicht verfügbar", str(exc))
            return False

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self._handle_tray_action("toggle")

    def _set_tray_visual(self, percent):
        """Render the CPU chip and live percentage into the native Qt tray icon."""
        if self.tray_icon is None:
            return
        try:
            pixmap = QPixmap()
            if pixmap.loadFromData(_tray_png(float(percent)), "PNG"):
                self.tray_icon.setIcon(QIcon(pixmap))
            self.tray_icon.setToolTip(
                f"CPU Manager – CPU-Auslastung: {percent:.0f}%"
                + (" (hohe Last)" if percent >= 80 else "")
            )
        except Exception:
            self.tray_icon.setToolTip(f"CPU Manager – CPU-Auslastung: {percent:.0f}%")

    def _update_tray_cpu(self, percent):
        if self.tray_enabled and self.tray_icon is not None:
            self._set_tray_visual(float(percent))

    def _handle_tray_action(self, action):
        if action == "show":
            self.showNormal()
            self.raise_()
            self.activateWindow()
        elif action == "toggle":
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.raise_()
                self.activateWindow()
        elif action == "quit":
            # Beenden ist keine Änderung der Tray-Einstellung.
            # Die Auswahl muss beim nächsten Programmstart erhalten bleiben.
            self.settings.sync()
            self._really_quit = True
            self.close()

    def _stop_tray(self):
        icon = self.tray_icon
        self.tray_icon = None
        if icon is not None:
            icon.hide()
            icon.deleteLater()
        menu = getattr(self, "_tray_menu", None)
        if menu is not None:
            menu.deleteLater()
            self._tray_menu = None

    def closeEvent(self, event):
        if not self._really_quit and self.tray_enabled and self.tray_icon is not None:
            event.ignore()
            self.hide()
            return
        self._stop_tray()
        event.accept()

    def change_services_visibility(self, show_services):
        """Persist the system-services visibility preference and refresh the process list."""
        self.settings.setValue("show_system_services", bool(show_services))
        self.refresh()

    def change_interval(self, _index=0):
        """Apply and persist the selected refresh interval."""
        seconds = int(self.interval_box.currentData() or 2)
        self.settings.setValue("measurement_interval_ms", seconds * 1000)
        self.timer.setInterval(seconds * 1000)
        self.status_label.setText(f"Echtzeit · Messintervall {seconds} s")

    def apply_theme(self, dark=False):
        """Apply and persist the user's light/dark theme preference."""
        self.settings.setValue("dark_mode", bool(dark))
        if dark:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #202124; color: #e8eaed; }
                QLineEdit, QComboBox, QTableWidget, QGroupBox { background-color: #292a2d; color: #e8eaed; border: 1px solid #5f6368; }
                QGroupBox { margin-top: 10px; padding-top: 7px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #e8eaed; }
                QTableWidget { alternate-background-color: #303136; gridline-color: #484a50; selection-background-color: #355a82; selection-color: #ffffff; }
                QTableWidget::item { background-color: #292a2d; color: #e8eaed; padding: 2px; }
                QTableWidget::item:alternate { background-color: #303136; color: #e8eaed; }
                QTableWidget::item:selected { background-color: #355a82; color: #ffffff; }
                QHeaderView::section { background-color: #35363a; color: #e8eaed; padding: 4px; border: 1px solid #5f6368; }
                QPushButton { background-color: #35363a; color: #e8eaed; border: 1px solid #686b70; border-radius: 4px; padding: 5px; }
                QPushButton:disabled { color: #777; }
                QProgressBar { background-color: #35363a; border: 1px solid #686b70; }
                QProgressBar::chunk { background-color: #4caf50; }
                QCheckBox { spacing: 5px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #f4f5f7; color: #202124; }
                QLineEdit, QComboBox, QTableWidget, QGroupBox { background-color: #ffffff; color: #202124; border: 1px solid #b8bcc2; }
                QGroupBox { margin-top: 10px; padding-top: 7px; }
                QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #202124; }
                QTableWidget { alternate-background-color: #f0f2f5; gridline-color: #d0d4da; selection-background-color: #c8def7; selection-color: #111111; }
                QTableWidget::item { background-color: #ffffff; color: #202124; padding: 2px; }
                QTableWidget::item:alternate { background-color: #f0f2f5; color: #202124; }
                QTableWidget::item:selected { background-color: #c8def7; color: #111111; }
                QHeaderView::section { background-color: #e8eaed; color: #202124; padding: 4px; border: 1px solid #c5c9ce; }
                QPushButton { background-color: #f7f7f7; color: #202124; border: 1px solid #b8bcc2; border-radius: 4px; padding: 5px; }
            """)
        # Repaint alternating rows using the active palette/style immediately.
        self.table.setAlternatingRowColors(False)
        self.table.setAlternatingRowColors(True)
        self.table.viewport().update()

    def _set_action_enabled(self, enabled):
        self.details_btn.setEnabled(enabled)
        actions_enabled = enabled and not self._action_running
        for b in (self.stop_btn, self.kill_btn, self.restart_btn):
            b.setEnabled(actions_enabled)

    def selected_pid(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.table.item(selected[0].row(), 0)
        try:
            return int(item.text())
        except (AttributeError, ValueError):
            return None

    def selection_changed(self):
        pid = self.selected_pid()
        self._set_action_enabled(pid is not None)
        if pid is not None:
            row = self._rows_by_pid.get(pid)
            if row:
                self.details_label.setText(f"Ausgewählt: {row.name} (PID {pid}) · {row.user} · CPU {row.cpu:.1f}% · RAM {row.rss_mb:.1f} MB · {self._translate_status(row.status)}")

    @staticmethod
    def _translate_status(status):
        translations = {
            "running": "läuft", "sleeping": "wartend", "disk-sleep": "Warten auf Datenträger",
            "stopped": "angehalten", "tracing-stop": "Nachverfolgung angehalten",
            "zombie": "Zombie", "dead": "beendet", "idle": "untätig",
            "locked": "gesperrt", "waking": "wird aktiviert",
        }
        return translations.get(str(status).lower(), str(status))

    @staticmethod
    def _translate_governor(governor):
        translations = {
            "ondemand": "bedarfsgesteuert", "performance": "Höchstleistung",
            "powersave": "Energiesparmodus", "schedutil": "dynamisch",
            "conservative": "sparsam", "userspace": "benutzergesteuert",
        }
        value = str(governor)
        return translations.get(value.lower(), value)

    def refresh(self):
        try:
            cores, total, vm, rows = self.monitor.snapshot()
        except Exception as exc:
            self.status_label.setText(f"Messfehler: {exc}")
            return
        show_services = self.services_toggle.isChecked()
        rows = [r for r in rows if show_services or not r.is_system_service]
        self._rows_by_pid = {r.pid: r for r in rows}
        self._draw_cores(cores)
        try:
            info = self.monitor.cpu_info()
            self.hardware_label.setText(
                f"Modell: {info['model']}    Architektur: {info['arch']}    "
                f"Kerne: {info['physical']} physisch / {info['logical']} logisch\n"
                f"Takt: {info['current_mhz']} aktuell / {info['max_mhz']} maximal    "
                f"Temperatur: {info['temperature']}    Taktregler: {self._translate_governor(info['governor'])}\n"
                f"Takt-/Temperaturstatus: {info['throttling']}"
            )
        except Exception as exc:
            self.hardware_label.setText(f"CPU-Informationen konnten nicht gelesen werden: {exc}")
        swap = psutil.swap_memory()
        try:
            load = os.getloadavg()
            load_text = f"Systemlast (1/5/15 Min.): {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}"
        except (AttributeError, OSError):
            load_text = "Systemlast: nicht verfügbar"
        self.summary.setText(
            f"Gesamt-CPU: {total:.1f}%    Arbeitsspeicher: {vm.used / (1024**3):.2f} / {vm.total / (1024**3):.2f} GiB ({vm.percent:.1f}%)    "
            f"Auslagerung: {swap.used / (1024**3):.2f} / {swap.total / (1024**3):.2f} GiB ({swap.percent:.1f}%)    {load_text}    Prozesse: {len(rows)}"
        )
        self._update_tray_cpu(total)
        self.status_label.setText(f"Echtzeit · Messintervall {self.interval_box.currentData()} s · {len(rows)} Prozesse")
        old_pid = self.selected_pid()
        sort = self.sort_box.currentIndex()
        if sort == 1:
            rows.sort(key=lambda r: (-r.rss_mb, -r.cpu, r.pid))
        elif sort == 2:
            rows.sort(key=lambda r: r.pid)
        elif sort == 3:
            rows.sort(key=lambda r: r.name.lower())
        else:
            rows.sort(key=lambda r: (-r.cpu, -r.rss_mb, r.pid))
        query = self.search.text().strip().lower()
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0)
        for r in rows:
            if query and query not in str(r.pid) and query not in r.name.lower() and query not in r.user.lower():
                continue
            idx = self.table.rowCount()
            self.table.insertRow(idx)
            vals = [str(r.pid), r.name, r.user, f"{r.cpu:.1f}", f"{r.rss_mb:.1f}", self._translate_status(r.status), str(r.threads)]
            for col, value in enumerate(vals):
                item = QTableWidgetItem(value)
                if col in (0,3,4,6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if col == 3 and r.cpu >= 80:
                    item.setForeground(QColor("#c62828"))
                item.setData(Qt.ItemDataRole.UserRole, r.pid)
                self.table.setItem(idx, col, item)
        self.table.setUpdatesEnabled(True)
        if old_pid is not None:
            for i in range(self.table.rowCount()):
                if self.table.item(i, 0).text() == str(old_pid):
                    self.table.selectRow(i)
                    break
        self.refresh_table_filter()
        self.selection_changed()

    def _draw_cores(self, values):
        while self.core_grid.count():
            item = self.core_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.core_bars = []
        columns = 4
        for i, val in enumerate(values):
            box = QWidget()
            lay = QVBoxLayout(box)
            lay.setContentsMargins(2,2,2,2)
            header = QHBoxLayout()
            name = QLabel(f"CPU {i}")
            pct = QLabel(f"{val:.0f}%")
            pct.setMinimumWidth(42)
            pct.setAlignment(Qt.AlignmentFlag.AlignRight)
            header.addWidget(name)
            header.addStretch(1)
            header.addWidget(pct)
            bar = QProgressBar()
            bar.setRange(0,100)
            bar.setValue(round(val))
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            if val >= 80:
                bar.setStyleSheet("QProgressBar::chunk { background: #d32f2f; }")
            elif val >= 50:
                bar.setStyleSheet("QProgressBar::chunk { background: #f9a825; }")
            else:
                bar.setStyleSheet("QProgressBar::chunk { background: #2e7d32; }")
            lay.addLayout(header)
            lay.addWidget(bar)
            self.core_grid.addWidget(box, i // columns, i % columns)
            self.core_bars.append((pct, bar))

    def refresh_table_filter(self):
        query = self.search.text().strip().lower()
        # Filtering is applied on the next full refresh; this method hides rows immediately.
        for i in range(self.table.rowCount()):
            values = [self.table.item(i, c).text().lower() for c in (0,1,2) if self.table.item(i,c)]
            self.table.setRowHidden(i, bool(query) and not any(query in v for v in values))

    def _confirm(self, title, message):
        # Schaltflächen ausdrücklich deutsch beschriften, unabhängig davon,
        # ob die deutschen Qt-Übersetzungen auf dem System installiert sind.
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        yes_button = dialog.addButton(QMessageBox.StandardButton.Yes)
        no_button = dialog.addButton(QMessageBox.StandardButton.No)
        yes_button.setText("Ja")
        no_button.setText("Nein")
        dialog.setDefaultButton(no_button)
        dialog.exec()
        return dialog.clickedButton() is yes_button

    def _permission_hint(self):
        if not is_root():
            QMessageBox.information(self, "Berechtigung", "Die App läuft ohne Administratorrechte. Prozesse anderer Benutzer bzw. Systemdienste können geschützt sein. Starte die App bei Bedarf über das mitgelieferte Startskript mit sudo; dadurch erhält die gesamte App erhöhte Rechte.")

    def show_details(self):
        pid = self.selected_pid()
        if pid is None: return
        try:
            d = process_details(pid)
            affinity = self.monitor.affinity(pid)
            cmd = " ".join(d["cmdline"]) or "(kein Kommandozeilentext verfügbar)"
            text = (f"PID: {d['pid']}\nName: {d['name']}\nBenutzer: {d['username']}\nStatus: {d['status']}\n"
                    f"Eltern-PID: {d['ppid']}\nAusführungsfäden: {self._rows_by_pid.get(pid).threads if pid in self._rows_by_pid else '?'}\n"
                    f"CPU-Affinität (erlaubte Kerne): {', '.join(map(str, affinity)) or 'nicht verfügbar'}\n"
                    f"Programm: {d['exe'] or 'nicht verfügbar'}\nBefehl: {cmd}")
            QMessageBox.information(self, f"Prozessdetails – PID {pid}", text)
        except Exception as exc:
            QMessageBox.warning(self, "Details nicht verfügbar", str(exc))

    def _run_process_action(self, label, operation, success_message=None):
        """Execute a process action on a worker thread and report back on the UI thread."""
        if self._action_running:
            return
        self._action_running = True
        for button in (self.stop_btn, self.kill_btn, self.restart_btn):
            button.setEnabled(False)
        self.status_label.setText(f"{label} läuft im Hintergrund …")
        worker = _ProcessActionThread(operation, self)
        self._action_threads.add(worker)
        worker.succeeded.connect(lambda result, w=worker: self._process_action_succeeded(w, label, result, success_message))
        worker.failed.connect(lambda error, w=worker: self._process_action_failed(w, label, error))
        worker.finished.connect(lambda w=worker: self._process_action_finished(w))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _process_action_succeeded(self, worker, label, result, success_message):
        if success_message:
            message = success_message(result)
            QMessageBox.information(self, "Aktion abgeschlossen", message)
        else:
            self.status_label.setText(f"{label} erfolgreich ausgeführt")
        self.refresh()

    def _process_action_failed(self, worker, label, error):
        QMessageBox.warning(self, f"{label} fehlgeschlagen", error)
        self.status_label.setText(f"{label} fehlgeschlagen")
        self.refresh()

    def _process_action_finished(self, worker):
        self._action_threads.discard(worker)
        self._action_running = False
        self.selection_changed()

    def stop_selected(self):
        pid = self.selected_pid()
        if pid is None:
            return
        row = self._rows_by_pid.get(pid)
        name = row.name if row else str(pid)
        if pid <= 1:
            QMessageBox.warning(self, "Geschützter Prozess", "PID 1 und grundlegende Systemprozesse können hier nicht beendet werden.")
            return
        if not self._confirm("Prozess beenden?", f"An {name} (PID {pid}) wird ein normales Beendigungssignal gesendet.\nNicht gespeicherte Daten können verloren gehen.\n\nFortfahren?"):
            return
        self._run_process_action("Beenden", lambda: terminate_process(pid))

    def kill_selected(self):
        pid = self.selected_pid()
        if pid is None:
            return
        row = self._rows_by_pid.get(pid)
        name = row.name if row else str(pid)
        if pid <= 1:
            QMessageBox.warning(self, "Geschützter Prozess", "PID 1 darf nicht beendet werden.")
            return
        if not self._confirm("Sofort beenden?", f"{name} (PID {pid}) wird ohne reguläre Aufräumphase beendet.\nDas kann Datenverlust verursachen.\n\nWirklich fortfahren?"):
            return
        self._run_process_action("Sofort beenden", lambda: kill_process(pid))

    def restart_selected(self):
        pid = self.selected_pid()
        if pid is None:
            return
        row = self._rows_by_pid.get(pid)
        name = row.name if row else str(pid)
        if pid <= 1:
            QMessageBox.warning(self, "Geschützter Prozess", "PID 1 darf nicht neu gestartet werden.")
            return
        if not self._confirm("Hintergrunddienst neu starten?", f"Es wird versucht, die zugehörige systemd-Diensteinheit für {name} (PID {pid}) zu ermitteln.\nFalls keine eindeutige Diensteinheit gefunden wird, passiert nichts. Der Dienst kann andere Programme kurz unterbrechen.\n\nFortfahren?"):
            return
        self._run_process_action(
            "Dienst neu starten",
            lambda: restart_process(pid),
            lambda unit: f"systemd hat den Neustart für {unit} angenommen."
        )

