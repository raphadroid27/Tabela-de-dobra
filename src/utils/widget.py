"""
Módulo utilitário para gerenciamento, análise, criação e validação de widgets na
aplicação. Inclui classes para análise de uso, factory, cache, operações e
gerenciamento de estado de widgets. Também oferece funções para criar, registrar,
validar e manipular widgets usados em formulários e operações.
"""

import logging
import os
import sys
from typing import Set, Dict, List, Tuple, Any, Callable
from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QLabel
from src.models.models import Espessura, Material, Canal
from src.utils.banco_dados import session
import src.config.globals as g

# Configurar logger
logger = logging.getLogger(__name__)

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


class WidgetUsageAnalyzer:
    """Analisador para identificar widgets globais não utilizados e padrões de uso."""

    def __init__(self, root_path: str):
        self.project_root = root_path
        self.src_path = os.path.join(root_path, 'src')
        self.widget_assignments = set()
        self.widget_usages = set()

    def get_all_global_widgets(self) -> Set[str]:
        """Retorna o conjunto de nomes de widgets definidos em globals.py."""
        widgets = set()
        globals_path = os.path.join(self.src_path, 'config', 'globals.py')

        if os.path.exists(globals_path):
            with open(globals_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and 'None' in line and not line.startswith('#'):
                        var_name = line.split('=')[0].strip()
                        if var_name.isupper():
                            widgets.add(var_name)
        return widgets

    def scan_python_file(self, file_path: str) -> Tuple[Set[str], Set[str]]:
        """Escaneia um arquivo Python procurando por usos de widgets globais."""
        assignments, usages = set(), set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
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
        if 'setattr(g,' in line:
            parts = line.split("'")
            if len(parts) >= 2:
                assignments.add(parts[1])

    def _process_direct_usage(self, line: str, usages: Set[str]):
        """Processa linhas com uso direto de widgets."""
        if 'g.' in line and not line.startswith('#'):
            for word in line.split():
                if word.startswith('g.') and len(word) > 2:
                    widget_name = self._extract_widget_name(word[2:])
                    if widget_name and widget_name.isupper():
                        usages.add(widget_name)

    def _process_getattr_line(self, line: str, usages: Set[str]):
        """Processa linhas com getattr para encontrar usos."""
        if 'getattr(g,' in line:
            parts = line.split("'")
            if len(parts) >= 2:
                usages.add(parts[1])

    def _extract_widget_name(self, text: str) -> str:
        """Extrai nome do widget removendo símbolos."""
        for sep in ['(', '[', '.', ',', ')']:
            text = text.split(sep)[0]
        return text

    def scan_project(self) -> Dict[str, Dict]:
        """Escaneia todo o projeto e coleta estatísticas de uso de widgets."""
        all_assignments, all_usages = set(), set()
        file_stats = {}

        for root, _, files in os.walk(self.src_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_root)
                    assignments, usages = self.scan_python_file(file_path)

                    all_assignments.update(assignments)
                    all_usages.update(usages)

                    if assignments or usages:
                        file_stats[rel_path] = {
                            'assignments': assignments,
                            'usages': usages
                        }

        self.widget_assignments = all_assignments
        self.widget_usages = all_usages
        return file_stats

    def analyze_usage(self) -> Dict[str, List[str]]:
        """Analisa o uso dos widgets e identifica problemas."""
        all_globals = self.get_all_global_widgets()

        return {
            'assigned_not_used': sorted(list(self.widget_assignments - self.widget_usages)),
            'used_not_assigned': sorted(list(self.widget_usages - self.widget_assignments)),
            'never_used': sorted(list(all_globals - self.widget_assignments - self.widget_usages)),
            'properly_used': sorted(list(self.widget_assignments & self.widget_usages)),
            'all_globals': sorted(list(all_globals))
        }

    def get_widgets_by_category(self) -> Dict[str, List[str]]:
        """Categoriza widgets globais por tipo/funcionalidade."""
        all_globals = self.get_all_global_widgets()
        categories = {
            'cabecalho': [], 'dobras': [], 'formularios': [],
            'deducao_form': [], 'material_form': [], 'canal_form': [],
            'espessura_form': [], 'usuario_form': [], 'impressao_form': [],
            'outros': []
        }

        for widget in all_globals:
            if any(prefix in widget for prefix in [
                'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
                'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
                'ABA_EXT_LBL', 'Z_EXT_LBL'
            ]):
                categories['cabecalho'].append(widget)
            elif any(prefix in widget for prefix in [
                'aba', 'medidadobra', 'metadedobra', 'blank', 'FRAME_DOBRA'
            ]):
                categories['dobras'].append(widget)
            elif widget.endswith('_FORM'):
                categories['formularios'].append(widget)
            elif widget.startswith('DED_'):
                categories['deducao_form'].append(widget)
            elif widget.startswith('MAT_'):
                categories['material_form'].append(widget)
            elif widget.startswith('CANAL_'):
                categories['canal_form'].append(widget)
            elif widget.startswith('ESP_'):
                categories['espessura_form'].append(widget)
            elif widget.startswith('USUARIO_') or widget.startswith('SENHA_'):
                categories['usuario_form'].append(widget)
            elif widget.startswith('IMPRESSAO_'):
                categories['impressao_form'].append(widget)
            else:
                categories['outros'].append(widget)

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
            "\nWIDGETS POR CATEGORIA:"
        ]

        for category, widgets in categories.items():
            if widgets:
                report.append(f"- {category.title()}: {len(widgets)} widgets")

        if usage_analysis['never_used']:
            report.extend([
                f"\n1. WIDGETS NUNCA UTILIZADOS ({len(usage_analysis['never_used'])}):",
                " Estes widgets podem ser removidos do globals.py:"
            ])
            for widget in usage_analysis['never_used']:
                report.append(f" - {widget}")

        return '\n'.join(report)


