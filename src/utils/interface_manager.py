"""
Módulo para gerenciar a interface principal do aplicativo.
Sistema robusto com gerenciamento seguro de widgets.
"""

import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.components.cabecalho import cabecalho
from src.components.avisos import avisos
from src.components.dobra_90 import dobras
from src.components import botoes
from src.config import globals as g
from src.utils.interface import todas_funcoes
from src.utils.widget_state_manager import widget_state_manager


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

    for widget_name in widget_names:
        if hasattr(g, widget_name):
            setattr(g, widget_name, None)

    # Limpar widgets de dobras se existirem
    if hasattr(g, 'VALORES_W') and hasattr(g, 'N'):
        for w in g.VALORES_W:
            for i in range(1, g.N):
                widget_name = f'aba{i}_entry_{w}'
                if hasattr(g, widget_name):
                    setattr(g, widget_name, None)


def carregar_interface(var, layout):
    """
    Atualiza o cabeçalho e recria os widgets no layout com base no valor de var.
    Versão robusta com gerenciamento seguro de widgets.

    Args:
        var (int): Define o layout do cabeçalho.
                  1 para apenas o cabeçalho principal.
                  2 para cabeçalho com avisos.
        layout: Layout onde os widgets serão adicionados.
    """
    try:
        # Definir flag para indicar que a interface está sendo recarregada
        g.INTERFACE_RELOADING = True

        print(
            f'Iniciando carregamento da interface: EXP_V={g.EXP_V}, EXP_H={g.EXP_H}')

        # Capturar estado atual dos widgets ANTES de qualquer modificação
        if hasattr(g, 'MAT_COMB') and g.MAT_COMB is not None:
            print("Capturando estado atual dos widgets...")
            widget_state_manager.capture_current_state()
        else:
            print("Primeira execução - não há widgets para capturar")

        # Limpar widgets antigos no layout de forma segura
        print("Limpando layout anterior...")
        safe_clear_layout(layout)

        # Limpar referências globais APÓS capturar estado
        print("Limpando referências globais...")
        clear_global_widget_references()

        # Forçar processamento para garantir que tudo foi limpo
        safe_process_events()

        # Criar novos widgets
        print("Criando novos widgets...")

        # Adicionar o cabeçalho principal
        print("Carregando cabeçalho...")
        cabecalho_widget = cabecalho()
        layout.addWidget(cabecalho_widget, 0, 0)

        # Adicionar avisos se necessário
        if var == 2:
            print("Carregando avisos...")
            avisos_widget = avisos()
            layout.addWidget(avisos_widget, 0, 1)

        # Determinar número de abas baseado na expansão vertical
        num_abas = 10 if g.EXP_V else 5
        g.N = num_abas + 1  # +1 porque a função cria abas de 1 até (N-1)

        # Adicionar dobras
        print(f"Carregando dobras para valores W: {g.VALORES_W}")
        for w in g.VALORES_W:
            print(f"  Criando dobra para W={w}")
            dobras_widget = dobras(w)
            layout.addWidget(dobras_widget, 1, w - 1)

        # Adicionar botões
        print("Carregando botões...")
        botoes_widget = botoes.criar_botoes()
        layout.addWidget(botoes_widget, 2, 0, 1, 2)  # span 2 columns

        # Configurar layout
        print("Configurando layout...")
        layout.setRowStretch(0, 0)  # Cabeçalho: tamanho fixo
        layout.setRowStretch(1, 1)  # Dobras: expansível
        layout.setRowStretch(2, 0)  # Botões: tamanho fixo
        layout.setSpacing(5)

        # Configurar colunas
        max_cols = max(2, len(g.VALORES_W))
        for col in range(max_cols + 1):
            layout.setColumnStretch(col, 0)
            layout.setColumnMinimumWidth(col, 0)

        for col in range(len(g.VALORES_W)):
            layout.setColumnStretch(col, 1)

        # Processar eventos para garantir que widgets estejam prontos
        safe_process_events()

        # Desabilitar gerenciamento de estado durante todas_funcoes
        widget_state_manager.disable()

        print("Executando todas as funções...")
        try:
            todas_funcoes()
        except RuntimeError as e:
            print(f"Erro ao executar todas as funções: {e}")
            traceback.print_exc()
        finally:
            # Sempre reabilitar, mesmo em caso de erro
            widget_state_manager.enable()

        # Processar eventos novamente
        safe_process_events()

        # Restaurar estado dos widgets
        print("Restaurando estado dos widgets...")
        widget_state_manager.restore_widget_state()

        # Processar eventos finais
        safe_process_events()

        print("Interface carregada com sucesso!")
        print(widget_state_manager.get_cache_info())

        # Agendar limpeza final
        def cleanup_final():
            g.INTERFACE_RELOADING = False
            print("Interface loading finalizada")

        QTimer.singleShot(100, cleanup_final)

    except Exception as e:
        # Garantir limpeza mesmo em caso de erro
        widget_state_manager.enable()
        g.INTERFACE_RELOADING = False

        print(f"ERRO CRÍTICO no carregamento da interface: {e}")
        traceback.print_exc()
        raise


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
