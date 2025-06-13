"""
Sistema de cache para resultados de cálculos com debounce para eventos de UI.
Reduz cálculos repetitivos e melhora responsividade da interface.
"""

import time
import threading
from functools import wraps
from typing import Any, Dict, Callable, Optional, Tuple
from collections import defaultdict


class CacheCalculos:
    """Cache inteligente para resultados de cálculos com debounce."""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._debounce_timers = {}
        self._cache_timeout = 300  # 5 minutos
        self._debounce_delay = 0.3  # 300ms

    def _generate_key(self, func_name: str, args: Tuple, kwargs: Dict) -> str:
        """Gera chave única para cache baseada em função e parâmetros."""
        key_parts = [func_name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)

    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se entrada do cache ainda é válida."""
        if key not in self._timestamps:
            return False
        return (time.time() - self._timestamps[key]) < self._cache_timeout

    def cached_calculation(self, func: Callable) -> Callable:
        """Decorator para cache de cálculos."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._generate_key(func.__name__, args, kwargs)

            # Verificar cache
            if key in self._cache and self._is_cache_valid(key):
                return self._cache[key]

            # Calcular e armazenar no cache
            result = func(*args, **kwargs)
            self._cache[key] = result
            self._timestamps[key] = time.time()

            return result

        return wrapper

    def debounced_calculation(self, func: Callable, delay: Optional[float] = None) -> Callable:
        """Decorator para debounce de cálculos."""
        if delay is None:
            delay = self._debounce_delay

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._generate_key(func.__name__, args, kwargs)

            # Cancelar timer anterior se existir
            if key in self._debounce_timers:
                self._debounce_timers[key].cancel()

            # Criar novo timer
            def delayed_execution():
                result = func(*args, **kwargs)
                # Armazenar no cache após execução
                self._cache[key] = result
                self._timestamps[key] = time.time()
                return result

            timer = threading.Timer(delay, delayed_execution)
            self._debounce_timers[key] = timer
            timer.start()

            # Retornar valor do cache se disponível
            if key in self._cache and self._is_cache_valid(key):
                return self._cache[key]

            return None  # Valor será calculado após debounce

        return wrapper

    def invalidate_pattern(self, pattern: str):
        """Invalida cache baseado em padrão de chave."""
        keys_to_remove = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_remove:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

    def invalidate_all(self):
        """Invalida todo o cache."""
        self._cache.clear()
        self._timestamps.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        total_entries = len(self._cache)
        valid_entries = sum(1 for k in self._cache.keys() if self._is_cache_valid(k))

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "hit_ratio": valid_entries / total_entries if total_entries > 0 else 0,
            "cache_size_mb": sum(len(str(v)) for v in self._cache.values()) / (1024 * 1024),
        }


# Instância global do cache de cálculos
calculation_cache = CacheCalculos()


class AntirreboteUI:
    """Sistema de debounce para eventos de UI."""

    def __init__(self):
        self._timers = defaultdict(lambda: None)
        self._default_delay = 0.3  # 300ms

    def debounce(self, key: str, func: Callable, delay: Optional[float] = None, *args, **kwargs):
        """
        Aplica debounce a uma função com chave específica.

        Args:
            key: Chave única para identificar o debounce
            func: Função a ser executada
            delay: Atraso em segundos (padrão: 300ms)
            *args, **kwargs: Argumentos para a função
        """
        if delay is None:
            delay = self._default_delay

        # Cancelar timer anterior
        if self._timers[key] is not None:
            self._timers[key].cancel()

        # Criar novo timer
        def execute():
            func(*args, **kwargs)
            self._timers[key] = None

        self._timers[key] = threading.Timer(delay, execute)
        self._timers[key].start()

    def cancel(self, key: str):
        """Cancela debounce para uma chave específica."""
        if self._timers[key] is not None:
            self._timers[key].cancel()
            self._timers[key] = None

    def cancel_all(self):
        """Cancela todos os debounces ativos."""
        for timer in self._timers.values():
            if timer is not None:
                timer.cancel()
        self._timers.clear()


# Instância global do debouncer
ui_debouncer = AntirreboteUI()


# Decorators convenientes
def cached_calc(func):
    """Decorator conveniente para cache de cálculos."""
    return calculation_cache.cached_calculation(func)


def debounced_calc(delay: float = 0.3):
    """Decorator conveniente para debounce de cálculos."""

    def decorator(func):
        return calculation_cache.debounced_calculation(func, delay)

    return decorator


def debounced_ui_update(key: str, delay: float = 0.3):
    """
    Decorator para debounce de atualizações de UI.

    Args:
        key: Chave única para o debounce
        delay: Atraso em segundos
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ui_debouncer.debounce(key, func, delay, *args, **kwargs)

        return wrapper

    return decorator