class WidgetValidator:
    """Classe para validação de widgets e verificação de estados."""

    @staticmethod
    def validate_required_widgets(widget_names: List[str]) -> Tuple[bool, List[str]]:
        """Valida se todos os widgets obrigatórios existem e estão inicializados."""
        validation_results = WidgetManager.validate_widgets_exist(widget_names)
        missing_widgets = [name for name,
                           exists in validation_results.items() if not exists]
        return not bool(missing_widgets), missing_widgets

    @staticmethod
    def validate_combobox_selections(combobox_names: List[str]) -> Tuple[bool, List[str]]:
        """Valida se todos os comboboxes possuem seleção."""
        empty_comboboxes = []

        for name in combobox_names:
            widget = WidgetManager.safe_get_widget(name)
            if not (widget and isinstance(widget, QComboBox) and widget.currentIndex() != -1):
                empty_comboboxes.append(name)

        return not bool(empty_comboboxes), empty_comboboxes

    @staticmethod
    def validate_entry_fields(entry_names: List[str]) -> Tuple[bool, List[str]]:
        """Valida se todos os campos de entrada estão preenchidos."""
        empty_entries = []

        for name in entry_names:
            widget = WidgetManager.safe_get_widget(name)
            if not (widget and isinstance(widget, QLineEdit) and widget.text().strip()):
                empty_entries.append(name)

        return not bool(empty_entries), empty_entries

    @staticmethod
    def get_widget_values(widget_names: List[str]) -> Dict[str, str]:
        """Obtém valores de widgets."""
        values = {}
        for name in widget_names:
            widget = WidgetManager.safe_get_widget(name)
            values[name] = WidgetManager.get_widget_value(widget)
        return values


