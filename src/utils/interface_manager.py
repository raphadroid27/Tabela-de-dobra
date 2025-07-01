"""
Módulo para gerenciar a interface principal do aplicativo.
Este módulo é responsável por carregar e recarregar a interface do aplicativo.
"""
from src.components.cabecalho import cabecalho
from src.components.avisos import avisos
from src.components.dobra_90 import dobras
from src.components import botoes
from src.config import globals as g
from src.utils.interface import (salvar_valores_cabecalho,
                                 restaurar_valores_cabecalho,
                                 restaurar_valores_dobra,
                                 todas_funcoes)
from src.utils.classes.tooltip import ToolTip


def carregar_interface(var, layout):
    """
    Atualiza o cabeçalho e recria os widgets no layout com base no valor de var.
    Nova versão com melhor gerenciamento de widgets órfãos.

    Args:
        var (int): Define o layout do cabeçalho.
                   1 para apenas o cabeçalho principal.
                   2 para cabeçalho com avisos.
        layout: Layout onde os widgets serão adicionados.
    """
    try:
        # Limpar todos os tooltips ativos e widgets órfãos antes de recriar a interface
        ToolTip.cleanup_all_tooltips()
        
        # Salvar os valores dos widgets do cabeçalho
        # Isso deve ser feito antes de recriar os widgets
        salvar_valores_cabecalho()

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

        print("Restaurando valores de dobra...")
        for w in g.VALORES_W:
            try:
                restaurar_valores_dobra(w)
            except Exception as e:
                print(f"Erro ao restaurar valores dobra {w}: {e}")

        print("Executando todas as funções...")
        try:
            todas_funcoes()
        except Exception as e:
            print(f"Erro ao executar todas as funções: {e}")

        print("Restaurando valores do cabeçalho...")
        try:
            restaurar_valores_cabecalho()
        except Exception as e:
            print(f"Erro ao restaurar valores do cabeçalho: {e}")
            
        print("Interface carregada com sucesso!")
        
        # Agendar limpeza final após carregar interface
        from PySide6.QtCore import QTimer
        def cleanup_final():
            ToolTip.cleanup_all_tooltips()
        QTimer.singleShot(100, cleanup_final)
        
    except Exception as e:
        print(f"ERRO CRÍTICO no carregamento da interface: {e}")
        import traceback
        traceback.print_exc()
        raise
