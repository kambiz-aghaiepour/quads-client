"""Theme manager for QUADS Client GUI — metallic dark-steel / brushed-nickel themes via QPalette + QSS"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor


class ThemeManager:
    """Manages dark (brushed dark steel) and light (brushed nickel) themes."""

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

    # ------------------------------------------------------------------ palettes

    @staticmethod
    def _dark_palette():
        """Brushed dark-steel palette."""
        p = QPalette()
        bg = QColor("#1e2128")  # dark steel blue-grey
        fg = QColor("#d4d8e2")  # cool white text
        panel = QColor("#16181f")  # darker panel / sidebar
        entry = QColor("#12141c")  # very dark sunken input
        alt = QColor("#242836")  # tree alternating row — clearly distinct from entry
        accent = QColor("#4a9eff")  # bright blue accent
        disabled = QColor("#5a5e6a")  # dimmed text
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, fg)
        p.setColor(QPalette.ColorRole.Base, entry)
        p.setColor(QPalette.ColorRole.AlternateBase, alt)
        p.setColor(QPalette.ColorRole.Text, fg)
        p.setColor(QPalette.ColorRole.Button, QColor("#3a3f4b"))
        p.setColor(QPalette.ColorRole.ButtonText, fg)
        p.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.Highlight, accent)
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        p.setColor(QPalette.ColorRole.ToolTipBase, panel)
        p.setColor(QPalette.ColorRole.ToolTipText, fg)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#4a4e5a"))
        p.setColor(QPalette.ColorRole.Link, accent)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
        return p

    @staticmethod
    def _light_palette():
        """Brushed nickel palette."""
        p = QPalette()
        bg = QColor("#c4c8d0")  # nickel grey
        fg = QColor("#1a1c22")  # near-black text
        entry = QColor("#dce0e8")  # light input background
        alt = QColor("#b8bcc4")  # tree alternating row
        accent = QColor("#0055cc")  # deep blue accent
        disabled = QColor("#9a9ea8")  # dimmed text
        p.setColor(QPalette.ColorRole.Window, bg)
        p.setColor(QPalette.ColorRole.WindowText, fg)
        p.setColor(QPalette.ColorRole.Base, entry)
        p.setColor(QPalette.ColorRole.AlternateBase, alt)
        p.setColor(QPalette.ColorRole.Text, fg)
        p.setColor(QPalette.ColorRole.Button, QColor("#c8ccd4"))
        p.setColor(QPalette.ColorRole.ButtonText, fg)
        p.setColor(QPalette.ColorRole.BrightText, QColor("#000000"))
        p.setColor(QPalette.ColorRole.Highlight, accent)
        p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        p.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffcc"))
        p.setColor(QPalette.ColorRole.ToolTipText, fg)
        p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9a9ea8"))
        p.setColor(QPalette.ColorRole.Link, accent)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled)
        p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled)
        return p

    # ------------------------------------------------------------------ QSS

    @staticmethod
    def _build_qss(mode):
        is_dark = mode == "dark"

        # Scale nav-button font with the current application base font
        app = QApplication.instance()
        nav_pt = app.font().pointSize() if app else 11

        if is_dark:
            # ── BRUSHED DARK STEEL ────────────────────────────────────────────
            # Horizontal brushed sweep — dark navy edges, visibly lighter centre
            bg_main = (
                "qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #111420,stop:0.3 #1c2134,stop:0.5 #232840,"
                "stop:0.7 #1c2134,stop:1 #111420)"
            )
            bg_sidebar = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0a0c14,stop:0.5 #171c2a,stop:1 #0a0c14)"

            # Buttons — raised metallic: lighter top fades to darker bottom
            btn_up = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #525869,stop:0.45 #3f4455,stop:0.55 #373c4d,stop:1 #2c3040)"
            )
            btn_hover = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #626879,stop:0.45 #4f5465,stop:0.55 #474c5d,stop:1 #3c4050)"
            )
            # Pressed — inverted gradient (darker top = sunk in)
            btn_dn = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #1e2230,stop:0.45 #262a38,stop:0.55 #2e3242,stop:1 #3c4052)"
            )
            btn_disabled = "#2c303c"

            # Asymmetric bevel borders — light top/left = raised surface
            bup_t = "#686d80"
            bup_l = "#5a5f72"
            bup_b = "#0d1018"
            bup_r = "#13161e"
            # Pressed: invert the bevel
            bdn_t = "#0d1018"
            bdn_l = "#13161e"
            bdn_b = "#686d80"
            bdn_r = "#5a5f72"

            # Inputs — sunken: dark top/left border, light bottom/right
            input_bg = "#12141c"
            iup_t = "#09090f"
            iup_l = "#0b0c14"
            iup_b = "#3c4052"
            iup_r = "#343849"

            fg = "#d4d8e2"
            fg_dis = "#4a4e5a"
            accent = "#4a9eff"
            accent_dk = "#2a6fb5"
            group_bdr = "#2e3244"
            group_title = "#8ab4e8"
            tree_alt = "#242836"
            hdr_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1," "stop:0 #31364a,stop:1 #252838)"
            sel_bg = accent
            sel_fg = "#000000"  # black on #4a9eff: 7.4:1 contrast (WCAG AAA)
            sb_hover = "#2a2e3e"
            scr_bg = "#13151c"
            scr_hdl = "#42475a"
            menu_bg = "#1a1d26"

        else:
            # ── BRUSHED NICKEL ────────────────────────────────────────────────
            # Horizontal nickel sweep: darker edges, bright centre highlight
            bg_main = (
                "qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                "stop:0 #adb1b9,stop:0.3 #c8ccd4,stop:0.5 #d4d8e0,"
                "stop:0.7 #c8ccd4,stop:1 #adb1b9)"
            )
            bg_sidebar = "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8a8e96,stop:0.5 #b4b8c4,stop:1 #8a8e96)"

            # Buttons — raised nickel
            btn_up = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #e0e4ec,stop:0.45 #ccd0d8,stop:0.55 #bcc0cc,stop:1 #abafc0)"
            )
            btn_hover = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #eef2fa,stop:0.45 #dce0ec,stop:0.55 #ccd0dc,stop:1 #bbbfd0)"
            )
            # Pressed — sunk in
            btn_dn = (
                "qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "stop:0 #9ea2ae,stop:0.45 #aaaebc,stop:0.55 #b6baca,stop:1 #c8ccda)"
            )
            btn_disabled = "#b8bcc8"

            # Asymmetric bevel
            bup_t = "#eef2fa"
            bup_l = "#dce0ea"
            bup_b = "#757880"
            bup_r = "#858890"
            bdn_t = "#757880"
            bdn_l = "#858890"
            bdn_b = "#eef2fa"
            bdn_r = "#dce0ea"

            # Inputs — sunken
            input_bg = "#dce0ea"
            iup_t = "#8a8e96"
            iup_l = "#94989e"
            iup_b = "#f4f8ff"
            iup_r = "#e8ecf8"

            fg = "#1a1c22"
            fg_dis = "#9a9ea8"
            accent = "#0055cc"
            accent_dk = "#003d99"
            group_bdr = "#9a9ea6"
            group_title = "#003d99"
            tree_alt = "#b8bcc4"
            hdr_bg = "qlineargradient(x1:0,y1:0,x2:0,y2:1," "stop:0 #d0d4dc,stop:1 #b8bcc8)"
            sel_bg = accent
            sel_fg = "#ffffff"  # white on #0055cc: 6.5:1 contrast (WCAG AA)
            sb_hover = "#d0d4dc"
            scr_bg = "#a4a8b0"
            scr_hdl = "#7c808a"
            menu_bg = "#c8ccd4"

        return f"""
