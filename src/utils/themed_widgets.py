# pylint: disable=cyclic-import
"""Widgets com suporte automático a dark title bar.

Este módulo exporta classes base que aplicam automaticamente dark title bar
quando o tema da aplicação está em modo escuro.

Uso:
    # Em vez de QDialog, use ThemedDialog
    # Em vez de QMainWindow, use ThemedMainWindow
    from src.utils.themed_widgets import ThemedDialog, ThemedMainWindow

    dialog = ThemedDialog(parent)
    # O dark title bar será aplicado automaticamente ao exibir

Para migrar código existente:
    1. Substitua QDialog por ThemedDialog
    2. Substitua QMainWindow por ThemedMainWindow
    3. Substitua QMessageBox por ThemedMessageBox (já feito em utilitarios.py)
    4. Para diálogos inline, use create_themed_dialog()
"""

from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from src.utils.theme_manager import theme_manager


class _ThemedWidgetMixin:
    """Mixin que adiciona registro automático no theme manager."""

    def showEvent(self, event):  # pylint: disable=invalid-name
        """Registra a janela no theme manager quando for exibida."""
        super().showEvent(event)
        theme_manager.register_window(self)


class ThemedDialog(_ThemedWidgetMixin, QDialog):
    """QDialog que aplica automaticamente dark title bar quando exibido.

    Use esta classe em vez de QDialog para ter suporte automático a dark title bar.
    """


class ThemedMainWindow(_ThemedWidgetMixin, QMainWindow):
    """QMainWindow que aplica automaticamente dark title bar quando exibida.

    Use esta classe em vez de QMainWindow para ter suporte automático a dark title bar.
    """


class ThemedMessageBox(_ThemedWidgetMixin, QMessageBox):
    """QMessageBox que aplica automaticamente dark title bar quando exibido.

    Use esta classe em vez de QMessageBox para ter suporte automático a dark title bar.
    """


def create_themed_dialog(parent: QWidget | None = None) -> ThemedDialog:
    """Cria um QDialog com dark title bar automático.

    Args:
        parent: Widget pai opcional

    Returns:
        ThemedDialog pronto para uso

    Exemplo:
        dialog = create_themed_dialog(parent)
        dialog.setWindowTitle("Meu Diálogo")
        dialog.exec()
    """
    return ThemedDialog(parent)


def apply_dark_titlebar(widget: QWidget) -> None:
    """Aplica dark title bar manualmente a um widget existente.

    Use esta função para widgets que já foram criados e não podem
    ser substituídos por ThemedDialog.

    Args:
        widget: Widget (janela ou diálogo) para aplicar dark title bar

    Exemplo:
        dialog = QDialog(parent)
        # ... configurar dialog ...
        apply_dark_titlebar(dialog)
        dialog.show()
    """
    theme_manager.register_window(widget)
