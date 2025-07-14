from PySide6.QtWidgets import QWidget, QHBoxLayout, QMenuBar, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt


class MenuCustom(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.menu_bar = QMenuBar(self)
        layout.addWidget(self.menu_bar)
        self.setLayout(layout)

    def get_menu_bar(self):
        return self.menu_bar
