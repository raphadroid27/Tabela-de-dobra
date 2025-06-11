"""
Otimizações específicas para SQLite incluindo índices, PRAGMA e cache de consultas.
"""
import time
from sqlalchemy.engine import Engine
from sqlalchemy import event, text

# Importar engine do banco de dados
try:
    from src.utils.banco_dados import engine
except ImportError:
    # Fallback se não conseguir importar
    engine = None


class SQLiteOptimizer:
    """Otimizador específico para banco SQLite."""
    
    def __init__(self, engine):
        self.engine = engine
        self._applied_optimizations = set()
    
    def apply_pragma_optimizations(self):
        """Aplica otimizações PRAGMA do SQLite."""
        if 'pragma' in self._applied_optimizations:
            return
        
        optimizations = [
            # Cache de páginas em memória (64MB)
            "PRAGMA cache_size = -65536;",
            
            # Journal mode WAL para melhor concorrência
            "PRAGMA journal_mode = WAL;",
            
            # Synchronous NORMAL para melhor performance
            "PRAGMA synchronous = NORMAL;",
            
            # Timeout para lock
            "PRAGMA busy_timeout = 5000;",
            
            # Otimização de memória
            "PRAGMA temp_store = MEMORY;",
            
            # Análise automática de estatísticas
            "PRAGMA automatic_index = ON;",
            
            # Checkpoint automático
            "PRAGMA wal_autocheckpoint = 1000;",
            
            # Otimização de I/O
            "PRAGMA mmap_size = 268435456;"  # 256MB
        ]
        
        try:
            with self.engine.connect() as conn:
                for pragma in optimizations:
                    conn.execute(text(pragma))
                conn.commit()
            
            self._applied_optimizations.add('pragma')
            print("✅ Otimizações PRAGMA SQLite aplicadas")
            
        except Exception as e:
            print(f"❌ Erro ao aplicar PRAGMA: {e}")
    
    def create_composite_indexes(self):
        """Cria índices compostos para melhorar performance de consultas."""
        if 'indexes' in self._applied_optimizations:
            return
        
        indexes = [
            # Índice composto para busca de deduções (consulta mais comum)
            "CREATE INDEX IF NOT EXISTS idx_deducao_lookup ON deducao(material_id, espessura_id, canal_id);",
            
            # Índice para espessuras por material
            "CREATE INDEX IF NOT EXISTS idx_espessura_material ON deducao(material_id, espessura_id);",
            
            # Índice para canais por material e espessura
            "CREATE INDEX IF NOT EXISTS idx_canal_material_esp ON deducao(material_id, espessura_id, canal_id);",
            
            # Índices individuais para ordenação
            "CREATE INDEX IF NOT EXISTS idx_material_nome ON material(nome);",
            "CREATE INDEX IF NOT EXISTS idx_espessura_valor ON espessura(valor);",
            "CREATE INDEX IF NOT EXISTS idx_canal_valor ON canal(valor);",
            
            # Índice para logs por data
            "CREATE INDEX IF NOT EXISTS idx_log_data ON log(data_hora);",
            
            # Índice para usuários ativos
            "CREATE INDEX IF NOT EXISTS idx_usuario_ativo ON usuario(ativo);"
        ]
        
        try:
            with self.engine.connect() as conn:
                for index_sql in indexes:
                    conn.execute(text(index_sql))
                conn.commit()
            
            self._applied_optimizations.add('indexes')
            print("✅ Índices compostos criados")
            
        except Exception as e:
            print(f"❌ Erro ao criar índices: {e}")
    
    def analyze_database(self):
        """Executa ANALYZE para atualizar estatísticas de consulta."""
        if 'analyze' in self._applied_optimizations:
            return
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("ANALYZE;"))
                conn.commit()
            
            self._applied_optimizations.add('analyze')
            print("✅ ANALYZE executado - estatísticas atualizadas")
            
        except Exception as e:
            print(f"❌ Erro ao executar ANALYZE: {e}")
    
    def vacuum_database(self, force: bool = False):
        """
        Executa VACUUM para otimizar arquivo do banco.
        
        Args:
            force: Se True, executa mesmo se já foi feito recentemente
        """
        if 'vacuum' in self._applied_optimizations and not force:
            return
        
        try:
            # VACUUM precisa ser executado fora de transação
            with self.engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text("VACUUM;"))
            
            self._applied_optimizations.add('vacuum')
            print("✅ VACUUM executado - banco otimizado")
            
        except Exception as e:
            print(f"❌ Erro ao executar VACUUM: {e}")
    
    def get_database_stats(self) -> dict:
        """Retorna estatísticas do banco de dados."""
        try:
            with self.engine.connect() as conn:
                # Informações sobre tamanho
                page_count = conn.execute(text("PRAGMA page_count;")).scalar()
                page_size = conn.execute(text("PRAGMA page_size;")).scalar()
                
                # Informações sobre cache
                cache_size = conn.execute(text("PRAGMA cache_size;")).scalar()
                
                # Informações sobre WAL
                wal_mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
                
                # Contadores de tabelas
                tables = {}
                table_names = ['material', 'espessura', 'canal', 'deducao', 'usuario', 'log']
                
                for table in table_names:
                    try:
                        count = conn.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
                        tables[table] = count
                    except:
                        tables[table] = 0
                
                return {
                    'database_size_mb': (page_count * page_size) / (1024 * 1024),
                    'page_count': page_count,
                    'page_size': page_size,
                    'cache_size_mb': abs(cache_size) / 1024 if cache_size < 0 else cache_size,
                    'journal_mode': wal_mode,
                    'table_counts': tables,
                    'optimizations_applied': list(self._applied_optimizations)
                }
                
        except Exception as e:
            print(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def apply_all_optimizations(self):
        """Aplica todas as otimizações disponíveis."""
        print("🚀 Aplicando otimizações SQLite...")
        
        self.apply_pragma_optimizations()
        self.create_composite_indexes()
        self.analyze_database()
        
        # VACUUM só em caso específico (arquivo grande)
        stats = self.get_database_stats()
        if stats.get('database_size_mb', 0) > 10:  # Se maior que 10MB
            self.vacuum_database()
        
        print("✅ Todas as otimizações SQLite aplicadas")
        return stats


# Instância global do otimizador
sqlite_optimizer = SQLiteOptimizer(engine) if engine else None


# Event listener para aplicar otimizações na conexão
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Aplica PRAGMA básicos em cada nova conexão."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        
        # Otimizações básicas por conexão
        basic_pragmas = [
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -8192",  # 8MB por conexão
            "PRAGMA temp_store = MEMORY",
            "PRAGMA busy_timeout = 5000"
        ]
        
        for pragma in basic_pragmas:
            try:
                cursor.execute(pragma)
            except:
                pass  # Ignorar erros em PRAGMA
        
        cursor.close()


def optimize_database():
    """Função conveniente para otimizar banco de dados."""
    if sqlite_optimizer:
        return sqlite_optimizer.apply_all_optimizations()
    return {}


def get_db_performance_stats():
    """Função conveniente para obter estatísticas de performance."""
    if sqlite_optimizer:
        return sqlite_optimizer.get_database_stats()
    return {}


class QueryPerformanceMonitor:
    """Monitor de performance de consultas."""
    
    def __init__(self):
        self.slow_queries = []
        self.query_times = {}
        self.slow_threshold = 0.1  # 100ms
    
    def log_query(self, query: str, execution_time: float):
        """Registra tempo de execução de consulta."""
        if execution_time > self.slow_threshold:
            self.slow_queries.append({
                'query': query,
                'time': execution_time,
                'timestamp': time.time()
            })
            
            # Manter apenas últimas 50 consultas lentas
            if len(self.slow_queries) > 50:
                self.slow_queries = self.slow_queries[-50:]
    
    def get_slow_queries(self):
        """Retorna consultas lentas registradas."""
        return self.slow_queries
    
    def clear_logs(self):
        """Limpa logs de consultas."""
        self.slow_queries.clear()
        self.query_times.clear()


# Monitor global de performance
query_monitor = QueryPerformanceMonitor()


# Decorator para monitorar consultas
def monitor_query_performance(func):
    """Decorator para monitorar performance de consultas."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            query_monitor.log_query(func.__name__, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            query_monitor.log_query(f"{func.__name__} (ERROR)", execution_time)
            raise
    return wrapper
