"""
Módulo para criar os botões e checkbuttons na interface gráfica.
Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
"""
import tkinter as tk
from src.components.dobra_90 import entradas_dobras
from src.utils.limpeza import limpar_dobras, limpar_tudo
import src.config.globals as g
import src.utils.classes.tooltip as tp


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
        if g.PRINC_FORM is None:
            return

        largura_atual = g.PRINC_FORM.winfo_width()

        if g.EXP_V is not None and g.EXP_V.get() == 1:
            g.PRINC_FORM.geometry(f"{largura_atual}x500")
            for w in g.VALORES_W:
                entradas_dobras(11, w)
        else:
            g.PRINC_FORM.geometry(f"{largura_atual}x400")
            for w in g.VALORES_W:
                entradas_dobras(6, w)

        # Recarregar a interface com base no estado da expansão horizontal
        if g.CARREGAR_INTERFACE_FUNC is not None and callable(g.CARREGAR_INTERFACE_FUNC):
            colunas = 2 if (g.EXP_H is not None and g.EXP_H.get() == 1) else 1
            g.CARREGAR_INTERFACE_FUNC(colunas, root)  # pylint: disable=not-callable

    def expandir_h():
        if g.PRINC_FORM is None:
            return

        altura_atual = g.PRINC_FORM.winfo_height()
        if g.EXP_H is not None and g.EXP_H.get() == 1:
            g.PRINC_FORM.geometry(f'680x{altura_atual}')
            g.VALORES_W = [1, 2]
        else:
            g.PRINC_FORM.geometry(f'340x{altura_atual}')
            g.VALORES_W = [1]

        # Recarregar a interface com base no estado da expansão horizontal
        if g.CARREGAR_INTERFACE_FUNC is not None and callable(g.CARREGAR_INTERFACE_FUNC):
            colunas = 2 if (g.EXP_H is not None and g.EXP_H.get() == 1) else 1
            g.CARREGAR_INTERFACE_FUNC(colunas, root)  # pylint: disable=not-callable

    # Verificar se as variáveis existem, se não, criar
    if g.EXP_V is None:
        g.EXP_V = tk.IntVar()
    if g.EXP_H is None:
        g.EXP_H = tk.IntVar()

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
              bg='lightyellow').grid(row=1, column=0, sticky='we', padx=2)

    # Botão para limpar todos os valores
    tk.Button(frame_botoes,
              text="Limpar Tudo",
              command=limpar_tudo,
              width=15,
              bg="lightcoral").grid(row=1, column=1, sticky='we', padx=2)

    tp.ToolTip(frame_botoes.grid_slaves(row=0, column=0)[0],
               text="Expande a interface verticalmente")
    tp.ToolTip(frame_botoes.grid_slaves(row=0, column=1)[0],
               text="Expande a interface horizontalmente")
    tp.ToolTip(frame_botoes.grid_slaves(row=1, column=0)[0],
               text="Limpa as dobras")
    tp.ToolTip(frame_botoes.grid_slaves(row=1, column=1)[0],
               text="Limpa todos os valores")

    return frame_botoes
