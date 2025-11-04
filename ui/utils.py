 
from PySide6 import QtWidgets, QtCore

def mk_label(text: str, buddy: QtWidgets.QWidget) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    try:
        lbl.setBuddy(buddy)
    except Exception:
        pass
    lbl.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
       # Ensure label height visually centers relative to the editor widget
    try:
        h = max(0, buddy.sizeHint().height())
        if h:
            lbl.setMinimumHeight(h)
    except Exception:
        pass
    lbl.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
    return lbl