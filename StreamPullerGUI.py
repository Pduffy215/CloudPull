from SearchArcaMatch import search_arca_match
from HelpWindow import StreamPullerHelpDialog
from Config import ARCA_API_KEY, ARCA_URL, CONFIG_DIR, ICON_PATH
from GetArcaKeys import get_arca_keys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QScrollArea, QFrame, QDialog, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QSplitter, QHeaderView, QMessageBox, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QEventLoop
from PyQt5.QtGui import QFont, QIcon, QFontMetrics
import sys
import os

# Theme constants
BG_DARK = "#0F172A"
BG_PANEL = "#1E293B"
ACCENT = "#3B82F6"
TEXT_PRIMARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"
MONO_FONT = "Courier New"

COLUMN_LABELS = ["Company", "Site", "Survey", "Measured", "Status"]



def pretty_label(key: str) -> str:
    return key.replace("_", " ").title()


def row_values(record: dict, pulled: bool) -> list:
    partitions = record.get("partitions", {}) if isinstance(record, dict) else {}
    indices = record.get("indices", {}) if isinstance(record, dict) else {}

    company = partitions.get("company_name") or ""
    site = partitions.get("site_name") or ""
    survey_no = indices.get("survey_no")
    survey_str = f"#{survey_no}" if survey_no is not None else ""
    start_time = indices.get("measurement_start_time") or ""
    log_info = "Pulled" if pulled else ""

    return [company, site, survey_str, start_time, log_info]

def build_pick(chosen):
    data = {
        "partitions": {"provider_name": chosen["partitions"]["provider_name"], "company_name": chosen["partitions"]["company_name"], "site_name": chosen["partitions"]["site_name"]},
        "indices": {"survey_number": chosen["indices"]["survey_no"]},
    }
    time_start = chosen["indices"]["measurement_start_time"]
    return time_start, data


def reselect(dialog):
    # Re-show an already-used dialog and wait for another pick. Returns (time_start, data) or None if cancelled
    dialog.selected_record = None
    dialog.setEnabled(True)
    dialog.show()

    loop = QEventLoop()
    dialog._loop = loop
    loop.exec_()

    if dialog.selected_record is not None:
        return build_pick(dialog.selected_record)
    return None

class RecordCard(QFrame):

    HIDDEN_KEYS = {"api_key", "idx_key", "doc_key"}

    def __init__(self, record: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._max_row_width = 0  # widest (key + spacing + value) row across every group, in px
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        record = self._strip_hidden_keys(record)

        scalar_fields = {k: v for k, v in record.items() if not isinstance(v, dict)}
        nested_fields = {k: v for k, v in record.items() if isinstance(v, dict)}

        if scalar_fields:
            layout.addWidget(self._make_group("Survey Info", scalar_fields))

        preferred_order = ["partitions", "indices"]
        ordered_keys = [k for k in preferred_order if k in nested_fields]
        ordered_keys += [k for k in nested_fields if k not in preferred_order]

        for section_name in ordered_keys:
            layout.addWidget(self._make_group(pretty_label(section_name), nested_fields[section_name]))

    def _strip_hidden_keys(self, record: dict) -> dict:
        cleaned = {}
        for k, v in record.items():
            if k.lower() in self.HIDDEN_KEYS or "api_key" in k.lower():
                continue
            if isinstance(v, dict):
                v = self._strip_hidden_keys(v)
            cleaned[k] = v
        return cleaned

    def _make_group(self, title: str, data: dict) -> QGroupBox:
        group = QGroupBox(title)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(8)

        for key, value in data.items():
            key_label = QLabel(pretty_label(key))
            key_label.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold;")
            key_label.setFont(QFont("Courier New", 12))

            val_label = QLabel(str(value))
            val_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val_label.setFont(QFont("Courier New", 11))
            val_label.setWordWrap(False)

            # a row's real width is key + spacing + value together, not either label alone
            key_w = QFontMetrics(key_label.font()).horizontalAdvance(key_label.text())
            val_w = QFontMetrics(val_label.font()).horizontalAdvance(val_label.text())
            row_w = key_w + val_w + form.horizontalSpacing()
            self._max_row_width = max(self._max_row_width, row_w)

            form.addRow(key_label, val_label)

        group.setLayout(form)
        return group

    def widest_row_width(self) -> int:
        return self._max_row_width


class SurveySelectorDialog(QDialog):

    def __init__(self, records: list, late_records: list, version: int, parent=None):
        super().__init__(parent)
        self.records = records
        self.late_records = late_records
        self.selected_record = None
        self._loop = None  

        self.setWindowTitle(f"Stream Puller v{version}")
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(min(1800, 0.9 * screen.width())), int(min(1000, 0.9 * screen.height())))
        self.move(screen.center() - self.rect().center())  # keep it centered too
        self._build_ui()
        self._apply_theme()

        # Preselect the first row so the preview isn't empty
        if self.table_widget.rowCount() > 0:
            self.table_widget.selectRow(0)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        header_row = QHBoxLayout()
        header = QLabel("Stream Puller")
        header.setFont(QFont(MONO_FONT, 18, QFont.Bold))
        header.setStyleSheet(f"color: {TEXT_PRIMARY};")
        header_row.addWidget(header)

        header_row.addStretch()

        help_btn = QPushButton("Help")
        help_btn.setFixedSize(100, 36)
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {BG_DARK};
                border-radius: 4px;
                border: none;
                font-weight: bold;
                padding: 0px;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: #60A5FA;
            }}
        """)
        help_btn.setFont(QFont(MONO_FONT, 11, QFont.Bold))
        help_btn.clicked.connect(self.show_help)
        header_row.addWidget(help_btn)

        outer.addLayout(header_row)

        splitter = QSplitter(Qt.Horizontal)

        # Left: table of records 
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(len(COLUMN_LABELS))
        self.table_widget.setHorizontalHeaderLabels(COLUMN_LABELS)
        self.table_widget.horizontalHeader().setFont(QFont(MONO_FONT, 16))
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setShowGrid(False)  
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.setVerticalScrollMode(QTableWidget.ScrollPerPixel)  # smooth scrolling
        self.table_widget.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)  # smooth scrolling
        self.table_widget.setSortingEnabled(True)

        self.records.extend(self.late_records)
        self.table_widget.setRowCount(len(self.records))
        for i, record in enumerate(self.records):
            pulled = record in self.late_records
            for col, value in enumerate(row_values(record, pulled)):
                cell = QTableWidgetItem(value)
                cell.setFont(QFont(MONO_FONT, 12))
                self.table_widget.setItem(i, col, cell)

        self.table_widget.currentCellChanged.connect(self._on_selection_changed)
        self.table_widget.cellDoubleClicked.connect(self._accept_selection)
        splitter.addWidget(self.table_widget)

        # Right: detail preview 
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setFrameShape(QFrame.NoFrame)
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(12, 0, 0, 0)
        self.preview_scroll.setWidget(self.preview_container)
        splitter.addWidget(self.preview_scroll)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        outer.addWidget(splitter)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Select")
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

        self.rejected.connect(self._on_rejected)

    def _on_selection_changed(self, current_row: int):
        while self.preview_layout.count():
            child = self.preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if current_row < 0 or current_row >= len(self.records):
            return

        card = RecordCard(self.records[current_row])
        self.preview_layout.addWidget(card)
        self.preview_layout.addStretch()

        # size the preview panel so the widest row isn't clipped
        needed_width = card.widest_row_width() + 80 
        self.preview_scroll.setMinimumWidth(min(needed_width, int(0.5 * self.width())))

    def _accept_selection(self):
        row = self.table_widget.currentRow()
        if row < 0:
            return
        self.selected_record = self.records[row]
        self.setEnabled(False)  # disable interaction, but stay visible for context
        if self._loop is not None:
            self._loop.quit()

    def _on_rejected(self):
        if self._loop is not None:
            self._loop.quit()

    def show_help(self):
        StreamPullerHelpDialog(self).exec_()

    def _apply_theme(self):
        self.setFont(QFont(MONO_FONT, 10))
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 6px;
                border-right: 2px solid {TEXT_MUTED};
            }}
            QFrame#card {{
                background-color: {BG_PANEL};
                border-radius: 8px;
            }}
            QGroupBox {{
                border: 1px solid {ACCENT};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 16pt;
                color: {ACCENT};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}
            QTableWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                gridline-color: {TEXT_MUTED};
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {ACCENT};
                color: {BG_DARK};
            }}
            QHeaderView::section {{
                background-color: {BG_DARK};
                color: {ACCENT};
                padding: 6px;
                border: 1px solid {ACCENT};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {ACCENT};
                color: {BG_DARK};
                border: none;
                border-radius: 4px;
                padding: 12px 72px;
                font-weight: bold;
                font-size: 24pt;
            }}
            QPushButton:hover {{
                background-color: #60A5FA;
            }}
            QScrollArea {{
                background-color: {BG_DARK};
                border: none;
            }}
        """)


