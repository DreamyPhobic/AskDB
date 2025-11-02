from __future__ import annotations


PRIMARY = "#4F8EF7"
PRIMARY_DARK = "#3C6CC3"
ACCENT = "#00BCD4"
BG = "#141517"
SURFACE = "#1c1e22"
SURFACE_ALT = "#262a30"
TEXT = "#E0E0E0"
TEXT_MUTED = "#B0B0B0"
ERROR = "#EF5350"
SUCCESS = "#66BB6A"
BORDER = "#2d3138"


def app_stylesheet() -> str:
    css = """
    QWidget {
        background: %(BG)s;
        color: %(TEXT)s;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
    }
    QMainWindow { background: %(BG)s; }
    QLabel { color: %(TEXT)s; background: transparent; }
    QLabel#SectionSubtitle { color: %(TEXT_MUTED)s; font-style: italic; }
    /* Workspace header */
    QWidget#WorkspaceHeader { background: %(SURFACE)s; border: 1px solid %(BORDER)s; border-radius: 8px; }
    QLabel#WorkspaceHeaderTitle { font-weight: 700; font-size: 15px; margin: 0px; padding: 0px; }
    QLabel#WorkspaceHeaderMeta { color: %(TEXT_MUTED)s; font-size: 12px; margin: 0px; padding: 0px; }

    /* About dialog */
    QFrame#AboutCard { background: %(SURFACE)s; border: 1px solid %(BORDER)s; border-radius: 12px; }
    QLabel#AboutTagline { color: %(TEXT_MUTED)s; }
    QPushButton#AboutLink { background: transparent; color: %(PRIMARY)s; border: 1px solid %(BORDER)s; padding: 6px 10px; border-radius: 8px; }
    QPushButton#AboutLink:hover { background: %(SURFACE_ALT)s; }
    /* Section titles */
    QLabel#SectionTitle {
        color: %(TEXT)s;
        font-weight: 700;
        font-size: 14px;
        padding-left: 8px;
        border-left: 3px solid %(PRIMARY)s;
        margin: 4px 0 6px 0;
    }
    QLineEdit, QPlainTextEdit, QTextEdit {
        background: %(SURFACE)s;
        border: 1px solid %(BORDER)s;
        border-radius: 8px;
        padding: 8px 10px;
        color: %(TEXT)s;
    }
    QComboBox {
        background: %(SURFACE)s;
        border: 1px solid %(BORDER)s;
        border-radius: 8px;
        padding: 8px 10px;
        color: %(TEXT)s;
    }

    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
        border-color: %(PRIMARY)s;
    }
    QPushButton {
        background: %(PRIMARY)s;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        color: white;
    }
    QPushButton:hover { background: %(PRIMARY_DARK)s; }
    QPushButton:disabled { background: %(SURFACE_ALT)s; color: %(TEXT_MUTED)s; }
    QListWidget {
        background: %(SURFACE)s;
        border: 1px solid %(BORDER)s;
        border-radius: 8px;
    }
    QListWidget::item { padding: 0px; margin: 4px; border: 1px solid %(BORDER)s; border-radius: 8px; background: %(SURFACE_ALT)s;}
    QListWidget::item:selected { background: %(PRIMARY)s; color: white; border: 1px solid %(PRIMARY)s; border-radius: 8px; }
    QListWidget#SideList::item { padding: 6px; margin: 4px; border: 1px solid %(BORDER)s; border-radius: 10px; }
    QListWidget#SideList::item:selected { background: %(PRIMARY)s; color: white; border: 1px solid %(PRIMARY)s; border-radius: 10px; }

    /* Chat list rows: no outer border, rely on bubble */
    QListWidget#ChatList::item { padding: 2px; margin: 2px; border: none; background: transparent; }
    QListWidget#ChatList::item:selected { background: transparent; border: none; }
    QTabWidget::pane { border-top: 1px solid %(SURFACE_ALT)s; }
    QTabBar::tab {
        background: %(SURFACE)s;
        padding: 8px 14px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }
    QTabBar::tab:selected { background: %(SURFACE_ALT)s; color: %(TEXT)s; }
    /* Splitter handles - clearer, with hover state */
    QSplitter::handle { background: %(BORDER)s; }
    QSplitter::handle:horizontal { width: 8px; }
    QSplitter::handle:vertical { height: 8px; }
    QSplitter::handle:hover { background: %(PRIMARY_DARK)s; }

    /* Spin boxes (port) */
    QAbstractSpinBox {
        background: %(SURFACE)s;
        border: 1px solid %(BORDER)s;
        border-radius: 8px;
        padding: 6px 8px;
        color: %(TEXT)s;
    }
    QAbstractSpinBox:focus { border-color: %(PRIMARY)s; }

    /* GroupBox titles */
    QGroupBox {
        border: 1px solid %(BORDER)s;
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 2px 6px;
        color: %(TEXT)s;
        font-weight: 600;
    }
    



    /* Chat bubbles */
    #ChatBubbleUser {
        background: %(SUCCESS)s; color: white; border-top-left-radius: 14px; border-top-right-radius: 14px; border-bottom-left-radius: 14px; border-bottom-right-radius: 4px; padding: 0px;
    }
    #ChatBubbleAI {
        background: %(SURFACE_ALT)s; color: %(TEXT)s; border-top-left-radius: 14px; border-top-right-radius: 14px; border-bottom-left-radius: 4px; border-bottom-right-radius: 14px; padding: 0px;
    }
    #ChatBubbleAISelected {
        background: %(PRIMARY)s; color: white; border-top-left-radius: 14px; border-top-right-radius: 14px; border-bottom-left-radius: 4px; border-bottom-right-radius: 14px; padding: 0px;
    }
    #ChatBubbleError {
        background: %(ERROR)s; color: white; border-radius: 12px; padding: 0px;
    }

    /* Code-like query items */
    #QueryItem {
        background: transparent;
        padding: 8px 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        color: %(TEXT)s;
    }
    #QueryItem[selected="true"] {
        background: %(PRIMARY)s;
        color: white;
    }
    #QueryMeta { color: %(TEXT_MUTED)s; font-size: 12px; }
    #ConnMeta { color: #ffffff; font-size: 12px; }
    #ConnItem { background: transparent; }

    /* Connection editor highlight */
    #ConnectionEditorFrame {
        background: %(SURFACE)s;
        border: 1px solid %(PRIMARY_DARK)s;
        border-radius: 12px;
        padding: 12px;
    }
    #SideListHeader { color: %(TEXT_MUTED)s; font-weight: 600; margin-top: 8px; margin-bottom: 4px; }
    #SideList {
        background: %(SURFACE)s;
        border: 1px solid %(SURFACE_ALT)s;
        border-radius: 8px;
    }

    /* SQL Output table styling */
    QTableWidget, QTableView {
        background: %(SURFACE)s;
        color: %(TEXT)s;
        gridline-color: #ffffff; /* make dividers white */
        selection-background-color: %(PRIMARY)s;
        selection-color: white;
        outline: 0;
        border: 1px solid %(SURFACE_ALT)s;
        border-radius: 8px;
    }
    QHeaderView::section {
        background: %(SURFACE_ALT)s;
        color: %(TEXT)s;
        border: 0px;
        padding: 6px 8px;
    }
    QTableCornerButton::section {
        background: %(SURFACE_ALT)s;
        border: 0px;
    }
    """
    return css % {
        "BG": BG,
        "TEXT": TEXT,
        "SURFACE": SURFACE,
        "SURFACE_ALT": SURFACE_ALT,
        "PRIMARY": PRIMARY,
        "PRIMARY_DARK": PRIMARY_DARK,
        "TEXT_MUTED": TEXT_MUTED,
        "ACCENT": ACCENT,
        "SUCCESS": SUCCESS,
        "ERROR": ERROR,
        "BORDER": BORDER,
    }


