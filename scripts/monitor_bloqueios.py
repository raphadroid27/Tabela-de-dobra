"""
Monitor de bloqueios do banco de dados.
Script para acompanhar e analisar bloqueios do banco em tempo real.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.cache_manager import cache_manager


class DatabaseLockAnalyzer:
    """Analisador de bloqueios do banco de dados."""

    def __init__(self):
        self.lock_file = Path("logs/database_locks.json")
        self.recovery_log = Path("logs/database_recovery.log")

    def load_lock_events(self):
        """Carrega eventos de bloqueio."""
        try:
            if self.lock_file.exists():
                with open(self.lock_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Erro ao carregar eventos: {e}")
        return []

    def analyze_recent_locks(self, hours=1):
        """Analisa bloqueios recentes."""
        events = self.load_lock_events()
        if not events:
            return None

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event
            for event in events
            if datetime.fromisoformat(event["timestamp"]) > cutoff_time
        ]

        if not recent_events:
            return None

        # Estatísticas
        total_locks = len(recent_events)
        resolved_locks = sum(1 for e in recent_events if e.get("resolved", False))
        avg_duration = sum(e["duration_seconds"] for e in recent_events) / total_locks
        max_duration = max(e["duration_seconds"] for e in recent_events)

        # Operações mais problemáticas
        operations = {}
        for event in recent_events:
            op = event["operation"]
            if op not in operations:
                operations[op] = {"count": 0, "total_duration": 0}
            operations[op]["count"] += 1
            operations[op]["total_duration"] += event["duration_seconds"]

        # Ordena por frequência
        top_operations = sorted(
            operations.items(), key=lambda x: x[1]["count"], reverse=True
        )[:5]

        return {
            "total_locks": total_locks,
            "resolved_locks": resolved_locks,
            "resolution_rate": (
                (resolved_locks / total_locks * 100) if total_locks > 0 else 0
            ),
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "top_operations": top_operations,
            "severity_breakdown": self._analyze_severity(recent_events),
        }

    def _analyze_severity(self, events):
        """Analisa severidade dos bloqueios."""
        severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

        for event in events:
            severity = event.get("severity", "MEDIUM")
            severity_counts[severity] += 1

        return severity_counts

    def get_recovery_stats(self):
        """Analisa estatísticas de recovery."""
        if not self.recovery_log.exists():
            return None

        try:
            with open(self.recovery_log, "r", encoding="utf-8") as f:
                lines = f.readlines()

            recovery_events = []
            for line in lines:
                if "AUDITORIA - Desbloqueio" in line:
                    try:
                        # Extrai JSON da linha de log
                        json_part = line.split("AUDITORIA - Desbloqueio: ")[1]
                        event_data = json.loads(json_part)
                        recovery_events.append(event_data)
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue

            if not recovery_events:
                return None

            # Estatísticas de recovery
            strategies_used = {}
            for event in recovery_events:
                strategy = event.get("strategy_used", "unknown")
                strategies_used[strategy] = strategies_used.get(strategy, 0) + 1

            return {
                "total_recoveries": len(recovery_events),
                "strategies_used": strategies_used,
                "recent_recoveries": recovery_events[-5:],  # Últimos 5
            }

        except (OSError, UnicodeDecodeError, ValueError) as e:
            print(f"Erro ao analisar recovery stats: {e}")
            return None

    def print_dashboard(self):  # pylint: disable=too-many-branches,too-many-statements
        """Exibe dashboard de monitoramento."""
        print("\n" + "=" * 60)
        print("📊 DASHBOARD DE MONITORAMENTO - BANCO DE DADOS")
        print("=" * 60)
        print(f"🕒 Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Análise de bloqueios na última hora
        print("\n🔒 BLOQUEIOS NA ÚLTIMA HORA:")
        recent_analysis = self.analyze_recent_locks(hours=1)

        if recent_analysis:
            print(f"   Total de bloqueios: {recent_analysis['total_locks']}")
            print(f"   Bloqueios resolvidos: {recent_analysis['resolved_locks']}")
            print(f"   Taxa de resolução: {recent_analysis['resolution_rate']:.1f}%")
            print(f"   Duração média: {recent_analysis['avg_duration']:.2f}s")
            print(f"   Duração máxima: {recent_analysis['max_duration']:.2f}s")

            print("\n   📈 Severidade dos bloqueios:")
            for severity, count in recent_analysis["severity_breakdown"].items():
                if count > 0:
                    print(f"      {severity}: {count}")

            if recent_analysis["top_operations"]:
                print("\n   🎯 Operações mais problemáticas:")
                for op, stats in recent_analysis["top_operations"]:
                    avg_dur = stats["total_duration"] / stats["count"]
                    print(
                        f"      {op}: {stats['count']} bloqueios (média: {avg_dur:.2f}s)"
                    )
        else:
            print("   ✅ Nenhum bloqueio detectado na última hora")

        # Análise de bloqueios nas últimas 24 horas
        print("\n🔒 BLOQUEIOS NAS ÚLTIMAS 24 HORAS:")
        daily_analysis = self.analyze_recent_locks(hours=24)

        if daily_analysis:
            print(f"   Total de bloqueios: {daily_analysis['total_locks']}")
            print(f"   Taxa de resolução: {daily_analysis['resolution_rate']:.1f}%")
            print(f"   Duração média: {daily_analysis['avg_duration']:.2f}s")
        else:
            print("   ✅ Nenhum bloqueio detectado nas últimas 24 horas")

        # Estatísticas de recovery
        print("\n🔧 ESTATÍSTICAS DE RECOVERY:")
        recovery_stats = self.get_recovery_stats()

        if recovery_stats:
            print(f"   Total de recoveries: {recovery_stats['total_recoveries']}")

            if recovery_stats["strategies_used"]:
                print("\n   📋 Estratégias utilizadas:")
                for strategy, count in recovery_stats["strategies_used"].items():
                    print(f"      {strategy}: {count} vezes")
        else:
            print("   ℹ️ Nenhum recovery executado ainda")

        # Status do cache
        print("\n💾 STATUS DO CACHE:")
        try:
            cache_status = cache_manager.get_cache_status()

            print(f"   Inicializado: {'✅' if cache_status['initialized'] else '❌'}")
            print(f"   Total de entradas: {cache_status['total_entries']}")
            print(f"   Entradas válidas: {cache_status['valid_entries']}")
            print(f"   Entradas expiradas: {cache_status['invalid_entries']}")

            if cache_status["cache_types"]:
                print("\n   📊 Tipos de cache:")
                for cache_type, count in cache_status["cache_types"].items():
                    print(f"      {cache_type}: {count} entradas")

        except (ImportError, AttributeError, KeyError) as e:
            print(f"   ❌ Erro ao verificar cache: {e}")

        print("\n" + "=" * 60)


def monitor_continuous():
    """Monitora bloqueios continuamente."""
    analyzer = DatabaseLockAnalyzer()

    print("🚀 Iniciando monitoramento contínuo de bloqueios...")
    print("Pressione Ctrl+C para parar")

    try:
        while True:
            analyzer.print_dashboard()

            # Aguarda 30 segundos
            time.sleep(30)

            # Limpa tela (funciona no Windows e Unix)
            os.system("cls" if os.name == "nt" else "clear")

    except KeyboardInterrupt:
        print("\n\n👋 Monitoramento interrompido pelo usuário")


def show_single_report():
    """Exibe relatório único."""
    analyzer = DatabaseLockAnalyzer()
    analyzer.print_dashboard()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        monitor_continuous()
    else:
        show_single_report()
