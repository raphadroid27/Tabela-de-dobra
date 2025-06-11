"""
Script consolidado para adicionar dados de materiais ao banco de dados.
Substitui os scripts individuais add_carbono.py, add_inox.py e add_h14.py.

Este script oferece uma interface unificada para adicionar dados de diferentes materiais
com validação e tratamento de erros aprimorado.
"""
import sys
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Adicionar src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.cache import cache_manager


class DataManager:
    """Gerenciador de dados para inserção de materiais no banco."""
    
    def __init__(self, db_path: str = 'database/tabela_de_dobra.db'):
        """Inicializa o gerenciador com conexão ao banco."""
        self.engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def adicionar_material_dados(self, material_nome: str, dados: List[Dict[str, Any]]) -> bool:
        """
        Adiciona dados para um material específico.
        
        Args:
            material_nome: Nome do material
            dados: Lista de dicionários com dados de espessura, canal, dedução, etc.
            
        Returns:
            bool: True se adicionado com sucesso, False caso contrário
        """
        try:
            # Buscar ou criar material
            material_obj = self.session.query(Material).filter_by(nome=material_nome).first()
            if not material_obj:
                material_obj = Material(nome=material_nome)
                self.session.add(material_obj)
                self.session.commit()
                print(f"Material '{material_nome}' criado.")
            
            dados_adicionados = 0
            
            for dado in dados:
                # Validar dados obrigatórios
                if not all(key in dado for key in ['espessura', 'canal', 'deducao']):
                    print(f"Dados incompletos para {dado}. Pulando...")
                    continue
                
                # Buscar ou criar espessura
                espessura_obj = self.session.query(Espessura).filter_by(valor=dado["espessura"]).first()
                if not espessura_obj:
                    espessura_obj = Espessura(valor=dado["espessura"])
                    self.session.add(espessura_obj)
                    self.session.commit()
                
                # Buscar ou criar canal
                canal_obj = self.session.query(Canal).filter_by(valor=dado["canal"]).first()
                if not canal_obj:
                    canal_obj = Canal(
                        valor=dado["canal"],
                        observacao=dado.get("canal_obs", ""),
                        comprimento_total=dado.get("comprimento_total")
                    )
                    self.session.add(canal_obj)
                    self.session.commit()
                
                # Verificar se dedução já existe
                deducao_existente = self.session.query(Deducao).filter(
                    Deducao.material_id == material_obj.id,
                    Deducao.espessura_id == espessura_obj.id,
                    Deducao.canal_id == canal_obj.id
                ).first()
                
                if not deducao_existente:
                    deducao_obj = Deducao(
                        valor=dado["deducao"],
                        material_id=material_obj.id,
                        espessura_id=espessura_obj.id,
                        canal_id=canal_obj.id,
                        forca=dado.get("forca"),
                        observacao=dado.get("obs", "")
                    )
                    self.session.add(deducao_obj)
                    dados_adicionados += 1
                else:
                    print(f"Dedução já existe para {material_nome} - Espessura: {dado['espessura']}, Canal: {dado['canal']}")
            
            self.session.commit()
            print(f"Adicionados {dados_adicionados} registros para {material_nome}")
            
            # Invalidar cache após inserção
            cache_manager.invalidate_all()
            
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar dados para {material_nome}: {e}")
            self.session.rollback()
            return False
    
    def close(self):
        """Fecha a sessão do banco."""
        self.session.close()


