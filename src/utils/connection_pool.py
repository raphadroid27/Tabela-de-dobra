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


class PoolConfig:
    """Configuração do pool de conexões."""

    def __init__(self, max_connections=20, db_path=None):
        self.max_connections = max_connections
        self.db_path = db_path or DB_PATH
        self.timeout = 90
        self.pool_recycle = 1800
        self.max_overflow = 5


class PoolStats:
    """Estatísticas do pool de conexões."""

    def __init__(self):
        self.total_requests = 0
        self.pool_hits = 0
        self.pool_misses = 0
        self.errors = 0

    def record_request(self):
        """Registra uma nova requisição."""
        self.total_requests += 1

    def record_hit(self):
        """Registra um cache hit."""
        self.pool_hits += 1

    def record_miss(self):
        """Registra um cache miss."""
        self.pool_misses += 1

    def record_error(self):
        """Registra um erro."""
        self.errors += 1

    def get_stats_dict(self):
        """Retorna estatísticas como dicionário."""
        return {
            "total_requests": self.total_requests,
            "pool_hits": self.pool_hits,
            "pool_misses": self.pool_misses,
            "errors": self.errors,
            "hit_ratio": self.pool_hits / max(1, self.total_requests) * 100,
            "error_ratio": self.errors / max(1, self.total_requests) * 100,
        }


class SQLiteConnectionPool:
    """Pool de conexões SQLite otimizado para acesso em rede."""

    def __init__(self, max_connections=20, db_path=None):
        self.config = PoolConfig(max_connections, db_path)
        self.pool = Queue(maxsize=self.config.max_connections)
        self.active_connections = 0
        self.lock = threading.RLock()
        self.stats = PoolStats()

        # Configurar engine
        self.engine = self._create_engine()
        self.db_session = self._create_session_maker()

        # Pré-criar algumas sessões
        self._initialize_pool()

    def _create_engine(self):
        """Cria e configura o engine SQLite."""
        engine = create_engine(
            f"sqlite:///{self.config.db_path}",
            pool_pre_ping=True,
            pool_recycle=self.config.pool_recycle,
            pool_size=self.config.max_connections,
            max_overflow=self.config.max_overflow,
            connect_args={
                "timeout": self.config.timeout,
                "check_same_thread": False,
            },
            echo=False,
        )

        event.listen(engine, "connect", self._apply_sqlite_optimizations)
        return engine

    def _create_session_maker(self):
        """Cria o session maker."""
        return sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )

    def _apply_sqlite_optimizations(self, dbapi_connection, _connection_record):
        """Aplica otimizações SQLite após a conexão para múltiplos usuários."""
        cursor = dbapi_connection.cursor()

        optimizations = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -256000",  # 256MB cache por conexão
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 1073741824",  # 1GB memory-mapped I/O
            "PRAGMA busy_timeout = 90000",  # 90s timeout para locks
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
            initial_connections = min(8, self.config.max_connections)
            for _ in range(initial_connections):
                session = self.db_session()
                self.pool.put(session)
                self.active_connections += 1
                logging.debug(
                    "Sessão adicionada ao pool (%d/%d)",
                    self.active_connections,
                    self.config.max_connections,
                )
        except SQLAlchemyError as e:
            logging.error("Erro ao inicializar pool de conexões: %s", e)

    def _try_get_session_from_pool(self, timeout):
        """Tenta obter uma sessão do pool."""
        try:
            session = self.pool.get(timeout=timeout)
            self.stats.record_hit()
            logging.debug("Sessão obtida do pool")
            return session
        except Empty:
            self.stats.record_miss()
            return None

    def _create_new_session_if_allowed(self, timeout):
        """Cria nova sessão se permitido, senão aguarda."""
        with self.lock:
            if self.active_connections < self.config.max_connections:
                session = self.db_session()
                self.active_connections += 1
                logging.debug(
                    "Nova sessão criada (%d/%d)",
                    self.active_connections,
                    self.config.max_connections,
                )
                return session

            # Pool cheio, aguardar com timeout reduzido
            return self.pool.get(timeout=timeout // 2)

    def _validate_session(self, session):
        """Valida se a sessão ainda está funcionando."""
        try:
            session.execute("SELECT 1")
            return True
        except SQLAlchemyError:
            if session:
                session.close()
            return False

    def _handle_session_error(self, session, attempt, retry_count, e):
        """Lida com erros na obtenção de sessão."""
        if session:
            try:
                session.close()
            except SQLAlchemyError:
                pass

        if attempt < retry_count - 1:
            wait_time = (attempt + 1) * 0.5  # Backoff progressivo
            logging.warning(
                "Erro na tentativa %d, aguardando %.1fs: %s", attempt + 1, wait_time, e
            )
            time.sleep(wait_time)
        else:
            logging.error("Falha após %d tentativas: %s", retry_count, e)
            raise e

    def _get_valid_session(self, timeout, attempt):
        """Obtém uma sessão válida do pool ou cria uma nova."""
        # Tentar obter sessão existente do pool
        session = self._try_get_session_from_pool(timeout)

        if session is None:
            # Se pool vazio, criar nova sessão se permitido
            session = self._create_new_session_if_allowed(timeout)

        if session is None:
            raise SQLAlchemyError("Não foi possível obter sessão do pool")

        # Verificar se sessão ainda é válida
        if self._validate_session(session):
            return session

        # Sessão inválida, recriar
        session = self.db_session()
        logging.debug("Sessão recriada devido a erro (tentativa %d)", attempt + 1)
        return session

    @contextmanager
    def get_session(self, timeout=45, retry_count=3):
        """Context manager para obter uma sessão do pool com retry automático."""
        session = None

        for attempt in range(retry_count):
            try:
                self.stats.record_request()
                session = self._get_valid_session(timeout, attempt)
                break

            except (SQLAlchemyError, Empty) as e:
                self.stats.record_error()
                self._handle_session_error(session, attempt, retry_count, e)
                session = None
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
            "max_connections": self.config.max_connections,
            **self.stats.get_stats_dict(),
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
