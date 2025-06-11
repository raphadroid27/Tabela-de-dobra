"""
Script de teste de performance para validar as otimizações implementadas.
"""
import time
import os
import sys
from typing import Dict, List
from functools import wraps
from contextlib import contextmanager

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.cache import cache_manager, get_materiais_cached, get_espessuras_cached, get_canais_cached
from src.utils.banco_dados import session
from src.models.models import Material, Espessura, Canal, Deducao

def measure_time(func):
    """Decorator para medir tempo de execução."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # em ms
        return result, execution_time
    return wrapper

class PerformanceTest:
    """Classe para testes de performance."""
    
    def __init__(self):
        self.results = {}
    
    @measure_time
    def test_direct_db_query_materials(self, iterations: int = 10) -> List:
        """Teste de consulta direta ao banco para materiais."""
        results = []
        for _ in range(iterations):
            materials = session.query(Material).order_by(Material.nome).all()
            results.extend(materials)
        return results
    
    @measure_time
    def test_cached_materials(self, iterations: int = 10) -> List:
        """Teste de consulta com cache para materiais."""
        results = []
        for _ in range(iterations):
            materials = get_materiais_cached()
            results.extend(materials)
        return results
    
    @measure_time
    def test_direct_db_query_espessuras(self, iterations: int = 10) -> List:
        """Teste de consulta direta ao banco para espessuras."""
        results = []
        for _ in range(iterations):
            espessuras = session.query(Espessura).order_by(Espessura.valor).all()
            results.extend(espessuras)
        return results
    
    @measure_time
    def test_cached_espessuras(self, iterations: int = 10) -> List:
        """Teste de consulta com cache para espessuras."""
        results = []
        for _ in range(iterations):
            espessuras = get_espessuras_cached()
            results.extend(espessuras)
        return results
    
    @measure_time
    def test_direct_db_query_canais(self, iterations: int = 10) -> List:
        """Teste de consulta direta ao banco para canais."""
        results = []
        for _ in range(iterations):
            canais = session.query(Canal).all()
            results.extend(canais)
        return results
    
    @measure_time
    def test_cached_canais(self, iterations: int = 10) -> List:
        """Teste de consulta com cache para canais."""
        results = []
        for _ in range(iterations):
            canais = get_canais_cached()
            results.extend(canais)
        return results
    
    @measure_time
    def test_complex_query_direct(self, iterations: int = 5) -> List:
        """Teste de consulta complexa direta ao banco."""
        results = []
        for _ in range(iterations):
            # Simular consulta complexa com JOINs
            deducoes = session.query(Deducao).join(Material).join(Espessura).join(Canal).filter(
                Material.nome.in_(['CARBONO', 'INOX']),
                Espessura.valor >= 1.0
            ).all()
            results.extend(deducoes)
        return results
    
    @measure_time
    def test_complex_query_cached(self, iterations: int = 5) -> List:
        """Teste de consulta complexa usando cache."""
        results = []
        for _ in range(iterations):
            # Simular mesma consulta usando dados cached
            materiais = get_materiais_cached()
            espessuras = get_espessuras_cached()
            deducoes = cache_manager.get_cached_data('deducoes')
            
            # Filtrar dados em memória
            materiais_filtrados = [m for m in materiais if m.nome in ['CARBONO', 'INOX']]
            espessuras_filtradas = [e for e in espessuras if e.valor >= 1.0]
            
            for d in deducoes:
                if (any(m.id == d.material_id for m in materiais_filtrados) and
                    any(e.id == d.espessura_id for e in espessuras_filtradas)):
                    results.append(d)
        return results
    
    def run_performance_tests(self):
        """Executa todos os testes de performance."""
        print("🚀 Iniciando Testes de Performance")
        print("=" * 50)
        
        iterations = 100  # Número de iterações para testes
        
        tests = [
            ("Materiais - Consulta Direta", self.test_direct_db_query_materials),
            ("Materiais - Cache", self.test_cached_materials),
            ("Espessuras - Consulta Direta", self.test_direct_db_query_espessuras),
            ("Espessuras - Cache", self.test_cached_espessuras),
            ("Canais - Consulta Direta", self.test_direct_db_query_canais),
            ("Canais - Cache", self.test_cached_canais),
            ("Consulta Complexa - Direta", self.test_complex_query_direct),
            ("Consulta Complexa - Cache", self.test_complex_query_cached),        ]
        
        for test_name, test_func in tests:
            print(f"\n📊 {test_name}")
            if "Complexa" in test_name:
                result, exec_time = test_func(5)  # Menos iterações para consultas complexas
            else:
                result, exec_time = test_func(iterations)
            
            print(f"⏱️  Tempo de execução: {exec_time:.2f} ms")
            print(f"📋 Registros processados: {len(result)}")
            
            self.results[test_name] = {
                'time': exec_time,
                'records': len(result)
            }
    
    def calculate_improvements(self):
        """Calcula as melhorias de performance."""
        print(f"\n📈 Análise de Melhorias de Performance")
        print("=" * 50)
        
        comparisons = [
            ("Materiais", "Materiais - Consulta Direta", "Materiais - Cache"),
            ("Espessuras", "Espessuras - Consulta Direta", "Espessuras - Cache"),
            ("Canais", "Canais - Consulta Direta", "Canais - Cache"),
            ("Consulta Complexa", "Consulta Complexa - Direta", "Consulta Complexa - Cache"),
        ]
        
        total_improvement = 0
        comparison_count = 0
        
        for category, direct_key, cached_key in comparisons:
            if direct_key in self.results and cached_key in self.results:
                direct_time = self.results[direct_key]['time']
                cached_time = self.results[cached_key]['time']
                
                if direct_time > 0:
                    improvement = ((direct_time - cached_time) / direct_time) * 100
                    total_improvement += improvement
                    comparison_count += 1
                    
                    print(f"\n🔍 {category}:")
                    print(f"   Consulta Direta: {direct_time:.2f} ms")
                    print(f"   Com Cache: {cached_time:.2f} ms")
                    print(f"   Melhoria: {improvement:.1f}%")
                    
                    if improvement > 0:
                        print(f"   ✅ Cache é {improvement:.1f}% mais rápido")
                    else:
                        print(f"   ⚠️  Cache é {abs(improvement):.1f}% mais lento")
        
        if comparison_count > 0:
            avg_improvement = total_improvement / comparison_count
            print(f"\n🎯 Melhoria Média de Performance: {avg_improvement:.1f}%")
        
        return self.results

def test_cache_invalidation():
    """Testa a invalidação de cache."""
    print(f"\n🔄 Teste de Invalidação de Cache")
    print("-" * 30)
    
    # Carregar cache inicial
    initial_materials = get_materiais_cached()
    print(f"📦 Cache inicial: {len(initial_materials)} materiais")
    
    # Invalidar cache
    cache_manager.invalidate_all()
    print("🧹 Cache invalidado")
    
    # Carregar cache novamente
    reloaded_materials = get_materiais_cached()
    print(f"🔄 Cache recarregado: {len(reloaded_materials)} materiais")
    
    # Verificar se os dados são iguais
    if len(initial_materials) == len(reloaded_materials):
        print("✅ Invalidação de cache funcionando corretamente")
    else:
        print("❌ Problema na invalidação de cache")

def main():
    """Função principal."""
    print("🧪 Suite de Testes de Performance - Tabela de Dobra")
    print("=" * 60)
    
    # Verificar se o banco de dados existe
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'tabela_de_dobra.db')
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    print(f"📊 Banco de dados encontrado: {db_path}")
    
    # Executar testes
    tester = PerformanceTest()
    
    try:
        # Testes de performance
        tester.run_performance_tests()
        
        # Análise de melhorias
        results = tester.calculate_improvements()
        
        # Teste de invalidação de cache
        test_cache_invalidation()
        
        print(f"\n🎉 Testes Concluídos com Sucesso!")
        print(f"📊 Resultados salvos internamente para análise")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