def select_survey_info(data, late_data):

    records = data if isinstance(data, list) else [data]
    late_records = late_data if isinstance(late_data, list) else [late_data]

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setWindowIcon(QIcon(ICON_PATH))

    with open(os.path.join(CONFIG_DIR, "VERSION.txt"), "r") as f:
        version = f.read().strip()

    dialog = SurveySelectorDialog(records, late_records, version)
    dialog.show()

    loop = QEventLoop()
    dialog._loop = loop
    loop.exec_()

    if dialog.selected_record is not None:
        return dialog.selected_record, dialog  # dialog stays open, disabled, for context
    dialog.close()
    return None, None


def site_picker_GUI():

    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_DIRECTORY", "Streams_Directory")
    json = {}
    directories = search_arca_match(idx_key, json)

    idx_key = get_arca_keys(ARCA_URL, ARCA_API_KEY, "VSC_STREAMS_LOG", "Streams_Log")
    entries = []
    late_entries = []
    unposted_names = []  # not added to either list — just reported via a warning

    for entry in directories[::-1]:
        json = {
            "partitions": {"provider_name": entry["partitions"]["provider_name"], "company_name": entry["partitions"]["company_name"], "site_name": entry["partitions"]["site_name"]},
            "indices": {"survey_no": entry["indices"]["survey_no"]},
        }
        log_response = search_arca_match(idx_key, json)

        if len(log_response) == 2:
            late_entries.append(entry)
        elif len(log_response) == 1:
            entries.append(entry)
        elif len(log_response) == 0:
            site_name = entry["partitions"]["site_name"]
            survey_no = entry["indices"]["survey_no"]
            unposted_names.append(f"{site_name} — Survey #{survey_no}")

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))

    if unposted_names:
        QMessageBox.warning(
            None,
            "Hasn't Been Posted",
            "The following haven't been posted and are not shown below:\n\n" + "\n".join(unposted_names)
        )

    chosen, dialog = select_survey_info(entries, late_entries)

    if chosen is not None:
        time_start, data = build_pick(chosen)
        return time_start, data, dialog


if __name__ == "__main__":

    result = site_picker_GUI()
    if result is None:
        print("No site selected — exiting.\n")

    else:
        time_start, data, dialog = result
        print(f"\nData: {data}")
        print(f"TimeStart: {time_start}\n")