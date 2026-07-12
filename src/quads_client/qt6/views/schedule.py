"""Schedule view for non-admin users"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QRadioButton, QButtonGroup, QSpinBox, QFileDialog,
    QScrollArea, QGroupBox, QFrame, QTextEdit, QListWidget,
    QAbstractItemView, QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from quads_client.qt6.widgets.date_picker import DatePickerDialog, get_next_sunday_22utc, get_two_weeks_sunday_22utc
from quads_client.qt6.widgets.host_filters import HostFilterFrame
from quads_client.qt6.widgets.dialogs import show_error_dialog


class ScheduleView(QWidget):
    """Schedule a cloud/host assignment (non-admin version)."""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self._available_hosts_loaded = False
        self._create_ui()

    def _create_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(20, 10, 20, 10)
        title_lbl = QLabel("Schedule Hosts")
        tf = title_lbl.font()
        tf.setPointSize(tf.pointSize() + 2)
        tf.setBold(True)
        title_lbl.setFont(tf)
        tbl.addWidget(title_lbl)
        tbl.addStretch()
        root.addWidget(title_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 12, 20, 20)
        cl.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # --- Mode selection ---
        mode_group = QGroupBox("Assignment Mode")
        mode_layout = QVBoxLayout(mode_group)
        self._mode_group = QButtonGroup(self)

        self._count_radio = QRadioButton("Reserve a count of matching hosts")
        self._count_radio.setChecked(True)
        self._mode_group.addButton(self._count_radio, 0)
        mode_layout.addWidget(self._count_radio)

        self._hosts_radio = QRadioButton("Specify hosts by name")
        self._mode_group.addButton(self._hosts_radio, 1)
        mode_layout.addWidget(self._hosts_radio)

        self._file_radio = QRadioButton("Load host list from file")
        self._mode_group.addButton(self._file_radio, 2)
        mode_layout.addWidget(self._file_radio)

        self._mode_group.idToggled.connect(self._on_mode_changed)
        cl.addWidget(mode_group)

        # --- Count mode panel ---
        self._count_panel = QGroupBox("Count & Filters")
        count_layout = QGridLayout(self._count_panel)
        count_layout.setSpacing(8)

        count_layout.addWidget(QLabel("Number of hosts:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 500)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(90)
        count_layout.addWidget(self.count_spin, 0, 1)

        # Host filters for count mode
        self.host_filters = HostFilterFrame(self, self.shell, show_dates=False)
        count_layout.addWidget(self.host_filters, 1, 0, 1, 2)
        cl.addWidget(self._count_panel)

        # --- Hosts mode panel ---
        self._hosts_panel = QGroupBox("Host Names")
        hosts_layout = QVBoxLayout(self._hosts_panel)
        hosts_layout.addWidget(QLabel("Enter hostnames separated by commas or newlines:"))
        self.hosts_entry = QLineEdit()
        self.hosts_entry.setPlaceholderText("e.g. host01,host02,host03")
        hosts_layout.addWidget(self.hosts_entry)

        # Available hosts browser (collapsible)
        self._avail_toggle_btn = QPushButton("▶ Browse Available Hosts")
        self._avail_toggle_btn.clicked.connect(self._toggle_available_hosts)
        hosts_layout.addWidget(self._avail_toggle_btn)

        self._avail_group = QGroupBox("Available Hosts")
        avail_inner = QVBoxLayout(self._avail_group)
        self._avail_list = QListWidget()
        self._avail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._avail_list.setFixedHeight(120)
        avail_inner.addWidget(self._avail_list)
        use_sel_btn = QPushButton("Use Selected Hosts")
        use_sel_btn.clicked.connect(self._use_selected_hosts)
        avail_inner.addWidget(use_sel_btn)
        self._avail_group.setVisible(False)
        hosts_layout.addWidget(self._avail_group)
        self._hosts_panel_visible = False

        self._hosts_panel.setVisible(False)
        cl.addWidget(self._hosts_panel)

        # --- File mode panel ---
        self._file_panel = QGroupBox("Host File")
        file_layout = QHBoxLayout(self._file_panel)
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText("Path to file with one hostname per line")
        file_layout.addWidget(self.file_entry)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        self._file_panel.setVisible(False)
        cl.addWidget(self._file_panel)

        # --- Cloud / Assignment ---
        cloud_group = QGroupBox("Cloud & Assignment")
        cloud_layout = QGridLayout(cloud_group)
        cloud_layout.setSpacing(8)

        cloud_layout.addWidget(QLabel("Cloud name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.cloud_entry = QLineEdit()
        self.cloud_entry.setPlaceholderText("e.g. cloud08")
        cloud_layout.addWidget(self.cloud_entry, 0, 1)

        cloud_layout.addWidget(QLabel("Description:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.desc_entry = QLineEdit()
        self.desc_entry.setPlaceholderText("Optional description")
        cloud_layout.addWidget(self.desc_entry, 1, 1)
        cl.addWidget(cloud_group)

        # --- Dates ---
        dates_group = QGroupBox("Schedule Dates")
        dates_layout = QGridLayout(dates_group)
        dates_layout.setSpacing(8)

        dates_layout.addWidget(QLabel("Start date (UTC):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        self.start_entry = QLineEdit()
        self.start_entry.setFixedWidth(160)
        dates_layout.addWidget(self.start_entry, 0, 1)
        cal_start_btn = QPushButton("📅")
        cal_start_btn.setFixedWidth(34)
        cal_start_btn.clicked.connect(self._pick_start_date)
        dates_layout.addWidget(cal_start_btn, 0, 2)

        dates_layout.addWidget(QLabel("End date (UTC):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        self.end_entry = QLineEdit()
        self.end_entry.setFixedWidth(160)
        dates_layout.addWidget(self.end_entry, 1, 1)
        cal_end_btn = QPushButton("📅")
        cal_end_btn.setFixedWidth(34)
        cal_end_btn.clicked.connect(self._pick_end_date)
        dates_layout.addWidget(cal_end_btn, 1, 2)

        now_tip = QLabel("Dates use YYYY-MM-DD HH:MM format in UTC")
        now_tip.setStyleSheet("color: gray; font-size: 10px;")
        dates_layout.addWidget(now_tip, 2, 0, 1, 3)

        # Set default dates
        start_default = get_next_sunday_22utc()
        self.start_entry.setText(start_default.strftime("%Y-%m-%d %H:%M"))
        end_default = get_two_weeks_sunday_22utc(start_default)
        self.end_entry.setText(end_default.strftime("%Y-%m-%d %H:%M"))

        cl.addWidget(dates_group)

        # --- Action buttons ---
        btn_row = QWidget()
        brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(0, 0, 0, 0)
        preview_btn = QPushButton("Preview")
        preview_btn.clicked.connect(self._preview_schedule)
        brl.addWidget(preview_btn)
        submit_btn = QPushButton("Submit Schedule")
        submit_btn.clicked.connect(self._submit_schedule)
        brl.addWidget(submit_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_form)
        brl.addWidget(clear_btn)
        brl.addStretch()
        cl.addWidget(btn_row)

        # --- Preview / Result ---
        result_group = QGroupBox("Result")
        result_layout = QVBoxLayout(result_group)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        self.result_text.setFont(mono)
        self.result_text.setMinimumHeight(120)
        result_layout.addWidget(self.result_text)
        cl.addWidget(result_group)

        cl.addStretch()

    def _on_mode_changed(self, button_id, checked):
        if not checked:
            return
        mode = self._mode_group.checkedId()
        self._count_panel.setVisible(mode == 0)
        self._hosts_panel.setVisible(mode == 1)
        self._file_panel.setVisible(mode == 2)

    def _toggle_available_hosts(self):
        self._hosts_panel_visible = not self._hosts_panel_visible
        self._avail_group.setVisible(self._hosts_panel_visible)
        self._avail_toggle_btn.setText(
            "▼ Browse Available Hosts" if self._hosts_panel_visible else "▶ Browse Available Hosts"
        )
        if self._hosts_panel_visible and not self._available_hosts_loaded:
            self._load_available_hosts()

    def _load_available_hosts(self):
        self._avail_list.clear()
        self._avail_list.addItem("Loading…")
        try:
            from quads_client.qt6.widgets.base import _WorkerThread

            def fetch():
                return self.shell.host_commands.get_hosts_programmatic(filter_params={"retired": False, "broken": False})

            thread = _WorkerThread(fetch)
            thread.result_ready.connect(self._populate_avail_list)
            thread.error_occurred.connect(lambda e: self._avail_list.clear())
            thread.start()
            self._avail_thread = thread
        except Exception:
            self._avail_list.clear()

    def _populate_avail_list(self, hosts):
        self._avail_list.clear()
        self._available_hosts_loaded = True
        if not hosts:
            self._avail_list.addItem("No hosts found")
            return
        for host in sorted(hosts, key=lambda h: h.get("name", "")):
            self._avail_list.addItem(host.get("name", ""))

    def _use_selected_hosts(self):
        selected_items = self._avail_list.selectedItems()
        if not selected_items:
            return
        hostnames = [item.text() for item in selected_items]
        current = self.hosts_entry.text().strip()
        if current:
            existing = [h.strip() for h in current.replace("\n", ",").split(",") if h.strip()]
            for h in hostnames:
                if h not in existing:
                    existing.append(h)
            self.hosts_entry.setText(",".join(existing))
        else:
            self.hosts_entry.setText(",".join(hostnames))

    def prefill_hosts(self, hostnames):
        """Called by available.py to prefill host names."""
        if not hostnames:
            return
        self._hosts_radio.setChecked(True)
        self.hosts_entry.setText(",".join(hostnames))

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Host File", "", "Text files (*.txt);;All files (*)")
        if path:
            self.file_entry.setText(path)

    def _pick_start_date(self):
        picker = DatePickerDialog(self, "Select Start Date", self.start_entry.text() or None)
        picker.exec()
        result = picker.get_result()
        if result:
            self.start_entry.setText(result)

    def _pick_end_date(self):
        range_start = self.start_entry.text() or None
        picker = DatePickerDialog(self, "Select End Date", self.end_entry.text() or None,
                                  range_start=range_start)
        picker.exec()
        result = picker.get_result()
        if result:
            self.end_entry.setText(result)

    def _build_params(self):
        """Collect form values into dict for API call. Returns (params, error_string)."""
        mode = self._mode_group.checkedId()
        cloud = self.cloud_entry.text().strip()
        start = self.start_entry.text().strip()
        end = self.end_entry.text().strip()

        if not cloud:
            return None, "Cloud name is required"
        if not start:
            return None, "Start date is required"
        if not end:
            return None, "End date is required"

        params = {
            "cloud": cloud,
            "description": self.desc_entry.text().strip(),
            "start": start,
            "end": end,
        }

        if mode == 0:
            params["count"] = self.count_spin.value()
            filters = self.host_filters.get_filters()
            params.update(filters)
        elif mode == 1:
            raw = self.hosts_entry.text().strip()
            if not raw:
                return None, "Enter at least one hostname"
            hosts = [h.strip() for h in raw.replace("\n", ",").split(",") if h.strip()]
            params["hosts"] = hosts
        elif mode == 2:
            file_path = self.file_entry.text().strip()
            if not file_path:
                return None, "Select a file"
            try:
                with open(file_path) as fh:
                    hosts = [line.strip() for line in fh if line.strip()]
                if not hosts:
                    return None, "File is empty"
                params["hosts"] = hosts
            except OSError as e:
                return None, f"Could not read file: {e}"

        return params, None

    def _preview_schedule(self):
        params, error = self._build_params()
        if error:
            QMessageBox.critical(self, "Form Error", error)
            return

        self.result_text.clear()
        self.result_text.setPlainText("Checking availability…")

        try:
            if "hosts" in params:
                lines = ["Hosts to schedule:"]
                for h in params["hosts"]:
                    lines.append(f"  {h}")
                lines.append(f"\nCloud: {params['cloud']}")
                lines.append(f"Start: {params['start']}")
                lines.append(f"End:   {params['end']}")
                if params.get("description"):
                    lines.append(f"Description: {params['description']}")
                preview_text = "\n".join(lines)
            else:
                result = self.shell.host_commands.get_available_hosts_programmatic(
                    start=params.get("start"),
                    end=params.get("end"),
                    filter_params={k: v for k, v in params.items()
                                   if k not in ("cloud", "description", "start", "end", "count")},
                )
                count = params.get("count", 1)
                available = result or []
                avail_names = [h.get("name", "") for h in available[:count]]
                lines = [f"Would schedule {min(count, len(available))} of {len(available)} available hosts:"]
                for n in avail_names:
                    lines.append(f"  {n}")
                if len(available) < count:
                    lines.append(f"\n⚠ Only {len(available)} hosts match (requested {count})")
                lines.append(f"\nCloud: {params['cloud']}")
                lines.append(f"Start: {params['start']}")
                lines.append(f"End:   {params['end']}")
                preview_text = "\n".join(lines)
            self.result_text.setPlainText(preview_text)
        except Exception as exc:
            import traceback
            self.result_text.setPlainText(f"Preview error:\n{exc}\n\n{traceback.format_exc()}")

    def _submit_schedule(self):
        if not self.shell.is_authenticated():
            QMessageBox.critical(self, "Not Authenticated", "Please connect and login first")
            return

        params, error = self._build_params()
        if error:
            QMessageBox.critical(self, "Form Error", error)
            return

        result = QMessageBox.question(
            self,
            "Confirm",
            f"Submit schedule for cloud '{params['cloud']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        self.result_text.clear()
        self.result_text.setPlainText("Submitting schedule…")

        try:
            success, message, details = self.shell.schedule_commands.create_schedule_programmatic(**params)
            if success:
                self.result_text.setPlainText(f"✓ Schedule created successfully\n\n{message or ''}")
            else:
                self.result_text.setPlainText(f"✗ Schedule failed:\n\n{message or ''}")
        except Exception as exc:
            import traceback
            self.result_text.setPlainText(f"Error:\n{exc}\n\n{traceback.format_exc()}")

    def _clear_form(self):
        self.cloud_entry.clear()
        self.desc_entry.clear()
        self.hosts_entry.clear()
        self.file_entry.clear()
        self.count_spin.setValue(1)
        self.host_filters.clear_filters()
        self.result_text.clear()
        start_default = get_next_sunday_22utc()
        self.start_entry.setText(start_default.strftime("%Y-%m-%d %H:%M"))
        end_default = get_two_weeks_sunday_22utc(start_default)
        self.end_entry.setText(end_default.strftime("%Y-%m-%d %H:%M"))
        self._count_radio.setChecked(True)

    def refresh(self):
        pass
