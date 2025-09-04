"""
Módulo para recuperação e desbloqueio de banco de dados SQLite.
Implementa estratégias seguras para lidar com bancos bloqueados.
"""

import json
import logging
import shutil
import sqlite3
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Timeouts padronizados por contexto de operação
DATABASE_TIMEOUTS = {
    "quick_check": 2.0,  # Verificações rápidas de status
    "normal_operation": 5.0,  # Operações normais de leitura/escrita
    "recovery_operation": 15.0,  # Operações de recovery e checkpoint
    "emergency_recovery": 30.0,  # Recovery de emergência com verificação completa
}

# Import opcional do psutil - removido conforme análise
# A funcionalidade será implementada usando ferramentas nativas do Python


def _parse_windows_processes(result_stdout: str) -> List[Dict[str, str]]:
    """Extrai processos Python da saída do tasklist do Windows."""
    processes = []
    lines = result_stdout.split("\n")[3:]  # Pula cabeçalho

    for line in lines:
        if not (line.strip() and "python" in line.lower()):
            continue

        parts = line.split()
        if len(parts) >= 2:
            processes.append(
                {
                    "name": parts[0],
                    "pid": parts[1],
                    "memory": parts[4] if len(parts) > 4 else "N/A",
                }
            )

    return processes


def _parse_unix_processes(result_stdout: str) -> List[Dict[str, str]]:
    """Extrai processos Python da saída do ps no Unix/Linux."""
    processes = []
    lines = result_stdout.split("\n")[1:]  # Pula cabeçalho

    for line in lines:
        if not ("python" in line.lower() and "tabela-de-dobra" in line):
            continue

        parts = line.split()
        if len(parts) >= 11:
            processes.append(
                {
                    "name": "python",
                    "pid": parts[1],
                    "memory": parts[3],
                    "command": " ".join(parts[10:]),
                }
            )

    return processes