/* ════════════════════════════════════════════════════════
   BASE — transparent so metallic surfaces show through.
   All more-specific rules below override this.
   ════════════════════════════════════════════════════════ */
QWidget {{
    background: transparent;
    color: {fg};
}}

/* ════════════════════════════════════════════════════════
   BACKGROUNDS — brushed metal gradient surfaces
   ════════════════════════════════════════════════════════ */
QMainWindow {{
    background: {bg_main};
}}
QWidget#main_content {{
    background: {bg_main};
}}
QStackedWidget {{
    /* transparent so the main_content metallic gradient shows through */
    background: transparent;
}}
QFrame#sidebar {{
    background: {bg_sidebar};
}}

/* ════════════════════════════════════════════════════════
   BUTTONS — metallic raised look with asymmetric bevel
   ════════════════════════════════════════════════════════ */
QPushButton {{
    background: {btn_up};
    color: {fg};
    border-style: solid;
    border-width: 1px;
    border-top-color:    {bup_t};
    border-left-color:   {bup_l};
    border-bottom-color: {bup_b};
    border-right-color:  {bup_r};
    border-radius: 3px;
    padding: 4px 12px;
    min-height: 22px;
}}
QPushButton:hover {{
    background: {btn_hover};
    border-top-color:    {bup_t};
    border-left-color:   {bup_l};
}}
QPushButton:pressed {{
    background: {btn_dn};
    border-top-color:    {bdn_t};
    border-left-color:   {bdn_l};
    border-bottom-color: {bdn_b};
    border-right-color:  {bdn_r};
    /* shift content 1 px down-right to simulate physical depression */
    padding: 5px 11px 3px 13px;
}}
QPushButton:disabled {{
    background: {btn_disabled};
    color: {fg_dis};
    border-top-color:    {group_bdr};
    border-left-color:   {group_bdr};
    border-bottom-color: {group_bdr};
    border-right-color:  {group_bdr};
}}

