"""
Módulo utilitário para gerenciamento, análise, criação e validação de widgets na aplicação.
Inclui classes para análise de uso, factory, cache, operações e gerenciamento de estado de widgets.
"""
import os
from typing import Set, Dict, List, Tuple, Any, Callable
from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QLabel
import src.config.globals as g


class WidgetUsageAnalyzer:
    """
    Analisador para identificar widgets globais não utilizados e padrões de uso.
    """

    def __init__(self, root_path: str):
        self.project_root = root_path
        self.src_path = os.path.join(root_path, 'src')
        self.widget_assignments = set()
        self.widget_usages = set()

    def get_all_global_widgets(self) -> Set[str]:
        """Retorna o conjunto de nomes de widgets definidos em globals.py."""
        widgets = set()

        # Obter widgets do arquivo globals.py
        globals_path = os.path.join(self.src_path, 'config', 'globals.py')
        if os.path.exists(globals_path):
            with open(globals_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Buscar definições de widgets (variáveis com valor None)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if '=' in line and 'None' in line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    if var_name.isupper():  # Convenção para constantes/widgets
                        widgets.add(var_name)

        return widgets

    def scan_python_file(self, file_path: str) -> Tuple[Set[str], Set[str]]:
        """
        Escaneia um arquivo Python procurando por usos de widgets globais.
        """
        assignments = set()
        usages = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            for line in lines:
                line = line.strip()

                # Processar linha para encontrar widgets
                self._processar_linha_setattr(line, assignments)
                self._processar_linha_uso_direto(line, usages)
                self._processar_linha_getattr(line, usages)

        except (OSError, IOError) as e:
            print(f"Erro ao analisar {file_path}: {e}")

        return assignments, usages

    def _processar_linha_setattr(self, line: str, assignments: Set[str]):
        """Processa linhas com setattr para encontrar atribuições."""
        if 'setattr(g,' not in line:
            return

        parts = line.split("'")
        if len(parts) >= 2:
            widget_name = parts[1]
            assignments.add(widget_name)

    def _processar_linha_uso_direto(self, line: str, usages: Set[str]):
        """Processa linhas com uso direto de widgets (g.WIDGET_NAME)."""
        if 'g.' not in line or line.startswith('#'):
            return

        words = line.split()
        for word in words:
            if not word.startswith('g.') or len(word) <= 2:
                continue

            # Extrair nome do widget
            widget_name = self._extrair_nome_widget(word[2:])
            if widget_name and widget_name.isupper():
                usages.add(widget_name)

    def _processar_linha_getattr(self, line: str, usages: Set[str]):
        """Processa linhas com getattr para encontrar usos."""
        if 'getattr(g,' not in line:
            return

        parts = line.split("'")
        if len(parts) >= 2:
            widget_name = parts[1]
            usages.add(widget_name)

    def _extrair_nome_widget(self, texto: str) -> str:
        """Extrai nome do widget removendo símbolos."""
        separadores = ['(', '[', '.', ',', ')']
        for sep in separadores:
            texto = texto.split(sep)[0]
        return texto

    def scan_project(self) -> Dict[str, Dict]:
        """Escaneia todo o projeto e coleta estatísticas de uso de widgets."""
        all_assignments = set()
        all_usages = set()
        file_stats = {}

        # Escanear todos os arquivos Python
        for root, files in os.walk(self.src_path):
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

        # Widgets atribuídos mas nunca usados
        assigned_not_used = self.widget_assignments - self.widget_usages

        # Widgets usados mas nunca atribuídos (possível problema)
        used_not_assigned = self.widget_usages - self.widget_assignments

        # Widgets definidos mas nunca atribuídos nem usados
        never_used = all_globals - self.widget_assignments - self.widget_usages

        # Widgets com uso normal
        properly_used = self.widget_assignments & self.widget_usages

        return {
            'assigned_not_used': sorted(list(assigned_not_used)),
            'used_not_assigned': sorted(list(used_not_assigned)),
            'never_used': sorted(list(never_used)),
            'properly_used': sorted(list(properly_used)),
            'all_globals': sorted(list(all_globals))
        }

    def get_widgets_by_category(self) -> Dict[str, List[str]]:
        """Categoriza widgets globais por tipo/funcionalidade."""
        all_globals = self.get_all_global_widgets()

        categories = {
            'cabecalho': [],
            'dobras': [],
            'formularios': [],
            'deducao_form': [],
            'material_form': [],
            'canal_form': [],
            'espessura_form': [],
            'usuario_form': [],
            'impressao_form': [],
            'outros': []
        }

        for widget in all_globals:
            if any(prefix in widget for prefix in [
                'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
                'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
                'ABA_EXT_LBL', 'Z_EXT_LBL'
            ]):
                categories['cabecalho'].append(widget)
            elif any(
                prefix in widget
                for prefix in ['aba', 'medidadobra', 'metadedobra', 'blank', 'FRAME_DOBRA']
            ):
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
        print("Analisando uso de widgets...")
        file_stats = self.scan_project()
        usage_analysis = self.analyze_usage()
        categories = self.get_widgets_by_category()

        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE ANÁLISE DE WIDGETS")
        report.append("=" * 80)

        # Estatísticas gerais
        report.append("\nESTATÍSTICAS GERAIS:")
        report.append(
            "- Total de widgets globais definidos: {len(usage_analysis['all_globals'])}")
        report.append(
            "- Widgets propriamente utilizados: {len(usage_analysis['properly_used'])}")
        report.append(
            "- Widgets atribuídos mas não usados: {len(usage_analysis['assigned_not_used'])}")
        report.append(
            "- Widgets usados mas não atribuídos: {len(usage_analysis['used_not_assigned'])}")
        report.append(
            "- Widgets nunca utilizados: {len(usage_analysis['never_used'])}")

        # Widgets por categoria
        report.append("\nWIDGETS POR CATEGORIA:")
        for category, widgets in categories.items():
            if widgets:
                report.append(f"- {category.title()}: {len(widgets)} widgets")

        # Possíveis otimizações
        report.append("\nOPORTUNIDADES DE OTIMIZAÇÃO:")

        if usage_analysis['never_used']:
            report.append(
                f"\n1. WIDGETS NUNCA UTILIZADOS ({len(usage_analysis['never_used'])}):")
            report.append(
                "   Estes widgets podem ser removidos do globals.py:")
            for widget in usage_analysis['never_used']:
                report.append(f"   - {widget}")

        if usage_analysis['assigned_not_used']:
            report.append(
                f"\n2. WIDGETS ATRIBUÍDOS MAS NÃO USADOS "
                f"({len(usage_analysis['assigned_not_used'])}):"
            )
            report.append("   Estes widgets são criados mas nunca utilizados:")
            for widget in usage_analysis['assigned_not_used']:
                report.append(f"   - {widget}")

        if usage_analysis['used_not_assigned']:
            report.append(
                f"\n3. POSSÍVEIS PROBLEMAS ({len(usage_analysis['used_not_assigned'])}):")
            report.append(
                "   Estes widgets são usados mas podem não estar sendo atribuídos:")
            for widget in usage_analysis['used_not_assigned']:
                report.append(f"   - {widget}")

        # Sugestões de melhoria
        report.append("\nSUGESTÕES DE MELHORIA:")
        report.append(
            "1. Considere criar widgets sob demanda ao invés de globalmente")
        report.append(
            "2. Agrupe widgets relacionados em classes ou estruturas")
        report.append(
            "3. Use factory patterns para criação de formulários similares")
        report.append("4. Implemente lazy loading para widgets não críticos")

        # Detalhes por arquivo
        report.append("\nUSO POR ARQUIVO:")
        for file_path, stats in file_stats.items():
            if stats['assignments'] or stats['usages']:
                report.append(f"\n{file_path}:")
                if stats['assignments']:
                    report.append(
                        f"  Atribuições: {', '.join(sorted(stats['assignments']))}")
                if stats['usages']:
                    report.append(
                        f"  Usos: {', '.join(sorted(stats['usages']))}")

        return '\n'.join(report)


class WidgetValidator:
    """
    Classe para validação de widgets e verificação de estados.
    """

    @staticmethod
    def validate_required_widgets(widget_names: List[str],
                                  operation_name: str = "operação") -> Tuple[bool, List[str]]:
        """Valida se todos os widgets obrigatórios existem e estão inicializados."""
        validation_results = WidgetManager.validate_widgets_exist(widget_names)
        missing_widgets = [name for name,
                           exists in validation_results.items() if not exists]

        if missing_widgets:
            print(
                f"Erro na {operation_name}: Widgets não inicializados: {missing_widgets}")
            return False, missing_widgets

        return True, []

    @staticmethod
    def validate_combobox_selections(combobox_names: List[str],
                                     operation_name: str = "operação") -> Tuple[bool, List[str]]:
        """Valida se todos os comboboxes possuem seleção."""
        empty_comboboxes = []

        for name in combobox_names:
            widget = WidgetManager.safe_get_widget(name)
            if widget and isinstance(widget, QComboBox):
                if widget.currentIndex() == -1:
                    empty_comboboxes.append(name)
            else:
                # Widget não existe ou não é combobox
                empty_comboboxes.append(name)

        if empty_comboboxes:
            print(
                f"Erro na {operation_name}: Comboboxes sem seleção: {empty_comboboxes}")
            return False, empty_comboboxes

        return True, []

    @staticmethod
    def validate_entry_fields(entry_names: List[str],
                              operation_name: str = "operação") -> Tuple[bool, List[str]]:
        """Valida se todos os campos de entrada estão preenchidos."""
        empty_entries = []

        for name in entry_names:
            widget = WidgetManager.safe_get_widget(name)
            if widget and isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    empty_entries.append(name)
            else:
                empty_entries.append(name)  # Widget não existe ou não é entry

        if empty_entries:
            print(f"Erro na {operation_name}: Campos vazios: {empty_entries}")
            return False, empty_entries

        return True, []

    @staticmethod
    def get_combobox_values(combobox_names: List[str]) -> Dict[str, str]:
        """
        Obtém os valores selecionados de múltiplos comboboxes.

        Args:
            combobox_names: Lista de nomes dos comboboxes

        Returns:
            Dicionário com os valores selecionados
        """
        values = {}
        for name in combobox_names:
            widget = WidgetManager.safe_get_widget(name)
            values[name] = WidgetManager.get_widget_value(widget)
        return values

    @staticmethod
    def get_entry_values(entry_names: List[str]) -> Dict[str, str]:
        """Obtém valores de múltiplos campos de entrada."""
        values = {}
        for name in entry_names:
            widget = WidgetManager.safe_get_widget(name)
            values[name] = WidgetManager.get_widget_value(widget)
        return values


class OperationHelper:
    """Classe auxiliar para operações comuns com widgets."""
    @staticmethod
    def validate_deducao_operation() -> Tuple[bool, Dict[str, str]]:
        """
        Valida e obtém valores para operações de dedução.

        Returns:
            Tupla (is_valid, values_dict)
        """
        required_widgets = ['DED_ESPES_COMB', 'DED_CANAL_COMB',
                            'DED_MATER_COMB', 'DED_VALOR_ENTRY']

        # Validar existência dos widgets
        is_valid = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar dedução"
        )
        if not is_valid:
            return False, {}

        # Validar seleções dos comboboxes
        combobox_names = ['DED_ESPES_COMB', 'DED_CANAL_COMB', 'DED_MATER_COMB']
        is_valid = WidgetValidator.validate_combobox_selections(
            combobox_names, "adicionar dedução"
        )
        if not is_valid:
            return False, {}

        # Validar campo de valor
        is_valid = WidgetValidator.validate_entry_fields(
            ['DED_VALOR_ENTRY'], "adicionar dedução"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        combobox_values = WidgetValidator.get_combobox_values(combobox_names)
        entry_values = WidgetValidator.get_entry_values(
            ['DED_VALOR_ENTRY', 'DED_OBSER_ENTRY', 'DED_FORCA_ENTRY'])

        # Combinar valores
        all_values = {**combobox_values, **entry_values}

        return True, all_values

    @staticmethod
    def validate_material_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de material.

        Returns:
            (is_valid, values_dict)
        """
        required_widgets = ['MAT_NOME_ENTRY',
                            'MAT_DENS_ENTRY', 'MAT_ESCO_ENTRY', 'MAT_ELAS_ENTRY']

        # Validar existência dos widgets
        is_valid = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar material"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_entry_values(required_widgets)

        # Validar se o nome não está vazio
        if not values.get('MAT_NOME_ENTRY', '').strip():
            print("Erro: Nome do material não pode estar vazio")
            return False, {}

        return True, values

    @staticmethod
    def validate_espessura_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de espessura.

        Returns:
            (is_valid, values_dict)
        """
        required_widgets = ['ESP_VALOR_ENTRY']

        # Validar existência dos widgets
        is_valid = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar espessura"
        )
        if not is_valid:
            return False, {}

        # Validar campo não vazio
        is_valid = WidgetValidator.validate_entry_fields(
            required_widgets, "adicionar espessura"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_entry_values(required_widgets)

        return True, values

    @staticmethod
    def validate_canal_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de canal.

        Returns:
            (is_valid, values_dict)
        """
        required_widgets = ['CANAL_VALOR_ENTRY']
        optional_widgets = ['CANAL_LARGU_ENTRY', 'CANAL_ALTUR_ENTRY',
                            'CANAL_COMPR_ENTRY', 'CANAL_OBSER_ENTRY']

        # Validar existência dos widgets obrigatórios
        is_valid = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar canal"
        )
        if not is_valid:
            return False, {}

        # Validar campo obrigatório não vazio
        is_valid = WidgetValidator.validate_entry_fields(
            required_widgets, "adicionar canal"
        )
        if not is_valid:
            return False, {}

        # Obter valores (obrigatórios e opcionais)
        all_widgets = required_widgets + optional_widgets
        values = WidgetValidator.get_entry_values(all_widgets)

        return True, values

    @staticmethod
    def validate_usuario_operation() -> Tuple[bool, Dict[str, str]]:
        """Valida e obtém valores para operações de usuário.

        Returns:
            (is_valid, values_dict)
        """
        required_widgets = ['USUARIO_ENTRY', 'SENHA_ENTRY']

        # Validar existência dos widgets
        is_valid = WidgetValidator.validate_required_widgets(
            required_widgets, "operação de usuário"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_entry_values(required_widgets)

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
        # Verificar se já existe no cache e não precisa recriar
        if not force_recreate and widget_name in cls._widget_cache:
            widget = cls._widget_cache[widget_name]
            if WidgetManager.is_widget_valid(widget):
                return widget
            # Widget no cache foi deletado, removê-lo
            del cls._widget_cache[widget_name]

        # Verificar se existe globalmente
        existing_widget = WidgetManager.safe_get_widget(widget_name)
        if existing_widget is not None and not force_recreate:
            cls._widget_cache[widget_name] = existing_widget
            return existing_widget

        # Criar widget usando função registrada
        if widget_name not in cls._widget_creators:
            print(f"Widget {widget_name} não tem criador registrado")
            return None

        try:
            widget = cls._widget_creators[widget_name]()
            if widget is not None:
                cls._widget_cache[widget_name] = widget
                WidgetManager.safe_set_widget(widget_name, widget)
                return widget

            # CORRIGIDO R1705: Código movido para fora do else (desindentar)
            print(f"Erro ao criar widget {widget_name}")
            return None

        except RuntimeError as e:
            print(f"Erro ao criar widget {widget_name}: {e}")
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


class OptimizedWidgetManager:
    """Gerenciador otimizado que combina criação sob demanda com cache inteligente."""

    def __init__(self):
        self.access_count = {}
        self.creation_count = {}

    def get_widget(self, widget_name: str, create_if_missing: bool = True) -> Any:
        """Obtém widget e atualiza estatísticas de acesso/criação."""
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


class WidgetManager:
    """Gerenciador centralizado para operações com widgets."""

    @staticmethod
    def is_widget_valid(widget: QWidget) -> bool:
        """Verifica se um widget é válido (não foi deletado)."""
        if widget is None:
            return False

        try:
            # Tenta acessar uma propriedade básica
            widget.objectName()
            return True
        except RuntimeError:
            return False

    @staticmethod
    def safe_get_widget(name: str, default: Any = None) -> Any:
        """Obtém um widget seguro das variáveis globais."""
        widget = getattr(g, name, default)
        if WidgetManager.is_widget_valid(widget):
            return widget
        return default

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
            # CORRIGIDO R1705: Removido "el" do "elif" após return
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
            # CORRIGIDO R1705: Removido "el" do "elif" após return
            if hasattr(widget, 'setText'):
                widget.setText(value)
                return True
            return False
        except (AttributeError, RuntimeError) as e:
            if not safe:
                raise
            print(f"Erro ao definir valor do widget: {e}")
            return False

    @staticmethod
    def clear_widget(widget: QWidget, safe: bool = True) -> bool:
        """Limpa um widget de forma segura e padronizada."""
        if not WidgetManager.is_widget_valid(widget):
            return False

        try:
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.clear()
                return True
            # CORRIGIDO R1705: Removido "el" do "elif" após return
            if isinstance(widget, QLabel):
                widget.setText("")
                return True
            return False
        except (AttributeError, RuntimeError) as e:
            if not safe:
                raise
            print(f"Erro ao limpar widget: {e}")
            return False

    @staticmethod
    def restore_combobox_selection(combobox: QComboBox, value: str,
                                   add_if_missing: bool = False) -> bool:
        """Restaura a seleção de um combobox de forma robusta."""
        if not WidgetManager.is_widget_valid(combobox) or not value:
            return False

        try:
            # Tentar setCurrentText primeiro
            combobox.setCurrentText(value)

            # Verificar se foi definido corretamente
            if combobox.currentText() == value:
                return True

            # Tentar encontrar por índice
            index = combobox.findText(value)
            if index >= 0:
                combobox.setCurrentIndex(index)
                return True

            # Adicionar se solicitado e for editável
            if add_if_missing and combobox.isEditable():
                combobox.addItem(value)
                combobox.setCurrentText(value)
                return True

            return False
        except (AttributeError, RuntimeError) as e:
            print(f"Erro ao restaurar combobox: {e}")
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

        # Widgets de entrada e labels de dobra
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

        # Widgets de blank
        widgets['medida_blank_label'] = cls.safe_get_widget(
            f'medida_blank_label_{valor_w}')
        widgets['metade_blank_label'] = cls.safe_get_widget(
            f'metade_blank_label_{valor_w}')

        return widgets

    @classmethod
    def clear_dobra_widgets(cls, valor_w: int) -> None:
        """Limpa widgets de dobra para um valor W."""
        widgets = cls.get_dobra_widgets(valor_w)

        # Limpar entries
        for entry in widgets['entries']:
            cls.clear_widget(entry)
            # Remover estilo personalizado se aplicável
            if hasattr(entry, 'setStyleSheet'):
                try:
                    entry.setStyleSheet("")
                except RuntimeError:
                    pass

        # Limpar labels
        for label_list in [widgets['medida_dobra_labels'], widgets['metade_dobra_labels']]:
            for label in label_list:
                cls.clear_widget(label)

        # Limpar widgets de blank
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
        return {name: cls.is_widget_valid(cls.safe_get_widget(name))
                for name in widget_names}

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
        """
        Obtém o valor de um widget de forma segura.

        Args:
            widget: Widget do qual obter o valor

        Returns:
            str: Valor do widget ou string vazia se houver erro
        """
        if not WidgetManager.is_widget_valid(widget):
            return ''

        try:
            if hasattr(widget, 'currentText'):
                return widget.currentText()
            # Corrigido R1705: Removido elif desnecessário após return
            if hasattr(widget, 'text'):
                return widget.text()
            return ''
        except RuntimeError:
            # Widget foi deletado durante a operação
            return ''

    def capture_current_state(self):
        """Captura o estado atual de todos os widgets relevantes."""
        if not self.is_enabled:
            return

        try:
            self._capture_cabecalho_state()
            self._capture_dobras_state()
            print(
                f"[STATE] Estado capturado com sucesso. Widgets no cache: {len(self.widget_cache)}")
        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao capturar estado: {e}")

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
        """Obtém valor do widget de forma segura com logging."""
        if not WidgetManager.is_widget_valid(widget):
            return ''

        try:
            value = self.safe_get_widget_value(widget)
            if value:  # Só mostrar se não estiver vazio
                print(f"[STATE] Capturado {widget_name}: '{value}'")
            return value
        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao capturar {widget_name}: {e}")
            return ''

    def safe_restore_combobox(self, widget, value):
        """Restaura valor de combobox de forma segura."""
        if not WidgetManager.is_widget_valid(widget) or not value:
            return False

        try:
            return self._try_restore_combobox_value(widget, value)
        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar combobox: {e}")
            return False

    def _try_restore_combobox_value(self, widget, value):
        """Tenta restaurar valor do combobox usando diferentes métodos."""
        if not hasattr(widget, 'setCurrentText'):
            return False

        # Método 1: setCurrentText direto
        widget.setCurrentText(value)
        if widget.currentText() == value:
            return True

        # Método 2: Encontrar índice
        index = widget.findText(value)
        if index >= 0:
            widget.setCurrentIndex(index)
            return True

        # Método 3: Adicionar item se combobox for editável
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
        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar entry: {e}")
            return False

    def restore_widget_state(self):
        """Restaura o estado dos widgets a partir do cache."""
        if not self.is_enabled or not self.widget_cache:
            print("[STATE] Cache vazio ou desabilitado - nada para restaurar")
            return

        try:
            print("[STATE] Restaurando estado dos widgets...")
            self._restore_cabecalho_state()
            self._restore_dobras_state()
            print("[STATE] Restauração concluída")
        except (AttributeError, TypeError, RuntimeError) as e:
            print(f"[STATE] Erro ao restaurar estado: {e}")

    def _restore_cabecalho_state(self):
        """Restaura o estado dos widgets do cabeçalho."""
        if 'cabecalho' not in self.widget_cache:
            return

        cabecalho_state = self.widget_cache['cabecalho']
        for widget_name, value in cabecalho_state.items():
            if value:  # Pular valores vazios
                self._restore_single_widget(widget_name, value)

    def _restore_dobras_state(self):
        """Restaura o estado dos widgets das dobras."""
        if 'dobras' not in self.widget_cache:
            return

        dobras_state = self.widget_cache['dobras']
        restored_count = 0

        for widget_name, value in dobras_state.items():
            if value:  # Pular valores vazios
                if self._restore_single_dobra_widget(widget_name, value):
                    restored_count += 1

        print(f"[STATE] Restaurados {restored_count} widgets de dobras")

    def _restore_single_widget(self, widget_name, value):
        """Restaura um único widget do cabeçalho."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return

        success = False

        if hasattr(widget, 'setCurrentText'):
            success = self.safe_restore_combobox(widget, value)
            if success:
                print(
                    f"[STATE] Restaurado {widget_name}: '{value}' (combobox)")
        elif hasattr(widget, 'setText'):
            success = self.safe_restore_entry(widget, value)
            if success:
                print(f"[STATE] Restaurado {widget_name}: '{value}' (entry)")

    def _restore_single_dobra_widget(self, widget_name, value):
        """Restaura um único widget de dobra e retorna se foi bem-sucedido."""
        widget = getattr(g, widget_name, None)
        if not WidgetManager.is_widget_valid(widget):
            return False

        success = self.safe_restore_entry(widget, value)
        if success:
            print(f"[STATE] Restaurado {widget_name}: '{value}'")
        return success

    def clear_cache(self):
        """Limpa o cache de widgets."""
        self.widget_cache.clear()
        print("[STATE] Cache limpo")

    def get_cache_info(self):
        """Retorna informações sobre o cache atual."""
        cabecalho_count = len(self.widget_cache.get('cabecalho', {}))
        dobras_count = len(self.widget_cache.get('dobras', {}))
        return f"Cache: {cabecalho_count} widgets de cabeçalho, {dobras_count} widgets de dobras"
