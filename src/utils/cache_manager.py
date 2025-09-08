"""Gerenciador de cache para dados do banco.

Mantém dados em memória para acesso quando o banco está bloqueado.
"""

import json
import logging
import os
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from sqlalchemy.exc import SQLAlchemyError

from src.models.models import Canal, Deducao, Espessura, Material
from src.utils.banco_dados import get_session
from src.utils.utilitarios import CACHE_DIR


class CacheManager:  # pylint: disable=too-many-instance-attributes
    """Gerencia cache de dados do banco para acesso offline."""

    def __init__(self):
        """Inicializa o gerenciador de cache."""
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._initialized = False
        self._dirty = False  # Flag para controle de persistência
        self._last_save: datetime = datetime.min  # controle de frequência de gravação

        # Configurações simplificadas de TTL por tipo de dado
        self._cache_ttl = {
            "materiais": 60,  # 1 hora para dados estáticos
            "espessuras": 60,  # 1 hora para dados estáticos
            "canais": 60,  # 1 hora para dados estáticos
            "deducoes": 5,  # 5 minutos para dados dinâmicos
        }

        # Arquivo para persistir cache entre sessões
        self.cache_file = Path(CACHE_DIR) / "database_cache.json"
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

    def _save_persistent_cache(self, force=False):
        """Salva cache no disco para persistência (escrita atômica + throttling)."""
        # Throttling: evita gravar muitas vezes em curto intervalo
        if not force:
            if not self._dirty:
                return
            if datetime.now() - self._last_save < timedelta(seconds=2):
                return

        try:
            cache_data = {
                "data": self._cache,
                "timestamps": {
                    key: timestamp.isoformat()
                    for key, timestamp in self._cache_timestamps.items()
                },
                "saved_at": datetime.now().isoformat(),
            }

            # Escrita atômica: grava em arquivo temporário e substitui
            tmp_dir = self.cache_file.parent
            tmp_dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", delete=False, dir=tmp_dir, encoding="utf-8"
            ) as tf:
                json.dump(cache_data, tf, indent=2, ensure_ascii=False)
                tmp_path = tf.name

            os.replace(tmp_path, self.cache_file)

            self._dirty = False
            self._last_save = datetime.now()

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logging.error("Erro ao salvar cache persistido: %s", e)

    def _is_cache_valid(self, key: str) -> bool:
        """Verifica se o cache ainda é válido baseado no TTL."""
        if key not in self._cache_timestamps:
            return False

        # Determina TTL baseado no tipo de dado
        cache_type = key.split("_")[0]  # ex: 'materiais' de 'materiais_list'
        ttl_minutes = self._cache_ttl.get(cache_type, 5)  # Default 5 minutos
        ttl = timedelta(minutes=ttl_minutes)

        return datetime.now() - self._cache_timestamps[key] < ttl

    def _update_cache_timestamp(self, key: str):
        """Atualiza o timestamp do cache."""
        self._cache_timestamps[key] = datetime.now()
        self._dirty = True  # Marca cache como modificado

    def _get_cached_data(
        self, cache_key: str, query_func, result_processor=None
    ) -> Any:
        """Método genérico para buscar dados com cache."""
        with self._lock:
            if self._is_cache_valid(cache_key):
                self.cache_logger.debug("Usando dados do cache: %s", cache_key)
                return self._cache[cache_key]

            try:
                with get_session() as session:
                    data = query_func(session)

                    if result_processor:
                        result = result_processor(data)
                    else:
                        result = data

                    self._cache[cache_key] = result
                    self._update_cache_timestamp(cache_key)

                    # Salvar cache apenas se necessário
                    if self._dirty:
                        self._save_persistent_cache()

                    self.cache_logger.info("Cache atualizado: %s", cache_key)
                    return result

            except SQLAlchemyError as e:
                self.cache_logger.warning("Banco bloqueado, usando cache: %s", e)
                cached_data = self._cache.get(
                    cache_key, [] if "list" in cache_key else None
                )

                if not cached_data and "list" in cache_key:
                    self.cache_logger.error("Nenhum dado em cache para: %s", cache_key)

                return cached_data

    def get_materiais(self) -> List[Dict]:
        """Retorna lista de materiais do cache ou banco."""
        return cast(
            List[Dict],
            self._get_cached_data(
                "materiais_list",
                lambda session: session.query(Material).all(),
                lambda materiais: [{"id": m.id, "nome": m.nome} for m in materiais],
            ),
        )

    def get_espessuras(self) -> List[Dict]:
        """Retorna lista de espessuras do cache ou banco."""
        return cast(
            List[Dict],
            self._get_cached_data(
                "espessuras_list",
                lambda session: session.query(Espessura)
                .order_by(Espessura.valor)
                .all(),
                lambda espessuras: [{"id": e.id, "valor": e.valor} for e in espessuras],
            ),
        )

    def get_canais(self) -> List[Dict]:
        """Retorna lista de canais do cache ou banco."""
        return cast(
            List[Dict],
            self._get_cached_data(
                "canais_list",
                lambda session: session.query(Canal).all(),
                lambda canais: [{"id": c.id, "valor": c.valor} for c in canais],
            ),
        )

    def get_deducao(
        self, material_nome: str, espessura_valor: float, canal_valor: str
    ) -> Optional[Dict]:
        """Busca dedução específica do cache ou banco."""
        # Padroniza prefixo no plural para alinhar com TTL/invalidade
        cache_key = f"deducoes_{material_nome}_{espessura_valor}_{canal_valor}"

        def query_deducao(session):
            return (
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

        def process_deducao(deducao):
            if deducao:
                return {
                    "valor": deducao.valor,
                    "observacao": deducao.observacao,
                    "forca": deducao.forca,
                }
            return None

        return cast(
            Optional[Dict],
            self._get_cached_data(cache_key, query_deducao, process_deducao),
        )

    def invalidate_cache(self, keys: Optional[List[str]] = None):
        """Invalida cache específico ou todo o cache."""
        with self._lock:
            if keys:
                # Expande padrões para lidar com singular/plural
                expanded = set(keys)
                if any(
                    k.startswith("deducao") or k.startswith("deducoes") for k in keys
                ):
                    expanded.update({"deducao", "deducao_", "deducoes", "deducoes_"})

                keys_to_remove = [
                    cache_key
                    for cache_key in list(self._cache.keys())
                    if any(cache_key.startswith(pattern) for pattern in expanded)
                ]

                for cache_key in keys_to_remove:
                    self._cache.pop(cache_key, None)
                    self._cache_timestamps.pop(cache_key, None)

                self.cache_logger.info(
                    "Cache invalidado para padrões: %s", list(expanded)
                )
            else:
                self._cache.clear()
                self._cache_timestamps.clear()
                self.cache_logger.info("Todo o cache foi invalidado")

            self._dirty = True
            self._save_persistent_cache(force=True)

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

            cache_types: Dict[str, int] = {}
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
                self._save_persistent_cache(force=True)

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

    def sync_cache_to_disk(self):
        """Sincroniza cache modificado para o disco."""
        if self._dirty:
            self._save_persistent_cache(force=True)
            logging.info("Cache sincronizado para disco")


# Instância global do cache
cache_manager = CacheManager()
