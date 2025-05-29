'''
Módulo para criar os botões e checkbuttons na interface gráfica.
Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
'''
import tkinter as tk
from src.utils.interface import limpar_dobras, limpar_tudo
import src.config.globals as g
from src.app_teste import carregar_interface
import src.utils.classes.tooltip as tp

class BotoesUI:
    '''
    Classe para criar os botões e checkbuttons na interface gráfica.
    Esta classe contém métodos para criar os botões e checkbuttons
    que serão exibidos na parte inferior da interface gráfica.
    Os botões serão utilizados para manipular as dobras e a interface
    de forma interativa.
    '''

    def __init__(self, root):
        '''
        Cria os botões e checkbuttons no frame inferior.

        Args:
            frame_inferior (tk.Frame): Frame onde os botões serão adicionados.
            frame_superior (tk.Frame): Frame superior para manipulação de interface.
        '''
        self.frame = tk.Frame(root)

        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)

        def expandir_v(self):
            largura_atual = g.PRINC_FORM.winfo_width()

            if self.expandir_v.get() == 1:
                g.PRINC_FORM.geometry(f"{largura_atual}x500")
                for w in self.valores_w:
                    self.entradas_dobras(11, w)
                carregar_interface(1, root)
            else:
                g.PRINC_FORM.geometry(f"{largura_atual}x400")
                for w in self.valores_w:
                    self.entradas_dobras(6, w)
                carregar_interface(1, root)

            # Verificar se avisos devem aparecer
            if g.EXP_H.get() == 1:
                carregar_interface(2, root)

        def expandir_h(self):
            altura_atual = g.PRINC_FORM.winfo_height()
            if g.EXP_H.get() == 1:
                g.PRINC_FORM.geometry(f'680x{altura_atual}')  # Define a altura atual e a nova largura
                self.valores_w = [1, 2]
                carregar_interface(2, root)
            else:
                g.PRINC_FORM.geometry(f'340x{altura_atual}')  # Define a altura atual e a nova largura
                self.valores_w = [1]
                carregar_interface(1, root)

            # Verificar se avisos devem aparecer
            if g.EXP_H.get() == 1:
                carregar_interface(2, root)

        tk.Checkbutton(
            self.frame,
            text="Expandir Vertical",
            variable=self.expandir_v,
            width=1,
            height=1,
            command=expandir_v
        ).grid(row=0, column=0, sticky='we')

        tk.Checkbutton(
            self.frame,
            text="Expandir Horizontal",
            variable=g.EXP_H,
            width=1,
            height=1,
            command=expandir_h
        ).grid(row=0, column=1, sticky='we')

        # Botão para limpar valores de dobras
        tk.Button(self.frame,
                text="Limpar Dobras",
                command=limpar_dobras,
                width=15,
                bg='yellow').grid(row=1, column=0, sticky='we', padx=2)

        # Botão para limpar todos os valores
        tk.Button(self.frame,
                text="Limpar Tudo",
                command=limpar_tudo,
                width=15,
                bg='red').grid(row=1, column=1, sticky='we', padx=2)

        tp.ToolTip(self.frame.grid_slaves(row=0, column=0)[0],
                text="Expande a interface verticalmente")
        tp.ToolTip(self.frame.grid_slaves(row=0, column=1)[0],
                text="Expande a interface horizontalmente")
        tp.ToolTip(self.frame.grid_slaves(row=1, column=0)[0],
                text="Limpa as dobras")
        tp.ToolTip(self.frame.grid_slaves(row=1, column=1)[0],
                text="Limpa todos os valores")

        return self.frame
