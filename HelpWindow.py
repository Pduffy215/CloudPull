from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QFrame,
    QPushButton, QHBoxLayout, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Same palette as SurveySelectorDialog, so this doesn't look bolted-on
BG_DARK = "#0F172A"
BG_PANEL = "#1E293B"
ACCENT = "#3B82F6"
ACCENT_HOVER = "#60A5FA"
TEXT_PRIMARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"
BORDER = "#334155"

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        color: {BG_DARK};
        border-radius: 4px;
        border: none;
        font-weight: bold;
        padding: 0px;
        font-size: 12pt;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
"""

# Each entry: (section title, [(item label, description), ...])
HELP_SECTIONS = [
    ("Pulling Streams", [
        ("Survey Table",
         "Each row is one survey found in ARCA, showing Company, Site, Survey, Measured time, and Status. Status shows \"Pulled\" if that survey was already pulled down once before."),
        ("Row selection",
         "Click a row to select it — the detail panel on the right updates immediately to show that survey's full info. Double-click a row to select it and confirm in one step, same as clicking Select."),
        ("Detail Preview — Survey Info",
         "Top-level fields for the survey that aren't part of Partitions or Indices — shown only if present."),
        ("Detail Preview — Partitions",
         "The provider, company, and site this survey belongs to — the identity fields ARCA uses to route and organize the data."),
        ("Detail Preview — Indices",
         "Searchable fields for this survey — survey number, measurement start time, and similar indexed values."),
        ("Select",
         "Confirms the currently highlighted row and closes the picker, returning that survey's data to continue the pull."),
    ]),
    ("Buttons", [
        ("Column headers",
         "Click a header to sort the table by that column. Click again to reverse the sort order."),
        ("Selectable text",
         "Every value in the preview can be selected and copied with your mouse, in case you need to paste a value elsewhere."),
        ("Cancel",
         "Closes the picker without choosing a survey, stopping the pull."),
        ("Help",
         "Opens this window."),
    ]),
]


class StreamPullerHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help — Stream Puller")
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(min(800, 0.7 * screen.width())), int(min(900, 0.75 * screen.height())))
        self.move(screen.center() - self.rect().center())
        self.setStyleSheet(f"background-color: {BG_DARK}; color: {TEXT_PRIMARY};")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(14)

        header = QLabel("Stream Puller — Help")
        header.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        outer.addWidget(header)

        # Scrollable content area — everything below the header scrolls independently
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_DARK}; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(24)

        for section_title, items in HELP_SECTIONS:
            content_layout.addWidget(self._make_section(section_title, items))

        content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

        # Close button, pinned below the scroll area
        button_row = QHBoxLayout()
        button_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(140, 44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(BUTTON_STYLE)
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        close_btn.clicked.connect(self.accept)
        button_row.addWidget(close_btn)
        outer.addLayout(button_row)

    def _make_section(self, title, items):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        section_label = QLabel(title)
        section_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        section_label.setStyleSheet(f"color: {ACCENT}; border: none;")
        layout.addWidget(section_label)

        for item_label, description in items:
            row = QLabel(f"<b style='color:{TEXT_PRIMARY};'>{item_label}</b><br>"
                         f"<span style='color:{TEXT_MUTED};'>{description}</span>")
            row.setWordWrap(True)
            row.setFont(QFont("Segoe UI", 11))
            row.setStyleSheet("border: none;")
            layout.addWidget(row)

        return panel


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dialog = StreamPullerHelpDialog()
    dialog.exec_()