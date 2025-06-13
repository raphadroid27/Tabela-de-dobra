"""
Sistema de cache de configuração para evitar I/O desnecessário em arquivos JSON.
Implementa write-back cache com invalidação inteligente.
"""

import json
import threading
from pathlib import Path
import os
from typing import Dict, Any


class CacheConfiguracao:
    """Cache inteligente para configurações de aplicação."""

    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self._cache = {}
        self._dirty_keys = set()
        self._last_modified = 0
        self._cache_timeout = 300  # 5 minutos
        self._write_timer = None
        self._write_delay = 2.0  # 2 segundos de delay para write-back
        self._lock = threading.RLock()

        # Carregar configuração inicial
        self._load_from_file()

    def _load_from_file(self):
        """Carrega configuração do arquivo."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                self._last_modified = self.config_file.stat().st_mtime
            else:
                self._cache = {}
                self._last_modified = 0
        except (json.JSONDecodeError, OSError) as e:
            print(f"Erro ao carregar configuração de {self.config_file}: {e}")
            self._cache = {}

    def _check_file_modified(self) -> bool:
        """Verifica se arquivo foi modificado externamente."""
        if not self.config_file.exists():
            return False

        current_mtime = self.config_file.stat().st_mtime
        return current_mtime > self._last_modified

    def _schedule_write(self):
        """Agenda escrita no arquivo com delay."""
        with self._lock:
            if self._write_timer:
                self._write_timer.cancel()

            self._write_timer = threading.Timer(self._write_delay, self._write_to_file)
            self._write_timer.start()

    def _write_to_file(self):
        """Escreve configuração no arquivo."""
        with self._lock:
            try:
                # Criar diretório se não existir
                self.config_file.parent.mkdir(parents=True, exist_ok=True)

                # Escrever arquivo temporário primeiro
                temp_file = self.config_file.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)

                # Mover arquivo temporário para final
                temp_file.replace(self.config_file)

                # Atualizar timestamp
                self._last_modified = self.config_file.stat().st_mtime
                self._dirty_keys.clear()

            except OSError as e:
                print(f"Erro ao salvar configuração em {self.config_file}: {e}")
            finally:
                self._write_timer = None

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor de configuração.

        Args:
            key: Chave da configuração
            default: Valor padrão se não encontrado

        Returns:
            Valor da configuração ou padrão
        """
        with self._lock:
            # Verificar se arquivo foi modificado externamente
            if self._check_file_modified():
                self._load_from_file()

            return self._cache.get(key, default)

    def set(self, key: str, value: Any):
        """
        Define valor de configuração.

        Args:
            key: Chave da configuração
            value: Valor a ser definido
        """
        with self._lock:
            old_value = self._cache.get(key)
            if old_value != value:
                self._cache[key] = value
                self._dirty_keys.add(key)
                self._schedule_write()

    def update(self, config_dict: Dict[str, Any]):
        """
        Atualiza múltiplas configurações.

        Args:
            config_dict: Dicionário com configurações
        """
        with self._lock:
            changed = False
            for key, value in config_dict.items():
                if self._cache.get(key) != value:
                    self._cache[key] = value
                    self._dirty_keys.add(key)
                    changed = True

            if changed:
                self._schedule_write()

    def delete(self, key: str) -> bool:
        """
        Remove configuração.

        Args:
            key: Chave a ser removida

        Returns:
            True se removido, False se não existia
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._dirty_keys.add(key)
                self._schedule_write()
                return True
            return False

    def get_all(self) -> Dict[str, Any]:
        """
        Retorna todas as configurações.

        Returns:
            Dicionário com todas as configurações
        """
        with self._lock:
            if self._check_file_modified():
                self._load_from_file()
            return self._cache.copy()

    def flush(self):
        """Força escrita imediata no arquivo."""
        with self._lock:
            if self._write_timer:
                self._write_timer.cancel()
                self._write_timer = None
            self._write_to_file()

    def invalidate(self):
        """Invalida cache e recarrega do arquivo."""
        with self._lock:
            self._load_from_file()
            self._dirty_keys.clear()

    def is_dirty(self) -> bool:
        """Verifica se há mudanças não salvas."""
        with self._lock:
            return bool(self._dirty_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            return {
                "total_keys": len(self._cache),
                "dirty_keys": len(self._dirty_keys),
                "file_exists": self.config_file.exists(),
                "last_modified": self._last_modified,
                "has_pending_write": self._write_timer is not None,
            }


class GerenciadorConfig:
    """Gerenciador global de configurações com cache."""

    def __init__(self):
        self._caches = {}

    def get_cache(self, config_file: str) -> CacheConfiguracao:
        """
        Obtém cache para arquivo de configuração específico.

        Args:
            config_file: Caminho para arquivo de configuração

        Returns:
            Cache de configuração
        """
        if config_file not in self._caches:
            self._caches[config_file] = CacheConfiguracao(config_file)
        return self._caches[config_file]

    def flush_all(self):
        """Força escrita de todos os caches."""
        for cache in self._caches.values():
            cache.flush()

    def invalidate_all(self):
        """Invalida todos os caches."""
        for cache in self._caches.values():
            cache.invalidate()

    def get_global_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de todos os caches."""
        stats = {}
        for file_path, cache in self._caches.items():
            stats[file_path] = cache.get_stats()
        return stats


# Instância global do gerenciador
config_manager = GerenciadorConfig()


def get_config_cache(config_file: str) -> CacheConfiguracao:
    """Função conveniente para obter cache de configuração."""
    return config_manager.get_cache(config_file)


def get_app_config() -> CacheConfiguracao:
    """Função conveniente para configuração principal da aplicação."""
    config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
    return get_config_cache(config_file)
