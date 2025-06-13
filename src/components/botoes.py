"""
Módulo para criar os botões e checkbuttons na interface gráfica.
"""

import tkinter as tk
import src.utils.classes.dica_ferramenta as tp
from src.utils.cache_widgets import (
    limpar_entradas_rapido,
    limpar_labels_rapido,
    limpar_cabecalho_rapido,
)
from src.utils.cache_calculos import ui_debouncer


def criar_botoes(parent, app_principal):
    """
    Cria os botões e checkbuttons no frame inferior.

    Args:
        parent (tk.Frame): Frame onde os botões serão adicionados.
        app_principal (AppUI): Referência para a aplicação principal.

    Returns:
        tk.Frame: Frame contendo os botões
    """
    frame = tk.Frame(parent)

    # Configurar grid
    for i in range(2):
        frame.columnconfigure(i, weight=1)
        frame.rowconfigure(i, weight=1)
    # Checkbutton para expandir verticalmente
    chk_v = tk.Checkbutton(
        frame,
        text="Expandir Vertical",
        variable=app_principal.expandir_v,
        width=1,
        height=1,
        command=lambda: manipulador_expansao_v(app_principal),
    )
    chk_v.grid(row=0, column=0, sticky="we")

    # Checkbutton para expandir horizontalmente
    chk_h = tk.Checkbutton(
        frame,
        text="Expandir Horizontal",
        variable=app_principal.expandir_h,
        width=1,
        height=1,
        command=lambda: manipulador_expansao_h(app_principal),
    )
    chk_h.grid(row=0, column=1, sticky="we")  # Botão para limpar valores de dobras
    btn_limpar_dobras = tk.Button(
        frame,
        text="Limpar Dobras",
        command=lambda: (
            limpar_dobras_todas_colunas(app_principal)
            if hasattr(app_principal, "cabecalho_ui")
            else None
        ),
        width=15,
        bg="yellow",
    )
    btn_limpar_dobras.grid(row=1, column=0, sticky="we", padx=2)

    # Botão para limpar todos os valores
    btn_limpar_tudo = tk.Button(
        frame,
        text="Limpar Tudo",
        command=lambda: (
            limpar_tudo_todas_colunas(app_principal)
            if hasattr(app_principal, "cabecalho_ui")
            else None
        ),
        width=15,
        bg="red",
    )
    btn_limpar_tudo.grid(row=1, column=1, sticky="we", padx=2)

    # Adicionar tooltips
    tp.DicaFerramenta(chk_v, text="Expande a interface verticalmente")
    tp.DicaFerramenta(chk_h, text="Expande a interface horizontalmente")
    tp.DicaFerramenta(btn_limpar_dobras, text="Limpa as dobras")
    tp.DicaFerramenta(btn_limpar_tudo, text="Limpa todos os valores")

    return frame


def manipulador_expansao_h(app_principal):
    """
    Manipula a expansão horizontal da interface.
    """
    try:
        altura_atual = app_principal.janela_principal.winfo_height()

        if app_principal.expandir_h.get() == 1:
            # Expandir horizontalmente - adicionar segunda coluna
            app_principal.janela_principal.geometry(f"680x{altura_atual}")
            app_principal.valores_w = [1, 2]
        else:
            # Contrair horizontalmente - uma coluna apenas
            app_principal.janela_principal.geometry(f"340x{altura_atual}")
            app_principal.valores_w = [1]

        # Recarregar interface
        import src.app as app_module

        app_module.carregar_interface(app_principal)

    except ValueError as e:
        print(f"Erro ao expandir horizontalmente: {e}")


def manipulador_expansao_v(app_principal):
    """
    Manipula a expansão vertical da interface.
    """
    try:
        largura_atual = app_principal.janela_principal.winfo_width()

        if app_principal.expandir_v.get() == 1:
            # Expandir verticalmente - 11 linhas de dobra
            app_principal.janela_principal.geometry(f"{largura_atual}x500")
        else:
            # Contrair verticalmente - 6 linhas de dobra
            app_principal.janela_principal.geometry(f"{largura_atual}x400")
        # Recarregar interface
        import src.app as app_module

        app_module.carregar_interface(app_principal)

    except ValueError as e:
        print(f"Erro ao expandir verticalmente: {e}")


def limpar_dobras_todas_colunas(app_principal):
    """
    Limpa dobras em todas as colunas disponíveis.
    Versão otimizada usando widget cache.
    """
    if (
        hasattr(app_principal, "cabecalho_ui")
        and hasattr(app_principal, "dobras_ui")
        and app_principal.dobras_ui
    ):
        # Usar versões otimizadas de limpeza
        for w in app_principal.valores_w:
            if w in app_principal.dobras_ui:
                dobras_ui = app_principal.dobras_ui[w]

                # Limpeza otimizada de entradas e labels
                limpar_entradas_rapido(dobras_ui, w)
                limpar_labels_rapido(dobras_ui, w)

        # Limpar dedução específica
        if (
            hasattr(app_principal.cabecalho_ui, "deducao_especifica_widget")
            and app_principal.cabecalho_ui.deducao_especifica_widget
        ):
            app_principal.cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)

        # Resetar valores globais
        import src.config.globals as g

        g.DOBRAS_VALORES = []
        # Focar no primeiro campo usando cache
        if 1 in app_principal.dobras_ui:
            from src.utils.cache_widgets import obter_widget_em_cache

            aba1_entry = obter_widget_em_cache(app_principal.dobras_ui[1], "aba1_entry_1")
            if aba1_entry:
                aba1_entry.focus_set()


def limpar_tudo_todas_colunas(app_principal):
    """
    Limpa tudo em todas as colunas disponíveis.
    Versão otimizada usando widget cache e debounce.
    """
    if (
        hasattr(app_principal, "cabecalho_ui")
        and hasattr(app_principal, "dobras_ui")
        and app_principal.dobras_ui
    ):
        # Usar limpeza otimizada do cabeçalho
        limpar_cabecalho_rapido(app_principal.cabecalho_ui)

        # Limpar dobras usando versão otimizada
        limpar_dobras_todas_colunas(app_principal)

        # Executar todas as funções com debounce para evitar cálculos excessivos
        def delayed_update():
            from src.utils.interface import todas_funcoes

            for w in app_principal.valores_w:
                if w in app_principal.dobras_ui:
                    todas_funcoes(app_principal.cabecalho_ui, app_principal.dobras_ui[w])

        # Aplicar debounce para não executar múltiplas vezes
        ui_debouncer.debounce("limpar_tudo_update", delayed_update, 0.5)

        # Focar no combobox de material usando cache
        from src.utils.cache_widgets import obter_widget_em_cache

        material_widget = obter_widget_em_cache(app_principal.cabecalho_ui, "material_widget")
        if material_widget:
            material_widget.focus_set()
