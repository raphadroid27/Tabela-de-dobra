"""
Factory pattern para criação de widgets sob demanda com tratamento robusto.
"""

from typing import Dict, Any, Callable
from PySide6.QtWidgets import QComboBox, QLineEdit
from src.utils.widget_manager import WidgetManager
from src.models.models import Espessura, Material, Canal
from src.utils.banco_dados import session


class WidgetFactory:
    """Factory para criação de widgets sob demanda."""

    _widget_creators: Dict[str, Callable] = {}
    _widget_cache: Dict[str, Any] = {}

    @classmethod
    def register_creator(cls, widget_name: str, creator_func: Callable):
        """
        Registra uma função criadora para um widget específico.

        Args:
            widget_name: Nome do widget
            creator_func: Função que cria o widget
        """
        cls._widget_creators[widget_name] = creator_func

    @classmethod
    def get_widget(cls, widget_name: str, force_recreate: bool = False) -> Any:
        """
        Obtém um widget, criando-o sob demanda se necessário.

        Args:
            widget_name: Nome do widget
            force_recreate: Se True, recria o widget mesmo se já existir

        Returns:
            O widget solicitado ou None se não puder ser criado
        """
        # Verificar se já existe no cache e não precisa recriar
        if not force_recreate and widget_name in cls._widget_cache:
            widget = cls._widget_cache[widget_name]
            if WidgetManager.is_widget_valid(widget):
                return widget
            else:
                # Widget no cache foi deletado, removê-lo
                del cls._widget_cache[widget_name]

        # Verificar se existe globalmente
        existing_widget = WidgetManager.safe_get_widget(widget_name)
        if existing_widget is not None and not force_recreate:
            cls._widget_cache[widget_name] = existing_widget
            return existing_widget

        # Criar widget usando função registrada
        if widget_name in cls._widget_creators:
            try:
                widget = cls._widget_creators[widget_name]()
                if widget is not None:
                    cls._widget_cache[widget_name] = widget
                    WidgetManager.safe_set_widget(widget_name, widget)
                    return widget
            except RuntimeError as e:
                print(f"Erro ao criar widget {widget_name}: {e}")
                return None

        print(f"Widget {widget_name} não tem criador registrado")
        return None

    @classmethod
    def clear_cache(cls):
        """Limpa o cache de widgets."""
        cls._widget_cache.clear()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Retorna estatísticas do cache."""
        # Limpar widgets inválidos do cache
        invalid_widgets = []
        for name, widget in cls._widget_cache.items():
            if not WidgetManager.is_widget_valid(widget):
                invalid_widgets.append(name)

        for name in invalid_widgets:
            del cls._widget_cache[name]

        return {
            'cached_widgets': len(cls._widget_cache),
            'registered_creators': len(cls._widget_creators)
        }

# Funções criadoras para widgets específicos


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


class OptimizedWidgetManager:
    """Gerenciador otimizado que combina criação sob demanda com cache inteligente."""

    def __init__(self):
        self.access_count = {}
        self.creation_count = {}

    def get_widget(self, widget_name: str, create_if_missing: bool = True) -> Any:
        """
        Obtém widget com estatísticas de acesso.

        Args:
            widget_name: Nome do widget
            create_if_missing: Se True, cria o widget se não existir

        Returns:
            O widget solicitado
        """
        # Atualizar estatísticas
        self.access_count[widget_name] = self.access_count.get(
            widget_name, 0) + 1

        # Tentar obter widget existente
        widget = WidgetManager.safe_get_widget(widget_name)

        # Criar se necessário e permitido
        if widget is None and create_if_missing:
            widget = WidgetFactory.get_widget(widget_name)
            if widget is not None:
                self.creation_count[widget_name] = self.creation_count.get(
                    widget_name, 0) + 1

        return widget

    def get_stats(self) -> Dict[str, Dict]:
        """Retorna estatísticas de uso."""
        return {
            'access_count': self.access_count,
            'creation_count': self.creation_count,
            'factory_stats': WidgetFactory.get_cache_stats()
        }

    def print_usage_report(self):
        """Imprime relatório de uso dos widgets."""
        stats = self.get_stats()

        print("=" * 50)
        print("RELATÓRIO DE USO DE WIDGETS")
        print("=" * 50)

        print("\nWIDGETS MAIS ACESSADOS:")
        sorted_access = sorted(
            stats['access_count'].items(), key=lambda x: x[1], reverse=True)
        for widget, count in sorted_access[:10]:  # Top 10
            print(f"  {widget}: {count} acessos")

        print("\nWIDGETS CRIADOS SOB DEMANDA:")
        for widget, count in stats['creation_count'].items():
            print(f"  {widget}: criado {count} vez(es)")

        print("\nESTATÍSTICAS DA FACTORY:")
        factory_stats = stats['factory_stats']
        print(f"  Widgets em cache: {factory_stats['cached_widgets']}")
        print(
            f"  Criadores registrados: {factory_stats['registered_creators']}")


# Instância global do gerenciador otimizado
optimized_widget_manager = OptimizedWidgetManager()

# Função utilitária para compatibilidade


def get_widget_on_demand(widget_name: str) -> Any:
    """
    Função utilitária para obter widgets sob demanda.

    Args:
        widget_name: Nome do widget

    Returns:
        O widget solicitado
    """
    return optimized_widget_manager.get_widget(widget_name)
