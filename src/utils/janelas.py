"""
Módulo com funções auxiliares para manipulação de janelas no aplicativo.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from src.config import globals as g


def no_topo(form):
    """
    Define se a janela deve ficar sempre no topo ou não.
    """
    def set_topmost(window, on_top):
        if window:
            if on_top:
                window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
            else:
                window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)
            window.show()

    if g.NO_TOPO_VAR is not None:
        on_top_valor = g.NO_TOPO_VAR
        set_topmost(form, on_top_valor)


def posicionar_janela(form, posicao=None):
    """
    Posiciona a janela em relação à janela principal.
    """
    # Verificar se a janela principal existe
    if g.PRINC_FORM is None:
        return

    screen = QApplication.primaryScreen()
    largura_monitor = screen.size().width()
    posicao_x = g.PRINC_FORM.x()
    largura_janela = g.PRINC_FORM.width()
    largura_form = form.width()

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = g.PRINC_FORM.x() + ((g.PRINC_FORM.width() - largura_form) // 2)
        y = g.PRINC_FORM.y() + ((g.PRINC_FORM.height() - form.height()) // 2)
    elif posicao == 'direita':
        x = g.PRINC_FORM.x() + largura_janela + 10
        y = g.PRINC_FORM.y()
        if x + largura_form > largura_monitor:
            x = g.PRINC_FORM.x() - largura_form - 10
    elif posicao == 'esquerda':
        x = g.PRINC_FORM.x() - largura_form - 10
        y = g.PRINC_FORM.y()
        if x < 0:
            x = g.PRINC_FORM.x() + largura_janela + 10
    else:
        return

    form.move(x, y)


def desabilitar_janelas():
    """
    Desabilita todas as janelas do aplicativo.
    """
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None:
            form.setEnabled(False)


def habilitar_janelas():
    """
    Habilita todas as janelas do aplicativo.
    """
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None:
            form.setEnabled(True)
