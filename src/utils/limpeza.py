"""
Módulo com funções utilitárias para limpeza da interface.
"""
from PySide6.QtWidgets import QLineEdit, QLabel, QComboBox
from src.config import globals as g
from src.utils.interface import todas_funcoes


def limpar_dobras():
    """
    Limpa os valores das dobras e atualiza os labels correspondentes.
    """
    def limpar_widgets(widgets, metodo, valor=""):
        """
        Limpa ou redefine widgets com base no método fornecido.

        Args:
            widgets (list): Lista de widgets a serem limpos.
            metodo (str): Método a ser chamado no widget (ex.: 'clear', 'setText').
            valor (str): Valor a ser usado no método (se aplicável).
        """
        for widget in widgets:
            if widget:
                if metodo == "clear":
                    if isinstance(widget, QLineEdit):
                        widget.clear()
                    elif isinstance(widget, QComboBox):
                        widget.clear()
                elif metodo == "setText":
                    if isinstance(widget, QLabel):
                        widget.setText(valor)

    # Obter widgets dinamicamente
    def obter_widgets(prefixo):
        return [
            getattr(g, f"{prefixo}{i}_label_{col}", None)
            for i in range(1, g.N)
            for col in g.VALORES_W
        ]

    # Limpar entradas e labels
    dobras = [getattr(g, f"aba{i}_entry_{col}", None) for i in range(1, g.N) for col in g.VALORES_W]
    medidas = obter_widgets("medidadobra")
    metades = obter_widgets("metadedobra")
    blanks = [getattr(g, f"medida_blank_label_{col}", None) for col in g.VALORES_W]
    metades_blanks = [getattr(g, f"metade_blank_label_{col}", None) for col in g.VALORES_W]

    # Limpar widgets
    limpar_widgets(dobras, "clear")
    limpar_widgets(medidas + metades + blanks + metades_blanks, "setText", "")

    # Limpar dedução específica
    if g.DED_ESPEC_ENTRY and isinstance(g.DED_ESPEC_ENTRY, QLineEdit):
        g.DED_ESPEC_ENTRY.clear()

    # Resetar valores globais
    g.DOBRAS_VALORES = []

    # Alterar a cor de fundo das entradas de dobras para branco
    for i in range(1, g.N):
        for col in g.VALORES_W:
            entry = getattr(g, f'aba{i}_entry_{col}', None)
            if entry and isinstance(entry, QLineEdit):
                entry.setStyleSheet("background-color: white;")

    # Verifique se o atributo existe antes de usá-lo
    aba1_entry = getattr(g, "aba1_entry_1", None)
    if aba1_entry and isinstance(aba1_entry, QLineEdit):
        aba1_entry.setFocus()


def limpar_tudo():
    """
    Limpa todos os campos e labels do aplicativo.
    """
    campos = [
        g.MAT_COMB, g.ESP_COMB, g.CANAL_COMB
    ]
    for campo in campos:
        if campo is not None and isinstance(campo, QComboBox):
            campo.setCurrentText('')  # Limpa o valor selecionado
            if campo != g.MAT_COMB:
                campo.clear()  # Limpa os valores disponíveis

    entradas = [
        g.RI_ENTRY, g.COMPR_ENTRY
    ]
    for entrada in entradas:
        if entrada is not None and isinstance(entrada, QLineEdit):
            entrada.clear()

    etiquetas = {
        g.K_LBL: "",
        g.DED_LBL: "",
        g.OFFSET_LBL: "",
        g.OBS_LBL: "",
        g.FORCA_LBL: "",
        g.ABA_EXT_LBL: "",
        g.Z_EXT_LBL: ""
    }
    for etiqueta, texto in etiquetas.items():
        if etiqueta is not None and isinstance(etiqueta, QLabel):
            etiqueta.setText(texto)

    limpar_dobras()
    todas_funcoes()

    if g.RAZAO_RIE_LBL and isinstance(g.RAZAO_RIE_LBL, QLabel):
        g.RAZAO_RIE_LBL.setText("N/A")
