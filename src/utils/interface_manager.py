"""
Módulo para gerenciar a interface principal do aplicativo.
Este módulo é responsável por carregar e recarregar a interface do aplicativo.
"""
from src.components.cabecalho import cabecalho
from src.components.avisos import avisos
from src.components.dobra_90 import dobras
from src.components import botoes
from src.config import globals as g
from src.utils.interface import todas_funcoes
from src.utils.classes.tooltip import ToolTip
from src.utils.widget_state_manager import widget_state_manager


def carregar_interface(var, layout):
    """
    Atualiza o cabeçalho e recria os widgets no layout com base no valor de var.
    Nova versão com gerenciamento robusto de estado dos widgets.

    Args:
        var (int): Define o layout do cabeçalho.
                   1 para apenas o cabeçalho principal.
                   2 para cabeçalho com avisos.
        layout: Layout onde os widgets serão adicionados.
    """
    try:
        # Limpar todos os tooltips ativos e widgets órfãos antes de recriar a interface
        ToolTip.cleanup_all_tooltips()
        
        # Capturar o estado atual dos widgets antes da recriação (apenas se há widgets para capturar)
        if hasattr(g, 'MAT_COMB') and g.MAT_COMB is not None:
            print("Capturando estado atual dos widgets...")
            widget_state_manager.capture_current_state()
        else:
            print("Primeira execução - não há widgets para capturar")

        print(f'Carregando interface: EXP_V={g.EXP_V}, EXP_H={g.EXP_H}')

        # Limpar widgets antigos no layout de forma mais robusta
        if hasattr(layout, 'count'):
            while layout.count():
                item = layout.takeAt(0)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.setParent(None)
                        widget.hide()
                        widget.deleteLater()

        # Forçar processamento de eventos para garantir limpeza
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.processEvents()

        # Adicionar o cabeçalho principal
        print("Carregando cabeçalho...")
        cabecalho_widget = cabecalho(None)
        layout.addWidget(cabecalho_widget, 0, 0)
        
        if var == 2:
            print("Carregando avisos...")
            avisos_widget = avisos(None)
            layout.addWidget(avisos_widget, 0, 1)

        print(f"Carregando dobras para valores W: {g.VALORES_W}")
        
        # Determinar número de abas baseado na expansão vertical
        num_abas = 10 if g.EXP_V else 5
        g.N = num_abas + 1  # +1 porque a função cria abas de 1 até (N-1)
        
        for w in g.VALORES_W:
            dobras_widget = dobras(None, w)
            layout.addWidget(dobras_widget, 1, w - 1)

        print("Carregando botões...")
        botoes_widget = botoes.criar_botoes(None)
        layout.addWidget(botoes_widget, 2, 0, 1, 2)  # span 2 columns
        
        # Configurar espaçamento entre os componentes principais
        layout.setRowStretch(0, 0)  # Cabeçalho: tamanho fixo
        layout.setRowStretch(1, 1)  # Dobras: expansível
        layout.setRowStretch(2, 0)  # Botões: tamanho fixo
        
        # Configurar espaçamento
        layout.setSpacing(5)
        
        # Configurar larguras das colunas de forma mais conservadora
        # Primeiro limpar apenas as colunas que realmente usamos
        max_cols = max(2, len(g.VALORES_W))  # No máximo 2 colunas
        for col in range(max_cols + 1):  # +1 para garantir limpeza
            layout.setColumnStretch(col, 0)
            layout.setColumnMinimumWidth(col, 0)
        
        # Configurar apenas as colunas que vamos usar
        for col in range(len(g.VALORES_W)):
            layout.setColumnStretch(col, 1)  # Colunas com largura igual na expansão

        # Forçar processamento de eventos para garantir que os widgets estejam prontos
        if app:
            app.processEvents()

        # Temporariamente desabilitar o sistema durante todas_funcoes para evitar capturas desnecessárias
        widget_state_manager.disable()
        
        print("Executando todas as funções...")
        try:
            todas_funcoes()
        except Exception as e:
            print(f"Erro ao executar todas as funções: {e}")

        # Reabilitar o sistema e restaurar o estado
        widget_state_manager.enable()
        
        # Restaurar o estado dos widgets após a criação completa
        print("Restaurando estado dos widgets...")
        widget_state_manager.restore_widget_state()

        # Forçar processamento de eventos após restauração
        if app:
            app.processEvents()
            
        print("Interface carregada com sucesso!")
        print(widget_state_manager.get_cache_info())
        
        # Agendar limpeza final após carregar interface
        from PySide6.QtCore import QTimer
        def cleanup_final():
            ToolTip.cleanup_all_tooltips()
        QTimer.singleShot(100, cleanup_final)
        
    except Exception as e:
        # Garantir que o sistema seja reabilitado mesmo em caso de erro
        widget_state_manager.enable()
        print(f"ERRO CRÍTICO no carregamento da interface: {e}")
        import traceback
        traceback.print_exc()
        raise
