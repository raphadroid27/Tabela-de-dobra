'''
Sistema de cache para otimizar consultas ao banco de dados.
Reduz consultas repetitivas e melhora a performance da aplicação.
'''
from functools import lru_cache, wraps
import time
from typing import List, Optional
from src.utils.banco_dados import session
from src.models.models import Material, Espessura, Canal, Deducao


class CacheManager:
    """Gerenciador de cache para consultas ao banco de dados."""
    
    def __init__(self):
        self._cache_timestamps = {}
        self.cache_timeout = 300  # 5 minutos
    
    def invalidate_cache(self, cache_type: str = None):
        """Invalida cache específico ou todos os caches."""
        if cache_type:
            # Limpar cache específico
            if hasattr(self, f'_get_{cache_type}'):
                getattr(self, f'_get_{cache_type}').cache_clear()
        else:
            # Limpar todos os caches
            for attr_name in dir(self):
                if attr_name.startswith('_get_') and hasattr(getattr(self, attr_name), 'cache_clear'):
                    getattr(self, attr_name).cache_clear()
        
        # Resetar timestamps
        if cache_type:
            self._cache_timestamps.pop(cache_type, None)
        else:
            self._cache_timestamps.clear()
    
    def _is_cache_valid(self, cache_type: str) -> bool:
        """Verifica se o cache ainda é válido baseado no timeout."""
        timestamp = self._cache_timestamps.get(cache_type, 0)
        return (time.time() - timestamp) < self.cache_timeout
    
    def _update_timestamp(self, cache_type: str):
        """Atualiza timestamp do cache."""
        self._cache_timestamps[cache_type] = time.time()

    @lru_cache(maxsize=32)
    def _get_materiais(self) -> List[Material]:
        """Cache interno para materiais."""
        return session.query(Material).all()
    
    def get_materiais(self) -> List[Material]:
        """Obtém lista de materiais com cache."""
        cache_type = 'materiais'
        if not self._is_cache_valid(cache_type):
            self._get_materiais.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_materiais()
    
    @lru_cache(maxsize=64)
    def _get_espessuras(self) -> List[Espessura]:
        """Cache interno para espessuras."""
        return session.query(Espessura).order_by(Espessura.valor).all()
    
    def get_espessuras(self) -> List[Espessura]:
        """Obtém lista de espessuras com cache."""
        cache_type = 'espessuras'
        if not self._is_cache_valid(cache_type):
            self._get_espessuras.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_espessuras()
    
    @lru_cache(maxsize=64)
    def _get_canais(self) -> List[Canal]:
        """Cache interno para canais."""
        return session.query(Canal).all()
    
    def get_canais(self) -> List[Canal]:
        """Obtém lista de canais com cache."""
        cache_type = 'canais'
        if not self._is_cache_valid(cache_type):
            self._get_canais.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_canais()
    
    @lru_cache(maxsize=128)
    def _get_deducao(self, material_id: int, espessura_id: int, canal_id: int) -> Optional[Deducao]:
        """Cache interno para dedução específica."""
        return session.query(Deducao).filter(
            Deducao.material_id == material_id,
            Deducao.espessura_id == espessura_id,
            Deducao.canal_id == canal_id
        ).first()
    
    def get_deducao(self, material_id: int, espessura_id: int, canal_id: int) -> Optional[Deducao]:
        """Obtém dedução específica com cache."""
        cache_type = 'deducoes'
        if not self._is_cache_valid(cache_type):
            self._get_deducao.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_deducao(material_id, espessura_id, canal_id)
    
    @lru_cache(maxsize=64)
    def _get_deducoes(self) -> List[Deducao]:
        """Cache interno para todas as deduções."""
        return session.query(Deducao).all()
    
    def get_deducoes(self) -> List[Deducao]:
        """Obtém lista de todas as deduções com cache."""
        cache_type = 'deducoes'
        if not self._is_cache_valid(cache_type):
            self._get_deducoes.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_deducoes()
    
    @lru_cache(maxsize=64)
    def _get_espessuras_por_material(self, material_id: int) -> List[Espessura]:
        """Cache interno para espessuras por material."""
        return session.query(Espessura).join(Deducao).filter(
            Deducao.material_id == material_id
        ).order_by(Espessura.valor).all()
    
    def get_espessuras_por_material(self, material_id: int) -> List[Espessura]:
        """Obtém espessuras disponíveis para um material específico."""
        cache_type = 'espessuras_material'
        if not self._is_cache_valid(cache_type):
            self._get_espessuras_por_material.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_espessuras_por_material(material_id)
    
    @lru_cache(maxsize=64)
    def _get_canais_por_material_espessura(self, material_id: int, espessura_id: int) -> List[Canal]:
        """Cache interno para canais por material e espessura."""
        return session.query(Canal).join(Deducao).filter(
            Deducao.material_id == material_id,
            Deducao.espessura_id == espessura_id
        ).order_by(Canal.valor).all()
    
    def get_canais_por_material_espessura(self, material_id: int, espessura_id: int) -> List[Canal]:
        """Obtém canais disponíveis para material e espessura específicos."""
        cache_type = 'canais_material_espessura'
        if not self._is_cache_valid(cache_type):
            self._get_canais_por_material_espessura.cache_clear()
            self._update_timestamp(cache_type)
        return self._get_canais_por_material_espessura(material_id, espessura_id)
    
    def get_cached_data(self, data_type: str):
        """Método genérico para obter dados cached."""
        if data_type == 'deducoes':
            return self.get_deducoes()
        elif data_type == 'materiais':
            return self.get_materiais()
        elif data_type == 'espessuras':
            return self.get_espessuras()
        elif data_type == 'canais':
            return self.get_canais()
        else:
            return []
    
    def invalidate_all(self):
        """Invalida todos os caches."""
        self.invalidate_cache()


# Instância global do cache
cache_manager = CacheManager()


def invalidate_cache_on_change(cache_types: List[str] = None):
    """Decorator para invalidar cache quando dados são modificados."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Invalidar caches relevantes após modificação
            if cache_types:
                for cache_type in cache_types:
                    cache_manager.invalidate_cache(cache_type)
            else:
                cache_manager.invalidate_cache()  # Invalidar tudo
            return result
        return wrapper
    return decorator


# Funções de conveniência para uso direto
def get_materiais_cached() -> List[Material]:
    """Obtém materiais com cache."""
    return cache_manager.get_materiais()

def get_espessuras_cached() -> List[Espessura]:
    """Obtém espessuras com cache."""
    return cache_manager.get_espessuras()

def get_canais_cached() -> List[Canal]:
    """Obtém canais com cache."""
    return cache_manager.get_canais()

def get_deducao_cached(material_id: int, espessura_id: int, canal_id: int) -> Optional[Deducao]:
    """Obtém dedução com cache."""
    return cache_manager.get_deducao(material_id, espessura_id, canal_id)

def get_deducoes_cached() -> List[Deducao]:
    """Obtém todas as deduções com cache."""
    return cache_manager.get_deducoes()
