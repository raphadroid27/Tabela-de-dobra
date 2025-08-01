"""
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.config import globals as g


class Janela:
    """
    Classe utilitária para manipulação e controle de janelas no aplicativo,
    incluindo posicionamento, estado 'sempre no topo', e gerenciamento de janelas órfãs.
    """
    @staticmethod
    def aplicar_no_topo_app_principal():
        """
        Alterna se a janela deve ficar sempre no topo ou não.
        """
        # Alternar o estado de NO_TOPO_VAR
        if g.NO_TOPO_VAR is None:
            g.NO_TOPO_VAR = False

        g.NO_TOPO_VAR = not g.NO_TOPO_VAR

        Janela.aplicar_no_topo_todas_janelas()

        print(f"No topo {'ativado' if g.NO_TOPO_VAR else 'desativado'}")

    @staticmethod
    def aplicar_no_topo_todas_janelas():
        """
        Aplica a configuração 'no topo' a todas as janelas abertas do aplicativo.
        """
        def set_topmost(window, on_top):
            if window and window.isVisible():  # Só aplicar a janelas visíveis
                current_flags = window.windowFlags()
                if on_top:
                    new_flags = current_flags | Qt.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowStaysOnTopHint

                essential_flags = Janela.janela_flags()

                new_flags = new_flags | essential_flags
                window.setWindowFlags(new_flags)
                window.show()

        if g.NO_TOPO_VAR is None:
            return

        # Lista de janelas que podem estar abertas
        janelas = [
            g.PRINC_FORM,
            getattr(g, 'DEDUC_FORM', None),
            getattr(g, 'ESPES_FORM', None),
            getattr(g, 'MATER_FORM', None),
            getattr(g, 'CANAL_FORM', None),
            getattr(g, 'SOBRE_FORM', None),
            getattr(g, 'USUAR_FORM', None),
            getattr(g, 'RIE_FORM', None),
            getattr(g, 'IMPRESSAO_FORM', None)
        ]

        count = 0
        for janela in janelas:
            if janela is not None:
                set_topmost(janela, g.NO_TOPO_VAR)
                count += 1

        if count > 0:
            print(
                f"Estado 'no topo' {'ativado' if g.NO_TOPO_VAR else 'desativado'}\n"
                f"aplicado a {count} janela(s)"
            )

    @staticmethod
    def aplicar_no_topo(form):
        """
        Aplica o estado atual de 'no topo' a uma janela específica sem alternar.
        Usado quando uma nova janela é criada e deve herdar o estado atual.
        """
        def set_topmost(window, on_top):
            if window:
                current_flags = window.windowFlags()
                if on_top:
                    new_flags = current_flags | Qt.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowStaysOnTopHint

                essential_flags = Janela.janela_flags()

                new_flags = new_flags | essential_flags
                window.setWindowFlags(new_flags)
                window.show()

        if g.NO_TOPO_VAR is None:
            g.NO_TOPO_VAR = False

        if form:
            set_topmost(form, g.NO_TOPO_VAR)
            print(
                f"Estado 'no topo' {'ativado' if g.NO_TOPO_VAR else 'desativado'} "
                "aplicado à nova janela"
            )

    @staticmethod
    def posicionar_janela(form, posicao=None):
        """
        Posiciona a janela em relação à janela principal.
        """
        # Verificar se a janela principal existe
        if g.PRINC_FORM is None:
            return

        screen = QApplication.primaryScreen()
        largura_monitor = screen.size().width()
        posicao_x = g.PRINC_FORM.x()
        largura_janela = g.PRINC_FORM.width()
        largura_form = form.width()

        if posicao is None:
            if posicao_x > largura_monitor / 2:
                posicao = 'esquerda'
            else:
                posicao = 'direita'

        if posicao == 'centro':
            x = g.PRINC_FORM.x() + ((g.PRINC_FORM.width() - largura_form) // 2)
            y = g.PRINC_FORM.y() + ((g.PRINC_FORM.height() - form.height()) // 2)
        elif posicao == 'direita':
            x = g.PRINC_FORM.x() + largura_janela + 10
            y = g.PRINC_FORM.y()
            if x + largura_form > largura_monitor:
                x = g.PRINC_FORM.x() - largura_form - 10
        elif posicao == 'esquerda':
            x = g.PRINC_FORM.x() - largura_form - 10
            y = g.PRINC_FORM.y()
            if x < 0:
                x = g.PRINC_FORM.x() + largura_janela + 10
        else:
            return

        form.move(x, y)

    @staticmethod
    def estado_janelas(estado: bool):
        """
        Desabilita ou habilita todas as janelas do aplicativo.
        """
        forms = [g.PRINC_FORM, g.DEDUC_FORM,
                 g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
        for form in forms:
            if form is not None:
                form.setEnabled(estado)

    @staticmethod
    def remover_janelas_orfas():
        """
        Remove todas as janelas órfãs que possam estar abertas,
        mas preserva formulários ativos.
        """
        try:
            app = QApplication.instance()
            if not app:
                return

            main_window = g.PRINC_FORM if hasattr(g, 'PRINC_FORM') else None

            # Lista de formulários ativos que devem ser preservados
            active_forms = []
            form_vars = ['DEDUC_FORM', 'MATER_FORM', 'CANAL_FORM', 'ESPES_FORM',
                         'SOBRE_FORM', 'AUTEN_FORM', 'USUAR_FORM', 'RIE_FORM', 'IMPRESSAO_FORM']

            for form_var in form_vars:
                if hasattr(g, form_var):
                    form = getattr(g, form_var)
                    if form is not None and hasattr(form, 'isVisible') and form.isVisible():
                        active_forms.append(form)

            top_level_widgets = app.topLevelWidgets()

            for widget in top_level_widgets[:]:  # Cópia para iteração segura
                if (widget != main_window and
                    widget not in active_forms and
                    widget.isVisible() and
                    not hasattr(widget, '_is_system_widget') and
                        not hasattr(widget, '_is_main_window')):

                    widget_type = type(widget).__name__
                    if widget_type in ['QLabel',
                                       'QFrame',
                                       'QWidget',
                                       'QDialog',
                                       'QWindow',
                                       'QMainWindow']:
                        try:
                            widget.hide()
                            widget.close()
                            widget.deleteLater()
                        except (RuntimeError, AttributeError):
                            pass

            # Processar eventos para garantir limpeza
            app.processEvents()

        except (RuntimeError, AttributeError):
            pass

    @staticmethod
    def janela_flags():
        """
        Define as flags essenciais para janelas do aplicativo.
        Essas flags garantem que a janela tenha todos os botões necessários
        na barra de título e se comporte corretamente no sistema operacional.
        """
        essential_flags = (Qt.Window |
                           Qt.WindowTitleHint |
                           Qt.WindowSystemMenuHint |
                           Qt.WindowMinimizeButtonHint |
                           Qt.WindowMaximizeButtonHint |
                           Qt.WindowCloseButtonHint)
        return essential_flags


aplicar_no_topo_app_principal = Janela.aplicar_no_topo_app_principal
aplicar_no_topo = Janela.aplicar_no_topo
aplicar_no_topo_todas_janelas = Janela.aplicar_no_topo_todas_janelas
remover_janelas_orfas = Janela.remover_janelas_orfas
posicionar_janela = Janela.posicionar_janela
HABILITAR_JANELAS = Janela.estado_janelas(True)
DESABILITAR_JANELAS = Janela.estado_janelas(False)
