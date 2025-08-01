"""
Módulo para gerenciar a interface principal do aplicativo.
Sistema robusto com gerenciamento seguro de widgets.
"""

import traceback
from PySide6.QtWidgets import QApplication, QGridLayout
from src.components.cabecalho import cabecalho
from src.components.avisos import avisos
from src.components.dobra_90 import dobras
from src.components import botoes
from src.config import globals as g
from src.utils.interface import todas_funcoes, calcular_valores
from src.utils.widget import widget_state_manager
from src.utils import utilitarios
from src.utils.utilitarios import tem_configuracao_dobras_valida


def safe_process_events():
    """Processa eventos de forma segura."""
    app = QApplication.instance()
    if app:
        app.processEvents()


def safe_clear_layout(layout):
    """
    Limpa um layout de forma segura, deletando widgets adequadamente.

    Args:
        layout: Layout a ser limpo
    """
    if not hasattr(layout, 'count'):
        return

    # Primeiro, remover todos os itens do layout
    items_to_remove = []
    while layout.count():
        item = layout.takeAt(0)
        if item:
            items_to_remove.append(item)

    # Depois, deletar os widgets
    for item in items_to_remove:
        if item:
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()

    # Forçar processamento para garantir limpeza
    safe_process_events()


def clear_global_widget_references():
    """Limpa referências globais de widgets antes da recriação."""
    widget_names = [
        'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
        'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
        'ABA_EXT_LBL', 'Z_EXT_LBL', 'DED_ESPEC_ENTRY'
    ]

    # Limpar widgets de dobras dinamicamente
    if tem_configuracao_dobras_valida():
        for w in g.VALORES_W:
            for i in range(1, 11):  # Limpar até o máximo de abas possível
                widget_names.extend([
                    f'aba{i}_entry_{w}',
                    f'medidadobra{i}_label_{w}',
                    f'metadedobra{i}_label_{w}'
                ])
            widget_names.extend([
                f'medida_blank_label_{w}',
                f'metade_blank_label_{w}'
            ])

    for widget_name in widget_names:
        if hasattr(g, widget_name):
            setattr(g, widget_name, None)


def carregar_interface(var, layout):
    """
    Atualiza o cabeçalho e recria os widgets no layout com base no valor de var.
    A atualização da interface é bloqueada para acelerar o processo.
    """
    if not g.PRINC_FORM:
        return

    try:
        # OTIMIZAÇÃO: Desabilita a atualização da UI para evitar repinturas custosas
        g.PRINC_FORM.setUpdatesEnabled(False)
        g.INTERFACE_RELOADING = True

        print(
            f'Iniciando carregamento da interface: EXP_V={g.EXP_V}, EXP_H={g.EXP_H}')

        # 1. Capturar e limpar estado anterior
        _preparar_interface_reload(layout)

        # 2. Criar novos widgets
        _criar_widgets_interface(var, layout)

        # 3. Configurar layout
        _configurar_layout_interface(layout)

        # 4. Executar funções e restaurar estado
        _finalizar_interface_reload()

    except RuntimeError as e:
        _tratar_erro_interface_reload(e)
    finally:
        # OTIMIZAÇÃO: Reabilita a atualização da UI e força uma repintura imediata
        if g.PRINC_FORM:
            g.PRINC_FORM.setUpdatesEnabled(True)
            g.PRINC_FORM.repaint()  # Força a repintura imediata dos widgets
            app = QApplication.instance()
            if app:
                app.processEvents()  # Garante que a repintura seja processada
        # Define a flag como falsa de forma síncrona
        g.INTERFACE_RELOADING = False


def _preparar_interface_reload(layout):
    """Prepara a interface para recarregamento."""
    # Capturar estado atual dos widgets
    if hasattr(g, 'MAT_COMB') and g.MAT_COMB is not None:
        print("Capturando estado atual dos widgets...")
        widget_state_manager.capture_current_state()
    else:
        print("Primeira execução - não há widgets para capturar")

    # Limpar widgets antigos
    print("Limpando layout anterior...")
    safe_clear_layout(layout)

    print("Limpando referências globais...")
    clear_global_widget_references()

    safe_process_events()


def _criar_widgets_interface(var, layout):
    """Cria os widgets da interface."""
    print("Criando novos widgets...")

    # Cabeçalho principal
    cabecalho_widget = cabecalho()
    layout.addWidget(cabecalho_widget, 0, 0)

    # Avisos se necessário (expandido horizontalmente)
    if var == 2:
        avisos_widget = avisos()
        layout.addWidget(avisos_widget, 0, 1)

    # Configurar número de abas (expandido verticalmente)
    num_abas = 10 if g.EXP_V else 5
    g.N = num_abas + 1

    # Dobras
    for i, w_val in enumerate(g.VALORES_W):
        dobras_widget = dobras(w_val)
        layout.addWidget(dobras_widget, 1, i)

    # Botões
    botoes_widget = botoes.criar_botoes()
    layout.addWidget(botoes_widget, 2, 0, 1, len(g.VALORES_W))


def _configurar_layout_interface(layout):
    """Configura o layout da interface."""
    print("Configurando layout...")
    layout.setRowStretch(0, 0)  # Cabeçalho: tamanho fixo
    layout.setRowStretch(1, 1)  # Dobras: expansível
    layout.setRowStretch(2, 0)  # Botões: tamanho fixo
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    # Configurar colunas
    for col in range(layout.columnCount()):
        layout.setColumnStretch(col, 0 if col > len(g.VALORES_W) - 1 else 1)


def _finalizar_interface_reload():
    """Finaliza o recarregamento da interface."""
    # Desabilitar gerenciamento de estado durante `todas_funcoes` para evitar loops
    widget_state_manager.disable()
    print("Executando todas as funções de preenchimento...")
    try:
        todas_funcoes()
    except RuntimeError as e:
        print(f"Erro ao executar todas as funções: {e}")
        traceback.print_exc()
    finally:
        widget_state_manager.enable()

    # Restaurar estado dos widgets
    print("Restaurando estado dos widgets...")
    widget_state_manager.restore_widget_state()

    # Recalcular todos os valores com base no estado restaurado
    print("Recalculando valores finais...")
    calcular_valores()

    print("Interface carregada com sucesso!")
    print(widget_state_manager.get_cache_info())


def _tratar_erro_interface_reload(e):
    """Trata erros durante o recarregamento da interface."""
    widget_state_manager.enable()
    g.INTERFACE_RELOADING = False
    print(f"ERRO CRÍTICO no carregamento da interface: {e}")
    traceback.print_exc()
    # Não relançar a exceção para tentar manter o app funcional
    # raise e


def reload_interface_safely():
    """Recarrega a interface de forma segura com tratamento de erros."""
    try:
        if hasattr(g, 'MAIN_LAYOUT') and g.MAIN_LAYOUT:
            var = 2 if g.EXP_H else 1
            carregar_interface(var, g.MAIN_LAYOUT)
        else:
            print("Layout principal não encontrado")
    except RuntimeError as e:
        print(f"Erro ao recarregar interface: {e}")
        traceback.print_exc()


def configurar_frame_principal(parent):
    """Configura o frame principal com colunas e linhas padrão."""
    # Esta função parece não ser mais usada, mas mantida por segurança.
    frame_principal = parent
    layout = QGridLayout(frame_principal)
    frame_principal.setLayout(layout)
    utilitarios.aplicar_medida_borda_espaco(layout)

    if not parent.layout():
        parent_layout = QGridLayout(parent)
        parent.setLayout(parent_layout)

    parent.layout().addWidget(frame_principal)
    return frame_principal
