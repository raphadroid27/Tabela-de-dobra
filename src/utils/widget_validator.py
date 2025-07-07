"""
Funções utilitárias para validação de widgets e operações comuns.
"""
from typing import List, Dict, Tuple
from PySide6.QtWidgets import QComboBox, QLineEdit
from src.utils.widget_manager import WidgetManager


class WidgetValidator:
    """
    Classe para validação de widgets e verificação de estados.
    """

    @staticmethod
    def validate_required_widgets(widget_names: List[str],
                                  operation_name: str = "operação") -> Tuple[bool, List[str]]:
        """
        Valida se todos os widgets obrigatórios existem e estão inicializados.

        Args:
            widget_names: Lista de nomes dos widgets obrigatórios
            operation_name: Nome da operação para mensagem de erro

        Returns:
            Tupla (is_valid, missing_widgets)
        """
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
        """
        Valida se todos os comboboxes têm seleções válidas.

        Args:
            combobox_names: Lista de nomes dos comboboxes
            operation_name: Nome da operação para mensagem de erro

        Returns:
            Tupla (is_valid, empty_comboboxes)
        """
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
        """
        Valida se todos os campos de entrada têm valores não vazios.

        Args:
            entry_names: Lista de nomes dos campos de entrada
            operation_name: Nome da operação para mensagem de erro

        Returns:
            Tupla (is_valid, empty_entries)
        """
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
        """
        Obtém os valores de múltiplos campos de entrada.

        Args:
            entry_names: Lista de nomes dos campos de entrada

        Returns:
            Dicionário com os valores dos campos
        """
        values = {}
        for name in entry_names:
            widget = WidgetManager.safe_get_widget(name)
            values[name] = WidgetManager.get_widget_value(widget)
        return values


class OperationHelper:
    """
    Classe auxiliar para operações comuns com widgets.
    """

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
        is_valid, missing = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar dedução"
        )
        if not is_valid:
            return False, {}

        # Validar seleções dos comboboxes
        combobox_names = ['DED_ESPES_COMB', 'DED_CANAL_COMB', 'DED_MATER_COMB']
        is_valid, empty = WidgetValidator.validate_combobox_selections(
            combobox_names, "adicionar dedução"
        )
        if not is_valid:
            return False, {}

        # Validar campo de valor
        is_valid, empty = WidgetValidator.validate_entry_fields(
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
        """
        Valida e obtém valores para operações de material.

        Returns:
            Tupla (is_valid, values_dict)
        """
        required_widgets = ['MAT_NOME_ENTRY',
                            'MAT_DENS_ENTRY', 'MAT_ESCO_ENTRY', 'MAT_ELAS_ENTRY']

        # Validar existência dos widgets
        is_valid, missing = WidgetValidator.validate_required_widgets(
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
        """
        Valida e obtém valores para operações de espessura.

        Returns:
            Tupla (is_valid, values_dict)
        """
        required_widgets = ['ESP_VALOR_ENTRY']

        # Validar existência dos widgets
        is_valid, missing = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar espessura"
        )
        if not is_valid:
            return False, {}

        # Validar campo não vazio
        is_valid, empty = WidgetValidator.validate_entry_fields(
            required_widgets, "adicionar espessura"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_entry_values(required_widgets)

        return True, values

    @staticmethod
    def validate_canal_operation() -> Tuple[bool, Dict[str, str]]:
        """
        Valida e obtém valores para operações de canal.

        Returns:
            Tupla (is_valid, values_dict)
        """
        required_widgets = ['CANAL_VALOR_ENTRY']
        optional_widgets = ['CANAL_LARGU_ENTRY', 'CANAL_ALTUR_ENTRY',
                            'CANAL_COMPR_ENTRY', 'CANAL_OBSER_ENTRY']

        # Validar existência dos widgets obrigatórios
        is_valid, missing = WidgetValidator.validate_required_widgets(
            required_widgets, "adicionar canal"
        )
        if not is_valid:
            return False, {}

        # Validar campo obrigatório não vazio
        is_valid, empty = WidgetValidator.validate_entry_fields(
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
        """
        Valida e obtém valores para operações de usuário.

        Returns:
            Tupla (is_valid, values_dict)
        """
        required_widgets = ['USUARIO_ENTRY', 'SENHA_ENTRY']

        # Validar existência dos widgets
        is_valid, missing = WidgetValidator.validate_required_widgets(
            required_widgets, "operação de usuário"
        )
        if not is_valid:
            return False, {}

        # Obter valores
        values = WidgetValidator.get_entry_values(required_widgets)

        return True, values


# Funções utilitárias para compatibilidade
def validate_widgets_for_operation(operation_type: str) -> Tuple[bool, Dict[str, str]]:
    """
    Função utilitária para validar widgets baseada no tipo de operação.

    Args:
        operation_type: Tipo da operação ('deducao', 'material', 'espessura', 'canal', 'usuario')

    Returns:
        Tupla (is_valid, values_dict)
    """
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