/* ── Sidebar navigation buttons ─────────────────────── */
QPushButton#nav_btn {{
    text-align: left;
    border: none;
    border-radius: 0px;
    padding: 7px 14px;
    font-size: {nav_pt}pt;
    background: transparent;
    color: {fg};
    /* no bevel — flat surface flush with the sidebar panel */
}}
QPushButton#nav_btn:hover {{
    background: {sb_hover};
}}
QPushButton#nav_btn:pressed {{
    /* subtle inset: slightly darker background, no bevel flip */
    background: {btn_dn};
    padding: 8px 14px 6px 15px;
}}
QPushButton#nav_btn[active="true"] {{
    border-left: 3px solid {accent};
    padding-left: 11px;
    font-weight: bold;
}}

/* ════════════════════════════════════════════════════════
   INPUT FIELDS — sunken inset (dark top/left = recessed)
   ════════════════════════════════════════════════════════ */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {input_bg};
    color: {fg};
    border-style: solid;
    border-width: 1px;
    border-top-color:    {iup_t};
    border-left-color:   {iup_l};
    border-bottom-color: {iup_b};
    border-right-color:  {iup_r};
    border-radius: 2px;
    padding: 2px 4px;
    selection-background-color: {sel_bg};
    selection-color: {sel_fg};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-top-color:  {accent_dk};
    border-left-color: {accent_dk};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    background: {btn_disabled};
    color: {fg_dis};
}}

/* ── ComboBox / SpinBox ─────────────────────────────── */
QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {{
    background: {input_bg};
    color: {fg};
    border-style: solid;
    border-width: 1px;
    border-top-color:    {iup_t};
    border-left-color:   {iup_l};
    border-bottom-color: {iup_b};
    border-right-color:  {iup_r};
    border-radius: 2px;
    padding: 2px 4px;
    min-height: 20px;
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
    background: {btn_up};
    border-left-style: solid;
    border-left-width: 1px;
    border-left-color: {iup_t};
    border-top-right-radius: 2px;
    border-bottom-right-radius: 2px;
}}
QComboBox::drop-down:hover {{
    background: {btn_hover};
}}
QComboBox QAbstractItemView {{
    background: {input_bg};
    color: {fg};
    selection-background-color: {sel_bg};
    selection-color: {sel_fg};
    border: 1px solid {group_bdr};
    outline: none;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background: {btn_up};
    border-left: 1px solid {iup_t};
    border-bottom: 1px solid {iup_t};
    border-top-right-radius: 2px;
    width: 16px;
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {{
    background: {btn_dn};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {btn_up};
    border-left: 1px solid {iup_t};
    border-bottom-right-radius: 2px;
    width: 16px;
}}
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: {btn_dn};
}}

/* ════════════════════════════════════════════════════════
   GROUP BOX
   ════════════════════════════════════════════════════════ */
QGroupBox {{
    border: 1px solid {group_bdr};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 4px;
    background: transparent;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: {group_title};
    font-weight: bold;
}}

/* ════════════════════════════════════════════════════════
   TREE / TABLE VIEWS
   ════════════════════════════════════════════════════════ */
QTreeWidget, QTreeView, QTableWidget, QTableView, QListWidget, QListView {{
    background: {input_bg};
    alternate-background-color: {tree_alt};
    color: {fg};
    border: 1px solid {group_bdr};
    gridline-color: {group_bdr};
    show-decoration-selected: 1;
    outline: none;
}}
QTreeWidget::item:selected, QTreeView::item:selected,
QTableWidget::item:selected, QTableView::item:selected,
QListWidget::item:selected, QListView::item:selected {{
    background: {sel_bg};
    color: {sel_fg};
}}
QHeaderView::section {{
    background: {hdr_bg};
    color: {fg};
    padding: 4px 8px;
    border: none;
    border-right: 1px solid {group_bdr};
    border-bottom: 1px solid {group_bdr};
    font-weight: bold;
}}
QHeaderView::section:pressed {{
    background: {btn_dn};
}}

