"""
Sistema centralizado de gerenciamento de widgets para evitar
redundâncias e melhorar a modularização.
"""
from typing import Any, Dict, List, Callable
from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QLabel
import src.config.globals as g


class WidgetManager:
    """
    Gerenciador centralizado para operações com widgets, evitando código redundante
    e proporcionando uma interface consistente para manipulação de widgets.
    """

    @staticmethod
    def safe_get_widget(name: str, default: Any = None) -> Any:
        """
        Obtém um widget de forma segura das variáveis globais.

        Args:
            name: Nome do widget nas variáveis globais
            default: Valor padrão se o widget não existir

        Returns:
            O widget ou o valor padrão
        """
        return getattr(g, name, default)

    @staticmethod
    def safe_set_widget(name: str, widget: Any) -> None:
        """
        Define um widget de forma segura nas variáveis globais.

        Args:
            name: Nome do widget nas variáveis globais
            widget: Widget a ser definido
        """
        setattr(g, name, widget)

    @staticmethod
    def get_widget_value(widget: QWidget, default: str = '') -> str:
        """
        Obtém o valor de um widget de forma padronizada.

        Args:
            widget: Widget do qual obter o valor
            default: Valor padrão se não conseguir obter

        Returns:
            Valor do widget ou padrão
        """
        if widget is None:
            return default

        try:
            if hasattr(widget, 'currentText'):
                return widget.currentText() or default
            elif hasattr(widget, 'text'):
                return widget.text() or default
            return default
        except AttributeError:
            return default

    @staticmethod
    def set_widget_value(widget: QWidget, value: str, safe: bool = True) -> bool:
        """
        Define o valor de um widget de forma padronizada.

        Args:
            widget: Widget no qual definir o valor
            value: Valor a ser definido
            safe: Se True, não levanta exceções

        Returns:
            True se conseguiu definir, False caso contrário
        """
        if widget is None:
            return False

        try:
            if hasattr(widget, 'setCurrentText'):
                widget.setCurrentText(value)
                return True
            elif hasattr(widget, 'setText'):
                widget.setText(value)
                return True
            return False
        except AttributeError as e:
            if not safe:
                raise
            print(f"Erro ao definir valor do widget: {e}")
            return False

    @staticmethod
    def clear_widget(widget: QWidget, safe: bool = True) -> bool:
        """
        Limpa um widget de forma padronizada.

        Args:
            widget: Widget a ser limpo
            safe: Se True, não levanta exceções

        Returns:
            True se conseguiu limpar, False caso contrário
        """
        if widget is None:
            return False

        try:
            if isinstance(widget, (QLineEdit, QComboBox)):
                widget.clear()
                return True
            elif isinstance(widget, QLabel):
                widget.setText("")
                return True
            return False
        except AttributeError as e:
            if not safe:
                raise
            print(f"Erro ao limpar widget: {e}")
            return False

    @staticmethod
    def restore_combobox_selection(combobox: QComboBox, value: str,
                                   add_if_missing: bool = False) -> bool:
        """
        Restaura a seleção de um combobox de forma robusta.

        Args:
            combobox: Combobox a ser restaurado
            value: Valor a ser selecionado
            add_if_missing: Se True, adiciona o item se não existir

        Returns:
            True se conseguiu restaurar, False caso contrário
        """
        if not combobox or not value:
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
        except AttributeError as e:
            print(f"Erro ao restaurar combobox: {e}")
            return False

    @classmethod
    def get_dobra_widgets(cls, valor_w: int) -> Dict[str, List[QWidget]]:
        """
        Obtém todos os widgets relacionados às dobras para um valor W específico.

        Args:
            valor_w: Valor W para o qual obter os widgets

        Returns:
            Dicionário com listas de widgets organizados por tipo
        """
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
        """
        Limpa todos os widgets de dobra para um valor W específico.

        Args:
            valor_w: Valor W para o qual limpar os widgets
        """
        widgets = cls.get_dobra_widgets(valor_w)

        # Limpar entries
        for entry in widgets['entries']:
            cls.clear_widget(entry)
            # Remover estilo personalizado se aplicável
            if hasattr(entry, 'setStyleSheet'):
                entry.setStyleSheet("")

        # Limpar labels
        for label_list in [widgets['medida_dobra_labels'], widgets['metade_dobra_labels']]:
            for label in label_list:
                cls.clear_widget(label)

        # Limpar widgets de blank
        for blank_widget in [widgets['medida_blank_label'], widgets['metade_blank_label']]:
            cls.clear_widget(blank_widget)

    @classmethod
    def get_cabecalho_widgets(cls) -> Dict[str, QWidget]:
        """
        Obtém todos os widgets do cabeçalho principal.

        Returns:
            Dicionário com os widgets do cabeçalho
        """
        widget_names = [
            'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
            'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
            'ABA_EXT_LBL', 'Z_EXT_LBL', 'DED_ESPEC_ENTRY'
        ]

        return {name: cls.safe_get_widget(name) for name in widget_names}

    @classmethod
    def get_form_widgets(cls, form_type: str) -> Dict[str, QWidget]:
        """
        Obtém todos os widgets de um formulário específico.

        Args:
            form_type: Tipo do formulário ('deducao', 'material', 'canal', 'espessura')

        Returns:
            Dicionário com os widgets do formulário
        """
        widget_maps = {
            'deducao': [
                'DED_MATER_COMB', 'DED_ESPES_COMB', 'DED_CANAL_COMB',
                'DED_VALOR_ENTRY', 'DED_OBSER_ENTRY', 'DED_FORCA_ENTRY',
                'LIST_DED', 'EDIT_DED'
            ],
            'material': [
                'MAT_NOME_ENTRY', 'MAT_DENS_ENTRY', 'MAT_ESCO_ENTRY',
                'MAT_ELAS_ENTRY', 'LIST_MAT', 'EDIT_MAT', 'MAT_BUSCA_ENTRY'
            ],
            'canal': [
                'CANAL_VALOR_ENTRY', 'CANAL_LARGU_ENTRY', 'CANAL_ALTUR_ENTRY',
                'CANAL_COMPR_ENTRY', 'CANAL_OBSER_ENTRY', 'LIST_CANAL',
                'EDIT_CANAL', 'CANAL_BUSCA_ENTRY'
            ],
            'espessura': [
                'ESP_VALOR_ENTRY', 'LIST_ESP', 'EDIT_ESP', 'ESP_BUSCA_ENTRY'
            ]
        }

        widget_names = widget_maps.get(form_type, [])
        return {name: cls.safe_get_widget(name) for name in widget_names}

    @classmethod
    def apply_operation_to_widgets(cls, widgets: List[QWidget],
                                   operation: Callable[[QWidget], Any],
                                   safe: bool = True) -> List[Any]:
        """
        Aplica uma operação a uma lista de widgets de forma segura.

        Args:
            widgets: Lista de widgets
            operation: Função a ser aplicada a cada widget
            safe: Se True, não para a execução em caso de erro

        Returns:
            Lista com os resultados da operação
        """
        results = []
        for widget in widgets:
            try:
                if widget is not None:
                    result = operation(widget)
                    results.append(result)
                else:
                    results.append(None)
            except AttributeError as e:
                if not safe:
                    raise
                print(f"Erro ao aplicar operação ao widget: {e}")
                results.append(None)
        return results

    @classmethod
    def batch_clear_widgets(cls, widget_names: List[str]) -> Dict[str, bool]:
        """
        Limpa múltiplos widgets em lote.

        Args:
            widget_names: Lista de nomes dos widgets a serem limpos

        Returns:
            Dicionário com o resultado de cada operação
        """
        results = {}
        for name in widget_names:
            widget = cls.safe_get_widget(name)
            results[name] = cls.clear_widget(widget)
        return results

    @classmethod
    def batch_set_widgets(cls, widget_values: Dict[str, str]) -> Dict[str, bool]:
        """
        Define valores em múltiplos widgets em lote.

        Args:
            widget_values: Dicionário com nome do widget e valor a ser definido

        Returns:
            Dicionário com o resultado de cada operação
        """
        results = {}
        for name, value in widget_values.items():
            widget = cls.safe_get_widget(name)
            results[name] = cls.set_widget_value(widget, value)
        return results

    @classmethod
    def validate_widgets_exist(cls, widget_names: List[str]) -> Dict[str, bool]:
        """
        Valida se uma lista de widgets existe e não é None.

        Args:
            widget_names: Lista de nomes dos widgets a serem validados

        Returns:
            Dicionário indicando se cada widget existe
        """
        return {name: cls.safe_get_widget(name) is not None for name in widget_names}


# Funções utilitárias globais para compatibilidade com código existente
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
