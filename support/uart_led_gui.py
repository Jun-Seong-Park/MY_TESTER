"""
MY_TESTER 보드 실시간 상태 모니터 GUI (PC 측).

보드 펌웨어(main.c)가 USART2(115200 8N1, J601-CP2102 경유)로 보내는
라인 프로토콜을 실시간 표시합니다:

    BOOT,...                 부팅 배너
    BTNIDLE,LEFT=..,...      부팅 시 버튼 idle 레벨 (풀 방향 실측 확인용)
    BTN,<name>,<1|0>         버튼 눌림(1)/뗌(0), name = LEFT|RIGHT|DOWN|UP
    LED,<RED|GREEN>,<1|0>    LED 논리 상태 (핀 HIGH=1)
    LCD,<text>               LCD 에 그려진 텍스트

PC -> 보드 명령 (ASCII 1바이트):
    's' (STOP) GREEN LED 하트비트 정지 / 'r' (RUN) 재개

Setup:  pip install pyserial PySide6
Run:    python uart_led_gui.py
"""

import sys

import serial
import serial.tools.list_ports
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QPushButton, QLabel, QTextEdit, QLineEdit, QGroupBox,
)

CMD_STOP = b"s"
CMD_RUN = b"r"
DEFAULT_BAUD = 115200

BTN_NAMES = ("UP", "LEFT", "RIGHT", "DOWN")
LED_NAMES = ("RED", "GREEN")

STYLE_BTN_IDLE = (
    "QLabel { background: #333; color: #888; border: 1px solid #555;"
    " border-radius: 6px; padding: 10px; font-weight: bold; }"
)
STYLE_BTN_PRESSED = (
    "QLabel { background: #2e7d32; color: white; border: 1px solid #1b5e20;"
    " border-radius: 6px; padding: 10px; font-weight: bold; }"
)
STYLE_LED_OFF = (
    "QLabel { background: #333; color: #777; border-radius: 6px;"
    " padding: 8px; font-weight: bold; }"
)
STYLE_LED_ON = {
    "RED": "QLabel { background: #c62828; color: white; border-radius: 6px;"
           " padding: 8px; font-weight: bold; }",
    "GREEN": "QLabel { background: #2e7d32; color: white; border-radius: 6px;"
             " padding: 8px; font-weight: bold; }",
}
STYLE_LCD = (
    "QLabel { background: #1a2b1a; color: #9be89b;"
    " font-family: Consolas, monospace; font-size: 16px;"
    " border: 3px solid #444; border-radius: 4px; padding: 14px; }"
)


class SerialReader(QThread):
    """백그라운드 수신 스레드: 개행 단위로 한 줄씩 signal 발행."""

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
                chunk = self._ser.read(64)  # timeout 까지 블로킹 후 반환
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
        self.setWindowTitle("MY_TESTER Board Monitor")
        self._ser = None
        self._reader = None

        # --- 포트/연결 행 ---
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

        # --- LCD 미러 ---
        lcd_group = QGroupBox("LCD (board display mirror)")
        self.lcd_label = QLabel("(not connected)")
        self.lcd_label.setStyleSheet(STYLE_LCD)
        self.lcd_label.setAlignment(Qt.AlignCenter)
        self.lcd_label.setMinimumHeight(64)
        lcd_lay = QVBoxLayout(lcd_group)
        lcd_lay.addWidget(self.lcd_label)

        # --- 버튼 십자 배치 인디케이터 ---
        btn_group = QGroupBox("Buttons (live)")
        self.btn_labels = {}
        for name in BTN_NAMES:
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(STYLE_BTN_IDLE)
            self.btn_labels[name] = lbl
        btn_grid = QGridLayout(btn_group)
        btn_grid.addWidget(self.btn_labels["UP"], 0, 1)
        btn_grid.addWidget(self.btn_labels["LEFT"], 1, 0)
        btn_grid.addWidget(self.btn_labels["RIGHT"], 1, 2)
        btn_grid.addWidget(self.btn_labels["DOWN"], 2, 1)

        # --- LED 인디케이터 + 하트비트 제어 ---
        led_group = QGroupBox("LEDs (logical state from firmware)")
        self.led_labels = {}
        led_row = QHBoxLayout(led_group)
        for name in LED_NAMES:
            lbl = QLabel(f"{name}: ?")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(STYLE_LED_OFF)
            self.led_labels[name] = lbl
            led_row.addWidget(lbl)

        self.toggle_btn = QPushButton("GREEN blink: RUN  (click to STOP)")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setMinimumHeight(44)
        self.toggle_btn.setEnabled(False)
        self.toggle_btn.toggled.connect(self.on_toggle)

        # --- 수신 로그 ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        mid_row = QHBoxLayout()
        mid_row.addWidget(btn_group, 1)
        mid_row.addWidget(led_group, 1)

        layout = QVBoxLayout(self)
        layout.addLayout(port_row)
        layout.addWidget(lcd_group)
        layout.addLayout(mid_row)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(QLabel("Raw log:"))
        layout.addWidget(self.log, 1)

        self.refresh_ports()

    # ---- 포트 / 연결 ----
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
        self._reader.line_received.connect(self._on_line)
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
        self.toggle_btn.blockSignals(True)  # 잔여 명령 전송 방지
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setText("GREEN blink: RUN  (click to STOP)")
        self.toggle_btn.blockSignals(False)
        self.port_box.setEnabled(True)
        self.baud_edit.setEnabled(True)
        self._append("[disconnected]")

    def _on_reader_dropped(self, msg):
        self._append(f"[serial error: {msg}]")
        self.disconnect_serial()

    # ---- 보드 -> PC 라인 파싱 ----
    def _on_line(self, text):
        self._append(text)
        parts = text.split(",")
        kind = parts[0] if parts else ""

        if kind == "BTN" and len(parts) >= 3:
            name, state = parts[1], parts[2]
            lbl = self.btn_labels.get(name)
            if lbl is not None:
                pressed = state.strip() == "1"
                lbl.setStyleSheet(STYLE_BTN_PRESSED if pressed else STYLE_BTN_IDLE)
        elif kind == "LED" and len(parts) >= 3:
            name, state = parts[1], parts[2]
            lbl = self.led_labels.get(name)
            if lbl is not None:
                on = state.strip() == "1"
                lbl.setText(f"{name}: {'ON' if on else 'OFF'}")
                lbl.setStyleSheet(STYLE_LED_ON[name] if on else STYLE_LED_OFF)
        elif kind == "LCD" and len(parts) >= 2:
            # 텍스트 안에 콤마가 있어도 원문 그대로 보여주기 위해 재결합
            self.lcd_label.setText(",".join(parts[1:]))

    # ---- PC -> 보드 명령 ----
    def on_toggle(self, checked):
        if checked:
            self._send(CMD_STOP)
            self.toggle_btn.setText("GREEN blink: STOPPED  (click to RUN)")
        else:
            self._send(CMD_RUN)
            self.toggle_btn.setText("GREEN blink: RUN  (click to STOP)")

    def _send(self, data):
        if self._ser is None:
            return
        try:
            self._ser.write(data)
            self._append(f"[sent {data!r}]")
        except (serial.SerialException, OSError) as exc:
            self._append(f"[send failed: {exc}]")
            self.disconnect_serial()

    # ---- 헬퍼 ----
    def _append(self, text):
        self.log.append(text)

    def closeEvent(self, event):
        self.disconnect_serial()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(560, 640)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
