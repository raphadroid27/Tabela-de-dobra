"""
Sistema de pool de conexões otimizado para SQLite em rede.
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from queue import Empty, Queue

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.utils.utilitarios import DB_PATH


class SQLiteConnectionPool:
    """Pool de conexões SQLite otimizado para acesso em rede."""

    def __init__(self, max_connections=20, db_path=None):
        self.max_connections = max_connections
        self.db_path = db_path or DB_PATH
        self.pool = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.RLock()
        self.stats = {
            'total_requests': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'errors': 0
        }

        # Configuração otimizada do engine para múltiplos usuários
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            pool_pre_ping=True,
            pool_recycle=1800,  # 30 minutos
            pool_size=max_connections,
            max_overflow=5,  # Permite overflow para picos
            connect_args={
                "timeout": 90,  # Aumentado para 90s
                "check_same_thread": False,
            },
            echo=False,
        )

        event.listen(self.engine, "connect", self._apply_sqlite_optimizations)

        self.db_session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,  # Controle manual de flush
        )

        # Pré-criar algumas sessões
        self._initialize_pool()

    def _apply_sqlite_optimizations(self, dbapi_connection, _connection_record):
        """Aplica otimizações SQLite após a conexão para múltiplos usuários."""
        cursor = dbapi_connection.cursor()

        optimizations = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -256000",        # 256MB cache por conexão
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 1073741824",     # 1GB memory-mapped I/O
            "PRAGMA busy_timeout = 90000",        # 90s timeout para locks
            "PRAGMA wal_autocheckpoint = 2000",
            "PRAGMA optimize",
            "PRAGMA analysis_limit = 1000",
        ]

        for pragma in optimizations:
            try:
                cursor.execute(pragma)
                logging.debug("Aplicado: %s", pragma)
            except (sqlite3.Error, SQLAlchemyError) as e:
                logging.error("Falha ao aplicar %s: %s", pragma, e)

        cursor.close()

    def _initialize_pool(self):
        """Inicializa o pool com conexões para múltiplos usuários."""
        try:
            # Inicia com 8 conexões para suportar 4+ usuários
            initial_connections = min(8, self.max_connections)
            for _ in range(initial_connections):
                session = self.db_session()
                self.pool.put(session)
                self.active_connections += 1
                logging.debug("Sessão adicionada ao pool (%d/%d)",
                              self.active_connections, self.max_connections)
        except SQLAlchemyError as e:
            logging.error("Erro ao inicializar pool de conexões: %s", e)

    @contextmanager
    def get_session(self, timeout=45, retry_count=3):
        """Context manager para obter uma sessão do pool com retry automático."""
        session = None

        for attempt in range(retry_count):
            try:
                self.stats['total_requests'] += 1

                # Tentar obter sessão existente do pool
                try:
                    session = self.pool.get(timeout=timeout)
                    self.stats['pool_hits'] += 1
                    logging.debug("Sessão obtida do pool (tentativa %d)", attempt + 1)
                except Empty:
                    self.stats['pool_misses'] += 1
                    # Se pool vazio, criar nova sessão se permitido
                    with self.lock:
                        if self.active_connections < self.max_connections:
                            session = self.db_session()
                            self.active_connections += 1
                            logging.debug("Nova sessão criada (%d/%d)",
                                          self.active_connections, self.max_connections)
                        else:
                            # Pool cheio, aguardar com timeout reduzido
                            session = self.pool.get(timeout=timeout // 2)

                if session is None:
                    raise SQLAlchemyError("Não foi possível obter sessão do pool")

                # Verificar se sessão ainda é válida
                try:
                    session.execute("SELECT 1")
                    break  # Sessão válida, sair do loop de retry
                except SQLAlchemyError:
                    # Sessão inválida, tentar recriar
                    if session:
                        session.close()
                    session = self.db_session()
                    logging.debug(
                        "Sessão recriada devido a erro (tentativa %d)", attempt + 1)
                    break

            except (SQLAlchemyError, Empty) as e:
                self.stats['errors'] += 1
                if session:
                    try:
                        session.close()
                    except SQLAlchemyError:
                        pass
                    session = None

                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 0.5  # Backoff progressivo
                    logging.warning("Erro na tentativa %d, aguardando %.1fs: %s",
                                    attempt + 1, wait_time, e)
                    time.sleep(wait_time)
                else:
                    logging.error("Falha após %d tentativas: %s", retry_count, e)
                    raise e
        try:
            yield session

            # Commit automático se não houver erros
            if session:
                session.commit()

        except SQLAlchemyError as e:
            if session:
                session.rollback()
                logging.error("Erro na sessão, rollback executado: %s", e)
            raise
        finally:
            if session:
                try:
                    # Retornar sessão ao pool se ainda válida
                    if not self.pool.full():
                        session.execute("SELECT 1")
                        self.pool.put(session)
                        logging.debug("Sessão retornada ao pool")
                    else:
                        session.close()
                        with self.lock:
                            self.active_connections -= 1
                        logging.debug("Sessão fechada (pool cheio)")
                except SQLAlchemyError as e:
                    logging.error("Erro ao retornar sessão ao pool: %s", e)
                    if session:
                        session.close()
                    with self.lock:
                        self.active_connections -= 1

    def get_stats(self):
        """Retorna estatísticas detalhadas do pool para monitoramento."""
        return {
            "pool_size": self.pool.qsize(),
            "active_connections": self.active_connections,
            "max_connections": self.max_connections,
            "total_requests": self.stats['total_requests'],
            "pool_hits": self.stats['pool_hits'],
            "pool_misses": self.stats['pool_misses'],
            "errors": self.stats['errors'],
            "hit_ratio": self.stats['pool_hits'] / max(1, self.stats['total_requests']) * 100,
            "error_ratio": self.stats['errors'] / max(1, self.stats['total_requests']) * 100,
        }

    def close_all(self):
        """Fecha todas as conexões do pool."""
        with self.lock:
            while not self.pool.empty():
                try:
                    session = self.pool.get_nowait()
                    session.close()
                except Empty:
                    break
            self.active_connections = 0
        logging.info("Todas as conexões do pool foram fechadas")


# Instância global do pool
connection_pool = SQLiteConnectionPool()


@contextmanager
def get_optimized_session():
    """
    Context manager para obter sessão otimizada.
    Use esta função em vez de session direta para melhor performance.
    """
    with connection_pool.get_session() as session:
        yield session


class BatchProcessor:
    """Processador de operações em lote para reduzir I/O."""

    def __init__(self, batch_size=50):
        self.batch_size = batch_size
        self.pending_operations = []
        self.lock = threading.Lock()

    def add_operation(self, operation_type, model_class, data):
        """Adiciona operação ao lote."""
        with self.lock:
            self.pending_operations.append(
                {
                    "type": operation_type,
                    "model": model_class,
                    "data": data,
                    "timestamp": time.time(),
                }
            )

            if len(self.pending_operations) >= self.batch_size:
                self._process_batch()

    def _process_batch(self):
        """Processa lote de operações."""
        if not self.pending_operations:
            return

        try:
            with get_optimized_session() as session:
                for op in self.pending_operations:
                    if op["type"] == "insert":
                        session.add(op["model"](**op["data"]))
                    elif op["type"] == "update":
                        # Implementar lógica de update conforme necessário
                        pass

                session.flush()  # Enviar para DB mas não commitar ainda
                operations_count = len(self.pending_operations)
                self.pending_operations.clear()
                logging.debug("Lote de %s operações processado", operations_count)

        except SQLAlchemyError as e:
            logging.error("Erro ao processar lote: %s", e)
            self.pending_operations.clear()

    def force_process(self):
        """Força processamento do lote atual."""
        with self.lock:
            self._process_batch()


# Instância global do processador de lotes
batch_processor = BatchProcessor()
