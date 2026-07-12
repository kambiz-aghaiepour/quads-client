"""Theme manager for QUADS Client GUI - PySide6 dark/light mode via QPalette + Fusion style"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeManager:
    """Manages dark/light themes via QPalette + QSS on the Fusion style"""

    _SEMANTIC = {
        "dark": {
            "success": "#4ec9b0",
            "provisioning": "#dcdcaa",
            "warning": "#ce9178",
            "error": "#f48771",
        },
        "light": {
            "success": "#006200",
            "provisioning": "#d97706",
            "warning": "#bf8803",
            "error": "#a31515",
        },
    }

    def __init__(self, initial_theme="dark"):
        self.current_theme_mode = initial_theme
        self.apply_theme(initial_theme)

    @staticmethod
    def _dark_palette():
        p = QPalette()
        bg = QColor("#1e1e1e")
        fg = QColor("#d4d4d4")
        panel = QColor("#252526")
        entry = QColor("#3c3c3c")
        accent = QColor("#007acc")
        disabled = QColor("#6a6a6a")
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, fg)
        p.setColor(QPalette.ColorRole.Base, entry)
        p.setColor(QPalette.ColorRole.AlternateBase, panel)
        p.setColor(QPalette.ColorRole.Text, fg)
        p.setColor(QPalette.ColorRole.Button, panel)
        p.setColor(QPalette.ColorRole.ButtonText, fg)
        p.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.Highlight, accent)
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipBase, panel)
        p.setColor(QPalette.ColorRole.ToolTipText, fg)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#5a5a5a"))
        p.setColor(QPalette.ColorRole.Link, accent)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
        return p

    @staticmethod
    def _light_palette():
        p = QPalette()
        bg = QColor("#ffffff")
        fg = QColor("#1a1a1a")
        panel = QColor("#f3f3f3")
        entry = QColor("#ffffff")
        accent = QColor("#0066cc")
        disabled = QColor("#a0a0a0")
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, fg)
        p.setColor(QPalette.ColorRole.Base, entry)
        p.setColor(QPalette.ColorRole.AlternateBase, panel)
        p.setColor(QPalette.ColorRole.Text, fg)
        p.setColor(QPalette.ColorRole.Button, panel)
        p.setColor(QPalette.ColorRole.ButtonText, fg)
        p.setColor(QPalette.ColorRole.BrightText, QColor("#000000"))
        p.setColor(QPalette.ColorRole.Highlight, accent)
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffcc"))
        p.setColor(QPalette.ColorRole.ToolTipText, fg)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9a9a9a"))
        p.setColor(QPalette.ColorRole.Link, accent)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
        return p

    @staticmethod
    def _build_qss(mode):
        is_dark = mode == "dark"
        accent = "#007acc" if is_dark else "#0066cc"
        sidebar_hover = "#3e3e42" if is_dark else "#dde8f8"
        tree_alt = "#252526" if is_dark else "#f5f5f5"
        group_border = "#3e3e42" if is_dark else "#cccccc"
        group_title = "#9cdcfe" if is_dark else "#444444"
        scrollbar_bg = "#2d2d2d" if is_dark else "#f0f0f0"
        scrollbar_handle = "#555555" if is_dark else "#b0b0b0"

        return f"""
QTreeWidget {{
    alternate-background-color: {tree_alt};
    show-decoration-selected: 1;
    border: 1px solid {group_border};
}}
QHeaderView::section {{
    padding: 4px 8px;
    border: none;
    border-right: 1px solid {group_border};
    border-bottom: 1px solid {group_border};
}}
QGroupBox {{
    border: 1px solid {group_border};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 4px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: {group_title};
    font-weight: bold;
}}
QPushButton#nav_btn {{
    text-align: left;
    border: none;
    border-radius: 0px;
    padding: 7px 14px;
    font-size: 13px;
}}
QPushButton#nav_btn:hover {{
    background-color: {sidebar_hover};
}}
QPushButton#nav_btn[active="true"] {{
    border-left: 3px solid {accent};
    padding-left: 11px;
    font-weight: bold;
}}
QScrollBar:vertical {{
    background: {scrollbar_bg};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {scrollbar_handle};
    min-height: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {scrollbar_bg};
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {scrollbar_handle};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""

    def apply_theme(self, mode="dark"):
        self.current_theme_mode = mode
        app = QApplication.instance()
        if app is None:
            return
        app.setStyle("Fusion")
        palette = self._dark_palette() if mode == "dark" else self._light_palette()
        app.setPalette(palette)
        app.setStyleSheet(self._build_qss(mode))

    def toggle_theme(self):
        new_mode = "light" if self.current_theme_mode == "dark" else "dark"
        self.apply_theme(new_mode)
        return new_mode

    def get_color(self, name):
        return self._SEMANTIC.get(self.current_theme_mode, {}).get(name, "#888888")

    def get_theme_info(self):
        return "PySide6 Fusion"

    def configure_toplevel(self, widget):
        pass  # No-op: QPalette propagates automatically to all child widgets

    @property
    def current_mode(self):
        return self.current_theme_mode
