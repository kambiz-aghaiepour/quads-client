"""Reusable host metadata filter widget for Available and Schedule views"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QCheckBox, QGroupBox,
)
from PySide6.QtCore import Qt

from quads_client.qt6.widgets.date_picker import DatePickerDialog


class HostFilterFrame(QWidget):
    """Reusable filter panel for host metadata search.

    Provides primary filters (Model, RAM, Start/End dates) and a collapsible
    advanced section (Disk, NIC, GPU filters). Used in both Available and
    Schedule views.
    """

    DISK_TYPES = ["All", "nvme", "ssd", "sata"]

    def __init__(self, parent, shell, show_dates=True):
        super().__init__(parent)
        self.shell = shell
        self.show_dates = show_dates
        self._advanced_visible = False
        self._create_ui()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # Row 1: Model + RAM
        row1 = QWidget()
        h1 = QHBoxLayout(row1)
        h1.setContentsMargins(0, 0, 0, 0)

        h1.addWidget(QLabel("Model:"))
        models = ["All"] + self.shell.get_available_models()
        self.model_combo = QComboBox()
        self.model_combo.addItems(models)
        self.model_combo.setFixedWidth(150)
        h1.addWidget(self.model_combo)
        h1.addSpacing(20)

        h1.addWidget(QLabel("RAM (GB):"))
        self.ram_entry = QLineEdit()
        self.ram_entry.setFixedWidth(80)
        h1.addWidget(self.ram_entry)
        h1.addStretch()
        root.addWidget(row1)

        # Row 2: Start/End dates (optional)
        if self.show_dates:
            row2 = QWidget()
            h2 = QHBoxLayout(row2)
            h2.setContentsMargins(0, 0, 0, 0)

            h2.addWidget(QLabel("Start Date:"))
            self.start_entry = QLineEdit()
            self.start_entry.setFixedWidth(150)
            h2.addWidget(self.start_entry)
            cal_start = QPushButton("📅")
            cal_start.setFixedWidth(32)
            cal_start.clicked.connect(self._pick_start_date)
            h2.addWidget(cal_start)
            h2.addSpacing(15)

            h2.addWidget(QLabel("End Date:"))
            self.end_entry = QLineEdit()
            self.end_entry.setFixedWidth(150)
            h2.addWidget(self.end_entry)
            cal_end = QPushButton("📅")
            cal_end.setFixedWidth(32)
            cal_end.clicked.connect(self._pick_end_date)
            h2.addWidget(cal_end)
            h2.addStretch()
            root.addWidget(row2)

        # Row 3: Advanced toggle
        self._adv_toggle_btn = QPushButton("▶ Advanced Filters")
        self._adv_toggle_btn.clicked.connect(self._toggle_advanced)
        self._adv_toggle_btn.setFixedWidth(160)
        root.addWidget(self._adv_toggle_btn)

        # Advanced group box (initially hidden)
        self._advanced_group = QGroupBox("Advanced Filters")
        adv_layout = QGridLayout(self._advanced_group)
        adv_layout.setSpacing(6)

        adv_layout.addWidget(QLabel("Disk Type:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.disk_type_combo = QComboBox()
        self.disk_type_combo.addItems(self.DISK_TYPES)
        self.disk_type_combo.setFixedWidth(100)
        adv_layout.addWidget(self.disk_type_combo, 0, 1)

        adv_layout.addWidget(QLabel("Disk Size (GB):"), 0, 2, Qt.AlignmentFlag.AlignRight)
        self.disk_size_entry = QLineEdit()
        self.disk_size_entry.setFixedWidth(80)
        adv_layout.addWidget(self.disk_size_entry, 0, 3)

        adv_layout.addWidget(QLabel("Disk Count:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.disk_count_entry = QLineEdit()
        self.disk_count_entry.setFixedWidth(80)
        adv_layout.addWidget(self.disk_count_entry, 1, 1)

        adv_layout.addWidget(QLabel("NIC Vendor:"), 1, 2, Qt.AlignmentFlag.AlignRight)
        nic_vendors = ["All"] + self.shell.get_available_nic_vendors()
        self.nic_vendor_combo = QComboBox()
        self.nic_vendor_combo.addItems(nic_vendors)
        self.nic_vendor_combo.setFixedWidth(180)
        adv_layout.addWidget(self.nic_vendor_combo, 1, 3)

        adv_layout.addWidget(QLabel("NIC Speed (Gbps):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        self.nic_speed_entry = QLineEdit()
        self.nic_speed_entry.setFixedWidth(80)
        adv_layout.addWidget(self.nic_speed_entry, 2, 1)

        self.gpu_check = QCheckBox("Has GPU")
        adv_layout.addWidget(self.gpu_check, 2, 2)

        self._advanced_group.setVisible(False)
        root.addWidget(self._advanced_group)

    def _toggle_advanced(self):
        self._advanced_visible = not self._advanced_visible
        self._advanced_group.setVisible(self._advanced_visible)
        self._adv_toggle_btn.setText(
            "▼ Advanced Filters" if self._advanced_visible else "▶ Advanced Filters"
        )

    def _pick_start_date(self):
        range_end = self.end_entry.get() if hasattr(self, "end_entry") else None
        picker = DatePickerDialog(
            self.window(),
            "Select Start Date",
            self.start_entry.text() or None,
            range_start=self.start_entry.text() or None,
            range_end=range_end,
        )
        picker.exec()
        result = picker.get_result()
        if result:
            self.start_entry.setText(result)

    def _pick_end_date(self):
        range_start = self.start_entry.text() if hasattr(self, "start_entry") else None
        picker = DatePickerDialog(
            self.window(),
            "Select End Date",
            self.end_entry.text() or None,
            range_start=range_start,
            range_end=self.end_entry.text() or None,
        )
        picker.exec()
        result = picker.get_result()
        if result:
            self.end_entry.setText(result)

    def get_filters(self):
        """Return active filters as a dict with API filter keys."""
        filters = {}

        model = self.model_combo.currentText()
        if model and model != "All":
            filters["model"] = model.upper()

        ram = self.ram_entry.text().strip()
        if ram:
            try:
                filters["memory__gte"] = int(ram) * 1024
            except ValueError:
                pass

        if self.show_dates:
            start = self.start_entry.text().strip()
            if start:
                filters["start"] = start.split()[0]
            end = self.end_entry.text().strip()
            if end:
                filters["end"] = end.split()[0]

        if self._advanced_visible:
            disk_type = self.disk_type_combo.currentText()
            if disk_type and disk_type != "All":
                filters["disks.disk_type"] = disk_type

            disk_size = self.disk_size_entry.text().strip()
            if disk_size:
                try:
                    filters["disks.size_gb__gte"] = int(disk_size)
                except ValueError:
                    pass

            disk_count = self.disk_count_entry.text().strip()
            if disk_count:
                try:
                    filters["disks.count__gte"] = int(disk_count)
                except ValueError:
                    pass

            nic_vendor = self.nic_vendor_combo.currentText()
            if nic_vendor and nic_vendor != "All":
                filters["interfaces.vendor"] = nic_vendor

            nic_speed = self.nic_speed_entry.text().strip()
            if nic_speed:
                try:
                    filters["interfaces.speed__gte"] = int(nic_speed)
                except ValueError:
                    pass

            if self.gpu_check.isChecked():
                filters["processors.vendor__like"] = "%"

        return filters

    def clear_filters(self):
        """Reset all filters to defaults."""
        self.model_combo.setCurrentIndex(0)
        self.ram_entry.clear()

        if self.show_dates:
            self.start_entry.clear()
            self.end_entry.clear()

        self.disk_type_combo.setCurrentIndex(0)
        self.disk_size_entry.clear()
        self.disk_count_entry.clear()
        self.nic_vendor_combo.setCurrentIndex(0)
        self.nic_speed_entry.clear()
        self.gpu_check.setChecked(False)
