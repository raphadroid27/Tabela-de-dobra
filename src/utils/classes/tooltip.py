"""
# Este código implementa uma classe de tooltip (dica de ferramenta) para widgets do PySide6.
# O tooltip é uma pequena janela que aparece quando o mouse passa sobre um widget,
"""
try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
except ImportError:
    # Fallback para PyQt6 se PySide6 não estiver disponível
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication


class ToolTip:
    """
    Classe para criar tooltips (dicas de ferramenta) para widgets do PySide6.
    """
    
    # Lista estática para rastrear todos os tooltips ativos
    _active_tooltips = []

    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay  # Atraso em milissegundos
        self.timer = QTimer()
        self.timer.setSingleShot(True)

        # Configurar tooltip diretamente no widget (método mais simples para PySide6)
        if hasattr(widget, 'setToolTip'):
            widget.setToolTip(text)
            
        # Adicionar à lista de tooltips ativos
        ToolTip._active_tooltips.append(self)

    def schedule_show(self, event=None):  # pylint: disable=unused-argument
        """
        Agendar a exibição do tooltip após um atraso, evitando múltiplos agendamentos.
        """
        if not self.timer.isActive():
            self.timer.start(self.delay)

    def show_tooltip(self, event=None):  # pylint: disable=unused-argument
        """
        Exibir o tooltip na posição do mouse.
        """
        # No PySide6, os tooltips são nativos, então esta implementação é simplificada
        return

    def hide_tooltip(self, event=None):  # pylint: disable=unused-argument
        """
        Ocultar o tooltip e cancelar o agendamento, se necessário.
        """
        if self.timer.isActive():
            self.timer.stop()
            
    def cleanup(self):
        """Limpa o tooltip e remove da lista ativa"""
        self.hide_tooltip()
        if hasattr(self.widget, 'setToolTip'):
            self.widget.setToolTip('')
        if self in ToolTip._active_tooltips:
            ToolTip._active_tooltips.remove(self)
    
    @classmethod
    def cleanup_all_tooltips(cls):
        """Limpa todos os tooltips ativos - versão melhorada para evitar janelas órfãs"""
        try:
            # Limpar tooltips da nossa classe
            for tooltip in cls._active_tooltips[:]:  # Cópia da lista para iteração segura
                tooltip.cleanup()
            cls._active_tooltips.clear()
            
            # Forçar limpeza de tooltips nativos do Qt
            app = QApplication.instance()
            if app:
                # Esconder qualquer tooltip ativo
                try:
                    from PySide6.QtWidgets import QToolTip
                    QToolTip.hideText()
                except (ImportError, AttributeError):
                    pass
                
                # Limpar widgets top-level órfãos relacionados a tooltips
                top_level_widgets = app.topLevelWidgets()
                for widget in top_level_widgets[:]:  # Cópia para iteração segura
                    widget_type = type(widget).__name__
                    if (widget.isVisible() and 
                        widget_type in ['QLabel', 'QTipLabel', 'QToolTip'] or
                        'tooltip' in widget_type.lower() or
                        'tip' in widget_type.lower()):
                        try:
                            widget.hide()
                            widget.close()
                            widget.deleteLater()
                        except:
                            pass
                
                # Processar eventos para garantir limpeza
                app.processEvents()
                
        except Exception as e:
            print(f"Erro na limpeza de tooltips: {e}")
