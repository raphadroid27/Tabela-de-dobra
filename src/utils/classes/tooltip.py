"""
# Este código implementa uma classe de tooltip (dica de ferramenta) para widgets do Tkinter.
# O tooltip é uma pequena janela que aparece quando o mouse passa sobre um widget,
"""
import tkinter as tk

class ToolTip:
    """
    Classe para criar tooltips (dicas de ferramenta) para widgets do Tkinter.
    """
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay  # Atraso em milissegundos
        self.tooltip_window = None
        self.id = None

        # Associar eventos ao widget
        self.widget.bind("<Enter>", self.schedule_show)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<ButtonPress>", self.hide_tooltip)

    def schedule_show(self, event=None): # pylint: disable=unused-argument
        """
        Agendar a exibição do tooltip após um atraso, evitando múltiplos agendamentos.
        """
        if self.id is None:
            self.id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self, event=None): # pylint: disable=unused-argument
        """
        Exibir o tooltip na posição do mouse.
        """
        if self.tooltip_window is not None:
            return
        # Obter posição do mouse
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 22
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="lightyellow",
            relief="solid",
            borderwidth=1,
            justify="left",
            wraplength=200,
        )
        label.pack()

    def hide_tooltip(self, event=None): # pylint: disable=unused-argument
        """
        Ocultar o tooltip e cancelar o agendamento, se necessário.
        """
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
