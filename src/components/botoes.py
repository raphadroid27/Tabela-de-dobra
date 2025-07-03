"""
Módulo para criar os botões e checkbuttons na interface gráfica.
Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
"""
from PySide6.QtWidgets import QWidget, QGridLayout, QCheckBox, QPushButton, QApplication
from PySide6.QtCore import Qt, QTimer
from src.utils.limpeza import limpar_dobras, limpar_tudo
import src.config.globals as g
import src.utils.classes.tooltip as tp


def criar_botoes(root):
    """
    Cria os botões e checkbuttons no frame inferior com nova lógica de expansão.

    Args:
        root: Widget pai onde os botões serão adicionados.
    """
    frame_botoes = QWidget()
    layout = QGridLayout(frame_botoes)
    
    # Configurar espaçamento e margens
    layout.setSpacing(5)  # Espaçamento entre widgets
    layout.setContentsMargins(5, 5, 5, 5)  # Margens internas

    class ExpansionManager:
        """Gerencia a expansão da interface de forma robusta"""
        
        def __init__(self):
            self.is_updating = False
            self.cleanup_timer = QTimer()
            self.cleanup_timer.setSingleShot(True)
            self.cleanup_timer.timeout.connect(self.force_cleanup_orphans)
        
        def force_cleanup_orphans(self):
            """Remove todas as janelas órfãs - usa função centralizada"""
            try:
                # Importar e usar a função centralizada de limpeza
                from src.app import cleanup_orphaned_windows
                cleanup_orphaned_windows()
            except ImportError:
                pass
                
            except:
                pass
        
        def update_interface_size(self, exp_h, exp_v):
            """Atualiza o tamanho da interface baseado nos estados de expansão"""
            if self.is_updating or not g.PRINC_FORM:
                return
            
            self.is_updating = True
            
            try:
                # Limpar tooltips e widgets órfãos antes da atualização
                tp.ToolTip.cleanup_all_tooltips()
                self.force_cleanup_orphans()
                
                # Calcular novo tamanho e configuração conforme especificado
                # Sem expansão: 340x400, 1 coluna, 5 linhas (Aba 1-5 + Blank)
                # Só horizontal: 680x400, 2 colunas, 5 linhas (Aba 1-5 + Blank)
                # Só vertical: 340x500, 1 coluna, 10 linhas (Aba 1-10 + Blank)  
                # Ambas: 680x500, 2 colunas, 10 linhas (Aba 1-10 + Blank)
                
                largura = 680 if exp_h else 340
                altura = 590 if exp_v else 460
                colunas = 2 if exp_h else 1
                num_abas = 10 if exp_v else 5
                
                # Atualizar estados globais
                g.EXP_H = exp_h
                g.EXP_V = exp_v
                g.VALORES_W = [1, 2] if exp_h else [1]
                
                print(f"Atualizando interface: {largura}x{altura}, {colunas} colunas, {num_abas} abas")
                
                # Aplicar setFixedSize para o tamanho atual (baseado na expansão)
                g.PRINC_FORM.setFixedSize(largura, altura)
                
                # Recarregar interface se necessário
                if hasattr(g, 'CARREGAR_INTERFACE_FUNC') and callable(g.CARREGAR_INTERFACE_FUNC):
                    g.CARREGAR_INTERFACE_FUNC(colunas, g.MAIN_LAYOUT)
                
                # Forçar limpeza completa do layout quando voltando ao estado normal
                if not exp_h and not exp_v:  # Estado normal 340x460
                    print("Estado normal detectado - aplicando ajustes básicos...")
                    # Aplicar apenas ajustes básicos, sem correção agressiva
                    QTimer.singleShot(100, lambda: self._basic_layout_fix())
                
                # Forçar atualização do layout para evitar espaços laterais
                if g.MAIN_LAYOUT:
                    g.MAIN_LAYOUT.invalidate()
                    g.MAIN_LAYOUT.activate()
                
                # Processar eventos para garantir atualização visual
                app = QApplication.instance()
                if app:
                    app.processEvents()
                
                # Nota: O número de abas é agora controlado pelo interface_manager.py
                
                # Restaurar configuração final após delay
                def restore_limits():
                    if g.PRINC_FORM:
                        # Manter o tamanho fixo baseado no estado atual de expansão
                        final_largura = 680 if g.EXP_H else 340
                        final_altura = 590 if g.EXP_V else 460
                        g.PRINC_FORM.setFixedSize(final_largura, final_altura)
                        
                        # Forçar reajuste completo do layout para eliminar espaços laterais
                        if g.MAIN_LAYOUT:
                            g.MAIN_LAYOUT.invalidate()
                            g.MAIN_LAYOUT.activate()
                            g.MAIN_LAYOUT.update()
                        
                        # Atualizar widget central
                        central_widget = g.PRINC_FORM.centralWidget()
                        if central_widget:
                            central_widget.updateGeometry()
                            central_widget.adjustSize()
                        
                        # Processar eventos novamente para garantir atualização
                        app = QApplication.instance()
                        if app:
                            app.processEvents()
                            
                    self.is_updating = False
                
                QTimer.singleShot(200, restore_limits)  # Aumentado para 200ms para melhor ajuste
                
                # Agendar limpeza de órfãos após mudanças
                self.cleanup_timer.start(300)  # Aumentado para 300ms
                
            except:
                self.is_updating = False
        
        def _basic_layout_fix(self):
            """Correção básica e conservadora para o layout no estado normal."""
            try:
                if not g.PRINC_FORM or not g.MAIN_LAYOUT:
                    return
                
                print("Aplicando ajuste básico do layout...")
                
                # Apenas resetar a segunda coluna se ela existir
                g.MAIN_LAYOUT.setColumnStretch(1, 0)
                
                # Garantir que a primeira coluna está configurada
                g.MAIN_LAYOUT.setColumnStretch(0, 1)
                
                # Forçar tamanho da janela
                g.PRINC_FORM.setFixedSize(340, 460)
                
                print("Ajuste básico aplicado!")
                
            except Exception as e:
                print(f"Erro no ajuste básico: {e}")

    # Criar gerenciador de expansão
    expansion_manager = ExpansionManager()
    
    def on_expandir_v(checked):
        """Callback para expansão vertical"""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(g.EXP_H, checked)

    def on_expandir_h(checked):
        """Callback para expansão horizontal"""
        if not expansion_manager.is_updating:
            expansion_manager.update_interface_size(checked, g.EXP_V)

    # Inicializar valores se não existirem
    if not hasattr(g, 'EXP_V') or g.EXP_V is None:
        g.EXP_V = False
    if not hasattr(g, 'EXP_H') or g.EXP_H is None:
        g.EXP_H = False

    # Checkbox para expandir vertical
    exp_v_check = QCheckBox("Expandir Vertical")
    exp_v_check.setChecked(g.EXP_V)
    exp_v_check.setFixedHeight(20)  # Altura fixa
    exp_v_check.toggled.connect(on_expandir_v)
    layout.addWidget(exp_v_check, 0, 0)

    # Checkbox para expandir horizontal
    exp_h_check = QCheckBox("Expandir Horizontal")
    exp_h_check.setChecked(g.EXP_H)
    exp_h_check.setFixedHeight(20)  # Altura fixa
    exp_h_check.toggled.connect(on_expandir_h)
    layout.addWidget(exp_h_check, 0, 1)

    # Botão para limpar valores de dobras
    limpar_dobras_btn = QPushButton("🧹 Limpar Dobras")
    limpar_dobras_btn.clicked.connect(limpar_dobras)
    limpar_dobras_btn.setFixedHeight(20)  # Altura fixa
    limpar_dobras_btn.setStyleSheet("""
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """)
    layout.addWidget(limpar_dobras_btn, 1, 0)

    # Botão para limpar todos os valores
    limpar_tudo_btn = QPushButton("🗑️ Limpar Tudo")
    limpar_tudo_btn.clicked.connect(limpar_tudo)
    limpar_tudo_btn.setFixedHeight(20)  # Altura fixa
    limpar_tudo_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff6b6b;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ff5252;
        }
        QPushButton:pressed {
            background-color: #e53935;
        }
    """)
    layout.addWidget(limpar_tudo_btn, 1, 1)

    # Configurar tooltips
    tp.ToolTip(exp_v_check, "Expande a interface verticalmente")
    tp.ToolTip(exp_h_check, "Expande a interface horizontalmente")
    tp.ToolTip(limpar_dobras_btn, "Limpa as dobras")
    tp.ToolTip(limpar_tudo_btn, "Limpa todos os valores")

    return frame_botoes