class OperationHelper:
    """Classe auxiliar para operações comuns com widgets."""

    @staticmethod
    def validate_deducao_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de dedução."""
        required_widgets = ['DED_ESPES_COMB', 'DED_CANAL_COMB',
                            'DED_MATER_COMB', 'DED_VALOR_ENTRY']

        is_valid, _ = WidgetValidator.validate_required_widgets(
            required_widgets)
        if not is_valid:
            return False, {}

        combobox_names = ['DED_ESPES_COMB', 'DED_CANAL_COMB', 'DED_MATER_COMB']
        is_valid, _ = WidgetValidator.validate_combobox_selections(
            combobox_names)
        if not is_valid:
            return False, {}

        is_valid, _ = WidgetValidator.validate_entry_fields(
            ['DED_VALOR_ENTRY'])
        if not is_valid:
            return False, {}

        combobox_values = WidgetValidator.get_widget_values(
            combobox_names)
        entry_values = WidgetValidator.get_widget_values(
            ['DED_VALOR_ENTRY', 'DED_OBSER_ENTRY', 'DED_FORCA_ENTRY'])

        return True, {**combobox_values, **entry_values}

    @staticmethod
    def validate_material_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de material."""
        required_widgets = ['MAT_NOME_ENTRY',
                            'MAT_DENS_ENTRY', 'MAT_ESCO_ENTRY', 'MAT_ELAS_ENTRY']

        is_valid, _ = WidgetValidator.validate_required_widgets(
            required_widgets)
        if not is_valid:
            return False, {}

        values = WidgetValidator.get_widget_values(required_widgets)
        if not values.get('MAT_NOME_ENTRY', '').strip():
            return False, {}

        return True, values

    @staticmethod
    def validate_espessura_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de espessura."""
        required_widgets = ['ESP_VALOR_ENTRY']

        is_valid, _ = WidgetValidator.validate_required_widgets(
            required_widgets)
        if not is_valid:
            return False, {}

        is_valid, _ = WidgetValidator.validate_entry_fields(
            required_widgets)
        if not is_valid:
            return False, {}

        return True, WidgetValidator.get_widget_values(required_widgets)

    @staticmethod
    def validate_canal_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de canal."""
        required_widgets = ['CANAL_VALOR_ENTRY']
        optional_widgets = ['CANAL_LARGU_ENTRY', 'CANAL_ALTUR_ENTRY',
                            'CANAL_COMPR_ENTRY', 'CANAL_OBSER_ENTRY']

        is_valid, _ = WidgetValidator.validate_required_widgets(
            required_widgets)
        if not is_valid:
            return False, {}

        is_valid, _ = WidgetValidator.validate_entry_fields(
            required_widgets)
        if not is_valid:
            return False, {}

        all_widgets = required_widgets + optional_widgets
        return True, WidgetValidator.get_widget_values(all_widgets)

    @staticmethod
    def validate_usuario_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de usuário."""
        required_widgets = ['USUARIO_ENTRY', 'SENHA_ENTRY']

        is_valid, _ = WidgetValidator.validate_required_widgets(
            required_widgets)
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_widget_values(required_widgets)

        return True, values


class WidgetFactory:
    """Factory para criação de widgets sob demanda."""

    _widget_creators: Dict[str, Callable] = {}
    _widget_cache: Dict[str, Any] = {}

    @classmethod
    def register_creator(cls, widget_name: str, creator_func: Callable):
        """Registra uma função criadora para um widget."""
        cls._widget_creators[widget_name] = creator_func

    @classmethod
    def get_widget(cls, widget_name: str, force_recreate: bool = False) -> Any:
        """Obtém ou cria um widget sob demanda, usando cache e criadores registrados."""
        if not force_recreate and widget_name in cls._widget_cache:
            widget = cls._widget_cache[widget_name]
            if WidgetManager.is_widget_valid(widget):
                return widget
            del cls._widget_cache[widget_name]

        existing_widget = WidgetManager.safe_get_widget(widget_name)
        if existing_widget is not None and not force_recreate:
            cls._widget_cache[widget_name] = existing_widget
            return existing_widget

        if widget_name not in cls._widget_creators:
            return None

        try:
            widget = cls._widget_creators[widget_name]()
            if widget is not None:
                cls._widget_cache[widget_name] = widget
                WidgetManager.safe_set_widget(widget_name, widget)
                return widget
            return None
        except RuntimeError:
            return None

    @classmethod
    def clear_cache(cls):
        """Limpa o cache de widgets."""
        cls._widget_cache.clear()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Retorna estatísticas do cache."""
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


