

"""
Módulo utilitário para gerenciamento e criação de widgets customizados na aplicação.
Inclui funções para criar, registrar, validar e manipular widgets usados em formulários e operações.
"""
import os
import sys
from typing import Any, Dict, Tuple
from PySide6.QtWidgets import QComboBox, QLineEdit
from src.utils.widget import (WidgetManager, WidgetFactory, OptimizedWidgetManager,
                              WidgetStateManager, WidgetUsageAnalyzer, OperationHelper)
from src.models.models import Espessura, Material, Canal
from src.utils.banco_dados import session


# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


def create_deducao_material_combo():
    """Cria combobox de material para formulário de dedução."""
    try:
        combo = QComboBox()
        combo.setFixedHeight(20)

        # Carregar materiais do banco
        materiais = [m.nome for m in session.query(
            Material).order_by(Material.nome)]
        combo.addItems(materiais)

        return combo
    except RuntimeError as e:
        print(f"Erro ao criar combobox de material: {e}")
        return None


def create_deducao_espessura_combo():
    """Cria combobox de espessura para formulário de dedução."""
    try:
        combo = QComboBox()
        combo.setFixedHeight(20)

        # Carregar espessuras do banco
        valores_espessura = session.query(Espessura.valor).distinct().all()
        valores_limpos = [float(valor[0])
                          for valor in valores_espessura if valor[0] is not None]
        combo.addItems([str(valor) for valor in sorted(valores_limpos)])

        return combo
    except RuntimeError as e:
        print(f"Erro ao criar combobox de espessura: {e}")
        return None


def create_deducao_canal_combo():
    """Cria combobox de canal para formulário de dedução."""
    try:
        combo = QComboBox()
        combo.setFixedHeight(20)

        # Carregar canais do banco
        valores_canal = session.query(Canal.valor).distinct().all()
        valores_canal_limpos = [str(valor[0])
                                for valor in valores_canal if valor[0] is not None]
        combo.addItems(sorted(valores_canal_limpos))

        return combo
    except RuntimeError as e:
        print(f"Erro ao criar combobox de canal: {e}")
        return None


def create_deducao_valor_entry():
    """Cria campo de entrada para valor de dedução."""
    try:
        entry = QLineEdit()
        entry.setFixedHeight(20)
        entry.setPlaceholderText("Digite o valor da dedução")
        return entry
    except RuntimeError as e:
        print(f"Erro ao criar entry de valor: {e}")
        return None


def create_deducao_observacao_entry():
    """Cria campo de entrada para observação de dedução."""
    try:
        entry = QLineEdit()
        entry.setFixedHeight(20)
        entry.setPlaceholderText("Observação (opcional)")
        return entry
    except RuntimeError as e:
        print(f"Erro ao criar entry de observação: {e}")
        return None


def create_deducao_forca_entry():
    """Cria campo de entrada para força de dedução."""
    try:
        entry = QLineEdit()
        entry.setFixedHeight(20)
        entry.setPlaceholderText("Força (opcional)")
        return entry
    except RuntimeError as e:
        print(f"Erro ao criar entry de força: {e}")
        return None


# Registrar criadores de widgets
WidgetFactory.register_creator('DED_MATER_COMB', create_deducao_material_combo)
WidgetFactory.register_creator(
    'DED_ESPES_COMB', create_deducao_espessura_combo)
WidgetFactory.register_creator('DED_CANAL_COMB', create_deducao_canal_combo)
WidgetFactory.register_creator('DED_VALOR_ENTRY', create_deducao_valor_entry)
WidgetFactory.register_creator(
    'DED_OBSER_ENTRY', create_deducao_observacao_entry)
WidgetFactory.register_creator('DED_FORCA_ENTRY', create_deducao_forca_entry)

optimized_widget_manager = OptimizedWidgetManager()


def get_widget_on_demand(widget_name: str) -> Any:
    """Obtém widget sob demanda pelo nome."""
    return optimized_widget_manager.get_widget(widget_name)


def validate_widgets_for_operation(operation_type: str) -> Tuple[bool, Dict[str, str]]:
    """Valida widgets conforme o tipo de operação."""
    operations = {
        'deducao': OperationHelper.validate_deducao_operation,
        'material': OperationHelper.validate_material_operation,
        'espessura': OperationHelper.validate_espessura_operation,
        'canal': OperationHelper.validate_canal_operation,
        'usuario': OperationHelper.validate_usuario_operation,
    }

    validator = operations.get(operation_type)
    if not validator:
        print(f"Tipo de operação '{operation_type}' não suportado")
        return False, {}

    return validator()


def safe_get_widget_value(widget_name: str, default: str = '') -> str:
    """Função global para obter valor de widget de forma segura."""
    widget = WidgetManager.safe_get_widget(widget_name)
    return WidgetManager.get_widget_value(widget, default)


def safe_set_widget_value(widget_name: str, value: str) -> bool:
    """Função global para definir valor de widget de forma segura."""
    widget = WidgetManager.safe_get_widget(widget_name)
    return WidgetManager.set_widget_value(widget, value)


def safe_clear_widget(widget_name: str) -> bool:
    """Função global para limpar widget de forma segura."""
    widget = WidgetManager.safe_get_widget(widget_name)
    return WidgetManager.clear_widget(widget)


def analyze_project_widgets(root_path: str = None) -> str:
    """Analisa o uso de widgets no projeto e retorna um relatório.

    Args:
        root_path: Caminho raiz do projeto (opcional).

    Returns:
        Relatório de análise.
    """
    if root_path is None:
        root_path = os.getcwd()

    analyzer = WidgetUsageAnalyzer(root_path)
    return analyzer.generate_report()


if __name__ == "__main__":
    # Executar análise se o script for chamado diretamente
    print(analyze_project_widgets())


# Instância global do gerenciador de estado
widget_state_manager = WidgetStateManager()
