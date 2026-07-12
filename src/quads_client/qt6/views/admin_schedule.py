"""Admin schedule management view"""

import shlex
import traceback

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QScrollArea,
    QGroupBox,
    QFrame,
    QDialog,
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QCheckBox,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt

from quads_client.qt6.widgets.base import BaseAdminView, FormDialog, ScrolledTreeview
from quads_client.qt6.widgets.date_picker import DatePickerDialog, get_next_sunday_22utc, get_two_weeks_sunday_22utc
from quads_client.qt6.widgets.dialogs import show_error_dialog


class AdminScheduleView(BaseAdminView):
    """Admin view for managing host assignments and schedules."""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Schedule Management", requires_admin=True)
        self._create_ui()

    def _create_ui(self):
        if not self.check_auth():
            return

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 10, 20, 20)
        cl.setSpacing(10)

        # Filter bar
        filter_bar = QWidget()
        fbl = QHBoxLayout(filter_bar)
        fbl.setContentsMargins(0, 0, 0, 0)
        fbl.addWidget(QLabel("Cloud:"))
        self.cloud_filter_entry = QLineEdit()
        self.cloud_filter_entry.setFixedWidth(160)
        self.cloud_filter_entry.setPlaceholderText("cloud name")
        fbl.addWidget(self.cloud_filter_entry)
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self._apply_filter)
        fbl.addWidget(filter_btn)
        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self._clear_filter)
        fbl.addWidget(clear_filter_btn)
        fbl.addStretch()
        cl.addWidget(filter_bar)

        # Action buttons
        action_bar = self.create_action_bar([
            ("+ Create Schedule", self._create_schedule),
            ("↔ Extend", self._extend_schedule),
            ("⊢ Shrink", self._shrink_schedule),
            ("⊠ Terminate", self._terminate_schedule),
            (
                "⟳ Refresh",
                lambda: self.safe_load_data_async(
                    self._fetch_schedules,
                    self._populate_tree,
                    disable_widgets=[self.tree.tree],
                ),
            ),
        ])
        cl.addWidget(action_bar)

        # Assignments tree
        columns = ("id", "cloud", "description", "owner", "validated")
        column_configs = {
            "id": ("ID", 80),
            "cloud": ("Cloud", 120),
            "description": ("Description", 300),
            "owner": ("Owner", 150),
            "validated": ("Validated", 100),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs)
        cl.addWidget(self.tree, 1)

        self.status_label = self.create_status_label()
        cl.addWidget(self.status_label)

        self._main_layout.addWidget(content, 1)

        self.safe_load_data_async(
            self._fetch_schedules,
            self._populate_tree,
            disable_widgets=[self.tree.tree],
        )

    def _fetch_schedules(self):
        cloud_filter = self.cloud_filter_entry.text().strip() if hasattr(self, "cloud_filter_entry") else ""
        filters = {"active": True}
        if cloud_filter:
            filters["cloud"] = cloud_filter
        return self.shell.connection.api.filter_assignments(filters)

    def _populate_tree(self, assignments):
        from quads_client.utils import extract_assignment_id, extract_cloud_name

        self.tree.clear()
        if not assignments:
            self.update_status("No assignments found")
            return
        for assignment in assignments:
            if not isinstance(assignment, dict):
                continue
            assignment_id = extract_assignment_id(assignment)
            cloud_name = extract_cloud_name(assignment)
            description = assignment.get("description", "")
            owner = assignment.get("owner", "")
            validated = "✓" if assignment.get("validated") else "○"
            self.tree.insert("", 0, values=(assignment_id, cloud_name, description, owner, validated))
        self.update_status(f"{len(assignments)} assignment(s)")

    def _apply_filter(self):
        self.safe_load_data_async(
            self._fetch_schedules,
            self._populate_tree,
            disable_widgets=[self.tree.tree],
        )

    def _clear_filter(self):
        self.cloud_filter_entry.clear()
        self._apply_filter()

    def _get_selected_data(self):
        """Return (item, assignment_id, cloud_name) for the selected tree row."""
        item, values = self.get_selected_item("Please select an assignment")
        if not values:
            return None, None, None
        assignment_id = values[0] if values else None
        cloud_name = values[1] if len(values) > 1 else None
        return item, assignment_id, cloud_name

    def _create_schedule(self, prefill_hosts=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Schedule")
        dialog.resize(560, 620)
        dialog.setMinimumSize(500, 560)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        dlayout = QVBoxLayout(dialog)
        dlayout.setContentsMargins(0, 0, 0, 0)

        header_lbl = QLabel("Create Host Schedule")
        hf = header_lbl.font()
        hf.setBold(True)
        hf.setPointSize(hf.pointSize() + 1)
        header_lbl.setFont(hf)
        header_lbl.setContentsMargins(20, 12, 20, 0)
        dlayout.addWidget(header_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        form_container = QWidget()
        form_main_layout = QVBoxLayout(form_container)
        form_main_layout.setContentsMargins(20, 10, 20, 10)
        form_main_layout.setSpacing(14)
        scroll.setWidget(form_container)
        dlayout.addWidget(scroll, 1)

        # Hosts
        hosts_group = QGroupBox("Hosts")
        hosts_vl = QVBoxLayout(hosts_group)

        host_mode_group = QButtonGroup(dialog)
        list_radio = QRadioButton("Comma-separated list:")
        list_radio.setChecked(True)
        host_mode_group.addButton(list_radio, 0)
        hosts_vl.addWidget(list_radio)

        hosts_entry = QLineEdit()
        hosts_entry.setPlaceholderText("e.g. host01,host02,host03")
        if prefill_hosts:
            hosts_entry.setText(prefill_hosts if isinstance(prefill_hosts, str) else ",".join(prefill_hosts))
        hosts_vl.addWidget(hosts_entry)

        file_radio = QRadioButton("From file:")
        host_mode_group.addButton(file_radio, 1)
        hosts_vl.addWidget(file_radio)

        file_row = QWidget()
        file_rl = QHBoxLayout(file_row)
        file_rl.setContentsMargins(0, 0, 0, 0)
        file_entry = QLineEdit()
        file_entry.setPlaceholderText("Path to file with one hostname per line")
        file_rl.addWidget(file_entry)
        browse_btn = QPushButton("Browse…")

        def browse_file():
            path, _ = QFileDialog.getOpenFileName(dialog, "Select Host List File", "", "All Files (*)")
            if path:
                file_entry.setText(path)

        browse_btn.clicked.connect(browse_file)
        file_rl.addWidget(browse_btn)
        hosts_vl.addWidget(file_row)

        def on_host_mode_toggle(button_id, checked):
            if not checked:
                return
            hosts_entry.setEnabled(button_id == 0)
            file_entry.setEnabled(button_id == 1)
            browse_btn.setEnabled(button_id == 1)

        host_mode_group.idToggled.connect(on_host_mode_toggle)
        file_entry.setEnabled(False)
        browse_btn.setEnabled(False)

        form_main_layout.addWidget(hosts_group)

        # Cloud & assignment
        assign_group = QGroupBox("Cloud & Assignment")
        assign_gl = QGridLayout(assign_group)
        assign_gl.setSpacing(8)

        assign_gl.addWidget(QLabel("Cloud name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        cloud_entry = QLineEdit()
        cloud_entry.setPlaceholderText("e.g. cloud08")
        assign_gl.addWidget(cloud_entry, 0, 1)

        assign_gl.addWidget(QLabel("Cloud owner:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        owner_entry = QLineEdit()
        owner_entry.setPlaceholderText("username")
        assign_gl.addWidget(owner_entry, 1, 1)

        assign_gl.addWidget(QLabel("Description:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        desc_entry = QLineEdit()
        desc_entry.setPlaceholderText("Optional")
        assign_gl.addWidget(desc_entry, 2, 1)

        assign_gl.addWidget(QLabel("Ticket:"), 3, 0, Qt.AlignmentFlag.AlignRight)
        ticket_entry = QLineEdit()
        assign_gl.addWidget(ticket_entry, 3, 1)

        qinq_check = QCheckBox("Enable QinQ")
        assign_gl.addWidget(qinq_check, 4, 1)

        assign_gl.addWidget(QLabel("VLAN:"), 5, 0, Qt.AlignmentFlag.AlignRight)
        vlan_entry = QLineEdit()
        vlan_entry.setFixedWidth(100)
        assign_gl.addWidget(vlan_entry, 5, 1)
        form_main_layout.addWidget(assign_group)

        # Dates
        dates_group = QGroupBox("Schedule Dates (UTC)")
        dates_gl = QGridLayout(dates_group)
        dates_gl.setSpacing(8)

        dates_gl.addWidget(QLabel("Start date:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        start_entry = QLineEdit()
        start_entry.setFixedWidth(160)
        start_default = get_next_sunday_22utc()
        start_entry.setText(start_default.strftime("%Y-%m-%d %H:%M"))
        dates_gl.addWidget(start_entry, 0, 1)
        cal_start_btn = QPushButton("📅")
        cal_start_btn.setFixedWidth(34)

        def pick_start():
            picker = DatePickerDialog(dialog, "Select Start Date", start_entry.text() or None)
            picker.exec()
            result = picker.get_result()
            if result:
                start_entry.setText(result)

        cal_start_btn.clicked.connect(pick_start)
        dates_gl.addWidget(cal_start_btn, 0, 2)

        dates_gl.addWidget(QLabel("End date:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        end_entry = QLineEdit()
        end_entry.setFixedWidth(160)
        end_default = get_two_weeks_sunday_22utc(start_default)
        end_entry.setText(end_default.strftime("%Y-%m-%d %H:%M"))
        dates_gl.addWidget(end_entry, 1, 1)
        cal_end_btn = QPushButton("📅")
        cal_end_btn.setFixedWidth(34)

        def pick_end():
            picker = DatePickerDialog(
                dialog, "Select End Date", end_entry.text() or None, range_start=start_entry.text() or None
            )
            picker.exec()
            result = picker.get_result()
            if result:
                end_entry.setText(result)

        cal_end_btn.clicked.connect(pick_end)
        dates_gl.addWidget(cal_end_btn, 1, 2)
        form_main_layout.addWidget(dates_group)
        form_main_layout.addStretch()

        # Button row
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        dlayout.addWidget(sep)

        btn_row_w = QWidget()
        brl = QHBoxLayout(btn_row_w)
        brl.setContentsMargins(20, 10, 20, 10)
        brl.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        brl.addWidget(cancel_btn)
        create_btn = QPushButton("Create Schedule")
        create_btn.setDefault(True)
        brl.addWidget(create_btn)
        brl.addStretch()
        dlayout.addWidget(btn_row_w)

        _result = []

        def on_create():
            cloud = cloud_entry.text().strip()
            start = start_entry.text().strip()
            end = end_entry.text().strip()
            host_mode = host_mode_group.checkedId()

            if not cloud or not start or not end:
                QMessageBox.critical(dialog, "Error", "Cloud, start, and end date are required")
                return

            if host_mode == 0:
                hosts_raw = hosts_entry.text().strip().replace("\n", ",")
                hosts_list = [h.strip() for h in hosts_raw.split(",") if h.strip()]
                if not hosts_list:
                    QMessageBox.critical(dialog, "Error", "Enter at least one hostname")
                    return
                host_args = [",".join(hosts_list)]
            else:
                file_path = file_entry.text().strip()
                if not file_path:
                    QMessageBox.critical(dialog, "Error", "Select a host list file")
                    return
                try:
                    with open(file_path) as fh:
                        lines = [ln.strip() for ln in fh if ln.strip()]
                    if not lines:
                        QMessageBox.critical(dialog, "Error", f"No hostnames found in file: {file_path}")
                        return
                except FileNotFoundError:
                    QMessageBox.critical(dialog, "Error", f"File not found: {file_path}")
                    return
                except Exception as exc:
                    QMessageBox.critical(dialog, "Error", f"Failed to read file: {exc}")
                    return
                host_args = ["host-list", file_path]

            args_parts = [cloud] + host_args + [start, end]
            if desc_entry.text().strip():
                args_parts += ["description", desc_entry.text().strip()]
            if owner_entry.text().strip():
                args_parts += ["cloud-owner", owner_entry.text().strip()]
            if ticket_entry.text().strip():
                args_parts += ["cloud-ticket", ticket_entry.text().strip()]
            if vlan_entry.text().strip():
                args_parts += ["vlan", vlan_entry.text().strip()]
            if qinq_check.isChecked():
                args_parts += ["qinq", "1"]

            _result.append(shlex.join(args_parts))
            dialog.accept()

        create_btn.clicked.connect(on_create)

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            args = _result[0]
            try:
                self.shell.schedule_commands.cmd_schedule_admin(args)
                self.safe_load_data_async(
                    self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree]
                )
                QMessageBox.information(self, "Success", "Schedule creation submitted")
            except Exception as exc:
                show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _extend_schedule(self):
        _, assignment_id, cloud_name = self._get_selected_data()
        if not assignment_id or not cloud_name:
            return

        dialog = self.create_simple_dialog(f"Extend Assignment #{assignment_id}", "350x160")
        layout = dialog.layout()
        layout.addWidget(QLabel(f"Extend {cloud_name} by:"))

        weeks_spin = QSpinBox()
        weeks_spin.setRange(1, 52)
        weeks_spin.setValue(2)
        row = QWidget()
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("Weeks:"))
        rl.addWidget(weeks_spin)
        rl.addStretch()
        layout.addWidget(row)

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Extend", dialog.accept)])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        weeks = weeks_spin.value()
        try:
            self.shell.schedule_commands.cmd_extend(f"{cloud_name} weeks {weeks}")
            self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
            QMessageBox.information(self, "Success", f"{cloud_name} extended by {weeks} weeks")
        except Exception as exc:
            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _shrink_schedule(self):
        _, assignment_id, cloud_name = self._get_selected_data()
        if not assignment_id or not cloud_name:
            return

        dialog = self.create_simple_dialog(f"Shrink Assignment #{assignment_id}", "380x220")
        layout = dialog.layout()
        layout.addWidget(QLabel(f"Shrink {cloud_name}:"))

        mode_group = QButtonGroup(dialog)
        weeks_radio = QRadioButton("By weeks:")
        weeks_radio.setChecked(True)
        mode_group.addButton(weeks_radio, 0)
        layout.addWidget(weeks_radio)

        weeks_spin = QSpinBox()
        weeks_spin.setRange(1, 52)
        weeks_spin.setValue(1)
        weeks_row = QWidget()
        wrl = QHBoxLayout(weeks_row)
        wrl.setContentsMargins(20, 0, 0, 0)
        wrl.addWidget(weeks_spin)
        wrl.addStretch()
        layout.addWidget(weeks_row)

        now_radio = QRadioButton("End now (terminate immediately)")
        mode_group.addButton(now_radio, 1)
        layout.addWidget(now_radio)

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Shrink", dialog.accept)])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        mode_id = mode_group.checkedId()
        try:
            if mode_id == 1:
                self.shell.user_commands.cmd_terminate(str(assignment_id))
                QMessageBox.information(self, "Success", f"Assignment #{assignment_id} terminated")
            else:
                weeks = weeks_spin.value()
                self.shell.schedule_commands.cmd_shrink(f"{cloud_name} weeks {weeks}")
                QMessageBox.information(self, "Success", f"{cloud_name} shrunk by {weeks} weeks")
            self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
        except Exception as exc:
            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _terminate_schedule(self):
        _, assignment_id, cloud_name = self._get_selected_data()
        if not assignment_id:
            return
        display = cloud_name or str(assignment_id)
        if not self.confirm_action(
            "Confirm Termination",
            f"Terminate assignment #{assignment_id} ({display})?\n\nThis will release all hosts in this assignment.",
        ):
            return
        try:
            self.shell.user_commands.cmd_terminate(str(assignment_id))
            self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
            QMessageBox.information(self, "Success", f"Assignment #{assignment_id} terminated")
        except Exception as exc:
            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def refresh(self):
        if hasattr(self, "tree"):
            self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
