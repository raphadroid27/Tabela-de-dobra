"""
BarraTitulo: Barra de título customizada para o aplicativo, com ícone, título, minimizar e fechar.
Permite arrastar a janela e adapta o tema (dark/light/auto).
"""

import darkdetect
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPoint
from src.utils.utilitarios import obter_caminho_icone


class BarraTitulo(QWidget):
    """
    Barra de título personalizada para janelas do aplicativo.
    Inclui ícone, título, botões de minimizar/fechar e suporte a tema.
    """

    def __init__(self, parent=None, tema='dark'):
        """
        Inicializa a barra de título customizada.
        :param parent: Janela pai.
        :param tema: Tema visual ('dark', 'light' ou 'auto').
        """
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

        # Ícone do app (clicável)
        icone_path = obter_caminho_icone()
        self.icone_label = QLabel(self)
        self.icone_label.setFixedSize(24, 24)
        self.icone_label.setScaledContents(True)
        self.icone_label.setPixmap(QPixmap(icone_path))
        layout.addWidget(self.icone_label)

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
        """
        Define o tema visual da barra de título (dark, light ou auto).
        """
        # Suporte ao modo 'auto' e detecção do tema real
        tema_real = tema
        if tema == 'auto':
            try:
                tema_real = 'dark' if darkdetect.isDark() else 'light'
            except ImportError:
                tema_real = 'dark'  # fallback seguro
        if tema_real == 'dark':
            self.setStyleSheet("background-color: #232629; color: #fff;")
        else:
            self.setStyleSheet("background-color: #f0f0f0; color: #222;")

    def minimizar(self):
        """
        Minimiza a janela pai.
        """
        if self.parent:
            self.parent.showMinimized()

    def fechar(self):
        """
        Fecha a janela pai.
        """
        if self.parent:
            self.parent.close()

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """
        Inicia o arrasto da janela ao pressionar o botão esquerdo do mouse.
        """
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.start = event.globalPosition().toPoint(
            ) - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """
        Move a janela enquanto o mouse é arrastado com o botão esquerdo pressionado.
        """
        if self.pressing and event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.start)
            event.accept()

    def mouseReleaseEvent(self, event):  # pylint: disable=invalid-name
        """
        Finaliza o arrasto da janela ao soltar o botão do mouse.
        """
        self.pressing = False
        event.accept()