/* ════════════════════════════════════════════════════════
   SCROLLBARS — slim metallic
   ════════════════════════════════════════════════════════ */
QScrollBar:vertical {{
    background: {scr_bg};
    width: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {scr_hdl};
    min-height: 24px;
    border-radius: 5px;
    margin: 1px;
}}
QScrollBar::handle:vertical:hover {{
    background: {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {scr_bg};
    height: 10px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {scr_hdl};
    min-width: 24px;
    border-radius: 5px;
    margin: 1px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {accent};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ════════════════════════════════════════════════════════
   MENU BAR / MENUS
   ════════════════════════════════════════════════════════ */
QMenuBar {{
    background: {bg_sidebar};
    color: {fg};
    border-bottom: 1px solid {group_bdr};
}}
QMenuBar::item {{
    padding: 4px 10px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background: {sb_hover};
    border-radius: 2px;
}}
QMenuBar::item:pressed {{
    background: {btn_dn};
}}
QMenu {{
    background: {menu_bg};
    color: {fg};
    border: 1px solid {group_bdr};
    padding: 2px 0;
}}
QMenu::item {{
    padding: 4px 24px 4px 24px;
}}
QMenu::item:selected {{
    background: {sel_bg};
    color: {sel_fg};
}}
QMenu::separator {{
    height: 1px;
    background: {group_bdr};
    margin: 3px 8px;
}}

/* ════════════════════════════════════════════════════════
   STATUS BAR
   ════════════════════════════════════════════════════════ */
QStatusBar {{
    background: {bg_sidebar};
    color: {fg};
    border-top: 1px solid {group_bdr};
}}
QStatusBar::item {{
    border: none;
}}

/* ════════════════════════════════════════════════════════
   TABS
   ════════════════════════════════════════════════════════ */
QTabWidget::pane {{
    border: 1px solid {group_bdr};
    background: transparent;
    top: -1px;
}}
QTabBar::tab {{
    background: {btn_up};
    color: {fg};
    border-style: solid;
    border-width: 1px;
    border-top-color:    {bup_t};
    border-left-color:   {bup_l};
    border-bottom-color: transparent;
    border-right-color:  {bup_r};
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    padding: 4px 14px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {btn_hover};
    border-bottom-color: transparent;
    font-weight: bold;
}}
QTabBar::tab:!selected {{
    margin-top: 2px;
}}
QTabBar::tab:hover:!selected {{
    background: {btn_hover};
}}
QTabBar::tab:pressed {{
    background: {btn_dn};
    border-top-color:    {bdn_t};
    border-left-color:   {bdn_l};
}}

/* ════════════════════════════════════════════════════════
   CHECKBOXES / RADIO BUTTONS
   ════════════════════════════════════════════════════════ */
QCheckBox, QRadioButton {{
    color: {fg};
    spacing: 6px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-style: solid;
    border-width: 1px;
    border-top-color:    {iup_t};
    border-left-color:   {iup_l};
    border-bottom-color: {iup_b};
    border-right-color:  {iup_r};
    border-radius: 2px;
    background: {input_bg};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent_dk};
}}
QCheckBox::indicator:hover {{
    border-top-color:  {accent_dk};
    border-left-color: {accent_dk};
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border-style: solid;
    border-width: 1px;
    border-top-color:    {iup_t};
    border-left-color:   {iup_l};
    border-bottom-color: {iup_b};
    border-right-color:  {iup_r};
    background: {input_bg};
}}
QRadioButton::indicator:checked {{
    background: {accent};
    border-color: {accent_dk};
}}

/* ════════════════════════════════════════════════════════
   DIALOG BACKGROUND
   ════════════════════════════════════════════════════════ */
QDialog {{
    background: {menu_bg};
}}

/* ════════════════════════════════════════════════════════
   SCROLL AREA — transparent so parent bg shows through
   ════════════════════════════════════════════════════════ */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
"""

    # ------------------------------------------------------------------ public API

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
        return "PySide6 Fusion — Metallic"

    def configure_toplevel(self, widget):
        pass  # QPalette propagates automatically to all child widgets

    @property
    def current_mode(self):
        return self.current_theme_mode
