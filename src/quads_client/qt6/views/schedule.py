"""Schedule view for self-service scheduling (SSM users)"""

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
    QRadioButton,
    QButtonGroup,
    QSpinBox,
    QFileDialog,
    QScrollArea,
    QGroupBox,
    QFrame,
    QTextEdit,
    QListWidget,
    QAbstractItemView,
    QMessageBox,
    QCheckBox,
    QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from quads_client.qt6.widgets.base import _WorkerThread
from quads_client.qt6.widgets.host_filters import HostFilterFrame
from quads_client.qt6.widgets.dialogs import show_error_dialog


class ScheduleView(QWidget):
    """Schedule a cloud/host assignment (SSM / non-admin mode)."""

    def __init__(self, parent, shell):
        super().__init__(parent)
        self.shell = shell
        self._avail_thread = None
        self._meta_thread = None
        self._available_hosts_loaded = False
        self._advanced_visible = False
        self._avail_visible = False
        self._preview_text = None  # sentinel: None = not yet built / in login-prompt mode
        self._create_ui()

    def _create_ui(self):
        # If this widget already has a layout (called again via refresh()), clear it
        # and reuse it to avoid Qt's "already has a layout" warning.
        existing = self.layout()
        if existing is not None:
            while existing.count():
                item = existing.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            root = existing
        else:
            root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self._preview_text = None  # reset sentinel before rebuild

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

        if not self.shell.is_authenticated():
            self._show_login_prompt(root)
            return

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 12, 20, 20)
        cl.setSpacing(14)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # "How many hosts?" header
        how_lbl = QLabel("How many hosts do you need?")
        hf = how_lbl.font()
        hf.setBold(True)
        how_lbl.setFont(hf)
        cl.addWidget(how_lbl)

        # --- Selection mode group ---
        mode_box = QGroupBox("Selection Mode")
        mode_grid = QGridLayout(mode_box)
        mode_grid.setSpacing(6)
        self._mode_group = QButtonGroup(self)

        count_radio = QRadioButton("Specific number of hosts")
        count_radio.setChecked(True)
        self._mode_group.addButton(count_radio, 0)
        mode_grid.addWidget(count_radio, 0, 0)

        count_row = QWidget()
        count_rl = QHBoxLayout(count_row)
        count_rl.setContentsMargins(0, 0, 0, 0)
        count_rl.addWidget(QLabel("Count:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 500)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(80)
        self.count_spin.valueChanged.connect(self._update_preview)
        count_rl.addWidget(self.count_spin)
        count_rl.addStretch()
        mode_grid.addWidget(count_row, 0, 1)

        hosts_radio = QRadioButton("Specific hostnames")
        self._mode_group.addButton(hosts_radio, 1)
        mode_grid.addWidget(hosts_radio, 1, 0)

        self.hosts_entry = QLineEdit()
        self.hosts_entry.setPlaceholderText("host01.example.com,host02.example.com")
        self.hosts_entry.setEnabled(False)
        self.hosts_entry.textChanged.connect(self._update_preview)
        mode_grid.addWidget(self.hosts_entry, 1, 1)

        file_radio = QRadioButton("Host list from file")
        self._mode_group.addButton(file_radio, 2)
        mode_grid.addWidget(file_radio, 2, 0)

        file_row = QWidget()
        file_rl = QHBoxLayout(file_row)
        file_rl.setContentsMargins(0, 0, 0, 0)
        self.file_entry = QLineEdit()
        self.file_entry.setPlaceholderText("Path to file with one hostname per line")
        self.file_entry.setEnabled(False)
        self.file_entry.textChanged.connect(self._update_preview)
        file_rl.addWidget(self.file_entry)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setEnabled(False)
        self.browse_btn.clicked.connect(self._browse_file)
        file_rl.addWidget(self.browse_btn)
        mode_grid.addWidget(file_row, 2, 1)

        self._mode_group.idToggled.connect(self._on_mode_changed)
        cl.addWidget(mode_box)

        # --- Description ---
        cl.addWidget(QLabel("Description:"))
        self.desc_entry = QLineEdit()
        self.desc_entry.setText("Development testing environment")
        self.desc_entry.textChanged.connect(self._update_preview)
        cl.addWidget(self.desc_entry)

        # --- Browse available hosts (collapsible) ---
        self.browse_avail_check = QCheckBox("Browse available hosts ▼")
        self.browse_avail_check.toggled.connect(self._toggle_browse_available)
        cl.addWidget(self.browse_avail_check)

        self._avail_group = QGroupBox("Available Hosts")
        avail_vl = QVBoxLayout(self._avail_group)

        avail_ctrl = QWidget()
        avail_ctrl_hl = QHBoxLayout(avail_ctrl)
        avail_ctrl_hl.setContentsMargins(0, 0, 0, 0)
        load_avail_btn = QPushButton("Load Available Hosts")
        load_avail_btn.clicked.connect(self._load_available_hosts)
        avail_ctrl_hl.addWidget(load_avail_btn)
        self._avail_status = QLabel("")
        self._avail_status.setStyleSheet("color: gray; font-size: 10px;")
        avail_ctrl_hl.addWidget(self._avail_status)
        avail_ctrl_hl.addStretch()
        avail_vl.addWidget(avail_ctrl)

        self._avail_list = QListWidget()
        self._avail_list.setAlternatingRowColors(True)
        self._avail_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._avail_list.setFixedHeight(120)
        avail_vl.addWidget(self._avail_list)

        avail_btns = QWidget()
        avail_btns_hl = QHBoxLayout(avail_btns)
        avail_btns_hl.setContentsMargins(0, 0, 0, 0)
        use_sel_btn = QPushButton("Use Selected Hosts")
        use_sel_btn.clicked.connect(self._use_selected_hosts)
        avail_btns_hl.addWidget(use_sel_btn)
        clear_avail_btn = QPushButton("Clear")
        clear_avail_btn.clicked.connect(self._avail_list.clear)
        avail_btns_hl.addWidget(clear_avail_btn)
        avail_btns_hl.addStretch()
        avail_vl.addWidget(avail_btns)

        self._avail_group.setVisible(False)
        cl.addWidget(self._avail_group)

        # --- Advanced options row ---
        adv_row = QWidget()
        adv_rl = QHBoxLayout(adv_row)
        adv_rl.setContentsMargins(0, 0, 0, 0)

        self._adv_check = QCheckBox("Show advanced options ▼")
        self._adv_check.toggled.connect(self._toggle_advanced)
        adv_rl.addWidget(self._adv_check)
        adv_rl.addStretch()

        # No Wipe
        self._nowipe_check = QCheckBox("No Wipe")
        self._nowipe_check.toggled.connect(self._update_preview)
        adv_rl.addWidget(self._nowipe_check)

        # VLAN
        self._vlan_check = QCheckBox("Use VLAN")
        self._vlan_check.toggled.connect(self._toggle_vlan)
        adv_rl.addWidget(self._vlan_check)
        self._vlan_combo = QComboBox()
        self._vlan_combo.addItem("Select VLAN…")
        self._vlan_combo.setEnabled(False)
        self._vlan_combo.setFixedWidth(110)
        self._vlan_combo.currentIndexChanged.connect(self._update_preview)
        adv_rl.addWidget(self._vlan_combo)

        # QinQ
        self._qinq_check = QCheckBox("Use QinQ")
        self._qinq_check.toggled.connect(self._toggle_qinq)
        adv_rl.addWidget(self._qinq_check)
        self._qinq_combo = QComboBox()
        self._qinq_combo.addItems(["0", "1"])
        self._qinq_combo.setEnabled(False)
        self._qinq_combo.setFixedWidth(55)
        self._qinq_combo.currentIndexChanged.connect(self._update_preview)
        adv_rl.addWidget(self._qinq_combo)

        # OS
        self._os_check = QCheckBox("Use OS")
        self._os_check.toggled.connect(self._toggle_os)
        adv_rl.addWidget(self._os_check)
        self._os_combo = QComboBox()
        self._os_combo.addItem("Select OS…")
        self._os_combo.setEnabled(False)
        self._os_combo.setFixedWidth(160)
        self._os_combo.currentIndexChanged.connect(self._update_preview)
        adv_rl.addWidget(self._os_combo)

        cl.addWidget(adv_row)

        # --- Collapsible advanced frame (host filters) ---
        self._adv_frame = QGroupBox("Advanced Options")
        adv_fl = QVBoxLayout(self._adv_frame)
        self.host_filters = HostFilterFrame(self._adv_frame, self.shell, show_dates=False)
        adv_fl.addWidget(self.host_filters)
        self._adv_frame.setVisible(False)
        cl.addWidget(self._adv_frame)

        # --- Preview ---
        preview_box = QGroupBox("Preview")
        preview_vl = QVBoxLayout(preview_box)
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setFixedHeight(120)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.StyleHint.TypeWriter)
        self._preview_text.setFont(mono)
        preview_vl.addWidget(self._preview_text)
        cl.addWidget(preview_box)

        # --- Result (hidden until scheduling completes) ---
        self._result_box = QGroupBox("Scheduling Result")
        result_vl = QVBoxLayout(self._result_box)
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setFixedHeight(100)
        self._result_text.setFont(mono)
        result_vl.addWidget(self._result_text)
        self._result_box.setVisible(False)
        cl.addWidget(self._result_box)

        # --- Buttons ---
        btn_row = QWidget()
        btn_rl = QHBoxLayout(btn_row)
        btn_rl.setContentsMargins(0, 0, 0, 0)
        btn_rl.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._cancel)
        btn_rl.addWidget(cancel_btn)
        schedule_btn = QPushButton("Schedule Now")
        schedule_btn.setDefault(True)
        schedule_btn.clicked.connect(self._schedule)
        btn_rl.addWidget(schedule_btn)
        cl.addWidget(btn_row)

        cl.addStretch()

        self._update_preview()
        self._load_metadata_async()

    # ------------------------------------------------------------------ helpers

    def _show_login_prompt(self, root):
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(QLabel("Please login to schedule hosts"))
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self._auto_login)
        cl.addWidget(login_btn)
        root.addWidget(center, 1)

    def _auto_login(self):
        target = self.shell.get_auto_login_server()
        if target:
            success, error = self.shell.connect_to_server(target)
            if success:
                self.refresh()
            else:
                show_error_dialog(self, "Login Failed", f"Failed to connect to {target}", error or "")
        else:
            self.shell.gui_app._show_servers_view()

    def _load_metadata_async(self):
        def fetch():
            vlans = self.shell.get_available_vlans()
            os_list = self.shell.get_available_os()
            return vlans, os_list

        def apply(result):
            vlans, os_list = result
            if vlans:
                self._vlan_combo.clear()
                self._vlan_combo.addItem("Select VLAN…")
                self._vlan_combo.addItems(vlans)
            if os_list:
                self._os_combo.clear()
                self._os_combo.addItem("Select OS…")
                self._os_combo.addItems(os_list)

        self._meta_thread = _WorkerThread(fetch)
        self._meta_thread.result_ready.connect(apply)
        self._meta_thread.start()

    # ------------------------------------------------------------------ mode

    def _on_mode_changed(self, button_id, checked):
        if not checked:
            return
        mode = self._mode_group.checkedId()
        self.count_spin.setEnabled(mode == 0)
        self.hosts_entry.setEnabled(mode == 1)
        self.file_entry.setEnabled(mode == 2)
        self.browse_btn.setEnabled(mode == 2)
        self._update_preview()

    # ------------------------------------------------------------------ toggles

    def _toggle_browse_available(self, checked):
        self._avail_group.setVisible(checked)

    def _toggle_advanced(self, checked):
        self._advanced_visible = checked
        self._adv_frame.setVisible(checked)
        self._update_preview()

    def _toggle_vlan(self, checked):
        self._vlan_combo.setEnabled(checked)
        if not checked:
            self._vlan_combo.setCurrentIndex(0)
        self._update_preview()

    def _toggle_qinq(self, checked):
        self._qinq_combo.setEnabled(checked)
        self._update_preview()

    def _toggle_os(self, checked):
        self._os_combo.setEnabled(checked)
        if not checked:
            self._os_combo.setCurrentIndex(0)
        self._update_preview()

    # ------------------------------------------------------------------ available hosts

    def _load_available_hosts(self):
        if not self.shell.is_authenticated():
            self._avail_status.setText("Not connected")
            return

        self._avail_status.setText("Loading…")
        self._avail_list.clear()

        filters = {}
        if self._advanced_visible and hasattr(self, "host_filters"):
            filters = self.host_filters.get_filters()

        def fetch():
            return self.shell.get_available_hosts_data(**filters)

        def on_loaded(hosts):
            self._avail_list.clear()
            if not hosts:
                self._avail_list.addItem("No available hosts found")
                self._avail_status.setText("No hosts found")
                return
            for host in hosts:
                self._avail_list.addItem(host.get("name", ""))
            self._avail_status.setText(f"Loaded {len(hosts)} host(s)")
            self._available_hosts_loaded = True

        def on_error(exc):
            self._avail_status.setText(f"Error: {exc}")

        self._avail_thread = _WorkerThread(fetch)
        self._avail_thread.result_ready.connect(on_loaded)
        self._avail_thread.error_occurred.connect(on_error)
        self._avail_thread.start()

    def _use_selected_hosts(self):
        selected = [item.text() for item in self._avail_list.selectedItems() if "." in item.text()]
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select hosts from the list")
            return

        current = self.hosts_entry.text().strip()
        if current:
            existing = [h.strip() for h in current.replace("\n", ",").split(",") if h.strip()]
            for h in selected:
                if h not in existing:
                    existing.append(h)
            self.hosts_entry.setText(",".join(existing))
        else:
            self.hosts_entry.setText(",".join(selected))

        # Switch to "specific hostnames" mode
        self._mode_group.button(1).setChecked(True)
        self._update_preview()

    # ------------------------------------------------------------------ file

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Host List File", "", "Text files (*.txt);;All files (*)")
        if path:
            self.file_entry.setText(path)

    # ------------------------------------------------------------------ preview

    def _update_preview(self):
        if self._preview_text is None:
            return
        mode = self._mode_group.checkedId()
        lines = []

        if mode == 0:
            lines.append(f"• {self.count_spin.value()} hosts will be automatically selected")
        elif mode == 1:
            raw = self.hosts_entry.text().strip()
            host_list = [h.strip() for h in raw.split(",") if h.strip()] if raw else []
            lines.append(f"• {len(host_list)} specific host(s)")
        else:
            fp = self.file_entry.text().strip()
            lines.append(f"• Hosts from file: {fp or 'Not selected'}")

        lines.append("• Cloud will be auto-assigned")
        lines.append("• Duration: 5 days or until Sunday 21:00 UTC")
        lines.append("• Assignment will be activated immediately")

        if self._vlan_check.isChecked():
            vlan = self._vlan_combo.currentText()
            if vlan and vlan != "Select VLAN…":
                lines.append(f"• VLAN: {vlan}")

        if self._qinq_check.isChecked():
            lines.append(f"• QinQ: {self._qinq_combo.currentText()}")

        if self._os_check.isChecked():
            os_val = self._os_combo.currentText()
            if os_val and os_val != "Select OS…":
                lines.append(f"• OS: {os_val}")

        if self._nowipe_check.isChecked():
            lines.append("• No wipe (data will be preserved)")

        if self._advanced_visible and hasattr(self, "host_filters"):
            af = self.host_filters.get_filters()
            if "model" in af:
                lines.append(f"• Filter: Model {af['model']}")
            if "memory__gte" in af:
                lines.append(f"• Filter: RAM >= {af['memory__gte'] // 1024} GB")
            if "disks.disk_type" in af:
                lines.append(f"• Filter: Disk type {af['disks.disk_type']}")
            if "disks.size_gb__gte" in af:
                lines.append(f"• Filter: Disk size >= {af['disks.size_gb__gte']} GB")
            if "disks.count__gte" in af:
                lines.append(f"• Filter: Disk count >= {af['disks.count__gte']}")
            if "interfaces.vendor" in af:
                lines.append(f"• Filter: NIC vendor {af['interfaces.vendor']}")
            if "interfaces.speed__gte" in af:
                lines.append(f"• Filter: NIC speed >= {af['interfaces.speed__gte']} Gbps")

        self._preview_text.setPlainText("\n".join(lines))

    # ------------------------------------------------------------------ schedule

    def _validate_hostnames(self, hostnames):
        errors = []
        for hostname in hostnames:
            hostname = hostname.strip()
            if not hostname:
                continue
            try:
                host = self.shell.connection.api.get_host(hostname)
                if not host:
                    errors.append(f"{hostname}: Host not found")
                    continue
                if host.get("broken"):
                    errors.append(f"{hostname}: Host is marked as broken")
                    continue
                if host.get("retired"):
                    errors.append(f"{hostname}: Host is retired")
                    continue
                if not host.get("can_self_schedule"):
                    errors.append(f"{hostname}: Not enabled for self-scheduling")
            except Exception as exc:
                errors.append(f"{hostname}: Error checking host ({exc})")
        return len(errors) == 0, errors

    def _schedule(self):
        if not self.shell.is_authenticated():
            QMessageBox.critical(self, "Not Authenticated", "Please connect and login first")
            return

        description = self.desc_entry.text().strip()
        if not description:
            QMessageBox.critical(self, "Error", "Description is required")
            return

        mode = self._mode_group.checkedId()
        args_parts = []

        if mode == 0:
            # Count mode
            args_parts.append(str(self.count_spin.value()))

        elif mode == 1:
            # Specific hostnames
            hosts_raw = self.hosts_entry.text().strip()
            if not hosts_raw:
                QMessageBox.critical(self, "Error", "Hostnames are required")
                return
            hostname_list = [h.strip() for h in hosts_raw.split(",") if h.strip()]
            is_valid, errors = self._validate_hostnames(hostname_list)
            if not is_valid:
                msg = "The following hostnames are invalid:\n\n"
                msg += "\n".join(f"  • {e}" for e in errors)
                QMessageBox.critical(self, "Invalid Hostnames", msg)
                return
            args_parts.append(",".join(hostname_list))

        else:
            # From file
            file_path = self.file_entry.text().strip()
            if not file_path:
                QMessageBox.critical(self, "Error", "Please select a host list file")
                return
            try:
                with open(file_path) as fh:
                    hostname_list = [ln.strip() for ln in fh if ln.strip()]
                if not hostname_list:
                    QMessageBox.critical(self, "Error", f"No hostnames found in file: {file_path}")
                    return
                is_valid, errors = self._validate_hostnames(hostname_list)
                if not is_valid:
                    msg = f"The following hostnames in {file_path} are invalid:\n\n"
                    msg += "\n".join(f"  • {e}" for e in errors)
                    QMessageBox.critical(self, "Invalid Hostnames", msg)
                    return
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
                return
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Failed to read file: {exc}")
                return
            args_parts += ["host-list", file_path]

        args_parts += ["description", description]

        if self._vlan_check.isChecked():
            vlan = self._vlan_combo.currentText()
            if vlan and vlan != "Select VLAN…" and vlan != "No free VLANs available":
                args_parts += ["vlan", vlan]

        if self._qinq_check.isChecked():
            args_parts += ["qinq", self._qinq_combo.currentText()]

        if self._os_check.isChecked():
            os_val = self._os_combo.currentText()
            if os_val and os_val != "Select OS…" and os_val != "No OS options available":
                args_parts += ["os", os_val]

        if self._nowipe_check.isChecked():
            args_parts.append("nowipe")

        if self._advanced_visible and hasattr(self, "host_filters"):
            af = self.host_filters.get_filters()
            if "model" in af:
                args_parts += ["model", af["model"]]
            if "memory__gte" in af:
                args_parts += ["ram", str(af["memory__gte"] // 1024)]
            if "disks.disk_type" in af:
                args_parts += ["disk-type", af["disks.disk_type"]]
            if "disks.size_gb__gte" in af:
                args_parts += ["disk-size", str(af["disks.size_gb__gte"])]
            if "disks.count__gte" in af:
                args_parts += ["disk-count", str(af["disks.count__gte"])]
            if "interfaces.vendor" in af:
                args_parts += ["nic-vendor", af["interfaces.vendor"]]
            if "interfaces.speed__gte" in af:
                args_parts += ["nic-speed", str(af["interfaces.speed__gte"])]

        args = shlex.join(args_parts)

        try:
            self.shell._capture_output = True
            self.shell._captured_messages = []

            self.shell.user_commands.cmd_schedule(args)

            if self.shell._captured_messages:
                result_lines = [msg for _, msg in self.shell._captured_messages]
                self._result_text.setPlainText("\n".join(result_lines))
                self._result_box.setVisible(True)

            errors = [msg for level, msg in self.shell._captured_messages if level == "error"]
            if errors:
                QMessageBox.critical(self, "Scheduling Failed", "\n".join(errors))
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    "Hosts scheduled successfully!\n\n"
                    "View your assignments in the 'My Hosts' or 'Assignments' tab.",
                )
        except Exception as exc:
            show_error_dialog(self, "Scheduling Failed", str(exc), traceback.format_exc())
        finally:
            self.shell._capture_output = False

    # ------------------------------------------------------------------ cancel / reset

    def _cancel(self):
        self._reset_form()

    def _reset_form(self):
        self._mode_group.button(0).setChecked(True)
        self.count_spin.setValue(1)
        self.hosts_entry.clear()
        self.file_entry.clear()
        self.desc_entry.setText("Development testing environment")
        self._nowipe_check.setChecked(False)
        self._vlan_check.setChecked(False)
        self._vlan_combo.setCurrentIndex(0)
        self._vlan_combo.setEnabled(False)
        self._qinq_check.setChecked(False)
        self._qinq_combo.setCurrentIndex(0)
        self._qinq_combo.setEnabled(False)
        self._os_check.setChecked(False)
        self._os_combo.setCurrentIndex(0)
        self._os_combo.setEnabled(False)
        self._adv_check.setChecked(False)
        self.browse_avail_check.setChecked(False)
        if hasattr(self, "host_filters"):
            self.host_filters.clear_filters()
        self._result_box.setVisible(False)
        self._update_preview()

    # ------------------------------------------------------------------ refresh

    def refresh(self):
        authenticated = self.shell.is_authenticated()
        fully_built = self._preview_text is not None
        if authenticated and fully_built:
            self._update_preview()
        else:
            # Auth state changed, or first build was in login-prompt mode — rebuild
            self._create_ui()

    def prefill_hosts(self, hostnames):
        """Called by available.py to switch to hosts mode and prefill names."""
        if not hostnames or self._preview_text is None:
            return
        self._mode_group.button(1).setChecked(True)
        self.hosts_entry.setText(",".join(hostnames))
        self._update_preview()
