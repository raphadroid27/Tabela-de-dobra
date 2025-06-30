"""
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
"""
from src.config import globals as g


def no_topo(form):
    """
    Define se a janela deve ficar sempre no topo ou não.
    """
    def set_topmost(window, on_top):
        if window and window.winfo_exists():
            window.attributes("-topmost", on_top)

    if g.NO_TOPO_VAR is not None:
        on_top_valor = g.NO_TOPO_VAR.get() == 1
        set_topmost(form, on_top_valor)


def posicionar_janela(form, posicao=None):
    """
    Posiciona a janela em relação à janela principal.
    """
    # Verificar se a janela principal existe
    if g.PRINC_FORM is None:
        return

    form.update_idletasks()
    g.PRINC_FORM.update_idletasks()
    largura_monitor = g.PRINC_FORM.winfo_screenwidth()
    posicao_x = g.PRINC_FORM.winfo_x()
    largura_janela = g.PRINC_FORM.winfo_width()
    largura_form = form.winfo_width()

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = g.PRINC_FORM.winfo_x() + ((g.PRINC_FORM.winfo_width() - largura_form) // 2)
        y = g.PRINC_FORM.winfo_y() + ((g.PRINC_FORM.winfo_height() - form.winfo_height()) // 2)
    elif posicao == 'direita':
        x = g.PRINC_FORM.winfo_x() + largura_janela + 10
        y = g.PRINC_FORM.winfo_y()
        if x + largura_form > largura_monitor:
            x = g.PRINC_FORM.winfo_x() - largura_form - 10
    elif posicao == 'esquerda':
        x = g.PRINC_FORM.winfo_x() - largura_form - 10
        y = g.PRINC_FORM.winfo_y()
        if x < 0:
            x = g.PRINC_FORM.winfo_x() + largura_janela + 10
    else:
        return

    form.geometry(f"+{x}+{y}")


def desabilitar_janelas():
    """
    Desabilita todas as janelas do aplicativo.
    """
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', True)
            form.focus_force()


def habilitar_janelas():
    """
    Habilita todas as janelas do aplicativo.
    """
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', False)
            form.focus_force()