def get_dados_carbono() -> List[Dict[str, Any]]:
    """Retorna dados do material CARBONO."""
    return [
        {"espessura": 0.5, "canal": "6", "deducao": 1.2, "forca": 2.0, "obs": ""},
        {"espessura": 0.5, "canal": "10", "deducao": 1.0, "forca": None, "obs": ""},
        {"espessura": 0.8, "canal": "6", "deducao": 1.6, "forca": 7.0, "obs": ""},
        {"espessura": 0.8, "canal": "10", "deducao": 1.6, "forca": 4.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "5", "deducao": 1.8, "forca": 15.0, "obs": "Máx=700"},
        {"espessura": 1.0, "canal": "6", "deducao": 1.7, "forca": 11.0, "obs": ""},
        {"espessura": 1.0, "canal": "10", "deducao": 2.0, "forca": 6.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "R=28", "deducao": 0.5, "forca": None, "obs": "Raio peça = 34"},
        {"espessura": 1.2, "canal": "5", "deducao": 2.0, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.2, "canal": "6", "deducao": 2.0, "forca": 18.0, "obs": ""},
        {"espessura": 1.2, "canal": "10", "deducao": 2.2, "forca": 9.0, "obs": "Canal ideal"},
        {"espessura": 1.5, "canal": "5", "deducao": 2.3, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.5, "canal": "6", "deducao": 2.4, "forca": 25.0, "obs": ""},
        {"espessura": 1.5, "canal": "10", "deducao": 2.7, "forca": 12.0, "obs": "Canal ideal"},
        {"espessura": 1.5, "canal": "R=28", "deducao": 0.5, "forca": None, "obs": "Raio peça = 30"},
        {"espessura": 2.0, "canal": "5", "deducao": 3.0, "forca": None, "obs": "Máx=500"},
        {"espessura": 2.0, "canal": "6", "deducao": 3.2, "forca": 42.0, "obs": ""},
        {"espessura": 2.0, "canal": "10", "deducao": 3.5, "forca": 20.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "16", "deducao": 3.8, "forca": 16.0, "obs": ""},
        {"espessura": 2.0, "canal": "R=28", "deducao": 0.5, "forca": None, "obs": "Raio peça = 30"},
        {"espessura": 2.7, "canal": "6", "deducao": 4.0, "forca": None, "obs": "Máx=300"},
        {"espessura": 2.7, "canal": "10", "deducao": 4.5, "forca": 38.0, "obs": ""},
        {"espessura": 2.7, "canal": "16", "deducao": 4.8, "forca": 26.0, "obs": "Canal ideal"},
        {"espessura": 2.7, "canal": "22", "deducao": 4.8, "forca": 23.0, "obs": ""},
        {"espessura": 2.7, "canal": "25", "deducao": 6.0, "forca": 14.0, "obs": ""},
        {"espessura": 3.2, "canal": "10", "deducao": 4.6, "forca": None, "obs": "Máx=200"},
        {"espessura": 3.2, "canal": "16", "deducao": 5.3, "forca": 43.0, "obs": ""},
        {"espessura": 3.2, "canal": "22", "deducao": 5.4, "forca": 31.0, "obs": ""},
        {"espessura": 3.2, "canal": "25", "deducao": 6.0, "forca": 23.0, "obs": "Canal ideal"},
        {"espessura": 3.2, "canal": "R=28", "deducao": 0.5, "forca": None, "obs": "Raio peça = 29"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.5, "forca": None, "obs": ""},
        {"espessura": 4.0, "canal": "25", "deducao": 7.0, "forca": 44.0, "obs": ""},
        {"espessura": 4.0, "canal": "35", "deducao": 8.4, "forca": 32.0, "obs": "Canal ideal"},
        {"espessura": 4.3, "canal": "22", "deducao": 6.8, "forca": 60.0, "obs": ""},
        {"espessura": 4.3, "canal": "25", "deducao": 7.6, "forca": 44.0, "obs": ""},
        {"espessura": 4.3, "canal": "35", "deducao": 8.0, "forca": 32.0, "obs": "Canal ideal"},
        {"espessura": 4.8, "canal": "16", "deducao": 7.5, "forca": None, "obs": "Máx=200"},
        {"espessura": 4.8, "canal": "22", "deducao": 8.0, "forca": None, "obs": ""},
        {"espessura": 4.8, "canal": "25", "deducao": 8.3, "forca": 76.0, "obs": ""},
        {"espessura": 4.8, "canal": "35", "deducao": 8.5, "forca": 54.0, "obs": "Canal ideal"},
        {"espessura": 6.4, "canal": "25", "deducao": 10.0, "forca": None, "obs": ""},
        {"espessura": 6.4, "canal": "35", "deducao": 10.7, "forca": 85.0, "obs": ""},
        {"espessura": 6.4, "canal": "50", "deducao": 11.7, "forca": 45.0, "obs": "Canal ideal"},
        {"espessura": 7.9, "canal": "35", "deducao": 13.0, "forca": None, "obs": ""},
        {"espessura": 7.9, "canal": "50", "deducao": 14.0, "forca": 88.0, "obs": "Furo Ø8 , dist. tang. e L.D 13 , não repuxa"},
        {"espessura": 7.9, "canal": "55", "deducao": 14.5, "forca": None, "obs": ""},
        {"espessura": 7.9, "canal": "80", "deducao": 15.4, "forca": 46.0, "obs": "Canal ideal"},
        {"espessura": 9.5, "canal": "35", "deducao": 14.8, "forca": None, "obs": "Máx=500"},
        {"espessura": 9.5, "canal": "50", "deducao": 16.0, "forca": 151.0, "obs": ""},
        {"espessura": 9.5, "canal": "80", "deducao": 17.5, "forca": 79.0, "obs": "Canal ideal"},
        {"espessura": 12.7, "canal": "55", "deducao": 20.5, "forca": None, "obs": ""},
        {"espessura": 12.7, "canal": "80", "deducao": 22.5, "forca": 124.0, "obs": "Canal ideal"},
        {"espessura": 15.9, "canal": "80", "deducao": 28.2, "forca": 213.0, "obs": "Canal ideal"},
    ]


