"""
Sistema de debounce para otimizar eventos da interface em ambientes de rede.
"""

import logging
import time
from functools import wraps
from typing import Any, Callable

from PySide6.QtCore import QObject, QTimer, Signal

from src.config import globals as g
from src.utils.interface import calcular_valores, listar
from src.utils.widget import WidgetManager

# Armazenamento global para timers de debounce
DEBOUNCE_TIMERS = {}


def debounce(delay_ms: int = 800):  # Aumentado para 800ms para ambiente de rede
    """
    Decorator que implementa debounce para funções otimizado para múltiplos usuários.

    Args:
        delay_ms: Delay em milissegundos antes de executar a função
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_id = f"{func.__name__}_{id(func)}"

            # Cancelar timer anterior se existir
            if func_id in DEBOUNCE_TIMERS:
                DEBOUNCE_TIMERS[func_id].stop()
                DEBOUNCE_TIMERS[func_id].deleteLater()

            # Criar novo timer
            timer = QTimer()
            timer.setSingleShot(True)
            # Capturar args e kwargs no momento da criação
            captured_args = args
            captured_kwargs = kwargs
            timer.timeout.connect(lambda: func(*captured_args, **captured_kwargs))
            timer.start(delay_ms)

            DEBOUNCE_TIMERS[func_id] = timer

        return wrapper

    return decorator


def throttle(interval_ms: int = 1000):
    """
    Decorator que implementa throttle para funções.

    Args:
        interval_ms: Intervalo mínimo entre execuções em milissegundos
    """

    def decorator(func: Callable):
        last_called = {"time": 0}

        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time() * 1000  # Converter para ms
            if now - last_called["time"] >= interval_ms:
                last_called["time"] = now
                return func(*args, **kwargs)
            return None  # Retorna None quando em throttle

        return wrapper

    return decorator


class OptimizedEventHandler(QObject):
    """Handler otimizado para eventos da interface."""

    # Sinais para operações em lote
    batch_update_signal = Signal(str, dict)

    def __init__(self):
        super().__init__()
        self.pending_updates = {}
        self.batch_timer = QTimer()
        self.batch_timer.setSingleShot(True)
        self.batch_timer.timeout.connect(self._process_batch_updates)

    @debounce(1000)  # Aumentado para 1s para cálculos em rede
    def handle_calculation_trigger(
        self, *args, **kwargs
    ):  # pylint: disable=unused-argument
        """Handler otimizado para triggers de cálculo em ambiente multi-usuário."""
        calcular_valores()

    @throttle(2000)  # Aumentado para 2s para atualizações de lista
    def handle_list_update(self, list_type: str):
        """Handler otimizado para atualizações de lista em ambiente multi-usuário."""
        listar(list_type)

    def batch_widget_update(self, widget_id: str, value: Any):
        """Adiciona atualização de widget ao lote."""
        self.pending_updates[widget_id] = value

        # Reiniciar timer para aguardar mais atualizações
        self.batch_timer.stop()
        self.batch_timer.start(100)  # 100ms para agrupar atualizações

    def _process_batch_updates(self):
        """Processa lote de atualizações de widgets."""
        if not self.pending_updates:
            return

        try:

            for widget_id, value in self.pending_updates.items():
                widget = getattr(g, widget_id, None)
                if widget:
                    WidgetManager.set_widget_value(widget, str(value))

            self.pending_updates.clear()

        except (AttributeError, TypeError, ValueError) as e:

            logging.error("Erro ao processar lote de atualizações: %s", e)
            self.pending_updates.clear()


# Instância global do handler otimizado
optimized_handler = OptimizedEventHandler()


class LazyLoader:
    """Carregador lazy para dados pesados."""

    def __init__(self):
        self._loaded_data = {}
        self._loading_flags = {}

    def load_data_lazy(self, data_key: str, loader_func: Callable):
        """
        Carrega dados de forma lazy.

        Args:
            data_key: Chave única para os dados
            loader_func: Função que carrega os dados
        """
        if data_key in self._loaded_data:
            return self._loaded_data[data_key]

        if data_key in self._loading_flags:
            return None  # Já está carregando

        self._loading_flags[data_key] = True

        try:
            data = loader_func()
            self._loaded_data[data_key] = data
            return data
        finally:
            self._loading_flags.pop(data_key, None)

    def invalidate_data(self, data_key: str):
        """Invalida dados em cache."""
        self._loaded_data.pop(data_key, None)

    def clear_all(self):
        """Limpa todos os dados em cache."""
        self._loaded_data.clear()
        self._loading_flags.clear()


# Instância global do lazy loader
lazy_loader = LazyLoader()


def optimize_ui_updates():
    """
    Otimiza atualizações da UI conectando handlers otimizados.
    Chame esta função após inicializar a interface.
    """
    try:

        # Conectar eventos otimizados aos widgets principais
        if hasattr(g, "MAT_COMB") and g.MAT_COMB:
            g.MAT_COMB.currentTextChanged.connect(
                optimized_handler.handle_calculation_trigger
            )

        if hasattr(g, "ESP_COMB") and g.ESP_COMB:
            g.ESP_COMB.currentTextChanged.connect(
                optimized_handler.handle_calculation_trigger
            )

        if hasattr(g, "CANAL_COMB") and g.CANAL_COMB:
            g.CANAL_COMB.currentTextChanged.connect(
                optimized_handler.handle_calculation_trigger
            )

        # Adicionar mais conexões conforme necessário

    except (AttributeError, RuntimeError, TypeError) as e:

        logging.error("Erro ao otimizar atualizações da UI: %s", e)


def cleanup_optimization():
    """Limpa recursos de otimização."""

    # Parar e limpar todos os timers de debounce
    for timer in DEBOUNCE_TIMERS.values():
        if timer.isActive():
            timer.stop()
        timer.deleteLater()

    DEBOUNCE_TIMERS.clear()

    # Limpar dados do lazy loader
    lazy_loader.clear_all()

    # Limpar handler otimizado
    if optimized_handler.batch_timer.isActive():
        optimized_handler.batch_timer.stop()
    optimized_handler.pending_updates.clear()
