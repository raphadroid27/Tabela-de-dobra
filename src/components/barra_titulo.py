"""
BarraTitulo: Barra de título customizada para o aplicativo, com ícone, título, minimizar e fechar.
Permite arrastar a janela e adapta o tema (dark/light/auto).
"""

import darkdetect
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from src.config import globals as g
from src.utils.utilitarios import ICON_PATH


class BarraTitulo(QWidget):
    """
    Barra de título personalizada para janelas do aplicativo.
    Inclui ícone, título, botões de minimizar/fechar e suporte a tema.
    """

    def __init__(self, parent=None, tema="dark"):
        """
        Inicializa a barra de título customizada.
        :param parent: Janela pai.
        :param tema: Tema visual ('dark', 'light' ou 'auto').
        """
        super().__init__(parent)
        self._parent = parent
        self.pressing = False
        self.start = QPoint(0, 0)
        self.setFixedHeight(32)
        self.setAutoFillBackground(True)

        self.current_theme = tema
        self.real_theme_applied = None
        self._is_updating_style = False

        self.set_tema(self.current_theme)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)

        icone_label = QLabel(self)
        icone_label.setFixedSize(24, 24)
        icone_label.setScaledContents(True)
        icone_label.setPixmap(QPixmap(ICON_PATH))
        layout.addWidget(icone_label)

        self.titulo = QLabel("Calculadora de Dobra", self)
        self.titulo.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self.titulo)
        layout.addStretch()

        btn_min = QPushButton("–", self)
        btn_min.setFixedSize(32, 28)
        btn_min.setStyleSheet("border: none; font-size: 16pt;")
        btn_min.clicked.connect(self.minimizar)
        layout.addWidget(btn_min)

        btn_close = QPushButton("×", self)
        btn_close.setFixedSize(32, 28)
        btn_close.setStyleSheet("border: none; font-size: 16pt;")
        btn_close.clicked.connect(self.fechar)
        layout.addWidget(btn_close)

        self.setLayout(layout)

        # Registrar esta barra de título para atualizações de tema
        self._registrar_barra_titulo()

    def _registrar_barra_titulo(self):
        """Registra esta barra de título na lista global para atualizações de tema."""
        if self not in g.BARRAS_TITULO_ATIVAS:
            g.BARRAS_TITULO_ATIVAS.append(self)

    def _desregistrar_barra_titulo(self):
        """Remove esta barra de título da lista global."""
        if self in g.BARRAS_TITULO_ATIVAS:
            g.BARRAS_TITULO_ATIVAS.remove(self)

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Desregistra a barra de título quando a janela é fechada."""
        self._desregistrar_barra_titulo()
        super().closeEvent(event)

    def deleteLater(self):  # pylint: disable=invalid-name
        """Desregistra a barra de título antes de deletar."""
        self._desregistrar_barra_titulo()
        super().deleteLater()

    def set_tema(self, tema):
        """
        Define o tema visual da barra de título (dark, light ou auto).
        """
        self.current_theme = tema

        tema_real = tema
        if tema == "auto":
            try:
                tema_real = "dark" if darkdetect.isDark() else "light"
            except (ImportError, TypeError):
                tema_real = "dark"

        if tema_real == self.real_theme_applied:
            return

        # SOLUÇÃO: Define a flag para True antes de mudar o estilo.
        self._is_updating_style = True
        try:
            if tema_real == "dark":
                self.setStyleSheet("background-color: transparent; color: #fff;")
            else:
                self.setStyleSheet("background-color: transparent; color: #222;")

            self.real_theme_applied = tema_real
        finally:
            # SOLUÇÃO: Define a flag de volta para False, mesmo se ocorrer um erro.
            self._is_updating_style = False

    def minimizar(self):
        """
        Minimiza a janela pai.
        """
        if self._parent:
            self._parent.showMinimized()

    def fechar(self):
        """
        Fecha a janela pai.
        """
        if self._parent:
            self._parent.close()

    def changeEvent(self, event):  # pylint: disable=invalid-name
        """
        Detecta a mudança de tema do sistema e atualiza a barra de título.
        """
        # SOLUÇÃO: Se a flag estiver ativa, ignora o evento para quebrar o loop.
        if self._is_updating_style:
            return

        super().changeEvent(event)
        if event.type() in [QEvent.Type.StyleChange, QEvent.Type.ThemeChange]:
            self.set_tema(self.current_theme)

    def mousePressEvent(self, event):  # pylint: disable=invalid-name
        """
        Inicia o arrasto da janela ao pressionar o botão esquerdo do mouse.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressing = True
            if self._parent:
                self.start = (
                    event.globalPosition().toPoint()
                    - self._parent.frameGeometry().topLeft()
                )
            event.accept()

    def mouseMoveEvent(self, event):  # pylint: disable=invalid-name
        """
        Move a janela enquanto o mouse é arrastado com o botão esquerdo pressionado.
        """
        if (
            self.pressing
            and event.buttons() == Qt.MouseButton.LeftButton
            and self._parent
        ):
            self._parent.move(event.globalPosition().toPoint() - self.start)
            event.accept()

    def mouseReleaseEvent(self, event):  # pylint: disable=invalid-name
        """
        Finaliza o arrasto da janela ao soltar o botão do mouse.
        """
        self.pressing = False
        event.accept()
