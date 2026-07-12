"""Date picker widget for GUI"""

import calendar
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QDialogButtonBox,
    QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def get_next_sunday_22utc(start_hour=22):
    """Return the next Sunday at start_hour UTC."""
    now = datetime.utcnow()
    days_ahead = 6 - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_sunday = now + timedelta(days=days_ahead)
    return next_sunday.replace(hour=start_hour, minute=0, second=0, microsecond=0)


def get_two_weeks_sunday_22utc(start_date, cadence="2 weeks", end_hour=22):
    """Return end date N weeks ahead from start_date on a Sunday at end_hour UTC."""
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        except ValueError:
            start_date = datetime.utcnow()

    days_to_add = 14 if cadence == "2 weeks" else 7
    end_date = start_date + timedelta(days=days_to_add)
    days_ahead = 6 - end_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    elif days_ahead > 0:
        end_date += timedelta(days=days_ahead)
    return end_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)


class DatePickerDialog(QDialog):
    """Calendar date-picker dialog with time selection."""

    # QSS color names for day button states (set as objectName + dynamic property)
    _STYLE_SELECTED = "background-color: #007acc; color: white; border-radius: 3px;"
    _STYLE_RANGE = "background-color: #4a9eff; color: white; border-radius: 3px;"
    _STYLE_TODAY = "border: 2px solid #007acc; border-radius: 3px;"
    _STYLE_NORMAL = ""
    _STYLE_EMPTY = "color: transparent; background: transparent; border: none;"

    def __init__(self, parent, title="Select Date", initial_date=None, range_start=None, range_end=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(440, 420)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.result_str = None
        self.today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Parse initial date
        if initial_date:
            try:
                if isinstance(initial_date, str):
                    try:
                        self.selected_date = datetime.strptime(initial_date, "%Y-%m-%d %H:%M")
                    except ValueError:
                        d = datetime.strptime(initial_date.split()[0], "%Y-%m-%d")
                        self.selected_date = d.replace(hour=22, minute=0)
                else:
                    self.selected_date = initial_date
            except (ValueError, IndexError):
                self.selected_date = datetime.utcnow().replace(hour=22, minute=0)
        else:
            self.selected_date = datetime.utcnow().replace(hour=22, minute=0)

        # Parse range
        self.range_start = self._parse_date(range_start)
        self.range_end = self._parse_date(range_end)

        self.current_month = self.selected_date.month
        self.current_year = self.selected_date.year

        self._create_ui()

    @staticmethod
    def _parse_date(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            return datetime.strptime(str(value).split()[0], "%Y-%m-%d")
        except (ValueError, IndexError):
            return None

    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Navigation row
        nav = QHBoxLayout()
        prev_btn = QPushButton("‹")
        prev_btn.setFixedWidth(36)
        prev_btn.clicked.connect(self._prev_month)
        nav.addWidget(prev_btn)

        self.month_label = QLabel()
        f = QFont()
        f.setBold(True)
        f.setPointSize(f.pointSize() + 1)
        self.month_label.setFont(f)
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav.addWidget(self.month_label, 1)

        next_btn = QPushButton("›")
        next_btn.setFixedWidth(36)
        next_btn.clicked.connect(self._next_month)
        nav.addWidget(next_btn)
        layout.addLayout(nav)

        # Calendar grid
        self._cal_widget = QWidget()
        self._cal_layout = QGridLayout(self._cal_widget)
        self._cal_layout.setSpacing(2)
        self._cal_layout.setContentsMargins(0, 0, 0, 0)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        bold = QFont()
        bold.setBold(True)
        for i, day in enumerate(days):
            lbl = QLabel(day)
            lbl.setFont(bold)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cal_layout.addWidget(lbl, 0, i)

        self.day_buttons = []
        for row in range(6):
            row_btns = []
            for col in range(7):
                btn = QPushButton()
                btn.setFixedSize(46, 30)
                r, c = row, col
                btn.clicked.connect(lambda checked=False, rr=r, cc=c: self._select_day(rr, cc))
                self._cal_layout.addWidget(btn, row + 1, col)
                row_btns.append(btn)
            self.day_buttons.append(row_btns)

        layout.addWidget(self._cal_widget)

        # Time row
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("Time (UTC):"))

        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(self.selected_date.hour)
        self.hour_spin.setFixedWidth(60)
        self.hour_spin.setWrapping(True)
        time_row.addWidget(self.hour_spin)

        time_row.addWidget(QLabel(":"))

        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(self.selected_date.minute)
        self.minute_spin.setFixedWidth(60)
        self.minute_spin.setWrapping(True)
        time_row.addWidget(self.minute_spin)
        time_row.addStretch()
        layout.addLayout(time_row)

        # OK / Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_calendar()

    def _update_calendar(self):
        month_name = calendar.month_name[self.current_month]
        self.month_label.setText(f"{month_name} {self.current_year}")

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for row_idx in range(6):
            week = cal[row_idx] if row_idx < len(cal) else [0] * 7
            for col_idx in range(7):
                btn = self.day_buttons[row_idx][col_idx]
                day = week[col_idx]

                if day == 0:
                    btn.setText("")
                    btn.setEnabled(False)
                    btn.setStyleSheet(self._STYLE_EMPTY)
                    continue

                btn.setText(str(day))
                btn.setEnabled(True)

                current_date = datetime(self.current_year, self.current_month, day)

                is_selected = (
                    day == self.selected_date.day
                    and self.current_month == self.selected_date.month
                    and self.current_year == self.selected_date.year
                )
                is_today = (
                    day == self.today.day
                    and self.current_month == self.today.month
                    and self.current_year == self.today.year
                )
                in_range = False
                if self.range_start and self.range_end:
                    in_range = self.range_start <= current_date <= self.range_end

                if is_selected:
                    btn.setStyleSheet(self._STYLE_SELECTED)
                elif in_range:
                    btn.setStyleSheet(self._STYLE_RANGE)
                elif is_today:
                    btn.setStyleSheet(self._STYLE_TODAY)
                else:
                    btn.setStyleSheet(self._STYLE_NORMAL)

    def _select_day(self, row, col):
        text = self.day_buttons[row][col].text()
        if text:
            day = int(text)
            self.selected_date = self.selected_date.replace(year=self.current_year, month=self.current_month, day=day)
            self._update_calendar()

    def _prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._update_calendar()

    def _next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self._update_calendar()

    def _ok(self):
        self.selected_date = self.selected_date.replace(
            hour=self.hour_spin.value(),
            minute=self.minute_spin.value(),
        )
        self.result_str = self.selected_date.strftime("%Y-%m-%d %H:%M")
        self.accept()

    def get_result(self):
        """Return the selected datetime string, or None if cancelled."""
        return self.result_str
