"""
Sistema de cache para otimizar acesso a dados frequentes.
"""

import logging
import time
from functools import wraps

# Cache global para dados frequentemente acessados
_cache_dados = {}
_cache_timestamps = {}
_cache_access_count = {}  # Contador de acessos para otimização
CACHE_TTL = 600  # Aumentado para 10 minutos para múltiplos usuários
# 30 minutos para dados compartilhados (materiais, espessuras, etc.)
CACHE_TTL_SHARED = 1800
CACHE_TTL_STATIC = 3600  # 1 hora para dados estáticos


def cache_com_ttl(ttl_seconds: int = CACHE_TTL, shared: bool = False):
    """
    Decorator para cache com TTL (Time To Live) otimizado para múltiplos usuários.

    Args:
        ttl_seconds: Tempo de vida do cache em segundos
        shared: Se True, usa TTL mais longo para dados compartilhados
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Usar TTL apropriado baseado no tipo de dados
            effective_ttl = CACHE_TTL_SHARED if shared else ttl_seconds

            # Criar chave única baseada na função e argumentos
            cache_key = (
                f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            )
            current_time = time.time()

            # Verificar se existe cache válido
            if (
                cache_key in _cache_dados
                and cache_key in _cache_timestamps
                and current_time - _cache_timestamps[cache_key] < effective_ttl
            ):
                # Incrementar contador de acesso
                _cache_access_count[cache_key] = _cache_access_count.get(
                    cache_key, 0) + 1
                logging.debug("Cache hit para %s (acessos: %d)",
                              func.__name__, _cache_access_count[cache_key])
                return _cache_dados[cache_key]

            # Executar função e armazenar resultado
            resultado = func(*args, **kwargs)
            _cache_dados[cache_key] = resultado
            _cache_timestamps[cache_key] = current_time
            _cache_access_count[cache_key] = 1

            logging.debug("Cache miss para %s - resultado armazenado", func.__name__)
            return resultado

        return wrapper

    return decorator


def limpar_cache():
    """Limpa todo o cache."""
    _cache_dados.clear()
    _cache_timestamps.clear()
    logging.info("Cache limpo")


def limpar_cache_expirado():
    """Remove entradas expiradas do cache."""
    current_time = time.time()
    chaves_expiradas = []

    for chave, timestamp in _cache_timestamps.items():
        if current_time - timestamp > CACHE_TTL:
            chaves_expiradas.append(chave)

    for chave in chaves_expiradas:
        _cache_dados.pop(chave, None)
        _cache_timestamps.pop(chave, None)

    if chaves_expiradas:
        logging.debug("Removidas %d entradas expiradas do cache", len(chaves_expiradas))


class CacheManager:
    """Gerenciador de cache para dados específicos."""

    def __init__(self):
        self._materiais_cache = None
        self._espessuras_cache = None
        self._canais_cache = None
        self._last_update = 0
        self._cache_duration = 300  # 5 minutos

    def _is_cache_valid(self) -> bool:
        """Verifica se o cache ainda é válido."""
        return (time.time() - self._last_update) < self._cache_duration

    def get_materiais(self):
        """Retorna materiais do cache ou None se inválido."""
        if self._is_cache_valid() and self._materiais_cache is not None:
            return self._materiais_cache
        return None

    def set_materiais(self, materiais):
        """Armazena materiais no cache."""
        self._materiais_cache = materiais
        self._last_update = time.time()

    def get_espessuras(self):
        """Retorna espessuras do cache ou None se inválido."""
        if self._is_cache_valid() and self._espessuras_cache is not None:
            return self._espessuras_cache
        return None

    def set_espessuras(self, espessuras):
        """Armazena espessuras no cache."""
        self._espessuras_cache = espessuras
        self._last_update = time.time()

    def get_canais(self):
        """Retorna canais do cache ou None se inválido."""
        if self._is_cache_valid() and self._canais_cache is not None:
            return self._canais_cache
        return None

    def set_canais(self, canais):
        """Armazena canais no cache."""
        self._canais_cache = canais
        self._last_update = time.time()

    def invalidar_cache(self):
        """Invalida todo o cache."""
        self._materiais_cache = None
        self._espessuras_cache = None
        self._canais_cache = None
        self._last_update = 0


# Instância global do gerenciador de cache
cache_manager = CacheManager()
