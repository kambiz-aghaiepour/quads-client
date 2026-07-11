"""Available hosts view - shows available hosts for scheduling"""

import tkinter as tk
from tkinter import ttk

from quads_client.gui.widgets.base import BaseAdminView, ScrolledTreeview
from quads_client.gui.widgets.host_filters import HostFilterFrame


class AvailableView(BaseAdminView):
    """View for displaying available hosts"""

    def __init__(self, parent, shell):
        super().__init__(parent, shell, "Available Hosts", requires_admin=False)
        self._create_ui()

    def _create_ui(self):
        """Create the UI"""
        # Header with refresh button
        self.create_header([("🔄 Refresh", self.refresh)])

        # Check if connected
        if not self.shell.is_authenticated():
            # Show not connected message
            message_frame = ttk.Frame(self)
            message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=50)

            ttk.Label(
                message_frame, text="Not connected to any QUADS server", font=("TkDefaultFont", 14), foreground="gray"
            ).pack(pady=20)

            ttk.Label(message_frame, text="Please connect to a server from the Servers view", foreground="gray").pack(
                pady=10
            )

            ttk.Button(
                message_frame, text="Go to Servers", command=lambda: self.shell.gui_app._show_servers_view()
            ).pack(pady=10)

            # Status label
            self.create_status_label()
            return

        # Filter frame with reusable HostFilterFrame
        self.filter_frame = HostFilterFrame(self, self.shell, show_dates=True)
        self.filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.filter_frame.populate_metadata_async()

        # Button row: Apply + Clear
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Button(button_frame, text="Apply", command=self._load_available).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Filters", command=self._clear_and_reload).pack(side=tk.LEFT, padx=5)

        # Content frame with scrolled treeview
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("host", "model", "type", "self_schedule")
        column_configs = {
            "host": ("Host", 300),
            "model": ("Model", 120),
            "type": ("Type", 100),
            "self_schedule": ("Self-Schedule", 120),
        }

        # Enable multi-selection with Ctrl+click and Shift+click
        self.tree = ScrolledTreeview(content_frame, columns, column_configs, selectmode="extended")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Enable copy/paste
        self._setup_clipboard()

        # Bind to selection events to update button states
        self.tree.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

        # Action buttons (store references for enable/disable)
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.copy_selected_btn = ttk.Button(action_frame, text="Copy Selected", command=self._copy_selected)
        self.copy_selected_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(action_frame, text="Copy All", command=self._copy_all).pack(side=tk.LEFT, padx=5)

        # Show "Admin Schedule" for admins, "Schedule Now" for normal users
        button_text = "Admin Schedule" if self.shell.is_admin() else "Schedule Now"
        self.schedule_now_btn = ttk.Button(action_frame, text=button_text, command=self._schedule_selected)
        self.schedule_now_btn.pack(side=tk.LEFT, padx=5)

        self.unselect_btn = ttk.Button(action_frame, text="Unselect All", command=self._unselect_all)
        self.unselect_btn.pack(side=tk.LEFT, padx=5)

        # Initially disable selection-dependent buttons
        self._update_button_states()

        # Status label
        self.create_status_label()

        # Initial load
        self._load_available()

    def _setup_clipboard(self):
        """Setup clipboard keyboard shortcuts"""
        # Ctrl+C / Cmd+C to copy
        self.tree.tree.bind("<Control-c>", lambda e: self._copy_selected())
        self.tree.tree.bind("<Command-c>", lambda e: self._copy_selected())

    def _on_selection_changed(self, event=None):
        """Handle tree selection changes"""
        self._update_button_states()

    def _update_button_states(self):
        """Enable/disable buttons based on selection"""
        if self.tree is None:
            return

        selection = self.tree.selection()
        has_selection = len(selection) > 0

        # Enable/disable selection-dependent buttons
        if hasattr(self, "copy_selected_btn"):
            self.copy_selected_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)

        if hasattr(self, "schedule_now_btn"):
            self.schedule_now_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)

        if hasattr(self, "unselect_btn"):
            self.unselect_btn.config(state=tk.NORMAL if has_selection else tk.DISABLED)

    def _unselect_all(self):
        """Clear all selections"""
        if self.tree is None:
            return

        # Clear selection
        for item in self.tree.selection():
            self.tree.tree.selection_remove(item)

        self.update_status("Selection cleared")

    def _clear_and_reload(self):
        """Clear all filters and reload"""
        self.filter_frame.clear_filters()
        self._load_available()

    def _load_available(self):
        """Load available hosts from server"""
        if not self.shell.is_authenticated():
            self.update_status("Not connected to server")
            return

        if self.tree is None:
            return

        self.tree.clear()
        filters = self.filter_frame.get_filters()

        def load_data():
            return self.shell.get_available_hosts_data(**filters)

        def on_loaded(hosts):
            if not hosts:
                self.update_status("No available hosts found")
                return

            for host in hosts:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        host["name"],
                        host["model"],
                        host["host_type"],
                        "Yes" if host["can_self_schedule"] else "No",
                    ),
                )

            self.update_status(f"Loaded {len(hosts)} available host(s)")
            self._update_button_states()

        self.safe_load_data_async(load_data, on_loaded)

    def _copy_selected(self):
        """Copy selected hostnames (first column only) to clipboard"""
        if self.tree is None:
            return

        selection = self.tree.selection()
        if not selection:
            self.update_status("No items selected to copy")
            return

        # Only copy hostnames (first column)
        hostnames = []
        for item in selection:
            values = self.tree.item(item, "values")
            hostname = values[0]  # First column is hostname
            hostnames.append(hostname)

        text = "\n".join(hostnames)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_status(f"Copied {len(hostnames)} hostname(s) to clipboard")

    def _copy_all(self):
        """Copy all rows to clipboard"""
        if self.tree is None:
            return

        items = self.tree.tree.get_children()
        if not items:
            self.update_status("No data to copy")
            return

        # Add header
        columns = self.tree.tree["columns"]
        header = "\t".join(self.tree.tree.heading(col)["text"] for col in columns)

        lines = [header]
        for item in items:
            values = self.tree.item(item, "values")
            lines.append("\t".join(str(v) for v in values))

        text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_status(f"Copied {len(items)} row(s) with headers to clipboard")

    def _schedule_selected(self):
        """Schedule selected hosts - open admin schedule dialog or navigate to SSM schedule view"""
        if self.tree is None:
            return

        selection = self.tree.selection()
        if not selection:
            self.update_status("No hosts selected - please select one or more hosts")
            return

        # Get selected hostnames
        hostnames = []
        for item in selection:
            values = self.tree.item(item, "values")
            hostname = values[0]
            hostnames.append(hostname)

        if not hostnames:
            self.update_status("No valid hosts selected")
            return

        # If admin, open admin schedule dialog with pre-filled hosts
        if self.shell.is_admin():
            # Get admin schedule view and call its create dialog with pre-filled hosts
            self.shell.gui_app._ensure_view("admin_schedule")
            if "admin_schedule" in self.shell.gui_app.views:
                admin_schedule_view = self.shell.gui_app.views["admin_schedule"]
                admin_schedule_view._create_schedule(prefill_hosts=",".join(hostnames))
                self.update_status(f"Opened admin schedule dialog with {len(hostnames)} host(s) pre-filled")
            else:
                self.update_status("Admin schedule view not available")
        else:
            # Navigate to SSM Schedule view and pre-fill hosts
            self.shell.gui_app._show_schedule_view()

            # Pre-fill the schedule view with selected hosts
            if "schedule" in self.shell.gui_app.views:
                schedule_view = self.shell.gui_app.views["schedule"]

                # Switch to "Specific hostnames" mode
                schedule_view.mode_var.set("hosts")
                schedule_view._on_mode_changed()

                # Fill in the hostnames
                schedule_view.hosts_entry.delete(0, tk.END)
                schedule_view.hosts_entry.insert(0, ",".join(hostnames))

                # Update preview
                schedule_view._update_preview()

            self.update_status(f"Navigated to Schedule with {len(hostnames)} host(s) pre-filled")

    def refresh(self):
        """Public method to refresh the view"""
        if self.tree is not None and self.shell.is_authenticated():
            self._load_available()
        else:
            # Connection state changed, need to rebuild UI
            for widget in self.winfo_children():
                widget.destroy()
            self.tree = None
            self._create_ui()