def get_database_processes():
    """
    Monitora processos que podem estar usando o banco de dados.
    Implementação nativa sem dependência do psutil.
    """
    processes = []

    try:
        if sys.platform == "win32":
            # Windows: usa tasklist para encontrar processos Python
            result = subprocess.run(
                ["tasklist", "/fi", "imagename eq python*"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                processes = _parse_windows_processes(result.stdout)
        else:
            # Unix/Linux: usa ps para encontrar processos Python
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=5, check=False
            )
            if result.returncode == 0:
                processes = _parse_unix_processes(result.stdout)

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        # Se falhar, retorna lista vazia - não é crítico
        pass

    return processes


class DatabaseUnlocker:
    """Utilitário para desbloquear bancos SQLite forçadamente com segurança."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.wal_path = Path(f"{db_path}-wal")
        self.shm_path = Path(f"{db_path}-shm")
        self.backup_dir = Path("backups/database")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Logs de auditoria
        self.audit_log = Path("logs/database_recovery.log")
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)

        # Configurar logger específico para recovery
        self._setup_recovery_logger()

    def _setup_recovery_logger(self):
        """Configura logger específico para operações de recovery."""
        self.recovery_logger = logging.getLogger("database_recovery")
        self.recovery_logger.setLevel(logging.INFO)

        if not self.recovery_logger.handlers:
            handler = logging.FileHandler(self.audit_log, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.recovery_logger.addHandler(handler)

    def _check_concurrent_processes(self):
        """Verifica se há outros processos que podem estar usando o banco."""
        processes = get_database_processes()
        if processes:
            self.recovery_logger.info("Processos Python detectados: %d", len(processes))
            for proc in processes[:3]:  # Log apenas os primeiros 3
                self.recovery_logger.info(
                    "Processo: PID=%s, Nome=%s, Memória=%s",
                    proc.get("pid", "N/A"),
                    proc.get("name", "N/A"),
                    proc.get("memory", "N/A"),
                )
        return len(processes)

    def create_emergency_backup(self) -> Optional[Path]:
        """Cria backup de emergência antes de tentar desbloqueio."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"emergency_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_name

            self.recovery_logger.info("Criando backup de emergência: %s", backup_path)

            # Tenta fazer backup mesmo com banco bloqueado
            try:
                shutil.copy2(self.db_path, backup_path)

                # Verifica integridade do backup
                if self._verify_backup_integrity(backup_path):
                    self.recovery_logger.info(
                        "Backup criado com sucesso: %s", backup_path
                    )
                    return backup_path

                self.recovery_logger.error(
                    "Backup criado mas com problemas de integridade"
                )
                return None

            except (OSError, PermissionError, IOError) as e:
                self.recovery_logger.error("Falha ao criar backup: %s", e)
                return None

        except (OSError, ValueError) as e:
            self.recovery_logger.error("Erro no processo de backup: %s", e)
            return None

    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verifica integridade do backup criado."""
        try:
            conn = sqlite3.connect(
                backup_path, timeout=DATABASE_TIMEOUTS["normal_operation"]
            )
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()

            return result and result[0] == "ok"

        except (sqlite3.Error, OSError):
            return False

    def force_unlock(self, create_backup: bool = True) -> bool:
        """
        Tenta desbloquear o banco usando várias estratégias.

        Args:
            create_backup: Se True, cria backup antes de tentar desbloqueio
        """
        self.recovery_logger.info("Iniciando processo de desbloqueio: %s", self.db_path)

        # Verifica processos concorrentes
        concurrent_processes = self._check_concurrent_processes()
        if concurrent_processes > 1:
            self.recovery_logger.warning(
                "Detectados %d processos Python - possível concorrência",
                concurrent_processes,
            )

        # Cria backup se solicitado
        backup_path = None
        if create_backup:
            backup_path = self.create_emergency_backup()
            if not backup_path:
                self.recovery_logger.warning("Continuando sem backup - RISCO!")

        strategies = [
            ("Desbloqueio Imediato", self._try_immediate_unlock),
            ("Checkpoint Recovery", self._try_checkpoint_recovery),
            ("Limpeza WAL/SHM", self._try_wal_cleanup),
            ("Recovery de Emergência", self._try_emergency_recovery),
        ]

        for strategy_name, strategy_func in strategies:
            self.recovery_logger.info("Executando estratégia: %s", strategy_name)
            try:
                if strategy_func():
                    self.recovery_logger.info(
                        "Banco desbloqueado com: %s", strategy_name
                    )
                    self._log_unlock_success(strategy_name, backup_path)
                    return True

            except (sqlite3.Error, OSError, ValueError) as e:
                self.recovery_logger.error(
                    "Estratégia '%s' falhou: %s", strategy_name, e
                )
                continue

        self.recovery_logger.error("Todas as estratégias de desbloqueio falharam")
        return False

    def _try_immediate_unlock(self) -> bool:
        """Tenta desbloqueio imediato com PRAGMA."""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=DATABASE_TIMEOUTS["quick_check"],
                isolation_level=None,
            )

            cursor = conn.cursor()

            # Força rollback de transações pendentes
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("ROLLBACK;")

            # Verifica se consegue fazer uma operação simples
            cursor.execute("SELECT 1;")
            cursor.fetchone()

            conn.close()
            return True

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                return False
            raise

    def _try_checkpoint_recovery(self) -> bool:
        """Tenta recovery via WAL checkpoint."""
        try:
            conn = sqlite3.connect(
                self.db_path, timeout=DATABASE_TIMEOUTS["recovery_operation"]
            )
            cursor = conn.cursor()

            # Força checkpoint do WAL
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            result = cursor.fetchone()

            # Verifica se checkpoint foi bem-sucedido
            success = result and result[0] == 0

            conn.close()
            return success

        except (sqlite3.Error, OSError):
            return False

    def _try_wal_cleanup(self) -> bool:
        """Remove arquivos WAL e SHM para forçar desbloqueio."""
        try:
            backup_suffix = f".backup_{int(time.time())}"
            files_moved = []

            # Move arquivos WAL/SHM ao invés de deletar
            for file_path in [self.wal_path, self.shm_path]:
                if file_path.exists():
                    backup_path = Path(f"{file_path}{backup_suffix}")
                    file_path.rename(backup_path)
                    files_moved.append((file_path, backup_path))
                    self.recovery_logger.info(
                        "Arquivo movido: %s -> %s", file_path, backup_path
                    )

            if files_moved:
                time.sleep(2)  # Aguarda liberação dos recursos

                if self._test_database_access():
                    return True

                # Restaura arquivos se não funcionou
                for original, backup in files_moved:
                    try:
                        backup.rename(original)
                    except (OSError, PermissionError):
                        pass

            return False

        except (OSError, PermissionError, ValueError) as e:
            self.recovery_logger.error("Erro na limpeza WAL/SHM: %s", e)
            return False

    def _try_emergency_recovery(self) -> bool:
        """Estratégia de emergência com verificação de integridade."""
        try:
            # Tenta abrir em modo recovery
            conn = sqlite3.connect(
                f"file:{self.db_path}?mode=rwc",
                uri=True,
                timeout=DATABASE_TIMEOUTS["emergency_recovery"],
            )

            cursor = conn.cursor()

            # Executa verificação de integridade
            cursor.execute("PRAGMA integrity_check;")
            integrity_result = cursor.fetchall()

            success = integrity_result and integrity_result[0][0] == "ok"

            if success:
                self.recovery_logger.info("Integrity check passou - banco recuperado")
            else:
                self.recovery_logger.error(
                    "Integrity check falhou: %s", integrity_result
                )

            conn.close()
            return success

        except (sqlite3.Error, OSError) as e:
            self.recovery_logger.error("Recovery de emergência falhou: %s", e)
            return False

    def _test_database_access(self) -> bool:
        """Testa se o banco está acessível."""
        try:
            conn = sqlite3.connect(
                self.db_path, timeout=DATABASE_TIMEOUTS["quick_check"]
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            conn.close()
            return True
        except (sqlite3.Error, OSError):
            return False

    def _log_unlock_success(self, strategy: str, backup_path: Optional[Path]):
        """Log detalhado do sucesso do desbloqueio para auditoria."""
        audit_info = {
            "timestamp": datetime.now().isoformat(),
            "database_path": str(self.db_path),
            "strategy_used": strategy,
            "backup_created": str(backup_path) if backup_path else None,
            "status": "SUCCESS",
        }

        self.recovery_logger.info(
            "AUDITORIA - Desbloqueio: %s", json.dumps(audit_info, indent=2)
        )


class DatabaseLockMonitor:
    """Monitor para rastrear frequência de bloqueios do banco."""

    def __init__(self):
        self.lock_events_file = Path("logs/database_locks.json")
        self.lock_events_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock_events: List[Dict] = self._load_lock_events()

    def _load_lock_events(self) -> List[Dict]:
        """Carrega histórico de eventos de bloqueio."""
        try:
            if self.lock_events_file.exists():
                with open(self.lock_events_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError, ValueError):
            pass
        return []

    def _save_lock_events(self):
        """Salva eventos de bloqueio."""
        try:
            with open(self.lock_events_file, "w", encoding="utf-8") as f:
                json.dump(self.lock_events, f, indent=2, ensure_ascii=False)
        except (OSError, ValueError) as e:
            logging.error("Erro ao salvar eventos de bloqueio: %s", e)

    def record_lock_event(
        self, operation: str, duration: float, resolved: bool = False
    ):
        """Registra um evento de bloqueio."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_seconds": duration,
            "resolved": resolved,
            "severity": self._calculate_severity(duration),
        }

        self.lock_events.append(event)

        # Mantém apenas últimos 1000 eventos
        if len(self.lock_events) > 1000:
            self.lock_events = self.lock_events[-1000:]

        self._save_lock_events()

        # Log do evento
        logging.warning(
            "BLOQUEIO DETECTADO - Operação: %s, Duração: %.2fs, Resolvido: %s",
            operation,
            duration,
            resolved,
        )

    def _calculate_severity(self, duration: float) -> str:
        """Calcula severidade baseada na duração do bloqueio."""
        if duration < 1:
            return "LOW"
        if duration < 5:
            return "MEDIUM"
        if duration < 15:
            return "HIGH"
        return "CRITICAL"

    def get_lock_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Retorna estatísticas de bloqueios nas últimas N horas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event
            for event in self.lock_events
            if datetime.fromisoformat(event["timestamp"]) > cutoff_time
        ]

        if not recent_events:
            return {
                "total_locks": 0,
                "average_duration": 0,
                "severity_distribution": {},
            }

        total_locks = len(recent_events)
        avg_duration = sum(e["duration_seconds"] for e in recent_events) / total_locks

        severity_dist = {}
        for event in recent_events:
            severity = event["severity"]
            severity_dist[severity] = severity_dist.get(severity, 0) + 1

        return {
            "total_locks": total_locks,
            "average_duration": avg_duration,
            "severity_distribution": severity_dist,
            "resolved_percentage": (
                sum(1 for e in recent_events if e["resolved"]) / total_locks * 100
            ),
        }

    def should_alert(self) -> bool:
        """Determina se deve alertar sobre alta frequência de bloqueios."""
        stats = self.get_lock_statistics(hours=1)  # Última hora

        # Alerta se mais de 5 bloqueios na última hora ou bloqueios críticos
        return (
            stats["total_locks"] > 5
            or stats.get("severity_distribution", {}).get("CRITICAL", 0) > 0
        )


