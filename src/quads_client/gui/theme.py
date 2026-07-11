"""Theme manager for QUADS Client GUI with dark/light mode support"""

import tkinter as tk  # noqa: F401
from tkinter import ttk


class ThemeManager:
    """Manages themes and color schemes for the GUI"""

    DARK_THEME = {
        "bg": "#1e1e1e",
        "fg": "#d4d4d4",
        "accent": "#007acc",
        "success": "#4ec9b0",  # Cyan-green for dark backgrounds (active/complete)
        "provisioning": "#dcdcaa",  # Light yellow for in-progress state
        "warning": "#dcdcaa",  # Yellow for warnings
        "error": "#f48771",  # Red-orange for errors
        "panel_bg": "#252526",
        "border": "#3e3e42",
        "button_bg": "#0e639c",
        "button_fg": "#ffffff",
        "entry_bg": "#343638",  # Dark gray per CustomTkinter/Material Design
        "entry_fg": "#dce4ee",  # Light text for readability
        "text_bg": "#1e1e1e",  # Match main background for Text widgets
        "text_fg": "#d4d4d4",  # Match main foreground
    }

    LIGHT_THEME = {
        "bg": "#ffffff",
        "fg": "#000000",
        "accent": "#0066cc",
        "success": "#006200",  # Dark green for WCAG AAA compliance (active/complete)
        "provisioning": "#d97706",  # Amber-600 for in-progress state (WCAG AA compliant)
        "warning": "#bf8803",  # Orange-brown for warnings
        "error": "#a31515",  # Darker red for better contrast
        "panel_bg": "#f3f3f3",
        "border": "#cccccc",
        "button_bg": "#0066cc",
        "button_fg": "#ffffff",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "text_bg": "#ffffff",  # White background for Text widgets
        "text_fg": "#000000",  # Black text
    }

    def __init__(self, root, initial_theme="dark"):
        self.root = root
        self.style = ttk.Style(root)
        self.current_theme_mode = initial_theme
        self.has_sv_ttk = False
        self.has_ttkthemes = False

        self._detect_available_themes()
        self.apply_theme(initial_theme)

    def _detect_available_themes(self):
        """Detect which theme packages are available"""
        try:
            import sv_ttk  # noqa: F401

            self.has_sv_ttk = True
        except ImportError:
            pass

        try:
            import ttkthemes  # noqa: F401

            self.has_ttkthemes = True
        except ImportError:
            pass

    def apply_theme(self, mode="dark"):
        """Apply theme based on mode (dark or light)"""
        self.current_theme_mode = mode

        if self.has_sv_ttk:
            self._apply_sv_ttk_theme(mode)
        elif self.has_ttkthemes:
            self._apply_ttkthemes_theme(mode)
        else:
            self._apply_builtin_theme(mode)

    def _apply_sv_ttk_theme(self, mode):
        """Apply Sun Valley theme (modern Windows 11-like)"""
        try:
            import sv_ttk

            if mode == "dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme("light")

            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply sv_ttk theme: {e}")
            self._apply_builtin_theme(mode)

    def _apply_ttkthemes_theme(self, mode):
        """Apply ttkthemes (arc, adapta, breeze, etc.)"""
        try:
            if mode == "dark":
                self.style.theme_use("arc")
            else:
                self.style.theme_use("breeze")

            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply ttkthemes: {e}")
            self._apply_builtin_theme(mode)

    def _apply_builtin_theme(self, mode):
        """Fallback to built-in 'clam' theme with custom colors"""
        try:
            self.style.theme_use("clam")
            self._apply_custom_colors(mode)
        except Exception as e:
            print(f"Warning: Failed to apply built-in theme: {e}")
            self.style.theme_use("default")

    def _apply_custom_colors(self, mode):
        """Apply custom color scheme to current theme"""
        colors = self.DARK_THEME if mode == "dark" else self.LIGHT_THEME

        self.root.configure(bg=colors["bg"])

        self.style.configure(".", background=colors["bg"], foreground=colors["fg"])

        self.style.configure("TFrame", background=colors["bg"], bordercolor=colors["border"])

        self.style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])

        # Only override TButton styling for built-in themes
        # sv-ttk handles its own button appearance natively
        if not self.has_sv_ttk:
            self.style.configure(
                "TButton",
                background=colors["button_bg"],
                foreground=colors["button_fg"],
                bordercolor=colors["border"],
                focuscolor=colors["accent"],
            )

            self.style.map(
                "TButton",
                background=[("active", colors["accent"]), ("pressed", colors["accent"])],
                foreground=[("active", colors["button_fg"]), ("pressed", colors["button_fg"]), ("disabled", "gray")],
            )

        self.style.configure(
            "Sidebar.TButton",
            background=colors["bg"],
            foreground=colors["fg"],
            borderwidth=0,
            relief="flat",
            anchor="w",
            padding=(10, 4),
            font=("TkDefaultFont", 11),
            bordercolor=colors["bg"],
            lightcolor=colors["bg"],
            darkcolor=colors["bg"],
            focuscolor=colors["bg"],
            shiftrelief=0,
        )

        self.style.map(
            "Sidebar.TButton",
            background=[("pressed", colors["panel_bg"]), ("active", colors["panel_bg"])],
            foreground=[("pressed", colors["fg"]), ("active", colors["fg"])],
            relief=[("pressed", "flat")],
            bordercolor=[("pressed", colors["bg"]), ("active", colors["bg"])],
            lightcolor=[("pressed", colors["bg"]), ("active", colors["bg"])],
            darkcolor=[("pressed", colors["bg"]), ("active", colors["bg"])],
        )

        self.style.configure(
            "Sidebar.Active.TButton",
            background=colors["bg"],
            foreground=colors["fg"],
            borderwidth=2,
            relief="solid",
            anchor="w",
            padding=(8, 2),
            font=("TkDefaultFont", 11),
            bordercolor=colors["accent"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"],
            focuscolor=colors["bg"],
            shiftrelief=0,
        )

        self.style.map(
            "Sidebar.Active.TButton",
            background=[("pressed", colors["panel_bg"]), ("active", colors["panel_bg"])],
            foreground=[("pressed", colors["fg"]), ("active", colors["fg"])],
            relief=[("pressed", "solid")],
            bordercolor=[("pressed", colors["accent"]), ("active", colors["accent"])],
            lightcolor=[("pressed", colors["accent"]), ("active", colors["accent"])],
            darkcolor=[("pressed", colors["accent"]), ("active", colors["accent"])],
        )

        self.style.configure(
            "TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            bordercolor=colors["border"],
        )

        self.style.configure(
            "Treeview",
            background=colors["bg"],
            foreground=colors["fg"],
            fieldbackground=colors["bg"],
            bordercolor=colors["border"],
        )

        # Configure selection and hover colors for dark mode
        if mode == "dark":
            # Dark mode: bright selection with dark text
            self.style.map(
                "Treeview",
                background=[("selected", "#007acc")],  # Blue selection background
                foreground=[("selected", "#ffffff")],  # White text on selection
            )
        else:
            # Light mode: standard selection colors
            self.style.map(
                "Treeview",
                background=[("selected", "#0078d7")],  # Blue selection background
                foreground=[("selected", "#ffffff")],  # White text on selection
            )

        self.style.configure(
            "Treeview.Heading",
            background=colors["panel_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            relief="flat",
        )

        self.style.map(
            "Treeview.Heading",
            background=[("active", colors["border"]), ("!active", colors["panel_bg"])],
            foreground=[("active", colors["fg"]), ("!active", colors["fg"])],
        )

        self.style.configure("TNotebook", background=colors["bg"], bordercolor=colors["border"])

        self.style.configure(
            "TNotebook.Tab",
            background=colors["panel_bg"],
            foreground=colors["fg"],
            padding=[10, 5],
        )

        self.style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["button_fg"])],
        )

        self.style.configure("TMenubutton", background=colors["panel_bg"])

        # Checkbutton and Radiobutton configurations for dark mode visibility
        self.style.configure(
            "TCheckbutton",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.map(
            "TCheckbutton",
            foreground=[("active", colors["fg"])],  # Keep text visible on hover
            background=[("active", colors["bg"])],
        )

        self.style.configure(
            "TRadiobutton",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.map(
            "TRadiobutton",
            foreground=[("active", colors["fg"])],  # Keep text visible on hover
            background=[("active", colors["bg"])],
        )

        # Combobox configuration
        self.style.configure(
            "TCombobox",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            background=colors["panel_bg"],
            bordercolor=colors["border"],
            arrowcolor=colors["entry_fg"],
        )

        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["entry_bg"])],
            foreground=[("readonly", colors["entry_fg"])],
        )

        # Combobox dropdown popup listbox (not stylable via ttk.Style)
        self.root.option_add("*TCombobox*Listbox.background", colors["entry_bg"])
        self.root.option_add("*TCombobox*Listbox.foreground", colors["entry_fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", colors["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

        # Spinbox configuration
        self.style.configure(
            "TSpinbox",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            bordercolor=colors["border"],
        )

        # LabelFrame configuration
        self.style.configure(
            "TLabelframe",
            background=colors["bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
        )

        self.style.configure(
            "TLabelframe.Label",
            background=colors["bg"],
            foreground=colors["fg"],
        )

        self.style.configure("Success.TLabel", foreground=colors["success"], background=colors["bg"])

        self.style.configure("Warning.TLabel", foreground=colors["warning"], background=colors["bg"])

        self.style.configure("Error.TLabel", foreground=colors["error"], background=colors["bg"])

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        new_mode = "light" if self.current_theme_mode == "dark" else "dark"
        self.apply_theme(new_mode)
        return new_mode

    def get_color(self, color_name):
        """Get a color from the current theme"""
        colors = self.DARK_THEME if self.current_theme_mode == "dark" else self.LIGHT_THEME
        return colors.get(color_name, "#000000")

    def get_theme_info(self):
        """Get information about active theme backend"""
        if self.has_sv_ttk:
            return "Sun Valley (sv-ttk)"
        elif self.has_ttkthemes:
            return "ttkthemes"
        else:
            return "Built-in (clam)"

    def configure_toplevel(self, toplevel):
        """Configure a Toplevel dialog with current theme colors"""
        colors = self.DARK_THEME if self.current_theme_mode == "dark" else self.LIGHT_THEME
        toplevel.configure(bg=colors["bg"])

    @property
    def current_mode(self):
        """Get current theme mode"""
        return self.current_theme_mode
