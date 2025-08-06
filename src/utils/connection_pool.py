"""
Sistema de pool de conexões otimizado para SQLite em rede.
"""

import logging
import threading
import time
from contextlib import contextmanager
from queue import Empty, Queue

import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.utils.utilitarios import DB_PATH


class SQLiteConnectionPool:
    """Pool de conexões SQLite otimizado para acesso em rede."""

    def __init__(self, max_connections=10, db_path=None):
        self.max_connections = max_connections
        self.db_path = db_path or DB_PATH
        self.pool = Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.RLock()

        # Configuração otimizada do engine
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            pool_pre_ping=True,
            pool_recycle=1800,  # 30 minutos
            connect_args={
                "timeout": 60,
                "check_same_thread": False,
            },
            echo=False,
        )

        # Aplicar otimizações SQLite após conexão
        from sqlalchemy import event

        event.listen(self.engine, "connect", self._apply_sqlite_optimizations)

        self.Session = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,  # Controle manual de flush
        )

        # Pré-criar algumas sessões
        self._initialize_pool()

    def _apply_sqlite_optimizations(self, dbapi_connection, _connection_record):
        """Aplica otimizações SQLite após a conexão."""
        cursor = dbapi_connection.cursor()

        optimizations = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -128000",  # 128MB cache
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 536870912",  # 512MB memory-mapped
            "PRAGMA busy_timeout = 60000",  # 60 segundos
            "PRAGMA wal_autocheckpoint = 1000",
        ]

        for pragma in optimizations:
            try:
                cursor.execute(pragma)
            except (sqlite3.Error, SQLAlchemyError) as e:
                logging.error("Falha ao aplicar %s: %s", pragma, e)

        cursor.close()

    def _initialize_pool(self):
        """Inicializa o pool com conexões."""
        try:
            for _ in range(min(3, self.max_connections)):  # Inicia com 3 conexões
                session = self.Session()
                self.pool.put(session)
                self.active_connections += 1
                logging.debug("Sessão adicionada ao pool")
        except SQLAlchemyError as e:
            logging.error("Erro ao inicializar pool de conexões: %s", e)

    @contextmanager
    def get_session(self, timeout=30):
        """
        Context manager para obter uma sessão do pool.

        Args:
            timeout: Tempo limite para obter sessão em segundos
        """
        session = None
        try:
            # Tentar obter sessão existente do pool
            try:
                session = self.pool.get(timeout=timeout)
                logging.debug("Sessão obtida do pool")
            except Empty:
                # Se pool vazio, criar nova sessão se permitido
                with self.lock:
                    if self.active_connections < self.max_connections:
                        session = self.Session()
                        self.active_connections += 1
                        logging.debug("Nova sessão criada")
                    else:
                        # Pool cheio, aguardar
                        session = self.pool.get(timeout=timeout)

            if session is None:
                raise SQLAlchemyError("Não foi possível obter sessão do pool")

            # Verificar se sessão ainda é válida
            try:
                session.execute("SELECT 1")
            except SQLAlchemyError:
                # Sessão inválida, criar nova
                session.close()
                session = self.Session()
                logging.debug("Sessão recriada devido a erro")

            yield session

            # Commit automático se não houver erros
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
                        self.pool.put(session)
                        logging.debug("Sessão retornada ao pool")
                    else:
                        session.close()
                        with self.lock:
                            self.active_connections -= 1
                        logging.debug("Sessão fechada (pool cheio)")
                except SQLAlchemyError as e:
                    logging.error("Erro ao retornar sessão ao pool: %s", e)
                    session.close()
                    with self.lock:
                        self.active_connections -= 1

    def get_stats(self):
        """Retorna estatísticas do pool."""
        return {
            "pool_size": self.pool.qsize(),
            "active_connections": self.active_connections,
            "max_connections": self.max_connections,
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
                        # Implementar lógica de update
                        pass

                session.flush()  # Enviar para DB mas não commitar ainda
                operations_count = len(self.pending_operations)
                self.pending_operations.clear()
                logging.debug(
                    "Lote de %s operações processado", operations_count
                )

        except SQLAlchemyError as e:
            logging.error("Erro ao processar lote: %s", e)
            self.pending_operations.clear()

    def force_process(self):
        """Força processamento do lote atual."""
        with self.lock:
            self._process_batch()


# Instância global do processador de lotes
batch_processor = BatchProcessor()