# Instância global do monitor
lock_monitor = DatabaseLockMonitor()


@contextmanager
def resilient_database_connection(db_path: str, operation_name: str = "unknown"):
    """Context manager que monitora e tenta resolver bloqueios automaticamente."""
    start_time = time.time()
    unlocker = DatabaseUnlocker(db_path)

    try:
        conn = sqlite3.connect(db_path, timeout=DATABASE_TIMEOUTS["recovery_operation"])
        yield conn
        conn.close()

    except sqlite3.OperationalError as e:
        duration = time.time() - start_time

        if "database is locked" in str(e).lower():
            # Registra o bloqueio
            lock_monitor.record_lock_event(operation_name, duration, resolved=False)

            # Tenta desbloqueio apenas para operações críticas
            if operation_name in ["initialization", "critical_read", "critical_write"]:
                logging.warning(
                    "Tentando desbloqueio automático para operação crítica: %s",
                    operation_name,
                )

                if unlocker.force_unlock(create_backup=True):
                    lock_monitor.record_lock_event(
                        operation_name, duration, resolved=True
                    )

                    # Tenta novamente após desbloqueio
                    conn = sqlite3.connect(
                        db_path, timeout=DATABASE_TIMEOUTS["normal_operation"]
                    )
                    yield conn
                    conn.close()
                    return

            # Se não conseguiu resolver, propaga o erro
            raise

        raise
