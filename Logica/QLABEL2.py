from PyQt5.QtCore import (Qt, pyqtSignal)
from PyQt5.QtWidgets import (QHBoxLayout, QToolTip, QPushButton, QApplication, QWidget, QLabel)
from PyQt5.QtGui import (QIcon, QPixmap, QFont)

class QLabel_alterada(QLabel):
    clicked=pyqtSignal()
    def __init__(self, parent=None):
        QLabel.__init__(self, parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()