def get_dados_inox() -> List[Dict[str, Any]]:
    """Retorna dados do material INOX."""
    return [
        {"espessura": 0.5, "canal": "6", "deducao": 1.3, "forca": 3.0, "obs": ""},
        {"espessura": 0.5, "canal": "10", "deducao": 1.1, "forca": None, "obs": ""},
        {"espessura": 0.8, "canal": "6", "deducao": 1.7, "forca": 9.0, "obs": ""},
        {"espessura": 0.8, "canal": "10", "deducao": 1.7, "forca": 5.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "5", "deducao": 1.9, "forca": 19.0, "obs": "Máx=700"},
        {"espessura": 1.0, "canal": "6", "deducao": 1.8, "forca": 14.0, "obs": ""},
        {"espessura": 1.0, "canal": "10", "deducao": 2.1, "forca": 8.0, "obs": "Canal ideal"},
        {"espessura": 1.2, "canal": "5", "deducao": 2.1, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.2, "canal": "6", "deducao": 2.1, "forca": 22.0, "obs": ""},
        {"espessura": 1.2, "canal": "10", "deducao": 2.3, "forca": 11.0, "obs": "Canal ideal"},
        {"espessura": 1.5, "canal": "5", "deducao": 2.4, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.5, "canal": "6", "deducao": 2.5, "forca": 31.0, "obs": ""},
        {"espessura": 1.5, "canal": "10", "deducao": 2.8, "forca": 15.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "5", "deducao": 3.1, "forca": None, "obs": "Máx=500"},
        {"espessura": 2.0, "canal": "6", "deducao": 3.3, "forca": 52.0, "obs": ""},
        {"espessura": 2.0, "canal": "10", "deducao": 3.6, "forca": 25.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "16", "deducao": 3.9, "forca": 20.0, "obs": ""},
        {"espessura": 2.7, "canal": "6", "deducao": 4.1, "forca": None, "obs": "Máx=300"},
        {"espessura": 2.7, "canal": "10", "deducao": 4.6, "forca": 47.0, "obs": ""},
        {"espessura": 2.7, "canal": "16", "deducao": 4.9, "forca": 32.0, "obs": "Canal ideal"},
        {"espessura": 2.7, "canal": "22", "deducao": 4.9, "forca": 29.0, "obs": ""},
        {"espessura": 3.2, "canal": "10", "deducao": 4.7, "forca": None, "obs": "Máx=200"},
        {"espessura": 3.2, "canal": "16", "deducao": 5.4, "forca": 54.0, "obs": ""},
        {"espessura": 3.2, "canal": "22", "deducao": 5.5, "forca": 39.0, "obs": ""},
        {"espessura": 3.2, "canal": "25", "deducao": 6.1, "forca": 29.0, "obs": "Canal ideal"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.6, "forca": None, "obs": ""},
        {"espessura": 4.0, "canal": "25", "deducao": 7.1, "forca": 55.0, "obs": ""},
        {"espessura": 4.0, "canal": "35", "deducao": 8.5, "forca": 40.0, "obs": "Canal ideal"},
        {"espessura": 4.3, "canal": "22", "deducao": 6.9, "forca": 75.0, "obs": ""},
        {"espessura": 4.3, "canal": "25", "deducao": 7.7, "forca": 55.0, "obs": ""},
        {"espessura": 4.3, "canal": "35", "deducao": 8.1, "forca": 40.0, "obs": "Canal ideal"},
        {"espessura": 4.8, "canal": "16", "deducao": 7.6, "forca": None, "obs": "Máx=200"},
        {"espessura": 4.8, "canal": "22", "deducao": 8.1, "forca": None, "obs": ""},
        {"espessura": 4.8, "canal": "25", "deducao": 8.4, "forca": 95.0, "obs": ""},
        {"espessura": 4.8, "canal": "35", "deducao": 8.6, "forca": 67.0, "obs": "Canal ideal"},
        {"espessura": 6.4, "canal": "25", "deducao": 10.1, "forca": None, "obs": ""},
        {"espessura": 6.4, "canal": "35", "deducao": 10.8, "forca": 106.0, "obs": ""},
        {"espessura": 6.4, "canal": "50", "deducao": 11.8, "forca": 56.0, "obs": "Canal ideal"},
    ]


