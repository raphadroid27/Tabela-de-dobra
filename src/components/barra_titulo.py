from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from src.config import globals as g


class BarraTitulo(QWidget):
    def __init__(self, parent=None, tema='dark'):
        super().__init__(parent)
        self.parent = parent
        self.pressing = False
        self.start = QPoint(0, 0)
        self.setFixedHeight(32)
        self.setAutoFillBackground(True)
        self.set_tema(tema)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        self.titulo = QLabel("Cálculo de Dobra", self)
        self.titulo.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(self.titulo)
        layout.addStretch()

        self.btn_min = QPushButton("–", self)
        self.btn_min.setFixedSize(32, 28)
        self.btn_min.setStyleSheet("border: none; font-size: 16pt;")
        self.btn_min.clicked.connect(self.minimizar)
        layout.addWidget(self.btn_min)

        self.btn_close = QPushButton("×", self)
        self.btn_close.setFixedSize(32, 28)
        self.btn_close.setStyleSheet("border: none; font-size: 16pt;")
        self.btn_close.clicked.connect(self.fechar)
        layout.addWidget(self.btn_close)

        self.setLayout(layout)

    def set_tema(self, tema):
        # Suporte ao modo 'auto' e detecção do tema real
        tema_real = tema
        if tema == 'auto':
            try:
                import darkdetect
                tema_real = 'dark' if darkdetect.isDark() else 'light'
            except ImportError:
                tema_real = 'dark'  # fallback seguro
        if tema_real == 'dark':
            self.setStyleSheet("background-color: #232629; color: #fff;")
        else:
            self.setStyleSheet("background-color: #f0f0f0; color: #222;")

    def minimizar(self):
        if self.parent:
            self.parent.showMinimized()

    def fechar(self):
        if self.parent:
            self.parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start = event.globalPosition().toPoint(
            ) - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.pressing and event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.start)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.pressing = False
        event.accept()
