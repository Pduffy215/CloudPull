from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal

SCALE = 1000

class LoadingBar(QDialog):
    cancelled = pyqtSignal()

    def __init__(self, total, width=30):
        _app = QApplication.instance() or QApplication([])
        super().__init__()
        self.total = total
        self._done = False  # distinguishes "closed itself on completion" from "user hit X"

        self.setWindowTitle("Stream Puller")
        self.setFixedSize(1200, 160)
        self.setStyleSheet("background-color: #0F172A; color: white;")

        self.label = QLabel("Fetching First Document...")
        self.label.setStyleSheet("color: white; font-size: 22px;")

        speed_row = QHBoxLayout()

        self.min_speed = QLabel("Min Mbps")
        self.min_speed.setStyleSheet("color: #64748B; font-size: 12px;")
        speed_row.addWidget(self.min_speed)
        speed_row.addStretch()

        self.speed = QLabel(" Mbps")
        self.speed.setStyleSheet("color: #3B82F6; font-size: 18px; font-weight: bold;")
        speed_row.addWidget(self.speed)
        speed_row.addStretch()

        self.max_speed = QLabel("Max Mbps")
        self.max_speed.setStyleSheet("color: #64748B; font-size: 12px;")
        speed_row.addWidget(self.max_speed)

        self.progress = QProgressBar()
        self.progress.setRange(0, total * SCALE)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setFixedHeight(40)
        self.progress.setStyleSheet(
            "QProgressBar { border: 1px solid #3B82F6; border-radius: 6px; text-align: center; color: white; font-size: 14px; }"
            "QProgressBar::chunk { background-color: #3B82F6; }"
        )

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(speed_row)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self._anim = QPropertyAnimation(self.progress, b"value")
        self._anim.setEasingCurve(QEasingCurve.Linear)
        self._anim.finished.connect(self._on_anim_finished)

        self.show()

    def set_total(self, total):
        self.total = total
        self.progress.setRange(0, total * SCALE)

    def update(self, current, prefix=""):
        self.label.setText(f"Loading {prefix} — {current}/{self.total}...")
        self._anim.stop()
        self._anim.setDuration(self.total * 200)
        self._anim.setStartValue(self.progress.value())
        self._anim.setEndValue(current * SCALE)
        self._pending_done = current >= self.total
        self._anim.start()

    def update_speed(self, speed, min_speed, max_speed):
        self.speed.setText(f"{speed} Mbps")
        self.min_speed.setText(f"Min_Mbps: {min_speed}")
        self.max_speed.setText(f"Max_Mbps: {max_speed}")

    def _on_anim_finished(self):
        if getattr(self, "_pending_done", False):
            self._done = True
            self.close()

    def closeEvent(self, event):
        if self._done:
            event.accept()  # this is the real, legitimate close (worker finished/failed)
            return

        self.cancelled.emit()
        event.ignore()
        