def get_dados_h14() -> List[Dict[str, Any]]:
    """Retorna dados do material H14."""
    return [
        {"espessura": 0.5, "canal": "6", "deducao": 1.1, "forca": 1.0, "obs": ""},
        {"espessura": 0.5, "canal": "10", "deducao": 0.9, "forca": None, "obs": ""},
        {"espessura": 0.8, "canal": "6", "deducao": 1.5, "forca": 5.0, "obs": ""},
        {"espessura": 0.8, "canal": "10", "deducao": 1.5, "forca": 3.0, "obs": "Canal ideal"},
        {"espessura": 1.0, "canal": "5", "deducao": 1.7, "forca": 11.0, "obs": "Máx=700"},
        {"espessura": 1.0, "canal": "6", "deducao": 1.6, "forca": 8.0, "obs": ""},
        {"espessura": 1.0, "canal": "10", "deducao": 1.9, "forca": 4.0, "obs": "Canal ideal"},
        {"espessura": 1.2, "canal": "5", "deducao": 1.9, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.2, "canal": "6", "deducao": 1.9, "forca": 13.0, "obs": ""},
        {"espessura": 1.2, "canal": "10", "deducao": 2.1, "forca": 6.0, "obs": "Canal ideal"},
        {"espessura": 1.5, "canal": "5", "deducao": 2.2, "forca": None, "obs": "Máx=700"},
        {"espessura": 1.5, "canal": "6", "deducao": 2.3, "forca": 19.0, "obs": ""},
        {"espessura": 1.5, "canal": "10", "deducao": 2.6, "forca": 8.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "5", "deducao": 2.9, "forca": None, "obs": "Máx=500"},
        {"espessura": 2.0, "canal": "6", "deducao": 3.1, "forca": 32.0, "obs": ""},
        {"espessura": 2.0, "canal": "10", "deducao": 3.4, "forca": 14.0, "obs": "Canal ideal"},
        {"espessura": 2.0, "canal": "16", "deducao": 3.7, "forca": 12.0, "obs": ""},
        {"espessura": 2.7, "canal": "6", "deducao": 3.9, "forca": None, "obs": "Máx=300"},
        {"espessura": 2.7, "canal": "10", "deducao": 4.4, "forca": 29.0, "obs": ""},
        {"espessura": 2.7, "canal": "16", "deducao": 4.7, "forca": 20.0, "obs": "Canal ideal"},
        {"espessura": 2.7, "canal": "22", "deducao": 4.7, "forca": 17.0, "obs": ""},
        {"espessura": 3.2, "canal": "10", "deducao": 4.5, "forca": None, "obs": "Máx=200"},
        {"espessura": 3.2, "canal": "16", "deducao": 5.2, "forca": 33.0, "obs": ""},
        {"espessura": 3.2, "canal": "22", "deducao": 5.3, "forca": 23.0, "obs": ""},
        {"espessura": 3.2, "canal": "25", "deducao": 5.9, "forca": 17.0, "obs": "Canal ideal"},
        {"espessura": 4.0, "canal": "16", "deducao": 6.4, "forca": None, "obs": ""},
        {"espessura": 4.0, "canal": "25", "deducao": 6.9, "forca": 33.0, "obs": ""},
        {"espessura": 4.0, "canal": "35", "deducao": 8.3, "forca": 24.0, "obs": "Canal ideal"},
        {"espessura": 4.3, "canal": "22", "deducao": 6.7, "forca": 45.0, "obs": ""},
        {"espessura": 4.3, "canal": "25", "deducao": 7.5, "forca": 33.0, "obs": ""},
        {"espessura": 4.3, "canal": "35", "deducao": 7.9, "forca": 24.0, "obs": "Canal ideal"},
        {"espessura": 4.8, "canal": "16", "deducao": 7.4, "forca": None, "obs": "Máx=200"},
        {"espessura": 4.8, "canal": "22", "deducao": 7.9, "forca": None, "obs": ""},
        {"espessura": 4.8, "canal": "25", "deducao": 8.2, "forca": 57.0, "obs": ""},
        {"espessura": 4.8, "canal": "35", "deducao": 8.4, "forca": 41.0, "obs": "Canal ideal"},
        {"espessura": 6.4, "canal": "25", "deducao": 9.9, "forca": None, "obs": ""},
        {"espessura": 6.4, "canal": "35", "deducao": 10.6, "forca": 64.0, "obs": ""},
        {"espessura": 6.4, "canal": "50", "deducao": 11.6, "forca": 34.0, "obs": "Canal ideal"},
    ]


