"""Funções auxiliares para manipulação de janelas no aplicativo."""

import logging
from typing import Dict, List, Optional, Set

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from src.config import globals as g


class TransparencyEventFilter(QObject):
    """
    Filtro de eventos para gerenciar a opacidade da janela com base no mouse
    e no estado de foco da janela, usando um temporizador para evitar problemas
    com menus e pop-ups.
    """

    def __init__(self, parent: QWidget):
        """Inicializa o filtro e o temporizador."""
        super().__init__(parent)
        self.watched_window = parent
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(50)  # Atraso de 50ms para verificar o estado
        self.timer.timeout.connect(self.make_transparent)

    def eventFilter(  # pylint: disable=C0103
        self, watched: QObject, event: QEvent
    ) -> bool:
        """Monitora eventos de mouse e foco para ajustar a opacidade."""
        if watched is not self.watched_window:
            return super().eventFilter(watched, event)

        event_type = event.type()

        if event_type in [QEvent.Type.Enter, QEvent.Type.WindowActivate]:
            # Para o temporizador e torna a janela opaca quando o mouse entra
            # ou a janela é ativada.
            self.timer.stop()
            self.watched_window.setWindowOpacity(1.0)
        elif event_type in [QEvent.Type.Leave, QEvent.Type.WindowDeactivate]:
            # Inicia o temporizador para aplicar a transparência quando o mouse sai
            # ou a janela é desativada.
            self.timer.start()

        return super().eventFilter(watched, event)

    def make_transparent(self):
        """
        Verifica se a janela deve se tornar transparente.
        Esta função é chamada pelo temporizador.
        """
        # Condições para NÃO tornar transparente:
        # 1. O mouse voltou para a janela.
        # 2. A janela ainda é a janela ativa.
        # 3. Um menu, submenu ou combobox está ativo.
        if (
            self.watched_window.underMouse()
            or self.watched_window.isActiveWindow()
            or QApplication.activePopupWidget()
            or QWidget.mouseGrabber()
        ):
            return

        self.watched_window.setWindowOpacity(0.5)


