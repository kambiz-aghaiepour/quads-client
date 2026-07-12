"""Assignments view - shows user's assignments in list format"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QSpinBox, QRadioButton, QButtonGroup, QDialog, QMessageBox,
)
from PySide6.QtCore import Qt

from quads_client.qt6.widgets.base import BaseAdminView, ScrolledTreeview, FormDialog


class AssignmentsView(BaseAdminView):
    """View for displaying user's assignments in a simple list"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Assignments", requires_admin=False)
        self._create_ui()

    def _create_ui(self):
        self.create_header([("🔄 Refresh", self._load_assignments)])

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 0, 20, 20)

        columns = ("id", "cloud", "description", "owner", "validated")
        column_configs = {
            "id": ("ID", 80),
            "cloud": ("Cloud", 120),
            "description": ("Description", 300),
            "owner": ("Owner", 150),
            "validated": ("Validated", 100),
        }
        self.tree = ScrolledTreeview(content, columns, column_configs)
        cl.addWidget(self.tree)
        self._main_layout.addWidget(content, 1)

        if self.shell.is_admin():
            self.create_action_bar([
                ("Extend", self._extend_assignment),
                ("Shrink", self._shrink_assignment),
                ("Terminate Selected", self._terminate_selected),
            ])
        else:
            self.create_action_bar([("Terminate Selected", self._terminate_selected)])

        self.create_status_label()
        self._load_assignments()

    def _load_assignments(self):
        from quads_client.utils import get_username_short, extract_assignment_id, extract_cloud_name

        is_admin = self.shell.is_admin()

        def load_data():
            if is_admin:
                return self.shell.connection.api.filter_assignments({"active": True})
            else:
                username = get_username_short(self.shell.connection.username)
                return self.shell.connection.api.filter_assignments({"owner": username, "active": True})

        self.tree.clear()
        label = "all assignment(s)" if is_admin else "your assignment(s)"

        def on_loaded(assignments):
            if not assignments:
                return
            for assignment in assignments:
                if isinstance(assignment, dict):
                    assignment_id = extract_assignment_id(assignment)
                    cloud_name = extract_cloud_name(assignment)
                    description = assignment.get("description", "No description")
                    owner = assignment.get("owner", "N/A")
                    validated = "✓" if assignment.get("validated") else "○"
                    self.tree.insert("", 0, values=(assignment_id, cloud_name, description, owner, validated))

        self.safe_load_data_async(load_data, on_loaded, success_message="Showing {count} " + label)

    def _terminate_selected(self):
        _, values = self.get_selected_item("Please select an assignment to terminate")
        if not values:
            return
        assignment_id = values[0]
        if not self.confirm_action(
            "Confirm Termination",
            f"Are you sure you want to terminate assignment #{assignment_id}?\n\n"
            "This will release all hosts in this assignment.",
        ):
            return
        self.safe_execute(
            lambda: self.shell.user_commands.cmd_terminate(str(assignment_id)),
            f"Assignment #{assignment_id} terminated\n\nNote: It may take a few moments for the termination to complete.",
            "Termination Failed",
            self._load_assignments,
        )

    def _extend_assignment(self):
        _, values = self.get_selected_item("Please select an assignment to extend")
        if not values:
            return
        assignment_id = values[0]
        cloud_name = values[1]

        dialog = self.create_simple_dialog(f"Extend Assignment #{assignment_id}", "350x180")
        layout = dialog.layout()

        title = QLabel(f"Extend assignment #{assignment_id} ({cloud_name})")
        tf = title.font()
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        input_row = QWidget()
        input_h = QHBoxLayout(input_row)
        input_h.setContentsMargins(0, 0, 0, 0)
        input_h.addWidget(QLabel("Number of weeks:"))
        weeks_spin = QSpinBox()
        weeks_spin.setRange(1, 52)
        weeks_spin.setValue(2)
        weeks_spin.setFixedWidth(80)
        input_h.addWidget(weeks_spin)
        input_h.addStretch()
        layout.addWidget(input_row)
        layout.addStretch()

        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Extend", dialog.accept)])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        weeks = weeks_spin.value()
        if not self.confirm_action(
            "Confirm Extend",
            f"Extend assignment #{assignment_id} ({cloud_name}) by {weeks} week(s)?\n\n"
            "This will extend ALL schedules in this assignment.",
        ):
            return

        self.safe_execute(
            lambda: self.shell.schedule_commands.cmd_extend(f"{cloud_name} weeks {weeks}"),
            f"Extended assignment #{assignment_id} by {weeks} week(s)",
            "Extend Failed",
            self._load_assignments,
        )

    def _shrink_assignment(self):
        _, values = self.get_selected_item("Please select an assignment to shrink")
        if not values:
            return
        assignment_id = values[0]
        cloud_name = values[1]

        dialog = self.create_simple_dialog(f"Shrink Assignment #{assignment_id}", "400x260")
        layout = dialog.layout()

        title = QLabel(f"Shrink assignment #{assignment_id} ({cloud_name})")
        tf = title.font()
        tf.setBold(True)
        title.setFont(tf)
        layout.addWidget(title)

        mode_group = QButtonGroup(dialog)
        mode_widget = QWidget()
        mode_grid = QGridLayout(mode_widget)
        mode_grid.setSpacing(8)

        weeks_radio = QRadioButton("By weeks:")
        mode_group.addButton(weeks_radio, 0)
        weeks_radio.setChecked(True)
        mode_grid.addWidget(weeks_radio, 0, 0)
        weeks_spin = QSpinBox()
        weeks_spin.setRange(1, 52)
        weeks_spin.setValue(1)
        weeks_spin.setFixedWidth(80)
        mode_grid.addWidget(weeks_spin, 0, 1, Qt.AlignmentFlag.AlignLeft)

        days_radio = QRadioButton("By days:")
        mode_group.addButton(days_radio, 1)
        mode_grid.addWidget(days_radio, 1, 0)
        days_spin = QSpinBox()
        days_spin.setRange(1, 365)
        days_spin.setValue(7)
        days_spin.setFixedWidth(80)
        mode_grid.addWidget(days_spin, 1, 1, Qt.AlignmentFlag.AlignLeft)

        now_radio = QRadioButton("End now (terminate)")
        mode_group.addButton(now_radio, 2)
        mode_grid.addWidget(now_radio, 2, 0, 1, 2)

        layout.addWidget(mode_widget)
        layout.addStretch()
        FormDialog.create_button_row(layout, [("Cancel", dialog.reject), ("Shrink", dialog.accept)])

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        mode_id = mode_group.checkedId()

        if mode_id == 2:  # now
            if not self.confirm_action(
                "Confirm Shrink",
                f"End assignment #{assignment_id} ({cloud_name}) NOW?\n\nThis will terminate the assignment immediately.",
            ):
                return
            self.safe_execute(
                lambda: self.shell.user_commands.cmd_terminate(str(assignment_id)),
                f"Assignment #{assignment_id} terminated",
                "Terminate Failed",
                self._load_assignments,
            )
            return

        if mode_id == 0:  # weeks
            weeks = weeks_spin.value()
            unit = "week(s)"
            confirm_msg = (
                f"Shrink assignment #{assignment_id} ({cloud_name}) by {weeks} {unit}?\n\n"
                "This will shrink ALL schedules in this assignment."
            )
            if not self.confirm_action("Confirm Shrink", confirm_msg):
                return
            cmd_args = f"{cloud_name} weeks {weeks}"

        else:  # days
            days = days_spin.value()
            unit = "day(s)"
            confirm_msg = (
                f"Shrink assignment #{assignment_id} ({cloud_name}) by {days} {unit}?\n\n"
                "This will shrink ALL schedules in this assignment."
            )
            if not self.confirm_action("Confirm Shrink", confirm_msg):
                return
            if days % 7 != 0:
                QMessageBox.warning(
                    self,
                    "Days Not Evenly Divisible",
                    f"{days} days is not evenly divisible by 7.\n\n"
                    f"Shrinking by {max(1, days // 7)} week(s) instead.",
                )
            cmd_args = f"{cloud_name} weeks {max(1, days // 7)}"

        self.safe_execute(
            lambda: self.shell.schedule_commands.cmd_shrink(cmd_args),
            f"Shrunk assignment #{assignment_id}",
            "Shrink Failed",
            self._load_assignments,
        )

    def refresh(self):
        self._load_assignments()
