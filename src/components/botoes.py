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

    class ExpansionManager:
        """Gerencia a expansão da interface de forma robusta"""
        
        def __init__(self):
            self.is_updating = False
            self.cleanup_timer = QTimer()
            self.cleanup_timer.setSingleShot(True)
            self.cleanup_timer.timeout.connect(self.force_cleanup_orphans)
        
        def force_cleanup_orphans(self):
            """Remove todas as janelas órfãs que possam ter sido criadas"""
            try:
                app = QApplication.instance()
                if not app:
                    return
                
                main_window = g.PRINC_FORM
                top_level_widgets = app.topLevelWidgets()
                
                for widget in top_level_widgets[:]:  # Cópia para iteração segura
                    if (widget != main_window and 
                        widget.isVisible() and 
                        not hasattr(widget, '_is_system_widget')):
                        
                        widget_type = type(widget).__name__
                        if widget_type in ['QLabel', 'QFrame', 'QWidget', 'QDialog', 'QWindow']:
                            try:
                                widget.hide()
                                widget.close()
                                widget.deleteLater()
                            except:
                                pass
                
                # Limpar tooltips nativos
                try:
                    from PySide6.QtWidgets import QToolTip
                    QToolTip.hideText()
                except (ImportError, AttributeError):
                    pass
                
                app.processEvents()
                
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
                altura = 500 if exp_v else 400
                colunas = 2 if exp_h else 1
                num_abas = 10 if exp_v else 5
                
                # Atualizar estados globais
                g.EXP_H = exp_h
                g.EXP_V = exp_v
                g.VALORES_W = [1, 2] if exp_h else [1]
                
                print(f"Atualizando interface: {largura}x{altura}, {colunas} colunas, {num_abas} abas")
                
                # Redimensionar janela com limites temporários
                g.PRINC_FORM.setMinimumSize(largura, altura)
                g.PRINC_FORM.setMaximumSize(largura, altura)
                g.PRINC_FORM.resize(largura, altura)
                
                # Recarregar interface se necessário
                if hasattr(g, 'CARREGAR_INTERFACE_FUNC') and callable(g.CARREGAR_INTERFACE_FUNC):
                    g.CARREGAR_INTERFACE_FUNC(colunas, g.MAIN_LAYOUT)
                
                # Nota: O número de abas é agora controlado pelo interface_manager.py
                
                # Restaurar limites flexíveis após um delay
                def restore_limits():
                    if g.PRINC_FORM:
                        g.PRINC_FORM.setMinimumSize(340, 400)
                        g.PRINC_FORM.setMaximumSize(680, 500)
                    self.is_updating = False
                
                QTimer.singleShot(100, restore_limits)
                
                # Agendar limpeza de órfãos após mudanças
                self.cleanup_timer.start(200)
                
            except:
                self.is_updating = False
    
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
    exp_v_check.toggled.connect(on_expandir_v)
    layout.addWidget(exp_v_check, 0, 0)

    # Checkbox para expandir horizontal
    exp_h_check = QCheckBox("Expandir Horizontal")
    exp_h_check.setChecked(g.EXP_H)
    exp_h_check.toggled.connect(on_expandir_h)
    layout.addWidget(exp_h_check, 0, 1)

    # Botão para limpar valores de dobras
    limpar_dobras_btn = QPushButton("Limpar Dobras")
    limpar_dobras_btn.clicked.connect(limpar_dobras)
    limpar_dobras_btn.setStyleSheet("background-color: lightyellow;")
    layout.addWidget(limpar_dobras_btn, 1, 0)

    # Botão para limpar todos os valores
    limpar_tudo_btn = QPushButton("Limpar Tudo")
    limpar_tudo_btn.clicked.connect(limpar_tudo)
    limpar_tudo_btn.setStyleSheet("background-color: lightcoral;")
    layout.addWidget(limpar_tudo_btn, 1, 1)

    # Configurar tooltips
    tp.ToolTip(exp_v_check, "Expande a interface verticalmente")
    tp.ToolTip(exp_h_check, "Expande a interface horizontalmente")
    tp.ToolTip(limpar_dobras_btn, "Limpa as dobras")
    tp.ToolTip(limpar_tudo_btn, "Limpa todos os valores")

    return frame_botoes
