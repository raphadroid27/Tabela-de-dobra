'''
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
'''
import tkinter as tk
from src.config import globals as g

def no_topo(form, app_principal):
    '''
    Define se a janela deve ficar sempre no topo ou não.
    '''
    def set_topmost(window, on_top):
        if window and window.winfo_exists():
            window.attributes("-topmost",on_top)

    on_top_valor = app_principal.no_topo_var.get() == 1
    set_topmost(form, on_top_valor)

def posicionar_janela(form, app_principal, posicao=None):
    '''
    Posiciona a janela em relação à janela principal.
    '''
    form.update_idletasks()
    app_principal.janela_principal.update_idletasks()
    largura_monitor = app_principal.janela_principal.winfo_screenwidth()
    posicao_x = app_principal.janela_principal.winfo_x()
    largura_janela = app_principal.janela_principal.winfo_width()
    largura_form = form.winfo_width()

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = app_principal.janela_principal.winfo_x() + ((app_principal.janela_principal.winfo_width() - largura_form) // 2)
        y = app_principal.janela_principal.winfo_y() + ((app_principal.janela_principal.winfo_height() - form.winfo_height()) // 2)
    elif posicao == 'direita':
        x = app_principal.janela_principal.winfo_x() + largura_janela + 10
        y = app_principal.janela_principal.winfo_y()
        if x + largura_form > largura_monitor:
            x = app_principal.janela_principal.winfo_x() - largura_form - 10
    elif posicao == 'esquerda':
        x = app_principal.janela_principal.winfo_x() - largura_form - 10
        y = app_principal.janela_principal.winfo_y()
        if x < 0:
            x = app_principal.janela_principal.winfo_x() + largura_janela + 10
    else:
        return

    form.geometry(f"+{x}+{y}")

def obter_todas_janelas_toplevel(app_principal, excluir_janela=None):
    '''
    Obtém todas as janelas Toplevel abertas do aplicativo.
    
    Args:
        app_principal: Instância do aplicativo principal
        excluir_janela: Janela que deve ser excluída da lista (por exemplo, o próprio auten_form)
    '''
    janelas = []
    
    def buscar_toplevel(widget):
        for child in widget.winfo_children():
            if isinstance(child, tk.Toplevel):
                # Só adiciona se não for a janela a ser excluída
                if excluir_janela is None or child != excluir_janela:
                    janelas.append(child)
            # Continua a busca recursivamente
            buscar_toplevel(child)
    
    # Buscar a partir da janela principal
    if app_principal and app_principal.janela_principal:
        buscar_toplevel(app_principal.janela_principal)
    
    return janelas

def desabilitar_janelas(app_principal, excluir_janela=None):
    '''
    Desabilita todas as janelas do aplicativo, incluindo a principal e todas as Toplevel abertas,
    exceto a janela especificada em excluir_janela.
    
    Args:
        app_principal: Instância do aplicativo principal
        excluir_janela: Janela que deve permanecer habilitada (por exemplo, auten_form)
    '''
    if not app_principal:
        return
        
    # Obter todas as janelas Toplevel abertas, excluindo a especificada
    janelas_toplevel = obter_todas_janelas_toplevel(app_principal, excluir_janela)
    
    # Lista de todas as janelas (principal + toplevel), excluindo a janela especificada
    forms = [app_principal.janela_principal] + janelas_toplevel
    
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', True)
            form.focus_force()

def habilitar_janelas(app_principal):
    '''
    Habilita todas as janelas do aplicativo, incluindo a principal e todas as Toplevel abertas.
    '''
    if not app_principal:
        return
        
    # Obter todas as janelas Toplevel abertas
    janelas_toplevel = obter_todas_janelas_toplevel(app_principal)
    
    # Lista de todas as janelas (principal + toplevel)
    forms = [app_principal.janela_principal] + janelas_toplevel
    
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', False)
            form.focus_force()
