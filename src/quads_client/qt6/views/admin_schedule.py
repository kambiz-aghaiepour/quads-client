"""Admin schedule management view"""

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
)
from PySide6.QtCore import Qt

from quads_client.qt6.widgets.base import BaseAdminView, FormDialog, ScrolledTreeview
from quads_client.qt6.widgets.date_picker import DatePickerDialog, get_next_sunday_22utc, get_two_weeks_sunday_22utc
from quads_client.qt6.widgets.dialogs import show_error_dialog


class AdminScheduleView(BaseAdminView):
    """Admin view for managing host schedules."""

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
        fbl.addWidget(QLabel("Search host:"))
        self.host_filter_entry = QLineEdit()
        self.host_filter_entry.setFixedWidth(200)
        self.host_filter_entry.setPlaceholderText("hostname or partial")
        fbl.addWidget(self.host_filter_entry)
        fbl.addSpacing(10)
        fbl.addWidget(QLabel("Cloud:"))
        self.cloud_filter_entry = QLineEdit()
        self.cloud_filter_entry.setFixedWidth(120)
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
        action_bar = self.create_action_bar(
            ("+ Create Schedule", self._create_schedule),
            ("✏ Edit", self._edit_schedule),
            ("🗑 Delete", self._delete_schedule),
            ("↔ Extend", self._extend_schedule),
            ("⊢ Shrink", self._shrink_schedule),
            (
                "⟳ Refresh",
                lambda: self.safe_load_data_async(
                    self._fetch_schedules,
                    self._populate_tree,
                    disable_widgets=[self.tree.tree],
                ),
            ),
        )
        cl.addWidget(action_bar)

        # Schedules tree
        self.tree = ScrolledTreeview(
            content,
            columns=("Host", "Cloud", "Start", "End", "Schedule ID"),
            widths=(200, 100, 160, 160, 100),
        )
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
        host_filter = self.host_filter_entry.text().strip() if hasattr(self, "host_filter_entry") else ""
        cloud_filter = self.cloud_filter_entry.text().strip() if hasattr(self, "cloud_filter_entry") else ""
        return self.shell.schedule_commands.get_schedules_programmatic(
            host=host_filter or None,
            cloud=cloud_filter or None,
        )

    def _populate_tree(self, schedules):
        self.tree.clear()
        if not schedules:
            self.update_status("No schedules found")
            return
        for sched in schedules:
            host = sched.get("host", {})
            host_name = host.get("name", "") if isinstance(host, dict) else str(host)
            cloud = sched.get("cloud", {})
            cloud_name = cloud.get("name", "") if isinstance(cloud, dict) else str(cloud)
            start = sched.get("start", "")
            end = sched.get("end", "")
            sched_id = str(sched.get("id", ""))
            self.tree.insert("", 0, values=(host_name, cloud_name, start, end, sched_id))
        self.update_status(f"{len(schedules)} schedule(s)")

    def _apply_filter(self):
        self.safe_load_data_async(
            self._fetch_schedules,
            self._populate_tree,
            disable_widgets=[self.tree.tree],
        )

    def _clear_filter(self):
        self.host_filter_entry.clear()
        self.cloud_filter_entry.clear()
        self._apply_filter()

    def _get_selected_schedule(self):
        item = self.get_selected_item(self.tree)
        if not item:
            return None, None
        values = self.tree.item(item, "values")
        sched_id = values[4] if len(values) > 4 else None
        return item, sched_id

    def _create_schedule(self, prefill_hosts=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Schedule")
        dialog.resize(560, 620)
        dialog.setMinimumSize(500, 550)
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

        # Mode selection
        mode_group = QGroupBox("Assignment Mode")
        mode_vl = QVBoxLayout(mode_group)
        _mode_group = QButtonGroup(dialog)
        count_radio = QRadioButton("Reserve by count (uses filters below)")
        count_radio.setChecked(True)
        _mode_group.addButton(count_radio, 0)
        mode_vl.addWidget(count_radio)
        hosts_radio = QRadioButton("Specify hosts by name")
        _mode_group.addButton(hosts_radio, 1)
        mode_vl.addWidget(hosts_radio)
        form_main_layout.addWidget(mode_group)

        # Count panel
        count_panel = QGroupBox("Count")
        count_gl = QGridLayout(count_panel)
        count_gl.addWidget(QLabel("Hosts count:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        count_spin = QSpinBox()
        count_spin.setRange(1, 500)
        count_spin.setValue(1)
        count_spin.setFixedWidth(90)
        count_gl.addWidget(count_spin, 0, 1)
        form_main_layout.addWidget(count_panel)

        # Hosts panel
        hosts_panel = QGroupBox("Hosts")
        hosts_vl = QVBoxLayout(hosts_panel)
        hosts_vl.addWidget(QLabel("Hostnames (comma-separated):"))
        hosts_entry = QLineEdit()
        hosts_entry.setPlaceholderText("e.g. host01,host02")
        if prefill_hosts:
            hosts_entry.setText(prefill_hosts if isinstance(prefill_hosts, str) else ",".join(prefill_hosts))
        hosts_vl.addWidget(hosts_entry)
        hosts_panel.setVisible(False)
        form_main_layout.addWidget(hosts_panel)

        def on_mode_toggle(button_id, checked):
            if not checked:
                return
            mode = _mode_group.checkedId()
            count_panel.setVisible(mode == 0)
            hosts_panel.setVisible(mode == 1)

        _mode_group.idToggled.connect(on_mode_toggle)

        if prefill_hosts:
            hosts_radio.setChecked(True)
            count_panel.setVisible(False)
            hosts_panel.setVisible(True)

        # Cloud & assignment
        assign_group = QGroupBox("Cloud & Assignment")
        assign_gl = QGridLayout(assign_group)
        assign_gl.setSpacing(8)

        assign_gl.addWidget(QLabel("Cloud name:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        cloud_entry = QLineEdit()
        cloud_entry.setPlaceholderText("e.g. cloud08")
        assign_gl.addWidget(cloud_entry, 0, 1)

        assign_gl.addWidget(QLabel("Description:"), 1, 0, Qt.AlignmentFlag.AlignRight)
        desc_entry = QLineEdit()
        desc_entry.setPlaceholderText("Optional")
        assign_gl.addWidget(desc_entry, 1, 1)

        assign_gl.addWidget(QLabel("Ticket:"), 2, 0, Qt.AlignmentFlag.AlignRight)
        ticket_entry = QLineEdit()
        assign_gl.addWidget(ticket_entry, 2, 1)

        qinq_check = QCheckBox("Enable QinQ")
        assign_gl.addWidget(qinq_check, 3, 1)

        vlan_label = QLabel("VLAN:")
        vlan_entry = QLineEdit()
        vlan_entry.setFixedWidth(100)
        assign_gl.addWidget(vlan_label, 4, 0, Qt.AlignmentFlag.AlignRight)
        assign_gl.addWidget(vlan_entry, 4, 1)
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
        dlayout.addWidget(btn_row_w)

        _result = []

        def on_create():
            mode = _mode_group.checkedId()
            cloud = cloud_entry.text().strip()
            start = start_entry.text().strip()
            end = end_entry.text().strip()
            if not cloud or not start or not end:
                QMessageBox.critical(dialog, "Error", "Cloud, start, and end date are required")
                return

            params = {
                "cloud": cloud,
                "description": desc_entry.text().strip(),
                "ticket": ticket_entry.text().strip(),
                "qinq": qinq_check.isChecked(),
                "vlan": vlan_entry.text().strip(),
                "start": start,
                "end": end,
            }
            if mode == 0:
                params["count"] = count_spin.value()
            else:
                raw = hosts_entry.text().strip()
                if not raw:
                    QMessageBox.critical(dialog, "Error", "Enter at least one hostname")
                    return
                params["hosts"] = [h.strip() for h in raw.replace("\n", ",").split(",") if h.strip()]

            _result.append(params)
            dialog.accept()

        create_btn.clicked.connect(on_create)
        brl.addWidget(create_btn)
        brl.addStretch()

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            params = _result[0]
            try:
                success, message, details = self.shell.schedule_commands.create_schedule_programmatic(**params)
                if success:
                    self.safe_load_data_async(
                        self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree]
                    )
                    QMessageBox.information(self, "Success", f"Schedule created\n\n{message or ''}")
                else:
                    QMessageBox.critical(self, "Error", message or "Schedule creation failed")
            except Exception as exc:
                import traceback

                show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _edit_schedule(self):
        item, sched_id = self._get_selected_schedule()
        if not sched_id:
            QMessageBox.warning(self, "No Selection", "Select a schedule to edit")
            return

        values = self.tree.item(item, "values")
        host_name, cloud_name, start, end, _ = values

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Schedule #{sched_id}")
        dialog.resize(500, 320)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)

        form_widget = QWidget()
        QGridLayout(form_widget)
        form_widget.layout().setSpacing(8)
        form_widget.layout().setContentsMargins(20, 15, 20, 10)

        form_widget.layout().addWidget(QLabel("Host:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        host_lbl = QLabel(host_name)
        hf = host_lbl.font()
        hf.setBold(True)
        host_lbl.setFont(hf)
        form_widget.layout().addWidget(host_lbl, 0, 1)

        start_entry = FormDialog.create_labeled_entry(form_widget, "Start (UTC):", 1)
        start_entry.setText(start)
        cal_start_btn = QPushButton("📅")
        cal_start_btn.setFixedWidth(34)
        form_widget.layout().addWidget(cal_start_btn, 1, 2)

        def pick_s():
            picker = DatePickerDialog(dialog, "Select Start Date", start_entry.text())
            picker.exec()
            r = picker.get_result()
            if r:
                start_entry.setText(r)

        cal_start_btn.clicked.connect(pick_s)

        end_entry = FormDialog.create_labeled_entry(form_widget, "End (UTC):", 2)
        end_entry.setText(end)
        cal_end_btn = QPushButton("📅")
        cal_end_btn.setFixedWidth(34)
        form_widget.layout().addWidget(cal_end_btn, 2, 2)

        def pick_e():
            picker = DatePickerDialog(
                dialog, "Select End Date", end_entry.text(), range_start=start_entry.text() or None
            )
            picker.exec()
            r = picker.get_result()
            if r:
                end_entry.setText(r)

        cal_end_btn.clicked.connect(pick_e)

        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(form_widget)

        _result = []

        def on_save():
            _result.append((start_entry.text().strip(), end_entry.text().strip()))
            dialog.accept()

        FormDialog.create_button_row(main_layout, [("Cancel", dialog.reject), ("Save", on_save)])

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            new_start, new_end = _result[0]
            try:
                success, message = self.shell.schedule_commands.edit_schedule_programmatic(
                    schedule_id=sched_id,
                    start=new_start,
                    end=new_end,
                )
                if success:
                    self.safe_load_data_async(
                        self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree]
                    )
                else:
                    QMessageBox.critical(self, "Error", message or "Edit failed")
            except Exception as exc:
                import traceback

                show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _delete_schedule(self):
        item, sched_id = self._get_selected_schedule()
        if not sched_id:
            QMessageBox.warning(self, "No Selection", "Select a schedule to delete")
            return
        values = self.tree.item(item, "values")
        host_name = values[0] if values else sched_id

        if not self.confirm_action(f"Delete schedule for '{host_name}' (ID: {sched_id})?"):
            return
        try:
            success, message = self.shell.schedule_commands.rm_schedule_programmatic(schedule_id=sched_id)
            if success:
                self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
            else:
                QMessageBox.critical(self, "Error", message or "Delete failed")
        except Exception as exc:
            import traceback

            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _extend_schedule(self):
        item, sched_id = self._get_selected_schedule()
        if not sched_id:
            QMessageBox.warning(self, "No Selection", "Select a schedule to extend")
            return

        dialog = self.create_simple_dialog("Extend Schedule", "300x130")
        layout = dialog.layout()
        layout.addWidget(QLabel(f"Extend schedule {sched_id} by:"))

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
            success, message = self.shell.schedule_commands.extend_schedule_programmatic(
                schedule_id=sched_id,
                weeks=weeks,
            )
            if success:
                self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
                QMessageBox.information(self, "Success", message or f"Extended by {weeks} weeks")
            else:
                QMessageBox.critical(self, "Error", message or "Extend failed")
        except Exception as exc:
            import traceback

            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def _shrink_schedule(self):
        item, sched_id = self._get_selected_schedule()
        if not sched_id:
            QMessageBox.warning(self, "No Selection", "Select a schedule to shrink")
            return

        dialog = self.create_simple_dialog("Shrink Schedule", "340x200")
        layout = dialog.layout()
        layout.addWidget(QLabel(f"Shrink schedule {sched_id}:"))

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

        days_radio = QRadioButton("By days:")
        mode_group.addButton(days_radio, 1)
        layout.addWidget(days_radio)

        days_spin = QSpinBox()
        days_spin.setRange(1, 365)
        days_spin.setValue(7)
        days_row = QWidget()
        drl = QHBoxLayout(days_row)
        drl.setContentsMargins(20, 0, 0, 0)
        drl.addWidget(days_spin)
        drl.addStretch()
        layout.addWidget(days_row)

        now_radio = QRadioButton("End now (terminate immediately)")
        mode_group.addButton(now_radio, 2)
        layout.addWidget(now_radio)

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Shrink", dialog.accept)])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        mode_id = mode_group.checkedId()
        try:
            if mode_id == 0:
                success, message = self.shell.schedule_commands.shrink_schedule_programmatic(
                    schedule_id=sched_id,
                    weeks=weeks_spin.value(),
                )
            elif mode_id == 1:
                success, message = self.shell.schedule_commands.shrink_schedule_programmatic(
                    schedule_id=sched_id,
                    days=days_spin.value(),
                )
            else:
                success, message = self.shell.schedule_commands.shrink_schedule_programmatic(
                    schedule_id=sched_id,
                    now=True,
                )
            if success:
                self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
                QMessageBox.information(self, "Success", message or "Schedule shrunk")
            else:
                QMessageBox.critical(self, "Error", message or "Shrink failed")
        except Exception as exc:
            import traceback

            show_error_dialog(self, "Error", str(exc), traceback.format_exc())

    def refresh(self):
        if hasattr(self, "tree"):
            self.safe_load_data_async(self._fetch_schedules, self._populate_tree, disable_widgets=[self.tree.tree])
