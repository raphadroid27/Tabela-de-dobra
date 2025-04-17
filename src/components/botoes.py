'''
Módulo para criar os botões e checkbuttons na interface gráfica.
Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
'''
import tkinter as tk
from src.components.dobra_90 import entradas_dobras
from src.utils.funcoes import limpar_dobras, limpar_tudo
import src.config.globals as g
from src.app import carregar_interface
import src.utils.tooltip as tp

def criar_botoes(root):
    """
    Cria os botões e checkbuttons no frame inferior.

    Args:
        frame_inferior (tk.Frame): Frame onde os botões serão adicionados.
        frame_superior (tk.Frame): Frame superior para manipulação de interface.
    """
    frame_botoes = tk.Frame(root)

    frame_botoes.columnconfigure(0, weight=1)
    frame_botoes.columnconfigure(1, weight=1)
    frame_botoes.rowconfigure(0, weight=1)
    frame_botoes.rowconfigure(1, weight=1)

    def expandir_v():
        largura_atual = g.PRINC_FORM.winfo_width()

        if g.EXP_V.get() == 1:
            g.PRINC_FORM.geometry(f"{largura_atual}x500")
            for w in g.VALORES_W:
                entradas_dobras(11, w)
            carregar_interface(1, root)
        else:
            g.PRINC_FORM.geometry(f"{largura_atual}x400")
            for w in g.VALORES_W:
                entradas_dobras(6, w)
            carregar_interface(1, root)

        # Verificar se avisos devem aparecer
        if g.EXP_H.get() == 1:
            carregar_interface(2, root)

    def expandir_h():
        altura_atual = g.PRINC_FORM.winfo_height()
        if g.EXP_H.get() == 1:
            g.PRINC_FORM.geometry(f'680x{altura_atual}')  # Define a altura atual e a nova largura
            g.VALORES_W = [1, 2]
            carregar_interface(2, root)
        else:
            g.PRINC_FORM.geometry(f'340x{altura_atual}')  # Define a altura atual e a nova largura
            g.VALORES_W = [1]
            carregar_interface(1, root)

        # Verificar se avisos devem aparecer
        if g.EXP_H.get() == 1:
            carregar_interface(2, root)

    tk.Checkbutton(
        frame_botoes,
        text="Expandir Vertical",
        variable=g.EXP_V,
        width=1,
        height=1,
        command=expandir_v
    ).grid(row=0, column=0, sticky='we')

    tk.Checkbutton(
        frame_botoes,
        text="Expandir Horizontal",
        variable=g.EXP_H,
        width=1,
        height=1,
        command=expandir_h
    ).grid(row=0, column=1, sticky='we')

    # Botão para limpar valores de dobras
    tk.Button(frame_botoes,
              text="Limpar Dobras",
              command=limpar_dobras,
              width=15,
              bg='yellow').grid(row=1, column=0, sticky='we', padx=2)

    # Botão para limpar todos os valores
    tk.Button(frame_botoes,
              text="Limpar Tudo",
              command=limpar_tudo,
              width=15,
              bg='red').grid(row=1, column=1, sticky='we', padx=2)

    tp.ToolTip(frame_botoes.grid_slaves(row=0, column=0)[0], text="Expande a interface verticalmente")
    tp.ToolTip(frame_botoes.grid_slaves(row=0, column=1)[0], text="Expande a interface horizontalmente")
    tp.ToolTip(frame_botoes.grid_slaves(row=1, column=0)[0], text="Limpa as dobras")
    tp.ToolTip(frame_botoes.grid_slaves(row=1, column=1)[0], text="Limpa todos os valores")

    return frame_botoes
