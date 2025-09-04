"""
Gerenciador de cache para dados do banco de dados.
Mantém dados em memória para acesso quando o banco está bloqueado.
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import get_session


class CacheManager:  # pylint: disable=too-many-instance-attributes
    """Gerencia cache de dados do banco para acesso offline."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_timeout = timedelta(minutes=5)  # Cache válido por 5 minutos
        self._lock = threading.RLock()
        self._initialized = False

        # Configurações de cache por tipo de dado
        self._cache_strategies = {
            "materiais": {"ttl_minutes": 60, "priority": "high"},  # 1 hora
            "espessuras": {"ttl_minutes": 60, "priority": "high"},  # 1 hora
            "canais": {"ttl_minutes": 60, "priority": "high"},  # 1 hora
            "deducoes": {"ttl_minutes": 5, "priority": "medium"},  # 5 minutos
        }

        # Arquivo para persistir cache entre sessões
        self.cache_file = Path("cache/database_cache.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Carrega cache persistido
        self._load_persistent_cache()

        # Configurar logger do cache
        self.cache_logger = logging.getLogger("cache_manager")

    def _load_persistent_cache(self):
        """Carrega cache persistido do disco."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # Reconstitui timestamps
                for key, timestamp_str in cache_data.get("timestamps", {}).items():
                    self._cache_timestamps[key] = datetime.fromisoformat(timestamp_str)

                # Carrega dados do cache
                self._cache = cache_data.get("data", {})

                logging.info(
                    "Cache persistido carregado: %d entradas", len(self._cache)
                )

        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            logging.warning("Erro ao carregar cache persistido: %s", e)
            self._cache = {}
            self._cache_timestamps = {}

    def _save_persistent_cache(self):
        """Salva cache no disco para persistência."""
        try:
            cache_data = {
                "data": self._cache,
                "timestamps": {
                    key: timestamp.isoformat()
                    for key, timestamp in self._cache_timestamps.items()
                },
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logging.error("Erro ao salvar cache persistido: %s", e)

    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se o cache ainda é válido baseado na estratégia."""
        if key not in self._cache_timestamps:
            return False

        # Determina TTL baseado no tipo de dado
        cache_type = key.split("_")[0]  # ex: 'materiais' de 'materiais_list'
        strategy = self._cache_strategies.get(cache_type, {"ttl_minutes": 5})
        ttl = timedelta(minutes=strategy["ttl_minutes"])

        return datetime.now() - self._cache_timestamps[key] < ttl

    def _update_cache_timestamp(self, key: str):
        """Atualiza o timestamp do cache."""
        self._cache_timestamps[key] = datetime.now()

    def get_materiais(self) -> List[Dict]:
        """Retorna lista de materiais do cache ou banco."""
        with self._lock:
            cache_key = "materiais_list"

            if self._is_cache_valid(cache_key):
                self.cache_logger.debug("Usando materiais do cache")
                return self._cache[cache_key]

            try:
                with get_session() as session:
                    materiais = session.query(Material).all()
                    result = [{"id": m.id, "nome": m.nome} for m in materiais]

                    self._cache[cache_key] = result
                    self._update_cache_timestamp(cache_key)
                    self._save_persistent_cache()

                    self.cache_logger.info(
                        "Cache atualizado: %d materiais", len(result)
                    )
                    return result

            except SQLAlchemyError as e:
                self.cache_logger.warning("Banco bloqueado, usando cache: %s", e)
                cached_data = self._cache.get(cache_key, [])

                if not cached_data:
                    self.cache_logger.error("Nenhum dado em cache para materiais!")

                return cached_data

    def get_espessuras(self) -> List[Dict]:
        """Retorna lista de espessuras do cache ou banco."""
        with self._lock:
            cache_key = "espessuras_list"

            if self._is_cache_valid(cache_key):
                self.cache_logger.debug("Usando espessuras do cache")
                return self._cache[cache_key]

            try:
                with get_session() as session:
                    espessuras = (
                        session.query(Espessura).order_by(Espessura.valor).all()
                    )
                    result = [{"id": e.id, "valor": e.valor} for e in espessuras]

                    self._cache[cache_key] = result
                    self._update_cache_timestamp(cache_key)
                    self._save_persistent_cache()

                    self.cache_logger.info(
                        "Cache atualizado: %d espessuras", len(result)
                    )
                    return result

            except SQLAlchemyError as e:
                self.cache_logger.warning("Banco bloqueado, usando cache: %s", e)
                cached_data = self._cache.get(cache_key, [])

                if not cached_data:
                    self.cache_logger.error("Nenhum dado em cache para espessuras!")

                return cached_data

    def get_canais(self) -> List[Dict]:
        """Retorna lista de canais do cache ou banco."""
        with self._lock:
            cache_key = "canais_list"

            if self._is_cache_valid(cache_key):
                self.cache_logger.debug("Usando canais do cache")
                return self._cache[cache_key]

            try:
                with get_session() as session:
                    canais = session.query(Canal).all()
                    result = [{"id": c.id, "valor": c.valor} for c in canais]

                    self._cache[cache_key] = result
                    self._update_cache_timestamp(cache_key)
                    self._save_persistent_cache()

                    self.cache_logger.info("Cache atualizado: %d canais", len(result))
                    return result

            except SQLAlchemyError as e:
                self.cache_logger.warning("Banco bloqueado, usando cache: %s", e)
                cached_data = self._cache.get(cache_key, [])

                if not cached_data:
                    self.cache_logger.error("Nenhum dado em cache para canais!")

                return cached_data

    def get_deducao(
        self, material_nome: str, espessura_valor: float, canal_valor: str
    ) -> Optional[Dict]:
        """Busca dedução específica do cache ou banco."""
        with self._lock:
            cache_key = f"deducao_{material_nome}_{espessura_valor}_{canal_valor}"

            if self._is_cache_valid(cache_key):
                self.cache_logger.debug("Usando dedução do cache: %s", cache_key)
                return self._cache[cache_key]

            try:
                with get_session() as session:
                    deducao = (
                        # pylint: disable=duplicate-code
                        session.query(Deducao)
                        .join(Material)
                        .join(Espessura)
                        .join(Canal)
                        .filter(
                            Material.nome == material_nome,
                            Espessura.valor == espessura_valor,
                            Canal.valor == canal_valor,
                        )
                        .first()
                    )

                    if deducao:
                        result = {
                            "valor": deducao.valor,
                            "observacao": deducao.observacao,
                            "forca": deducao.forca,
                        }
                    else:
                        result = None

                    self._cache[cache_key] = result
                    self._update_cache_timestamp(cache_key)
                    self._save_persistent_cache()

                    self.cache_logger.debug(
                        "Cache atualizado para dedução: %s", cache_key
                    )
                    return result

            except SQLAlchemyError as e:
                self.cache_logger.warning(
                    "Banco bloqueado, usando cache para dedução: %s", e
                )
                cached_data = self._cache.get(cache_key)

                if cached_data is None:
                    self.cache_logger.warning(
                        "Nenhum dado em cache para dedução: %s", cache_key
                    )

                return cached_data

    def invalidate_cache(self, keys: Optional[List[str]] = None):
        """Invalida cache específico ou todo o cache."""
        with self._lock:
            if keys:
                # Remove chaves que começam com os padrões fornecidos
                keys_to_remove = [
                    cache_key
                    for cache_key in self._cache.keys()
                    if any(cache_key.startswith(pattern) for pattern in keys)
                ]

                for cache_key in keys_to_remove:
                    self._cache.pop(cache_key, None)
                    self._cache_timestamps.pop(cache_key, None)

                    self.cache_logger.info("Cache invalidado para: %s", keys)
            else:
                self._cache.clear()
                self._cache_timestamps.clear()
                self.cache_logger.info("Todo o cache foi invalidado")

            self._save_persistent_cache()

    def preload_cache(self):
        """Pré-carrega dados essenciais no cache."""
        self.cache_logger.info("Pré-carregando cache de dados...")
        try:
            # Carrega dados estáticos primeiro
            self.get_materiais()
            self.get_espessuras()
            self.get_canais()

            self._initialized = True
            self.cache_logger.info("Cache pré-carregado com sucesso.")

        except (SQLAlchemyError, AttributeError, ValueError) as e:
            self.cache_logger.error("Erro ao pré-carregar cache: %s", e)
            # Mesmo com erro, marca como inicializado para usar cache existente
            self._initialized = True

    def get_cache_status(self) -> Dict[str, Any]:
        """Retorna status atual do cache."""
        with self._lock:
            total_entries = len(self._cache)
            valid_entries = sum(
                1 for key in self._cache.keys() if self._is_cache_valid(key)
            )

            cache_types = {}
            for key in self._cache.keys():
                cache_type = key.split("_")[0]
                cache_types[cache_type] = cache_types.get(cache_type, 0) + 1

            return {
                "initialized": self._initialized,
                "total_entries": total_entries,
                "valid_entries": valid_entries,
                "invalid_entries": total_entries - valid_entries,
                "cache_types": cache_types,
                "last_update": (
                    max(self._cache_timestamps.values()).isoformat()
                    if self._cache_timestamps
                    else None
                ),
            }

    def cleanup_expired_cache(self):
        """Remove entradas expiradas do cache."""
        with self._lock:
            expired_keys = [
                key for key in self._cache.keys() if not self._is_cache_valid(key)
            ]

            for key in expired_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

            if expired_keys:
                self.cache_logger.info(
                    "Removidas %d entradas expiradas do cache", len(expired_keys)
                )
                self._save_persistent_cache()

    def force_refresh(self, cache_types: Optional[List[str]] = None):
        """Força atualização do cache."""
        with self._lock:
            if cache_types:
                # Invalida tipos específicos
                self.invalidate_cache(cache_types)
            else:
                # Invalida tudo
                self.invalidate_cache()

            # Recarrega dados essenciais
            self.preload_cache()


# Instância global do cache
cache_manager = CacheManager()
