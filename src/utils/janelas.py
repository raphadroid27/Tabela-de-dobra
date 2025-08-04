"""
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from src.config import globals as g


class Janela:
    """
    Classe utilitária para manipulação e controle de janelas no aplicativo,
    incluindo posicionamento, estado 'sempre no topo', e gerenciamento de janelas órfãs.
    """
    _on_top_state: bool = False

    @staticmethod
    def get_on_top_state() -> bool:
        """Retorna o estado atual de 'sempre no topo'."""
        return Janela._on_top_state

    @staticmethod
    def set_on_top_state(state: bool) -> None:
        """
        Define o estado 'sempre no topo' e o aplica a todas as janelas.
        """
        if Janela._on_top_state == state:
            return  # Não faz nada se o estado já for o desejado

        Janela._on_top_state = state
        Janela.aplicar_no_topo_todas_janelas()
        logging.info("No topo %s", 'ativado' if Janela._on_top_state else 'desativado')

    @staticmethod
    def aplicar_no_topo_todas_janelas() -> None:
        """
        Aplica a configuração 'no topo' a todas as janelas abertas do aplicativo.
        """
        def set_topmost(window: Optional[QWidget], on_top: bool) -> None:
            if window and window.isVisible():  # Só aplicar a janelas visíveis
                current_flags = window.windowFlags()
                if on_top:
                    new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint

                essential_flags = Janela.janela_flags()

                new_flags = new_flags | essential_flags
                window.setWindowFlags(new_flags)
                window.show()

        # CORREÇÃO: Lê o estado diretamente do atributo da classe.
        on_top_state = Janela._on_top_state

        # Lista de janelas que podem estar abertas
        janelas = [
            g.PRINC_FORM,
            getattr(g, "DEDUC_FORM", None),
            getattr(g, "ESPES_FORM", None),
            getattr(g, "MATER_FORM", None),
            getattr(g, "CANAL_FORM", None),
            getattr(g, "SOBRE_FORM", None),
            getattr(g, "USUAR_FORM", None),
            getattr(g, "RIE_FORM", None),
            getattr(g, "IMPRESSAO_FORM", None),
        ]

        count = 0
        for janela in janelas:
            if janela is not None:
                set_topmost(janela, on_top_state)
                count += 1

        if count > 0:
            logging.info(
                "Estado 'no topo' %s aplicado a %d janela(s)",
                'ativado' if on_top_state else 'desativado',
                count
            )

    @staticmethod
    def aplicar_no_topo(form: Optional[QWidget]) -> None:
        """
        Aplica o estado atual de 'no topo' a uma janela específica sem alternar.
        Usado quando uma nova janela é criada e deve herdar o estado atual.
        """
        def set_topmost(window: Optional[QWidget], on_top: bool) -> None:
            if window:
                current_flags = window.windowFlags()
                if on_top:
                    new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint

                essential_flags = Janela.janela_flags()

                new_flags = new_flags | essential_flags
                window.setWindowFlags(new_flags)
                window.show()

        # CORREÇÃO: Lê o estado diretamente do atributo da classe.
        current_state = Janela._on_top_state

        if form:
            set_topmost(form, current_state)
            logging.info(
                "Estado 'no topo' %s aplicado à nova janela",
                'ativado' if current_state else 'desativado'
            )

    @staticmethod
    def posicionar_janela(form: Optional[QWidget], posicao: Optional[str] = None) -> None:
        """
        Posiciona a janela em relação à janela principal.
        """
        if g.PRINC_FORM is None or form is None:
            return

        screen = QApplication.primaryScreen()
        if not screen:
            return

        largura_monitor = screen.size().width()
        posicao_x = g.PRINC_FORM.x()
        largura_janela = g.PRINC_FORM.width()
        largura_form = form.width()

        if posicao is None:
            posicao = "esquerda" if posicao_x > largura_monitor / 2 else "direita"

        if posicao == "centro":
            x = g.PRINC_FORM.x() + ((g.PRINC_FORM.width() - largura_form) // 2)
            y = g.PRINC_FORM.y() + ((g.PRINC_FORM.height() - form.height()) // 2)
        elif posicao == "direita":
            x = g.PRINC_FORM.x() + largura_janela + 10
            y = g.PRINC_FORM.y()
            if x + largura_form > largura_monitor:
                x = g.PRINC_FORM.x() - largura_form - 10
        elif posicao == "esquerda":
            x = g.PRINC_FORM.x() - largura_form - 10
            y = g.PRINC_FORM.y()
            if x < 0:
                x = g.PRINC_FORM.x() + largura_janela + 10
        else:
            return

        form.move(x, y)

    @staticmethod
    def estado_janelas(estado: bool) -> None:
        """
        Desabilita ou habilita todas as janelas do aplicativo.
        """
        forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
        for form in forms:
            if form is not None:
                form.setEnabled(estado)

    @staticmethod
    def remover_janelas_orfas() -> None:
        """
        Remove todas as janelas órfãs que possam estar abertas,
        mas preserva formulários ativos.
        """
        try:
            app = QApplication.instance()
            if not app:
                return

            main_window = g.PRINC_FORM if hasattr(g, "PRINC_FORM") else None
            active_forms = []
            form_vars = [
                "DEDUC_FORM", "MATER_FORM", "CANAL_FORM", "ESPES_FORM",
                "SOBRE_FORM", "AUTEN_FORM", "USUAR_FORM", "RIE_FORM", "IMPRESSAO_FORM",
            ]

            for form_var in form_vars:
                form = getattr(g, form_var, None)
                if form and hasattr(form, "isVisible") and form.isVisible():
                    active_forms.append(form)

            top_level_widgets = app.topLevelWidgets() if hasattr(app, 'topLevelWidgets') else []

            for widget in top_level_widgets[:]:
                is_special = (
                    widget == main_window or
                    widget in active_forms or
                    hasattr(widget, "_is_system_widget") or
                    hasattr(widget, "_is_main_window")
                )
                if widget.isVisible() and not is_special:
                    try:
                        widget.hide()
                        widget.close()
                        widget.deleteLater()
                    except (RuntimeError, AttributeError):
                        pass

            app.processEvents()
        except (RuntimeError, AttributeError):
            pass

    @staticmethod
    def janela_flags() -> Qt.WindowType:
        """
        Define as flags essenciais para janelas do aplicativo.
        """
        return (
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )


# CORREÇÃO: A função `aplicar_no_topo_app_principal` não é mais necessária.
# Os aliases agora apontam para os métodos corretos.
aplicar_no_topo = Janela.aplicar_no_topo
aplicar_no_topo_todas_janelas = Janela.aplicar_no_topo_todas_janelas
remover_janelas_orfas = Janela.remover_janelas_orfas
posicionar_janela = Janela.posicionar_janela


def habilitar_janelas() -> None:
    """Habilita todas as janelas do aplicativo."""
    Janela.estado_janelas(True)


def desabilitar_janelas() -> None:
    """Desabilita todas as janelas do aplicativo."""
    Janela.estado_janelas(False)