class OptimizedWidgetManager:
    """Gerenciador otimizado que combina criação sob demanda com cache inteligente."""

    def __init__(self):
        self.access_count = {}
        self.creation_count = {}

    def get_widget(self, widget_name: str, create_if_missing: bool = True) -> Any:
        """Obtém widget e atualiza estatísticas de acesso/criação."""
        self.access_count[widget_name] = self.access_count.get(
            widget_name, 0) + 1

        widget = WidgetManager.safe_get_widget(widget_name)

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
    def safe_set_widget(name: str, widget: Any) -> None:
        """Define um widget de forma segura nas variáveis globais."""
        setattr(g, name, widget)

    @staticmethod
    def get_widget_value(widget: QWidget, default: str = '') -> str:
        """Obtém o valor de um widget de forma segura e padronizada."""
        if not WidgetManager.is_widget_valid(widget):
            return default

        try:
            if hasattr(widget, 'currentText'):
                return widget.currentText() or default
            if hasattr(widget, 'text'):
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
            if hasattr(widget, 'setCurrentText'):
                widget.setCurrentText(value)
                return True
            if hasattr(widget, 'setText'):
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

    @staticmethod
    def restore_combobox_selection(combobox: QComboBox, value: str,
                                   add_if_missing: bool = False) -> bool:
        """Restaura a seleção de um combobox de forma robusta."""
        if not WidgetManager.is_widget_valid(combobox) or not value:
            return False

        try:
            combobox.setCurrentText(value)
            if combobox.currentText() == value:
                return True

            index = combobox.findText(value)
            if index >= 0:
                combobox.setCurrentIndex(index)
                return True

            if add_if_missing and combobox.isEditable():
                combobox.addItem(value)
                combobox.setCurrentText(value)
                return True

            return False
        except (AttributeError, RuntimeError):
            return False

    @classmethod
    def get_dobra_widgets(cls, valor_w: int) -> Dict[str, List[QWidget]]:
        """Retorna widgets de dobras para um valor W."""
        if not hasattr(g, 'N'):
            return {}

        widgets = {
            'entries': [],
            'medida_dobra_labels': [],
            'metade_dobra_labels': [],
            'medida_blank_label': None,
            'metade_blank_label': None
        }

        for i in range(1, g.N):
            entry = cls.safe_get_widget(f'aba{i}_entry_{valor_w}')
            medida_label = cls.safe_get_widget(
                f'medidadobra{i}_label_{valor_w}')
            metade_label = cls.safe_get_widget(
                f'metadedobra{i}_label_{valor_w}')

            if entry:
                widgets['entries'].append(entry)
            if medida_label:
                widgets['medida_dobra_labels'].append(medida_label)
            if metade_label:
                widgets['metade_dobra_labels'].append(metade_label)

        widgets['medida_blank_label'] = cls.safe_get_widget(
            f'medida_blank_label_{valor_w}')
        widgets['metade_blank_label'] = cls.safe_get_widget(
            f'metade_blank_label_{valor_w}')

        return widgets

    @classmethod
    def clear_dobra_widgets(cls, valor_w: int) -> None:
        """Limpa widgets de dobra para um valor W."""
        widgets = cls.get_dobra_widgets(valor_w)

        for entry in widgets['entries']:
            cls.clear_widget(entry)
            if hasattr(entry, 'setStyleSheet'):
                try:
                    entry.setStyleSheet("")
                except RuntimeError:
                    pass

        for label_list in [widgets['medida_dobra_labels'], widgets['metade_dobra_labels']]:
            for label in label_list:
                cls.clear_widget(label)

        for blank_widget in [widgets['medida_blank_label'], widgets['metade_blank_label']]:
            cls.clear_widget(blank_widget)

    @classmethod
    def get_cabecalho_widgets(cls) -> Dict[str, QWidget]:
        """Retorna dicionário com widgets do cabeçalho principal."""
        widget_names = [
            'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
            'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
            'ABA_EXT_LBL', 'Z_EXT_LBL', 'DED_ESPEC_ENTRY'
        ]
        return {name: cls.safe_get_widget(name) for name in widget_names}

    @classmethod
    def validate_widgets_exist(cls, widget_names: List[str]) -> Dict[str, bool]:
        """Verifica se cada widget da lista existe e é válido."""
        return {name: cls.is_widget_valid(cls.safe_get_widget(name)) for name in widget_names}

    @classmethod
    def batch_clear_widgets(cls, widget_names: List[str]) -> Dict[str, bool]:
        """Limpa múltiplos widgets em lote."""
        results = {}
        for name in widget_names:
            widget = cls.safe_get_widget(name)
            results[name] = cls.clear_widget(widget)
        return results

    @classmethod
    def batch_set_widgets(cls, widget_values: Dict[str, str]) -> Dict[str, bool]:
        """Define valores em múltiplos widgets em lote."""
        results = {}
        for name, value in widget_values.items():
            widget = cls.safe_get_widget(name)
            results[name] = cls.set_widget_value(widget, value)
        return results


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
            return ''

        try:
            if hasattr(widget, 'currentText'):
                return widget.currentText()
            if hasattr(widget, 'text'):
                return widget.text()
            return ''
        except RuntimeError:
            return ''

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
        widget_names = ['MAT_COMB', 'ESP_COMB', 'CANAL_COMB',
                        'COMPR_ENTRY', 'RI_ENTRY', 'DED_ESPEC_ENTRY']

        for widget_name in widget_names:
            widget = getattr(g, widget_name, None)
            value = self._get_widget_value_safely(widget, widget_name)
            cabecalho_state[widget_name] = value

        self.widget_cache['cabecalho'] = cabecalho_state

    def _capture_dobras_state(self):
        """Captura o estado dos widgets das dobras."""
        dobras_state = {}

        if not (hasattr(g, 'VALORES_W') and hasattr(g, 'N')):
            self.widget_cache['dobras'] = dobras_state
            return

        for w in g.VALORES_W:
            for i in range(1, g.N):
                widget_name = f'aba{i}_entry_{w}'
                widget = getattr(g, widget_name, None)
                value = self._get_widget_value_safely(widget, widget_name)
                dobras_state[widget_name] = value

        self.widget_cache['dobras'] = dobras_state

    def _get_widget_value_safely(self, widget, widget_name):
        """Obtém valor do widget de forma segura."""
        if not WidgetManager.is_widget_valid(widget):
            return ''

        try:
            value = self.safe_get_widget_value(widget)
            # Debug removido para produção - logging seria aqui se necessário
            return value
        except (AttributeError, TypeError, RuntimeError):
            return ''

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
        if not hasattr(widget, 'setCurrentText'):
            return False

        widget.setCurrentText(value)
        if widget.currentText() == value:
            return True

        index = widget.findText(value)
        if index >= 0:
            widget.setCurrentIndex(index)
            return True

        if hasattr(widget, 'isEditable') and widget.isEditable():
            widget.addItem(value)
            widget.setCurrentText(value)
            return True

        return False

    def safe_restore_entry(self, widget, value):
        """Restaura valor de entry de forma segura."""
        if not WidgetManager.is_widget_valid(widget) or not value:
            return False

        try:
            if hasattr(widget, 'setText'):
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
        if 'cabecalho' not in self.widget_cache:
            return

        cabecalho_state = self.widget_cache['cabecalho']
        for widget_name, value in cabecalho_state.items():
            if value:
                self._restore_single_widget(widget_name, value)

    def _restore_dobras_state(self):
        """Restaura o estado dos widgets das dobras."""
        if 'dobras' not in self.widget_cache:
            return

        dobras_state = self.widget_cache['dobras']
        for widget_name, value in dobras_state.items():
            if value:
                self._restore_single_dobra_widget(widget_name, value)

    def _restore_single_widget(self, widget_name, value):
        """Restaura um único widget do cabeçalho."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return

        if hasattr(widget, 'setCurrentText'):
            self.safe_restore_combobox(widget, value)
        elif hasattr(widget, 'setText'):
            self.safe_restore_entry(widget, value)

    def _restore_single_dobra_widget(self, widget_name, value):
        """Restaura um único widget de dobra."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return False

        return self.safe_restore_entry(widget, value)

    def clear_cache(self):
        """Limpa o cache de widgets."""
        self.widget_cache.clear()

    def get_cache_info(self):
        """Retorna informações sobre o cache atual."""
        cabecalho_count = len(self.widget_cache.get('cabecalho', {}))
        dobras_count = len(self.widget_cache.get('dobras', {}))
        return f"Cache: {cabecalho_count} widgets de cabeçalho, {dobras_count} widgets de dobras"


