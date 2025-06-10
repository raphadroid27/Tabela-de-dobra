'''
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
'''
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

def desabilitar_janelas(app_principal):
    '''
    Desabilita todas as janelas do aplicativo.
    '''
    forms = [app_principal.janela_principal]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', True)
            form.focus_force()

def habilitar_janelas(app_principal):
    '''
    Habilita todas as janelas do aplicativo.
    '''
    forms = [app_principal.janela_principal]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', False)
            form.focus_force()
