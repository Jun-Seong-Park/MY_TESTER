"""
UART LED control GUI (PC side) for the MY_TESTER board.

Sends single-byte commands to the board over UART (USART2, 115200 8N1) and shows
the text the board sends back.

Protocol (PC -> board), one ASCII byte per command:
    's' (0x73)  STOP - board stops blinking, LED off
    'r' (0x72)  RUN  - board resumes normal blinking

The toggle button maps to:
    engaged  -> 's' (stop)
    released -> 'r' (run)

NOTE: the board firmware (main.c) must be updated separately to react to these
bytes (interrupt RX -> set a "stopped" flag). This script only SENDS them.

Setup:  pip install pyserial PySide6
Run:    python uart_led_gui.py
"""

import sys

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QTextEdit, QLineEdit,
)

CMD_STOP = b"s"
CMD_RUN = b"r"
DEFAULT_BAUD = 115200


class SerialReader(QThread):
    """Background reader: emits one signal per newline-terminated line."""

    line_received = Signal(str)
    disconnected = Signal(str)

    def __init__(self, ser):
        super().__init__()
        self._ser = ser
        self._running = True

    def run(self):
        buf = bytearray()
        while self._running:
            try:
                chunk = self._ser.read(64)  # blocks up to ser.timeout, then returns
            except (serial.SerialException, OSError) as exc:
                self.disconnected.emit(str(exc))
                return
            if not chunk:
                continue
            buf.extend(chunk)
            while b"\n" in buf:
                line, _, rest = buf.partition(b"\n")
                buf = bytearray(rest)
                self.line_received.emit(line.decode(errors="replace").rstrip("\r"))

    def stop(self):
        self._running = False


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MY_TESTER UART LED Control")
        self._ser = None
        self._reader = None

        # --- port / connection row ---
        self.port_box = QComboBox()
        self.baud_edit = QLineEdit(str(DEFAULT_BAUD))
        self.baud_edit.setFixedWidth(80)
        self.refresh_btn = QPushButton("Refresh")
        self.connect_btn = QPushButton("Connect")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.clicked.connect(self.toggle_connection)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        port_row.addWidget(self.port_box, 1)
        port_row.addWidget(QLabel("Baud:"))
        port_row.addWidget(self.baud_edit)
        port_row.addWidget(self.refresh_btn)
        port_row.addWidget(self.connect_btn)

        # --- toggle command button ---
        self.toggle_btn = QPushButton("LED: RUN  (click to STOP)")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setMinimumHeight(60)
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.toggled.connect(self.on_toggle)

        # --- board output log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addLayout(port_row)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(QLabel("Board output:"))
        layout.addWidget(self.log, 1)

        self.refresh_ports()

    # ---- ports / connection ----
    def refresh_ports(self):
        self.port_box.clear()
        for port in serial.tools.list_ports.comports():
            label = f"{port.device}  ({port.description})"
            self.port_box.addItem(label, userData=port.device)

    def toggle_connection(self):
        if self._ser is None:
            self.connect_serial()
        else:
            self.disconnect_serial()

    def connect_serial(self):
        device = self.port_box.currentData()
        if not device:
            self._append("[no port selected]")
            return
        try:
            baud = int(self.baud_edit.text())
        except ValueError:
            self._append("[invalid baud]")
            return
        try:
            self._ser = serial.Serial(device, baud, timeout=0.1)
        except (serial.SerialException, ValueError) as exc:
            self._append(f"[open failed: {exc}]")
            self._ser = None
            return

        self._reader = SerialReader(self._ser)
        self._reader.line_received.connect(self._append)
        self._reader.disconnected.connect(self._on_reader_dropped)
        self._reader.start()

        self.connect_btn.setText("Disconnect")
        self.toggle_btn.setEnabled(True)
        self.port_box.setEnabled(False)
        self.baud_edit.setEnabled(False)
        self._append(f"[connected {device} @ {baud}]")

    def disconnect_serial(self):
        if self._reader is not None:
            self._reader.stop()
            self._reader.wait(1000)
            self._reader = None
        if self._ser is not None:
            try:
                self._ser.close()
            except OSError:
                pass
            self._ser = None
        self.connect_btn.setText("Connect")
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.blockSignals(True)   # avoid firing a stray command
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setText("LED: RUN  (click to STOP)")
        self.toggle_btn.blockSignals(False)
        self.port_box.setEnabled(True)
        self.baud_edit.setEnabled(True)
        self._append("[disconnected]")

    def _on_reader_dropped(self, msg):
        self._append(f"[serial error: {msg}]")
        self.disconnect_serial()

    # ---- commands ----
    def on_toggle(self, checked):
        if checked:
            self._send(CMD_STOP)
            self.toggle_btn.setText("LED: STOPPED  (click to RUN)")
        else:
            self._send(CMD_RUN)
            self.toggle_btn.setText("LED: RUN  (click to STOP)")

    def _send(self, data):
        if self._ser is None:
            return
        try:
            self._ser.write(data)
            self._append(f"[sent {data!r}]")
        except (serial.SerialException, OSError) as exc:
            self._append(f"[send failed: {exc}]")
            self.disconnect_serial()

    # ---- helpers ----
    def _append(self, text):
        self.log.append(text)

    def closeEvent(self, event):
        self.disconnect_serial()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(540, 440)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
