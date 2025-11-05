from __future__ import annotations

from typing import Optional
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets

from .utils import markdown_to_html


class ChatBubbleWidget(QtWidgets.QFrame):
    def __init__(self, text: str, role: str = "ai", parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        self.label = QtWidgets.QLabel("")
        self.label.setWordWrap(True)
        self.label.setText(markdown_to_html(text))
        self.label.setTextFormat(QtCore.Qt.RichText)
        self.label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        
        # Allow horizontal growth to compute proper height for wrapping
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        
        layout.addWidget(self.label)
        # extra spacer at bottom to ensure descenders never clip
        if role == "you":
            self.setObjectName("ChatBubbleUser")
            # Ensure text is visible regardless of theme inheritance
            self.label.setStyleSheet("color: white;")
        elif role == "error":
            self.setObjectName("ChatBubbleError")
            self.label.setStyleSheet("color: white;")
        else:
            self.setObjectName("ChatBubbleAI")
            self.label.setStyleSheet("color: #E0E0E0;")

    def sizeHint(self) -> QtCore.QSize:  # compute based on label plus margins
        sh = self.label.sizeHint()
        m = self.layout().contentsMargins()
        return QtCore.QSize(sh.width() + m.left() + m.right(), sh.height() + m.top() + m.bottom() + 8)


class QueryListItemWidget(QtWidgets.QFrame):
    def __init__(self, index: int, sql: str, source_text: str, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("QueryItem")
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(6, 4, 6, 6)
        outer.setSpacing(4)

        # Small title on top: "Query #n"
        self.title = QtWidgets.QLabel(f"Query #{index}")
        self.title.setObjectName("QueryMeta")
        self.title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        outer.addWidget(self.title)

        self.code = QtWidgets.QLabel(sql)
        self.code.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.code.setWordWrap(True)
        self.code.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.code.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.code.setMargin(0)
        self.code.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.code)
        # Let clicks fall-through so QListWidget row gets selected on any inner click
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

    def sizeHint(self) -> QtCore.QSize:
        # Compute size: title + spacing + code
        code_sh = self.code.sizeHint()
        title_sh = self.title.sizeHint()
        m = self.layout().contentsMargins()
        total_h = title_sh.height() + self.layout().spacing() + code_sh.height() + m.top() + m.bottom()
        total_w = max(title_sh.width(), code_sh.width()) + m.left() + m.right()
        return QtCore.QSize(total_w, total_h)


def _icon_path_for_db(db_type: str) -> Path:
    base = Path(__file__).resolve().parents[1]  # project root
    dt = (db_type or "").lower()
    name = "generic.svg"
    if dt.startswith("post"):
        name = "postgres.svg"
    elif dt.startswith("mysql"):
        name = "mysql.svg"
    elif dt.startswith("sqlite"):
        name = "sqlite.svg"
    return base / "assets" / "icons" / name


class ConnectionListItemWidget(QtWidgets.QFrame):
    def __init__(self, title: str, subtitle: str, db_type: str = "", parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        # Transparent to let QListWidget selection show through
        self.setObjectName("ConnItem")
        self._outer = QtWidgets.QHBoxLayout(self)
        # Keep modest margins; too-large margins + default sizeHint can clip text in item views
        self._outer.setContentsMargins(6, 6, 6, 6)
        self._outer.setSpacing(6)

        # Icon
        self._icon = QtWidgets.QLabel()
        self._icon.setFixedSize(24, 24)
        self._icon.setScaledContents(True)
        p = _icon_path_for_db(db_type)
        if p.exists():
            pix = QtGui.QPixmap(str(p))
            self._icon.setPixmap(pix)
        self._outer.addWidget(self._icon, 0, QtCore.Qt.AlignTop)

        self._text_v = QtWidgets.QVBoxLayout()
        self._text_v.setContentsMargins(0, 0, 0, 0)
        self._text_v.setSpacing(2)
        self._title = QtWidgets.QLabel(title)
        self._title.setStyleSheet("font-weight: 600;")
        self._title.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self._subtitle = QtWidgets.QLabel(subtitle)
        self._subtitle.setObjectName("ConnMeta")
        self._subtitle.setWordWrap(True)
        self._subtitle.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self._text_v.addWidget(self._title)
        self._text_v.addWidget(self._subtitle)
        self._outer.addLayout(self._text_v)
        # Let clicks fall-through so QListWidget row gets selected on any inner click
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

    def sizeHint(self) -> QtCore.QSize:
        """Provide a robust sizeHint that accounts for icon, text, spacing and margins.

        QListWidget with setItemWidget relies on the widget's sizeHint; if margins are
        increased without compensating here, Qt may underestimate height leading to
        clipped top/bottom of the subtitle. This computes height explicitly.
        """
        # Text block height = title + spacing + subtitle
        t_sh = self._title.sizeHint()
        s_sh = self._subtitle.sizeHint()
        text_block_h = t_sh.height() + self._text_v.spacing() + s_sh.height()
        # Icon height
        icon_h = self._icon.sizeHint().height()
        # Outer margins
        m = self._outer.contentsMargins()
        total_h = max(text_block_h, icon_h) + m.top() + m.bottom()
        # Width: icon + spacing + max(title, subtitle) width + margins
        text_w = max(t_sh.width(), s_sh.width())
        total_w = self._icon.sizeHint().width() + self._outer.spacing() + text_w + m.left() + m.right()
        return QtCore.QSize(total_w, total_h + 8)


class ChatMessageRowWidget(QtWidgets.QWidget):
    def __init__(self, text: str, role: str = "ai", parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(8)

        icon_label = QtWidgets.QLabel()
        icon_label.setFixedSize(20, 20)
        icon_label.setScaledContents(True)
        # Simple circle avatar via stylesheet
        if role == "you":
            icon_label.setStyleSheet("background:#2E7D32;border-radius:10px;")
        elif role == "error":
            icon_label.setStyleSheet("background:#EF5350;border-radius:10px;")
        else:
            icon_label.setStyleSheet("background:#FFFFFF;border-radius:10px;")

        self.role = role
        self.bubble = ChatBubbleWidget(text, role=role)
        self.bubble.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.bubble.setMaximumWidth(500)

        if role == "you":
            row.addStretch(1)
            row.addWidget(self.bubble, 0)
            row.addWidget(icon_label, 0, QtCore.Qt.AlignBottom)
        else:
            row.addWidget(icon_label, 0, QtCore.Qt.AlignBottom)
            row.addWidget(self.bubble, 0)
            row.addStretch(1)
        
        # Let clicks fall-through so QListWidget row gets selected on any inner click
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

    def sizeHint(self) -> QtCore.QSize:  # ensure enough height
        m = self.layout().contentsMargins()
        # Ensure height accommodates the bubble and the 20px avatar
        h = max(self.bubble.sizeHint().height(), 20) + m.top() + m.bottom()
        return QtCore.QSize(self.bubble.sizeHint().width() + m.left() + m.right(), h)

    def set_selected(self, selected: bool) -> None:
        if self.role != "you":
            # Toggle AI bubble selection style
            self.bubble.setObjectName("ChatBubbleAISelected" if selected else "ChatBubbleAI")
            # Force style refresh
            self.bubble.style().unpolish(self.bubble)
            self.bubble.style().polish(self.bubble)


