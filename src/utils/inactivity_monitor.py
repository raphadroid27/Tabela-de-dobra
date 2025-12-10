"""Monitor de inatividade para fechar janelas automaticamente após período sem interação."""

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QWidget

_INACTIVITY_EVENTS = {
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseButtonRelease,
    QEvent.Type.MouseMove,
    QEvent.Type.KeyPress,
    QEvent.Type.KeyRelease,
    QEvent.Type.Wheel,
    QEvent.Type.FocusIn,
}


class _InactivityEventFilter(QObject):
    """Reinicia o timer de inatividade quando eventos relevantes ocorrem."""

    def __init__(self, on_activity):
        super().__init__()
        self._on_activity = on_activity

    def eventFilter(  # pylint: disable=invalid-name
        self, obj, event
    ):  # pylint: disable=unused-argument
        """Intercepta eventos de interação e reinicia o timer."""
        if event.type() in _INACTIVITY_EVENTS:
            self._on_activity()
        return super().eventFilter(obj, event)


def _instalar_filtro_recursivo(widget, filtro):
    """Instala o filtro de eventos no widget e em todos os seus filhos."""
    widget.installEventFilter(filtro)
    for child in widget.findChildren(QWidget):
        child.installEventFilter(filtro)


def ativar_monitor_inatividade(window, timeout_ms, on_timeout_callback):
    """Ativa monitor de inatividade em uma janela.

    Args:
        window: Janela QWidget/QDialog a ser monitorada
        timeout_ms: Tempo de inatividade em milissegundos antes de chamar callback
        on_timeout_callback: Função a ser chamada quando timeout ocorrer
    """
    if not window:
        return

    timer = QTimer(window)
    timer.setInterval(timeout_ms)
    timer.setSingleShot(True)
    timer.timeout.connect(on_timeout_callback)

    filtro = _InactivityEventFilter(timer.start)
    _instalar_filtro_recursivo(window, filtro)

    # Armazena no widget para evitar garbage collection
    window.inactivity_timer = timer  # type: ignore[attr-defined]
    window.inactivity_filter = filtro  # type: ignore[attr-defined]

    timer.start()
