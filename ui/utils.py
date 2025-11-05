 
from PySide6 import QtWidgets, QtCore
import re


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

def markdown_to_html(text):
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert newlines to <br> so QLabel shows them
    text = text.replace('\n', '<br>')
    return text