class Janela:
    """
    Classe utilitária para manipulação e controle de janelas no aplicativo.
    """

    _on_top_state: bool = False
    _transparency_state: bool = False
    _event_filters: Dict[int, TransparencyEventFilter] = {}
    _configured_windows: Set[int] = set()
    _monitor_timer: Optional[QTimer] = None

    @staticmethod
    def _get_all_app_windows() -> List[QWidget]:
        """Retorna uma lista de todas as janelas de formulário visíveis do aplicativo."""
        app = QApplication.instance()
        if not app:
            return []

        app_windows: List[QWidget] = []
        for widget in app.topLevelWidgets():
            is_window = bool(widget.windowFlags() & Qt.WindowType.Window)
            if is_window and widget.isVisible():
                app_windows.append(widget)
        return app_windows

    @staticmethod
    def _monitorar_janelas():
        """Timer callback para encontrar e configurar novas janelas."""
        todas_janelas = Janela._get_all_app_windows()
        id_janelas_atuais = {id(w) for w in todas_janelas}

        novas_janelas = [
            w for w in todas_janelas if id(w) not in Janela._configured_windows
        ]

        if novas_janelas:
            on_top_state = Janela.get_on_top_state()
            transparency_state = Janela.get_transparency_state()

            for window in novas_janelas:
                current_flags = window.windowFlags()
                if on_top_state:
                    new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
                else:
                    new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint
                window.setWindowFlags(new_flags | Janela.janela_flags())

                Janela._gerenciar_filtro_transparencia(window, transparency_state)

                window.show()
                Janela._configured_windows.add(id(window))

        janelas_fechadas = Janela._configured_windows - id_janelas_atuais
        Janela._configured_windows.difference_update(janelas_fechadas)

    @staticmethod
    def _iniciar_monitoramento():
        """Inicia o QTimer para monitorar novas janelas."""
        if Janela._monitor_timer is None:
            Janela._monitor_timer = QTimer()
            Janela._monitor_timer.timeout.connect(Janela._monitorar_janelas)
            Janela._monitor_timer.start(500)  # Verifica a cada 500ms

    @staticmethod
    def _verificar_estado_monitoramento():
        """Inicia ou para o monitor de janelas com base nas configurações ativas."""
        if Janela._on_top_state or Janela._transparency_state:
            Janela._iniciar_monitoramento()
        elif Janela._monitor_timer is not None:
            Janela._monitor_timer.stop()
            Janela._monitor_timer = None
            Janela._configured_windows.clear()

    @staticmethod
    def get_on_top_state() -> bool:
        """Retorna o estado atual da configuração 'no topo'."""
        return Janela._on_top_state

    @staticmethod
    def set_on_top_state(state: bool) -> None:
        """Define o estado da configuração 'no topo'."""
        if Janela._on_top_state == state:
            return
        Janela._on_top_state = state
        Janela.aplicar_no_topo_todas_janelas()
        Janela._verificar_estado_monitoramento()
        logging.info("No topo %s", "ativado" if Janela._on_top_state else "desativado")

    @staticmethod
    def get_transparency_state() -> bool:
        """Retorna o estado atual da configuração 'transparência'."""
        return Janela._transparency_state

    @staticmethod
    def set_transparency_state(state: bool) -> None:
        """Define o estado da configuração 'transparência'."""
        if Janela._transparency_state == state:
            return
        Janela._transparency_state = state
        Janela.aplicar_transparencia_todas_janelas()
        Janela._verificar_estado_monitoramento()
        logging.info(
            "Transparência %s",
            "ativada" if Janela._transparency_state else "desativada",
        )

    @staticmethod
    def aplicar_no_topo_todas_janelas() -> None:
        """Aplica a configuração 'no topo' a todas as janelas abertas do aplicativo."""

        def set_topmost(window: Optional[QWidget], on_top: bool) -> None:
            if window and window.isVisible():
                current_flags = window.windowFlags()
                desired = (
                    current_flags | Qt.WindowType.WindowStaysOnTopHint
                    if on_top
                    else current_flags & ~Qt.WindowType.WindowStaysOnTopHint
                )
                desired |= Janela.janela_flags()
                if desired != current_flags:
                    window.setWindowFlags(desired)
                    window.show()

        on_top_state = Janela._on_top_state
        janelas = Janela._get_all_app_windows()
        for janela in janelas:
            set_topmost(janela, on_top_state)
            Janela._configured_windows.add(id(janela))

        if janelas:
            logging.info(
                "Estado 'no topo' %s aplicado a %d janela(s)",
                "ativado" if on_top_state else "desativado",
                len(janelas),
            )

    @staticmethod
    def aplicar_transparencia_todas_janelas() -> None:
        """Aplica a configuração 'transparência' a todas as janelas abertas do aplicativo."""
        state = Janela._transparency_state
        janelas = Janela._get_all_app_windows()
        for window in janelas:
            Janela._gerenciar_filtro_transparencia(window, state)
            Janela._configured_windows.add(id(window))

    @staticmethod
    def _gerenciar_filtro_transparencia(window: QWidget, activate: bool) -> None:
        filter_obj = Janela._event_filters.get(id(window))
        if activate:
            if not filter_obj:
                filter_obj = TransparencyEventFilter(window)
                window.installEventFilter(filter_obj)
                Janela._event_filters[id(window)] = filter_obj
            # Garante que a janela esteja opaca ao ativar o filtro
            window.setWindowOpacity(1.0)
        else:
            if filter_obj:
                window.removeEventFilter(filter_obj)
                del Janela._event_filters[id(window)]
            window.setWindowOpacity(1.0)

    @staticmethod
    def posicionar_janela(
        form: Optional[QWidget], posicao: Optional[str] = None
    ) -> None:
        """Posiciona uma janela em relação à janela principal."""
        if g.PRINC_FORM is None or form is None:
            return
        screen = QApplication.primaryScreen()
        if not screen:
            return
        largura_monitor = screen.size().width()
        posicao_x_principal = g.PRINC_FORM.x()
        largura_principal = g.PRINC_FORM.width()
        largura_form = form.width()
        posicao_final = posicao
        if posicao_final is None:
            posicao_final = (
                "esquerda" if posicao_x_principal > largura_monitor / 2 else "direita"
            )
        if posicao_final == "centro":
            x = posicao_x_principal + (largura_principal - largura_form) // 2
            y = g.PRINC_FORM.y() + (g.PRINC_FORM.height() - form.height()) // 2
        elif posicao_final == "direita":
            x = posicao_x_principal + largura_principal + 10
            y = g.PRINC_FORM.y()
            if x + largura_form > largura_monitor:
                x = posicao_x_principal - largura_form - 10
        elif posicao_final == "esquerda":
            x = posicao_x_principal - largura_form - 10
            y = g.PRINC_FORM.y()
            if x < 0:
                x = posicao_x_principal + largura_principal + 10
        else:
            return
        form.move(x, y)

    @staticmethod
    def estado_janelas(estado: bool) -> None:
        """Define o estado de habilitação das janelas."""
        forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
        for form in forms:
            if form is not None:
                form.setEnabled(estado)

    @staticmethod
    def remover_janelas_orfas() -> None:
        """Remove janelas órfãs (não visíveis) do aplicativo."""
        try:
            app = QApplication.instance()
            if not app:
                return
            main_window = g.PRINC_FORM if hasattr(g, "PRINC_FORM") else None
            active_forms = []
            form_vars = [
                "DEDUC_FORM",
                "MATER_FORM",
                "CANAL_FORM",
                "ESPES_FORM",
                "SOBRE_FORM",
                "AUTEN_FORM",
                "USUAR_FORM",
                "RIE_FORM",
                "IMPRESSAO_FORM",
            ]
            for form_var in form_vars:
                form = getattr(g, form_var, None)
                if form and hasattr(form, "isVisible") and form.isVisible():
                    active_forms.append(form)
            top_level_widgets = (
                app.topLevelWidgets() if hasattr(app, "topLevelWidgets") else []
            )
            for widget in top_level_widgets[:]:
                is_special = (
                    widget == main_window
                    or widget in active_forms
                    or hasattr(widget, "_is_system_widget")
                    or hasattr(widget, "_is_main_window")
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
        """Retorna as flags da janela principal."""
        return (
            Qt.WindowType.Window
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )
