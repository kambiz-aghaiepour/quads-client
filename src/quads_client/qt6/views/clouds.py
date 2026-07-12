"""Clouds view - admin cloud management"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QDialog, QListWidget, QAbstractItemView,
    QMessageBox, QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QShortcut, QKeySequence

from quads_client.qt6.widgets.base import BaseAdminView, ScrolledTreeview, FormDialog


class CloudsView(BaseAdminView):
    """View for managing clouds (admin only)"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Cloud Management", requires_admin=True)
        self._create_ui()

    def _create_ui(self):
        self.create_header([
            ("➕ Create Cloud", self._create_cloud),
            ("🔄 Refresh", self._load_clouds),
        ])

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)

        columns = ("cloud", "assignment", "owner", "description", "vlan", "wipe")
        column_configs = {
            "cloud": ("Cloud", 100),
            "assignment": ("Assignment", 100),
            "owner": ("Owner", 120),
            "description": ("Description", 300),
            "vlan": ("VLAN", 80),
            "wipe": ("Wipe", 60),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs)
        cl.addWidget(self.tree)
        self._main_layout.addWidget(content, 1)

        self.create_action_bar([
            ("View Details", self._view_details),
            ("Modify Cloud", self._modify_cloud),
            ("Terminate", self._terminate_assignment),
        ])
        self.create_status_label()
        self._load_clouds()

    def _load_clouds(self):
        def load_data():
            clouds = self.shell.connection.api.get_clouds()
            if not clouds:
                return []
            active_assignments = {}
            try:
                all_assignments = self.shell.connection.api.filter_assignments({"active": True})
                if all_assignments:
                    for assignment in all_assignments:
                        if isinstance(assignment, dict):
                            cloud_obj = assignment.get("cloud", {})
                            cname = cloud_obj.get("name") if isinstance(cloud_obj, dict) else str(cloud_obj)
                            if cname:
                                active_assignments[cname] = assignment
            except Exception:
                pass
            return (clouds, active_assignments)

        self.tree.clear()

        def on_loaded(data):
            if not data:
                return
            clouds, active_assignments = data
            for cloud in clouds:
                cloud_name = cloud.get("name", "")
                assignment_id = "-"
                owner = "-"
                description = "-"
                vlan = "-"
                wipe = "No"
                assignment = active_assignments.get(cloud_name)
                if assignment and isinstance(assignment, dict):
                    assignment_id = str(assignment.get("id", "-"))
                    owner = assignment.get("owner", "-") or "-"
                    desc_full = assignment.get("description", "-") or "-"
                    description = desc_full[:40] if len(desc_full) > 40 else desc_full
                    wipe = "Yes" if assignment.get("wipe", False) else "No"
                    vlan_obj = assignment.get("vlan")
                    if isinstance(vlan_obj, dict):
                        vlan = str(vlan_obj.get("vlan_id", "-"))
                    elif vlan_obj:
                        vlan = str(vlan_obj)
                self.tree.insert("", 0, values=(cloud_name, assignment_id, owner, description, vlan, wipe))
            self.update_status(f"Showing {len(clouds)} cloud(s) | Last updated: Just now")

        self.safe_load_data_async(load_data, on_loaded)

    def _create_cloud(self):
        dialog = self.create_simple_dialog("Create Cloud", "400x150")
        layout = dialog.layout()

        layout.addWidget(QLabel("Cloud Name:"))
        name_entry = QLineEdit()
        name_entry.setFocus()
        layout.addWidget(name_entry)
        layout.addStretch()

        _result = []

        def on_create():
            cloud_name = name_entry.text().strip()
            if not cloud_name:
                QMessageBox.warning(dialog, "Error", "Cloud name is required")
                return
            _result.append(cloud_name)
            dialog.accept()

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Create", on_create)])

        if dialog.exec() == QDialog.DialogCode.Accepted and _result:
            cloud_name = _result[0]
            self.safe_execute(
                lambda: self.shell.cloud_commands.cmd_cloud_create(cloud_name),
                f"Cloud '{cloud_name}' created",
                "Create Cloud Failed",
                self._load_clouds,
            )

    def _terminate_assignment(self):
        _, values = self.get_selected_item("Please select a cloud to terminate")
        if not values:
            return
        cloud_name = values[0]
        assignment_id = values[1]
        if assignment_id == "-":
            QMessageBox.warning(self, "No Assignment", f"Cloud '{cloud_name}' has no active assignment to terminate")
            return
        if not self.confirm_action(
            "Confirm Termination",
            f"Are you sure you want to terminate assignment #{assignment_id} for cloud '{cloud_name}'?\n\n"
            "This will release all hosts in this assignment.",
        ):
            return
        self.safe_execute(
            lambda: self.shell.user_commands.cmd_terminate(str(assignment_id)),
            f"Assignment #{assignment_id} terminated\n\nNote: It may take a few moments to complete.",
            "Termination Failed",
            self._load_clouds,
        )

    def _modify_cloud(self):
        _, values = self.get_selected_item("Please select a cloud to modify")
        if not values:
            return
        cloud_name = values[0]

        dialog = self.create_simple_dialog(f"Modify Cloud: {cloud_name}", "500x400")
        layout = dialog.layout()

        title = QLabel(f"Modify assignment attributes for {cloud_name}")
        tf = title.font()
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        # Form widget with QGridLayout
        form_widget = QWidget()
        QGridLayout(form_widget)
        layout.addWidget(form_widget)

        desc_entry = FormDialog.create_labeled_entry(form_widget, "Description:", 0)
        owner_entry = FormDialog.create_labeled_entry(form_widget, "Cloud Owner:", 1)
        ticket_entry = FormDialog.create_labeled_entry(form_widget, "Ticket ID:", 2)
        cc_entry = FormDialog.create_labeled_entry(form_widget, "CC Users:", 3)
        vlan_entry = FormDialog.create_labeled_entry(form_widget, "VLAN ID:", 4)

        qinq_check = QCheckBox("Enable QinQ")
        form_widget.layout().addWidget(qinq_check, 5, 1)

        wipe_check = QCheckBox("Enable wipe")
        form_widget.layout().addWidget(wipe_check, 6, 1)

        layout.addStretch()

        _result_args = []

        def on_modify():
            args = cloud_name
            if desc_entry.text().strip():
                safe_desc = desc_entry.text().strip().replace('"', '\\"')
                args += f' description "{safe_desc}"'
            if owner_entry.text().strip():
                args += f" cloud-owner {owner_entry.text().strip()}"
            if ticket_entry.text().strip():
                args += f" cloud-ticket {ticket_entry.text().strip()}"
            if cc_entry.text().strip():
                safe_cc = cc_entry.text().strip().replace('"', '\\"')
                args += f' cc-users "{safe_cc}"'
            if vlan_entry.text().strip():
                args += f" vlan {vlan_entry.text().strip()}"
            if qinq_check.isChecked():
                args += " qinq 1"
            if wipe_check.isChecked():
                args += " wipe"
            if args == cloud_name:
                QMessageBox.warning(dialog, "No Changes", "No modifications specified")
                return
            _result_args.append(args)
            dialog.accept()

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Modify", on_modify)])

        if dialog.exec() == QDialog.DialogCode.Accepted and _result_args:
            args = _result_args[0]
            self.safe_execute(
                lambda: self.shell.cloud_commands.cmd_mod_cloud(args),
                f"Cloud '{cloud_name}' modified",
                "Modify Cloud Failed",
                self._load_clouds,
            )

    def _get_cloud_hosts(self, cloud_name):
        hostnames = []
        if cloud_name == "cloud01":
            hosts = self.shell.connection.api.filter_hosts({"cloud": "cloud01"})
            if hosts and isinstance(hosts, list):
                for host in hosts:
                    if isinstance(host, dict):
                        name = host.get("name", "")
                    elif isinstance(host, str):
                        name = host
                    else:
                        name = getattr(host, "name", "")
                    if name and name not in hostnames:
                        hostnames.append(name)
        else:
            current_schedules = self.shell.connection.api.get_current_schedules({"cloud": cloud_name})
            if current_schedules:
                for schedule in current_schedules:
                    host = schedule.get("host")
                    if host:
                        hostname = host.get("name") if isinstance(host, dict) else host
                        if hostname and hostname not in hostnames:
                            hostnames.append(hostname)
        hostnames.sort()
        return hostnames

    def _view_details(self):
        _, values = self.get_selected_item("Please select a cloud to view")
        if not values:
            return
        cloud_name = values[0]

        try:
            hostnames = self._get_cloud_hosts(cloud_name)
        except Exception as e:
            from quads_client.qt6.widgets.dialogs import show_error_dialog
            show_error_dialog(self, "Failed to get cloud details", str(e))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Hosts in {cloud_name}")
        dialog.resize(700, 500)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlayout = QVBoxLayout(dialog)

        count = len(hostnames)
        count_text = f"{count} host(s) assigned" if count > 0 else "No hosts currently assigned"
        count_label = QLabel(count_text)
        cf = count_label.font()
        cf.setBold(True)
        count_label.setFont(cf)
        dlayout.addWidget(count_label)

        list_widget = QListWidget()
        list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        mono.setPointSize(10)
        list_widget.setFont(mono)
        for hostname in hostnames:
            list_widget.addItem(hostname)
        dlayout.addWidget(list_widget)

        def select_all():
            list_widget.selectAll()

        def copy_selected():
            items = list_widget.selectedItems()
            if items:
                text = "\n".join(item.text() for item in items)
                QApplication.clipboard().setText(text)

        shortcut_a = QShortcut(QKeySequence("Ctrl+A"), list_widget)
        shortcut_a.activated.connect(select_all)
        shortcut_c = QShortcut(QKeySequence.StandardKey.Copy, list_widget)
        shortcut_c.activated.connect(copy_selected)

        btn_row = QWidget()
        btn_h = QHBoxLayout(btn_row)
        btn_h.setContentsMargins(0, 0, 0, 0)

        sel_all_btn = QPushButton("Select All")
        sel_all_btn.clicked.connect(select_all)
        btn_h.addWidget(sel_all_btn)

        desel_btn = QPushButton("Deselect All")
        desel_btn.clicked.connect(list_widget.clearSelection)
        btn_h.addWidget(desel_btn)

        copy_btn = QPushButton("Copy Selected")
        copy_btn.clicked.connect(copy_selected)
        btn_h.addWidget(copy_btn)

        btn_h.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_h.addWidget(close_btn)

        dlayout.addWidget(btn_row)
        dialog.exec()

    def refresh(self):
        self._load_clouds()
