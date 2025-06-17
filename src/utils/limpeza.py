'''
Módulo com funções utilitárias para limpeza da interface.
'''
import tkinter as tk
from src.config import globals as g
from src.utils.interface import todas_funcoes

def limpar_dobras():
    '''
    Limpa os valores das dobras e atualiza os labels correspondentes.
    '''
    def limpar_widgets(widgets, metodo, valor=""):
        '''
        Limpa ou redefine widgets com base no método fornecido.

        Args:
            widgets (list): Lista de widgets a serem limpos.
            metodo (str): Método a ser chamado no widget (ex.: 'delete', 'config').
            valor (str): Valor a ser usado no método (se aplicável).
        '''
        for widget in widgets:
            if widget:
                if metodo == "delete":
                    getattr(widget, metodo)(0, tk.END)
                else:
                    widget.config(text=valor)

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
    limpar_widgets(dobras, "delete")
    limpar_widgets(medidas + metades + blanks + metades_blanks, "config", "")

    # Limpar dedução específica
    if g.DED_ESPEC_ENTRY:
        g.DED_ESPEC_ENTRY.delete(0, tk.END)

    # Resetar valores globais
    g.DOBRAS_VALORES = []

    # Alterar a cor de fundo das entradas de dobras para branco
    for i in range(1, g.N):
        for col in g.VALORES_W:
            entry = getattr(g, f'aba{i}_entry_{col}', None)
            if entry:
                entry.config(bg="white")

    # Verifique se o atributo existe antes de usá-lo
    aba1_entry = getattr(g, "aba1_entry_1", None)
    if aba1_entry:
        aba1_entry.focus_set()


def limpar_tudo():
    '''
    Limpa todos os campos e labels do aplicativo.
    '''
    campos = [
        g.MAT_COMB, g.ESP_COMB, g.CANAL_COMB
    ]
    for campo in campos:
        campo.set('')  # Limpa o valor selecionado
        if campo != g.MAT_COMB:
            campo.configure(values=[])  # Limpa os valores disponíveis

    entradas = [
        g.RI_ENTRY, g.COMPR_ENTRY
    ]
    for entrada in entradas:
        entrada.delete(0, tk.END)

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
        etiqueta.config(text=texto)

    limpar_dobras()
    todas_funcoes()

    if g.RAZAO_RIE_LBL and g.RAZAO_RIE_LBL.winfo_exists():
        g.RAZAO_RIE_LBL.config(text="N/A")
