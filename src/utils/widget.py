"""
Módulo utilitário para gerenciamento, análise, criação e validação de widgets na
aplicação. Inclui classes para análise de uso, factory, cache, operações e
gerenciamento de estado de widgets. Também oferece funções para criar, registrar,
validar e manipular widgets usados em formulários e operações.
"""

import logging
import os
import sys
from typing import Any, Callable, Dict, List, Set, Tuple

from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QWidget

import src.config.globals as g
from src.models.models import Canal, Espessura, Material
from src.utils.banco_dados import Session
from src.utils.estilo import ALTURA_PADRAO_COMPONENTE
from src.utils.utilitarios import (
    WIDGET_CABECALHO,
    WIDGETS_DOBRAS,
    WIDGETS_ENTRADA_CABECALHO,
    tem_configuracao_dobras_valida,
)

logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


class WidgetUsageAnalyzer:
    """Analisador para identificar widgets globais não utilizados e padrões de uso."""

    def __init__(self, root_path: str):
        self.project_root = root_path
        self.src_path = os.path.join(root_path, "src")
        self.widget_assignments: Set[str] = set()
        self.widget_usages: Set[str] = set()

    def get_all_global_widgets(self) -> Set[str]:
        """Retorna o conjunto de nomes de widgets definidos em globals.py."""
        widgets = set()
        globals_path = os.path.join(self.src_path, "config", "globals.py")

        if os.path.exists(globals_path):
            with open(globals_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and "None" in line and not line.startswith("#"):
                        var_name = line.split("=")[0].strip()
                        if var_name.isupper():
                            widgets.add(var_name)
        return widgets

    def scan_python_file(self, file_path: str) -> Tuple[Set[str], Set[str]]:
        """Escaneia um arquivo Python procurando por usos de widgets globais."""
        assignments: Set[str] = set()
        usages: Set[str] = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    self._process_setattr_line(line, assignments)
                    self._process_direct_usage(line, usages)
                    self._process_getattr_line(line, usages)
        except (OSError, IOError):
            pass

        return assignments, usages

    def _process_setattr_line(self, line: str, assignments: Set[str]):
        """Processa linhas com setattr para encontrar atribuições."""
        if "setattr(g," in line:
            parts = line.split("'")
            if len(parts) >= 2:
                assignments.add(parts[1])

    def _process_direct_usage(self, line: str, usages: Set[str]):
        """Processa linhas com uso direto de widgets."""
        if "g." in line and not line.startswith("#"):
            for word in line.split():
                if word.startswith("g.") and len(word) > 2:
                    widget_name = self._extract_widget_name(word[2:])
                    if widget_name and widget_name.isupper():
                        usages.add(widget_name)

    def _process_getattr_line(self, line: str, usages: Set[str]):
        """Processa linhas com getattr para encontrar usos."""
        if "getattr(g," in line:
            parts = line.split("'")
            if len(parts) >= 2:
                usages.add(parts[1])

    def _extract_widget_name(self, text: str) -> str:
        """Extrai nome do widget removendo símbolos."""
        for sep in ["(", "[", ".", ",", ")"]:
            text = text.split(sep)[0]
        return text

    def scan_project(self) -> Dict[str, Dict]:
        """Escaneia todo o projeto e coleta estatísticas de uso de widgets."""
        all_assignments, all_usages = set(), set()
        file_stats = {}

        for root, _, files in os.walk(self.src_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_root)
                    assignments, usages = self.scan_python_file(file_path)

                    all_assignments.update(assignments)
                    all_usages.update(usages)

                    if assignments or usages:
                        file_stats[rel_path] = {
                            "assignments": assignments,
                            "usages": usages,
                        }

        self.widget_assignments = all_assignments
        self.widget_usages = all_usages
        return file_stats

    def analyze_usage(self) -> Dict[str, List[str]]:
        """Analisa o uso dos widgets e identifica problemas."""
        all_globals = self.get_all_global_widgets()

        return {
            "assigned_not_used": sorted(
                list(self.widget_assignments - self.widget_usages)
            ),
            "used_not_assigned": sorted(
                list(self.widget_usages - self.widget_assignments)
            ),
            "never_used": sorted(
                list(all_globals - self.widget_assignments - self.widget_usages)
            ),
            "properly_used": sorted(list(self.widget_assignments & self.widget_usages)),
            "all_globals": sorted(list(all_globals)),
        }

    def get_widgets_by_category(self) -> Dict[str, List[str]]:
        """Categoriza widgets globais por tipo/funcionalidade."""
        all_globals = self.get_all_global_widgets()
        categories: Dict[str, List[str]] = {
            "cabecalho": [],
            "dobras": [],
            "formularios": [],
            "deducao_form": [],
            "material_form": [],
            "canal_form": [],
            "espessura_form": [],
            "usuario_form": [],
            "impressao_form": [],
            "outros": [],
        }

        for widget in all_globals:
            if any(prefix in widget for prefix in WIDGET_CABECALHO):
                categories["cabecalho"].append(widget)
            elif any(prefix in widget for prefix in WIDGETS_DOBRAS):
                categories["dobras"].append(widget)
            elif widget.endswith("_FORM"):
                categories["formularios"].append(widget)
            elif widget.startswith("DED_"):
                categories["deducao_form"].append(widget)
            elif widget.startswith("MAT_"):
                categories["material_form"].append(widget)
            elif widget.startswith("CANAL_"):
                categories["canal_form"].append(widget)
            elif widget.startswith("ESP_"):
                categories["espessura_form"].append(widget)
            elif widget.startswith("USUARIO_") or widget.startswith("SENHA_"):
                categories["usuario_form"].append(widget)
            elif widget.startswith("IMPRESSAO_"):
                categories["impressao_form"].append(widget)
            else:
                categories["outros"].append(widget)

        return categories

    def generate_report(self) -> str:
        """Gera um relatório resumido da análise de widgets."""
        self.scan_project()
        usage_analysis = self.analyze_usage()
        categories = self.get_widgets_by_category()

        report = [
            "=" * 80,
            "RELATÓRIO DE ANÁLISE DE WIDGETS",
            "=" * 80,
            "\nESTATÍSTICAS GERAIS:",
            f"- Total de widgets globais definidos: {len(usage_analysis['all_globals'])}",
            f"- Widgets propriamente utilizados: {len(usage_analysis['properly_used'])}",
            f"- Widgets atribuídos mas não usados: {len(usage_analysis['assigned_not_used'])}",
            f"- Widgets usados mas não atribuídos: {len(usage_analysis['used_not_assigned'])}",
            f"- Widgets nunca utilizados: {len(usage_analysis['never_used'])}",
            "\nWIDGETS POR CATEGORIA:",
        ]

        for category, widgets in categories.items():
            if widgets:
                report.append(f"- {category.title()}: {len(widgets)} widgets")

        if usage_analysis["never_used"]:
            report.extend(
                [
                    f"\n1. WIDGETS NUNCA UTILIZADOS ({len(usage_analysis['never_used'])}):",
                    " Estes widgets podem ser removidos do globals.py:",
                ]
            )
            for widget in usage_analysis["never_used"]:
                report.append(f" - {widget}")

        return "\n".join(report)


class WidgetFactory:
    """Factory para criação de widgets sob demanda."""

    _widget_creators: Dict[str, Callable] = {}
    _widget_cache: Dict[str, Any] = {}

    @classmethod
    def register_creator(cls, widget_name: str, creator_func: Callable):
        """Registra uma função criadora para um widget."""
        cls._widget_creators[widget_name] = creator_func


class WidgetManager:
    """Gerenciador centralizado para operações com widgets."""

    @staticmethod
    def is_widget_valid(widget: QWidget) -> bool:
        """Verifica se um widget é válido (não foi deletado)."""
        if widget is None:
            return False
        try:
            widget.objectName()
            return True
        except RuntimeError:
            return False

    @staticmethod
    def safe_get_widget(name: str, default: Any = None) -> Any:
        """Obtém um widget seguro das variáveis globais."""
        widget = getattr(g, name, default)
        return widget if WidgetManager.is_widget_valid(widget) else default

    @staticmethod
    def get_widget_value(widget: QWidget, default: str = "") -> str:
        """Obtém o valor de um widget de forma segura e padronizada."""
        if not WidgetManager.is_widget_valid(widget):
            return default

        try:
            if hasattr(widget, "currentText"):
                return widget.currentText() or default
            if hasattr(widget, "text"):
                return widget.text() or default
            return default
        except (AttributeError, RuntimeError):
            return default

    @staticmethod
    def set_widget_value(widget: QWidget, value: str, safe: bool = True) -> bool:
        """Define o valor de um widget de forma segura e padronizada."""
        if not WidgetManager.is_widget_valid(widget):
            return False

        try:
            if hasattr(widget, "setCurrentText"):
                widget.setCurrentText(value)
                return True
            if hasattr(widget, "setText"):
                widget.setText(value)
                return True
            return False
        except (AttributeError, RuntimeError):
            return False if safe else None

    @staticmethod
    def clear_widget(widget: QWidget, safe: bool = True) -> bool:
        """Limpa um widget de forma segura e padronizada."""
        if not WidgetManager.is_widget_valid(widget):
            return False

        try:
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.clear()
                return True
            if isinstance(widget, QLabel):
                widget.setText("")
                return True
            return False
        except (AttributeError, RuntimeError):
            return False if safe else None

    @classmethod
    def validate_widgets_exist(cls, widget_names: List[str]) -> Dict[str, bool]:
        """Verifica se cada widget da lista existe e é válido."""
        return {
            name: cls.is_widget_valid(cls.safe_get_widget(name))
            for name in widget_names
        }


class WidgetStateManager:
    """Gerenciador de estado dos widgets para preservar valores durante recriações da interface."""

    def __init__(self):
        self.widget_cache = {}
        self.is_enabled = True

    def enable(self):
        """Habilita o gerenciamento de estado."""
        self.is_enabled = True

    def disable(self):
        """Desabilita o gerenciamento de estado."""
        self.is_enabled = False

    def safe_get_widget_value(self, widget):
        """Obtém o valor de um widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return ""

        try:
            if hasattr(widget, "currentText"):
                return widget.currentText()
            if hasattr(widget, "text"):
                return widget.text()
            return ""
        except RuntimeError:
            return ""

    def capture_current_state(self):
        """Captura o estado atual de todos os widgets relevantes."""
        if not self.is_enabled:
            return

        try:
            self._capture_cabecalho_state()
            self._capture_dobras_state()
        except (AttributeError, TypeError, RuntimeError):
            pass

    def _capture_cabecalho_state(self):
        """Captura o estado dos widgets do cabeçalho."""
        cabecalho_state = {}

        for widget_name in WIDGETS_ENTRADA_CABECALHO:
            widget = getattr(g, widget_name, None)
            value = self._get_widget_value_safely(widget, widget_name)
            cabecalho_state[widget_name] = value

        self.widget_cache["cabecalho"] = cabecalho_state

    def _capture_dobras_state(self):
        """Captura o estado dos widgets das dobras."""
        dobras_state: Dict[str, Any] = {}

        if not tem_configuracao_dobras_valida():
            self.widget_cache["dobras"] = dobras_state
            return

        for w in g.VALORES_W:
            for i in range(1, g.N):
                widget_name = f"aba{i}_entry_{w}"
                widget = getattr(g, widget_name, None)
                value = self._get_widget_value_safely(widget, widget_name)
                dobras_state[widget_name] = value

        self.widget_cache["dobras"] = dobras_state

    def _get_widget_value_safely(self, widget, _):
        """Obtém valor do widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return ""

        try:
            value = self.safe_get_widget_value(widget)
            # Debug removido para produção - logging seria aqui se necessário
            return value
        except (AttributeError, TypeError, RuntimeError):
            return ""

    def safe_restore_combobox(self, widget, value):
        """Restaura valor de combobox de forma segura."""
        if not WidgetManager.is_widget_valid(widget) or not value:
            return False

        try:
            return self._try_restore_combobox_value(widget, value)
        except (AttributeError, TypeError, RuntimeError):
            return False

    def _try_restore_combobox_value(self, widget, value):
        """Tenta restaurar valor do combobox usando diferentes métodos."""
        if not hasattr(widget, "setCurrentText"):
            return False

        widget.setCurrentText(value)
        if widget.currentText() == value:
            return True

        index = widget.findText(value)
        if index >= 0:
            widget.setCurrentIndex(index)
            return True

        if hasattr(widget, "isEditable") and widget.isEditable():
            widget.addItem(value)
            widget.setCurrentText(value)
            return True

        return False

    def safe_restore_entry(self, widget, value):
        """Restaura valor de entry de forma segura."""
        if not WidgetManager.is_widget_valid(widget) or not value:
            return False

        try:
            if hasattr(widget, "setText"):
                widget.setText(value)
                return True
            return False
        except (AttributeError, TypeError, RuntimeError):
            return False

    def restore_widget_state(self):
        """Restaura o estado dos widgets a partir do cache."""
        if not self.is_enabled or not self.widget_cache:
            return

        try:
            self._restore_cabecalho_state()
            self._restore_dobras_state()
        except (AttributeError, TypeError, RuntimeError):
            pass

    def _restore_cabecalho_state(self):
        """Restaura o estado dos widgets do cabeçalho."""
        if "cabecalho" not in self.widget_cache:
            return

        cabecalho_state = self.widget_cache["cabecalho"]
        for widget_name, value in cabecalho_state.items():
            if value:
                self._restore_single_widget(widget_name, value)

    def _restore_dobras_state(self):
        """Restaura o estado dos widgets das dobras."""
        if "dobras" not in self.widget_cache:
            return

        dobras_state = self.widget_cache["dobras"]
        for widget_name, value in dobras_state.items():
            if value:
                self._restore_single_dobra_widget(widget_name, value)

    def _restore_single_widget(self, widget_name, value):
        """Restaura um único widget do cabeçalho."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return

        if hasattr(widget, "setCurrentText"):
            self.safe_restore_combobox(widget, value)
        elif hasattr(widget, "setText"):
            self.safe_restore_entry(widget, value)

    def _restore_single_dobra_widget(self, widget_name, value):
        """Restaura um único widget de dobra."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return False

        return self.safe_restore_entry(widget, value)

    def get_cache_info(self):
        """Retorna informações sobre o cache atual."""
        cabecalho_count = len(self.widget_cache.get("cabecalho", {}))
        dobras_count = len(self.widget_cache.get("dobras", {}))
        return f"Cache: {cabecalho_count} widgets de cabeçalho, {dobras_count} widgets de dobras"


def _create_combo_base(height: int = ALTURA_PADRAO_COMPONENTE) -> QComboBox:
    """Cria um combobox base com configurações padrão."""
    combo = QComboBox()
    combo.setFixedHeight(height)
    return combo


def _create_entry_base(
    height: int = ALTURA_PADRAO_COMPONENTE, placeholder: str = ""
) -> QLineEdit:
    """Cria um entry base com configurações padrão."""
    entry = QLineEdit()
    entry.setFixedHeight(height)
    if placeholder:
        entry.setPlaceholderText(placeholder)
    return entry


def create_deducao_material_combo():
    """Cria combobox de material para formulário de dedução."""
    try:
        combo = _create_combo_base()
        # Carregar materiais do banco
        materiais = [m.nome for m in Session.query(Material).order_by(Material.nome)]
        combo.addItems(materiais)
        return combo
    except RuntimeError as e:
        logger.error("Erro ao criar combobox de material: %s", e)
        return None


def create_deducao_espessura_combo():
    """Cria combobox de espessura para formulário de dedução."""
    try:
        combo = _create_combo_base()
        # Carregar espessuras do banco
        valores_espessura = Session.query(Espessura.valor).distinct().all()
        valores_limpos = [
            float(valor[0]) for valor in valores_espessura if valor[0] is not None
        ]
        combo.addItems([str(valor) for valor in sorted(valores_limpos)])
        return combo
    except RuntimeError as e:
        logger.error("Erro ao criar combobox de espessura: %s", e)
        return None


def create_deducao_canal_combo():
    """Cria combobox de canal para formulário de dedução."""
    try:
        combo = _create_combo_base()
        # Carregar canais do banco
        valores_canal = Session.query(Canal.valor).distinct().all()
        valores_canal_limpos = [
            str(valor[0]) for valor in valores_canal if valor[0] is not None
        ]
        combo.addItems(sorted(valores_canal_limpos))
        return combo
    except RuntimeError as e:
        logger.error("Erro ao criar combobox de canal: %s", e)
        return None


def create_deducao_valor_entry():
    """Cria campo de entrada para valor de dedução."""
    try:
        return _create_entry_base(placeholder="Digite o valor da dedução")
    except RuntimeError as e:
        logger.error("Erro ao criar entry de valor: %s", e)
        return None


def create_deducao_observacao_entry():
    """Cria campo de entrada para observação de dedução."""
    try:
        return _create_entry_base(placeholder="Observação (opcional)")
    except RuntimeError as e:
        logger.error("Erro ao criar entry de observação: %s", e)
        return None


def create_deducao_forca_entry():
    """Cria campo de entrada para força de dedução."""
    try:
        return _create_entry_base(placeholder="Força (opcional)")
    except RuntimeError as e:
        logger.error("Erro ao criar entry de força: %s", e)
        return None


# Registrar criadores de widgets
WidgetFactory.register_creator("DED_MATER_COMB", create_deducao_material_combo)
WidgetFactory.register_creator("DED_ESPES_COMB", create_deducao_espessura_combo)
WidgetFactory.register_creator("DED_CANAL_COMB", create_deducao_canal_combo)
WidgetFactory.register_creator("DED_VALOR_ENTRY", create_deducao_valor_entry)
WidgetFactory.register_creator("DED_OBSER_ENTRY", create_deducao_observacao_entry)
WidgetFactory.register_creator("DED_FORCA_ENTRY", create_deducao_forca_entry)


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
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Iniciando análise de widgets do projeto...")
    RESULT = analyze_project_widgets()
    logger.info("Análise concluída.")
    logger.info(RESULT)

widget_state_manager = WidgetStateManager()