def main():
    """Função principal para executar o script."""
    print("=== Script Consolidado de Adição de Materiais ===")
    
    # Validar argumentos
    if len(sys.argv) < 2:
        print("Uso: python adicionar_materiais.py <material1> [material2] [material3]")
        print("Materiais disponíveis: carbono, inox, h14, all")
        return
    
    # Mapeamento de materiais e dados
    materiais_dados = {
        'carbono': ('CARBONO', get_dados_carbono),
        'inox': ('INOX', get_dados_inox),
        'h14': ('H14', get_dados_h14)
    }
    
    # Processar argumentos
    materiais_para_adicionar = sys.argv[1:]
    if 'all' in materiais_para_adicionar:
        materiais_para_adicionar = list(materiais_dados.keys())
    
    # Inicializar gerenciador
    data_manager = DataManager()
    
    try:
        for material_key in materiais_para_adicionar:
            material_key = material_key.lower()
            
            if material_key not in materiais_dados:
                print(f"Material '{material_key}' não reconhecido. Materiais disponíveis: {list(materiais_dados.keys())}")
                continue
            
            material_nome, get_dados_func = materiais_dados[material_key]
            dados = get_dados_func()
            
            print(f"\n--- Adicionando dados para {material_nome} ---")
            sucesso = data_manager.adicionar_material_dados(material_nome, dados)
            
            if sucesso:
                print(f"✅ Dados de {material_nome} adicionados com sucesso!")
            else:
                print(f"❌ Erro ao adicionar dados de {material_nome}")
    
    finally:
        data_manager.close()
        print("\n=== Processo concluído ===")


if __name__ == "__main__":
    main()
