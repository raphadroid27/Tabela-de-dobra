"""
Classe para criar uma Entry com placeholder no tkinter.
Essa classe é uma extensão da Entry padrão do tkinter,
adicionando a funcionalidade de placeholder.
"""
import tkinter as tk


class PlaceholderEntry:
    """Classe para criar uma Entry com placeholder no tkinter."""

    def __init__(self, master, placeholder, placeholder_color="grey", text_color="black", **kwargs):
        """
        kwargs permite passar outros argumentos padrão do tkinter Entry (como width e justify).
        """
        self.entry = tk.Entry(master, fg=placeholder_color, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.text_color = text_color

        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.placeholder_color)

        self.entry.bind("<FocusIn>", self._remove_placeholder)
        self.entry.bind("<FocusOut>", self._add_placeholder)

    def _remove_placeholder(self, _event):
        """Remove o placeholder quando o usuário clica na Entry."""
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.text_color)

    def _add_placeholder(self, _event):
        """Adiciona o placeholder novamente se a Entry estiver vazia."""
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)

    def get(self):
        """Obtém o texto atual da Entry, sem o placeholder."""
        if self.entry.get() == self.placeholder:
            return ""
        return self.entry.get()

    def pack(self, **kwargs):
        """Facilita o uso do método pack."""
        self.entry.pack(**kwargs)

    def grid(self, **kwargs):
        """Facilita o uso do método grid."""
        self.entry.grid(**kwargs)

    def place(self, **kwargs):
        """Facilita o uso do método place."""
        self.entry.place(**kwargs)

    def bind(self, sequence, func, add=None):
        """Expõe o método bind da Entry subjacente."""
        self.entry.bind(sequence, func, add)

    def __getattr__(self, attr):
        """Redireciona chamadas de métodos para a Entry interna."""
        return getattr(self.entry, attr)
