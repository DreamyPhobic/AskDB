from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About AskDB")
        self.resize(560, 420)

        root_v = QtWidgets.QVBoxLayout(self)
        root_v.setContentsMargins(16, 16, 16, 16)
        root_v.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        root_v.setSpacing(12)

        # Top: centered app icon, title, subtitle
        app_icon_lbl = QtWidgets.QLabel()
        app_icon_lbl.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        icon_pm = self._load_app_icon_pixmap(72)
        if icon_pm is not None and not icon_pm.isNull():
            app_icon_lbl.setPixmap(icon_pm)
            try:
                self.setWindowIcon(QtGui.QIcon(icon_pm))
            except Exception:
                pass
        root_v.addWidget(app_icon_lbl, 0, QtCore.Qt.AlignHCenter)

        app_title = QtWidgets.QLabel("AskDB")
        app_title.setStyleSheet("font-size:18px;font-weight:700;margin:0;padding:0;")
        app_title.setAlignment(QtCore.Qt.AlignHCenter)
        root_v.addWidget(app_title)

        tagline = QtWidgets.QLabel("Ask your database anything")
        tagline.setObjectName("AboutTagline")
        tagline.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        root_v.addWidget(tagline)

        root_v.addSpacing(8)

        # Middle card: avatar on left, bio on right
        card = QtWidgets.QFrame()
        card.setObjectName("AboutCard")
        card_h = QtWidgets.QHBoxLayout(card)
        card_h.setContentsMargins(14, 14, 14, 14)
        card_h.setSpacing(14)

        avatar_label = QtWidgets.QLabel()
        avatar_label.setFixedSize(100, 100)
        pix = self._load_profile_pixmap()
        has_avatar = pix is not None and not pix.isNull()
        if has_avatar:
            avatar_label.setPixmap(self._rounded_pixmap(pix, 100))
            card_h.addWidget(avatar_label, 0, QtCore.Qt.AlignTop)

        bio = QtWidgets.QLabel(
            (
                "I’m Harsh Gupta, a software engineer who loves learning and building. "
                "AskDB is my first AI project. I built it because writing SQL can be hard "
                "or time‑consuming for both non‑tech and tech folks. This app lets you "
                "talk to your database in plain English and have AI generate and run the SQL for you."
            )
        )
        bio.setWordWrap(True)
        card_h.addWidget(bio, 1)

        root_v.addWidget(card)

        # Bottom-right links
        links_row = QtWidgets.QHBoxLayout()
        links_row.addStretch(1)
        btn_ln = QtWidgets.QPushButton("LinkedIn")
        btn_ln.setObjectName("AboutLink")
        btn_ln.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://www.linkedin.com/in/harshgupta-se/")))
        btn_gh = QtWidgets.QPushButton("GitHub")
        btn_gh.setObjectName("AboutLink")
        btn_gh.clicked.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/DreamyPhobic")))
        links_row.addWidget(btn_ln)
        links_row.addWidget(btn_gh)
        root_v.addLayout(links_row)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btns.accepted.connect(self.accept)
        root_v.addWidget(btns)

    def _rounded_pixmap(self, src: QtGui.QPixmap, size: int) -> QtGui.QPixmap:
        s = QtCore.QSize(size, size)
        img = QtGui.QImage(s, QtGui.QImage.Format_ARGB32_Premultiplied)
        img.fill(0)
        p = QtGui.QPainter(img)
        p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        path = QtGui.QPainterPath()
        path.addEllipse(0, 0, size, size)
        p.setClipPath(path)
        p.drawPixmap(0, 0, src.scaled(size, size, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation))
        p.end()
        pm = QtGui.QPixmap.fromImage(img)
        return pm

    def _load_profile_pixmap(self) -> Optional[QtGui.QPixmap]:
        # Load explicit path per request: root/assets/profile.jpeg
        root = Path(__file__).resolve().parents[1]
        p = root / "assets" / "profile.jpeg"
        if p.exists():
            return QtGui.QPixmap(str(p))
        return None

    def _load_app_icon_pixmap(self, size: int) -> Optional[QtGui.QPixmap]:
        root = Path(__file__).resolve().parents[1]
        # Prefer explicit logo.png at assets/logo.png
        png_path = root / "assets" / "logo.png"
        if png_path.exists():
            pm = QtGui.QPixmap(str(png_path))
            if not pm.isNull():
                return pm.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        # Fallback: generic icon (optional)
        svg_path = root / "assets" / "icons" / "generic.svg"
        if svg_path.exists():
            icon = QtGui.QIcon(str(svg_path))
            return icon.pixmap(size, size)
        return None


