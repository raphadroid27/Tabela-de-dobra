#!/usr/bin/env python3
"""
Script de Otimização Integrado - Tabela de Dobra

Este script é um orquestrador que aplica todas as otimizações de performance 
implementadas no projeto, fornecendo um relatório detalhado dos resultados.
"""

import os
import sys
import time
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("🚀 Script de Otimização Integrado - Tabela de Dobra")
print("Carregando módulos de otimização...")

# Lista de módulos opcionais
modules_loaded = {}

# Carregar cache de banco
try:
    from src.utils.cache import cache_manager
    modules_loaded['cache_banco'] = True
    print("✅ Cache de banco carregado")
except ImportError as e:
    modules_loaded['cache_banco'] = False
    print(f"❌ Cache de banco: {e}")

# Carregar cache de widgets
try:
    from src.utils.cache_widgets import cache_widget
    modules_loaded['cache_widgets'] = True
    print("✅ Cache de widgets carregado")
except ImportError as e:
    modules_loaded['cache_widgets'] = False
    print(f"❌ Cache de widgets: {e}")

# Carregar cache de calculos
try:
    from src.utils.cache_calculos import calculation_cache
    modules_loaded['cache_calculos'] = True
    print("✅ Cache de cálculos carregado")
except ImportError as e:
    modules_loaded['cache_calculos'] = False
    print(f"❌ Cache de cálculos: {e}")

# Carregar otimizador SQLite
try:
    from src.utils.otimizador_sqlite import optimize_database
    modules_loaded['sqlite'] = True
    print("✅ Otimizador SQLite carregado")
except ImportError as e:
    modules_loaded['sqlite'] = False
    print(f"❌ Otimizador SQLite: {e}")

# Carregar testes de performance
try:
    from scripts.testar_performance import executar_testes_performance
    modules_loaded['testes'] = True
    print("✅ Testes de performance carregados")
except ImportError as e:
    modules_loaded['testes'] = False
    print(f"❌ Testes de performance: {e}")


def executar_otimizacoes():
    """Executa otimizações disponíveis."""
    print("\n🔧 Aplicando otimizações disponíveis...")
    resultados = {}
    
    # Cache de banco
    if modules_loaded.get('cache_banco'):
        try:
            cache_manager.invalidate_cache()
            materiais = cache_manager.get_materiais()
            resultados['cache_banco'] = f"✅ Cache limpo, {len(materiais)} materiais carregados"
        except Exception as e:
            resultados['cache_banco'] = f"❌ Erro: {e}"
    else:
        resultados['cache_banco'] = "⏭️ Não disponível"
    
    # Cache de widgets
    if modules_loaded.get('cache_widgets'):
        try:
            cache_widget.limpar_cache()
            resultados['cache_widgets'] = "✅ Cache de widgets limpo"
        except Exception as e:
            resultados['cache_widgets'] = f"❌ Erro: {e}"
    else:
        resultados['cache_widgets'] = "⏭️ Não disponível"
    
    # Cache de cálculos
    if modules_loaded.get('cache_calculos'):
        try:
            calculation_cache.invalidate_all()
            resultados['cache_calculos'] = "✅ Cache de cálculos limpo"
        except Exception as e:
            resultados['cache_calculos'] = f"❌ Erro: {e}"
    else:
        resultados['cache_calculos'] = "⏭️ Não disponível"
    
    # SQLite
    if modules_loaded.get('sqlite'):
        try:
            stats = optimize_database()
            resultados['sqlite'] = f"✅ Banco otimizado - {stats.get('database_size_mb', 0):.1f}MB"
        except Exception as e:
            resultados['sqlite'] = f"❌ Erro: {e}"
    else:
        resultados['sqlite'] = "⏭️ Não disponível"
    
    return resultados


def executar_testes():
    """Executa testes de performance se disponível."""
    print("\n🧪 Executando testes de performance...")
    
    if not modules_loaded.get('testes'):
        print("❌ Testes de performance não disponíveis")
        return None
    
    try:
        resultado = executar_testes_performance()
        print("✅ Testes executados com sucesso")
        return resultado
    except Exception as e:
        print(f"❌ Erro nos testes: {e}")
        return None


def gerar_relatorio(resultados, testes=None):
    """Gera relatório final."""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE OTIMIZAÇÕES")
    print("=" * 60)
    
    print("\n🔧 Otimizações aplicadas:")
    for nome, resultado in resultados.items():
        print(f"   • {nome}: {resultado}")
    
    if testes:
        print("\n🧪 Resultados dos testes:")
        if isinstance(testes, dict):
            for categoria, dados in testes.items():
                print(f"   • {categoria}: {dados}")
    
    print("\n🚀 Otimização concluída!")
    print("=" * 60)


def main():
    """Função principal."""
    inicio = time.time()
    
    # Verificar argumentos
    apenas_testes = '--apenas-testes' in sys.argv or '-t' in sys.argv
    
    if apenas_testes:
        print("\n🧪 Modo: Apenas testes de performance")
        resultado_testes = executar_testes()
        gerar_relatorio({}, resultado_testes)
    else:
        print("\n⚡ Modo: Otimização completa")
        resultados = executar_otimizacoes()
        resultado_testes = executar_testes()
        gerar_relatorio(resultados, resultado_testes)
    
    tempo_total = time.time() - inicio
    print(f"\n⏱️ Tempo total: {tempo_total:.2f} segundos")
    print("✅ Script concluído!")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)