"""
Módulo com funções utilitárias para limpeza da interface.
"""
from PySide6.QtWidgets import QLabel, QComboBox
from src.config import globals as g
from src.utils.interface import todas_funcoes
from src.utils.widget import WidgetManager


class Limpeza:
    """Classe utilitária para limpeza de campos e labels na interface do aplicativo.
    Inclui métodos para limpar dobras, campos de entrada, comboboxes e labels.
    """
    @staticmethod
    def limpar_dobras():
        """
        Limpa os valores das dobras e atualiza os labels correspondentes.
        Versão otimizada usando o WidgetManager.
        """
        # Limpar todos os widgets de dobra para cada valor W
        if hasattr(g, 'VALORES_W'):
            for w in g.VALORES_W:
                WidgetManager.clear_dobra_widgets(w)

        # Limpar dedução específica
        ded_espec_entry = WidgetManager.safe_get_widget('DED_ESPEC_ENTRY')
        WidgetManager.clear_widget(ded_espec_entry)

        # Focar no primeiro campo de entrada se existir
        primeiro_entry = WidgetManager.safe_get_widget("aba1_entry_1")
        if primeiro_entry and hasattr(primeiro_entry, 'setFocus'):
            primeiro_entry.setFocus()

    @staticmethod
    def limpar_tudo():
        """
        Limpa todos os campos e labels do aplicativo.
        Versão otimizada usando o WidgetManager.
        """
        # Limpar comboboxes do cabeçalho
        cabecalho_widgets = WidgetManager.get_cabecalho_widgets()

        # Limpar comboboxes principais (preservar material para último)
        combobox_names = ['ESP_COMB', 'CANAL_COMB']
        for name in combobox_names:
            widget = cabecalho_widgets.get(name)
            if widget and isinstance(widget, QComboBox):
                WidgetManager.set_widget_value(widget, '')  # Limpa seleção
                widget.clear()  # Limpa itens

        # Limpar material por último (só a seleção, não os itens)
        mat_comb = cabecalho_widgets.get('MAT_COMB')
        if mat_comb and isinstance(mat_comb, QComboBox):
            WidgetManager.set_widget_value(mat_comb, '')

        # Limpar campos de entrada
        entrada_names = ['RI_ENTRY', 'COMPR_ENTRY']
        for name in entrada_names:
            widget = cabecalho_widgets.get(name)
            WidgetManager.clear_widget(widget)

        # Limpar labels com valores específicos
        label_values = {
            'K_LBL': "",
            'DED_LBL': "",
            'OFFSET_LBL': "",
            'OBS_LBL': "",
            'FORCA_LBL': "",
            'ABA_EXT_LBL': "",
            'Z_EXT_LBL': ""
        }
        WidgetManager.batch_set_widgets(label_values)

        Limpeza.limpar_dobras()
        todas_funcoes()

        if g.RAZAO_RIE_LBL and isinstance(g.RAZAO_RIE_LBL, QLabel):
            g.RAZAO_RIE_LBL.setText("N/A")


limpar_tudo = Limpeza.limpar_tudo
limpar_dobras = Limpeza.limpar_dobras
