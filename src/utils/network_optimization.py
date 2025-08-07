"""
Configurações e otimizações específicas para ambiente de rede com múltiplos usuários.
"""

import logging
import threading
import time
from typing import Dict, Any

# Configurações para múltiplos usuários
NETWORK_CONFIG = {
    # Pool de conexões
    'max_connections': 20,
    'initial_connections': 8,
    'connection_timeout': 90,
    'retry_attempts': 3,

    # Cache
    'cache_ttl_default': 600,      # 10 minutos
    'cache_ttl_shared': 1800,      # 30 minutos (materiais, espessuras)
    'cache_ttl_static': 3600,      # 1 hora (dados raramente alterados)

    # UI Optimization
    'debounce_calculation': 1000,   # 1s para cálculos
    'debounce_list_update': 2000,   # 2s para listas
    'throttle_ui_update': 1500,     # 1.5s para updates da UI

    # Session Management
    'heartbeat_interval': 60,       # 60s entre heartbeats
    'session_cleanup_interval': 300,  # 5 min para limpeza de sessões mortas

    # Batch Processing
    'batch_size': 50,               # Operações por lote
    'batch_timeout': 5000,          # 5s timeout para lotes

    # Performance Monitoring
    'enable_stats': True,
    'stats_log_interval': 300,      # 5 min para log de estatísticas
}


class NetworkPerformanceMonitor:
    """Monitor de performance para ambiente de rede."""

    def __init__(self):
        self.stats = {
            'db_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ui_updates': 0,
            'errors': 0,
            'avg_response_time': 0,
            'active_users': 0,
        }
        self.start_time = time.time()
        self.last_reset = time.time()
        self.lock = threading.Lock()

    def record_db_operation(self, duration: float = 0):
        """Registra operação de banco de dados."""
        with self.lock:
            self.stats['db_operations'] += 1
            if duration > 0:
                # Calcular média móvel do tempo de resposta
                current_avg = self.stats['avg_response_time']
                count = self.stats['db_operations']
                self.stats['avg_response_time'] = (
                    (current_avg * (count - 1) + duration) / count
                )

    def record_cache_hit(self):
        """Registra cache hit."""
        with self.lock:
            self.stats['cache_hits'] += 1

    def record_cache_miss(self):
        """Registra cache miss."""
        with self.lock:
            self.stats['cache_misses'] += 1

    def record_ui_update(self):
        """Registra atualização da UI."""
        with self.lock:
            self.stats['ui_updates'] += 1

    def record_error(self):
        """Registra erro."""
        with self.lock:
            self.stats['errors'] += 1

    def set_active_users(self, count: int):
        """Define número de usuários ativos."""
        with self.lock:
            self.stats['active_users'] = count

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas atuais."""
        with self.lock:
            runtime = time.time() - self.start_time
            total_operations = self.stats['cache_hits'] + self.stats['cache_misses']
            cache_hit_ratio = (
                self.stats['cache_hits'] / max(1, total_operations) * 100
            )

            return {
                **self.stats,
                'runtime_seconds': runtime,
                'cache_hit_ratio': cache_hit_ratio,
                'operations_per_second': self.stats['db_operations'] / max(1, runtime),
                'error_ratio': self.stats['errors'] / max(1, self.stats['db_operations']) * 100,
            }

    def reset_stats(self):
        """Reseta estatísticas."""
        with self.lock:
            self.stats = {key: 0 for key in self.stats}
            self.last_reset = time.time()

    def log_stats(self):
        """Registra estatísticas no log."""
        stats = self.get_stats()
        logging.info("=== Performance Stats ===")
        logging.info("Usuários ativos: %d", stats['active_users'])
        logging.info("Operações DB: %d (%.1f/s)",
                     stats['db_operations'], stats['operations_per_second'])
        logging.info("Cache hit ratio: %.1f%%", stats['cache_hit_ratio'])
        logging.info("Tempo médio resposta: %.3fs", stats['avg_response_time'])
        logging.info("Taxa de erro: %.1f%%", stats['error_ratio'])
        logging.info("Updates UI: %d", stats['ui_updates'])
        logging.info("Runtime: %.0fs", stats['runtime_seconds'])


# Instância global do monitor
performance_monitor = NetworkPerformanceMonitor()


def get_network_config(key: str = None):
    """Retorna configuração de rede."""
    if key:
        return NETWORK_CONFIG.get(key)
    return NETWORK_CONFIG


def optimize_for_network():
    """Aplica otimizações específicas para ambiente de rede."""
    logging.info("Aplicando otimizações para ambiente de rede multi-usuário...")

    # Log das configurações aplicadas
    for key, value in NETWORK_CONFIG.items():
        logging.debug("Config %s: %s", key, value)

    # Iniciar monitoramento se habilitado
    if NETWORK_CONFIG.get('enable_stats', False):
        _start_stats_logging()


def _start_stats_logging():
    """Inicia log periódico de estatísticas."""
    def log_periodically():
        while True:
            time.sleep(NETWORK_CONFIG['stats_log_interval'])
            performance_monitor.log_stats()

    stats_thread = threading.Thread(target=log_periodically, daemon=True)
    stats_thread.start()
    logging.info("Monitor de performance iniciado")


def get_performance_stats():
    """Retorna estatísticas de performance."""
    return performance_monitor.get_stats()


def cleanup_network_resources():
    """Limpa recursos de rede ao fechar aplicação."""
    logging.info("Limpando recursos de rede...")
    performance_monitor.log_stats()  # Log final
    performance_monitor.reset_stats()
