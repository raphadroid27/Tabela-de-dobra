"""Menu de barra customizada para o aplicativo."""

from PySide6.QtWidgets import QHBoxLayout, QMenuBar, QWidget


class MenuCustom(QWidget):
    """Barra de menu customizada para uso no topo da aplicação."""

    def __init__(self, parent=None):
        """Inicializa o widget de menu customizado."""
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.menu_bar = QMenuBar(self)
        layout.addWidget(self.menu_bar)
        self.setLayout(layout)

    def get_menu_bar(self):
        """Retorna a instância do QMenuBar interno."""
        return self.menu_bar
