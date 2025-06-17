'''
Módulo para gerenciar a interface principal do aplicativo.
Este módulo é responsável por carregar e recarregar a interface do aplicativo.
'''
from src.components.cabecalho import cabecalho
from src.components.avisos import avisos
from src.components.dobra_90 import dobras
from src.components import botoes
from src.config import globals as g
from src.utils.interface import (salvar_valores_cabecalho,
                                 restaurar_valores_cabecalho,
                                 restaurar_valores_dobra,
                                 todas_funcoes)


def carregar_interface(var, frame_superior):
    '''
    Atualiza o cabeçalho e recria os widgets no frame de dobras com base no valor de var.

    Args:
        var (int): Define o layout do cabeçalho.
                   1 para apenas o cabeçalho principal.
                   2 para cabeçalho com avisos.
        frame_superior (tk.Frame): Frame onde os widgets serão adicionados.
    '''
    # Salvar os valores dos widgets do cabeçalho
    # Isso deve ser feito antes de recriar os widgets
    salvar_valores_cabecalho()

    print(f'g.EXP_V: {g.EXP_V.get()}')
    print(f'g.EXP_H: {g.EXP_H.get()}')

    # Limpar widgets antigos no frame superior
    for widget in frame_superior.winfo_children():
        widget.destroy()

    # Adicionar o cabeçalho principal
    cabecalho(frame_superior).grid(row=0, column=0, sticky='wens', ipadx=2, ipady=2)
    if var == 2:
        avisos(frame_superior).grid(row=0, column=1, sticky='wens', ipadx=2, ipady=2)

    for w in g.VALORES_W:
        dobras(frame_superior, w).grid(row=1, column=w - 1, sticky='we', ipadx=2, ipady=2)

    botoes.criar_botoes(frame_superior).grid(row=2,
                                             column=0,
                                             sticky='wens',
                                             ipadx=2,
                                             ipady=2,
                                             columnspan=2)

    for w in g.VALORES_W:
        restaurar_valores_dobra(w)

    restaurar_valores_cabecalho()
    todas_funcoes()