def _create_combo_base(height: int = 20) -> QComboBox:
    """Cria um combobox base com configurações padrão."""
    combo = QComboBox()
    combo.setFixedHeight(height)
    return combo


def _create_entry_base(height: int = 20, placeholder: str = "") -> QLineEdit:
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
        materiais = [m.nome for m in session.query(
            Material).order_by(Material.nome)]
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
        valores_espessura = session.query(Espessura.valor).distinct().all()
        valores_limpos = [float(valor[0])
                          for valor in valores_espessura if valor[0] is not None]
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
        valores_canal = session.query(Canal.valor).distinct().all()
        valores_canal_limpos = [str(valor[0])
                                for valor in valores_canal if valor[0] is not None]
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
WidgetFactory.register_creator('DED_MATER_COMB', create_deducao_material_combo)
WidgetFactory.register_creator(
    'DED_ESPES_COMB', create_deducao_espessura_combo)
WidgetFactory.register_creator('DED_CANAL_COMB', create_deducao_canal_combo)
WidgetFactory.register_creator('DED_VALOR_ENTRY', create_deducao_valor_entry)
WidgetFactory.register_creator(
    'DED_OBSER_ENTRY', create_deducao_observacao_entry)
WidgetFactory.register_creator('DED_FORCA_ENTRY', create_deducao_forca_entry)

# DEPRECATED: OptimizedWidgetManager é redundante com WidgetManager
# Considere usar WidgetManager diretamente no futuro
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
        logger.warning("Tipo de operação '%s' não suportado", operation_type)
        return False, {}

    return validator()


# DEPRECATED: Funções wrapper redundantes - use WidgetManager diretamente
def safe_get_widget_value(widget_name: str, default: str = '') -> str:
    """Função global para obter valor de widget de forma segura.
    DEPRECATED: Use WidgetManager.get_widget_value() diretamente."""
    widget = WidgetManager.safe_get_widget(widget_name)
    return WidgetManager.get_widget_value(widget, default)


def safe_set_widget_value(widget_name: str, value: str) -> bool:
    """Função global para definir valor de widget de forma segura.
    DEPRECATED: Use WidgetManager.set_widget_value() diretamente."""
    widget = WidgetManager.safe_get_widget(widget_name)
    return WidgetManager.set_widget_value(widget, value)


def safe_clear_widget(widget_name: str) -> bool:
    """Função global para limpar widget de forma segura.
    DEPRECATED: Use WidgetManager.clear_widget() diretamente."""
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
