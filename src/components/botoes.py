'''
Módulo para criar os botões e checkbuttons na interface gráfica.
Este módulo é responsável por criar os botões e checkbuttons que
serão exibidos na parte inferior da interface gráfica. Os botões
serão utilizados para manipular as dobras e a interface de forma
interativa.
'''
import tkinter as tk
from src.utils.interface import limpar_dobras, limpar_tudo
import src.utils.classes.tooltip as tp

class BotoesUI:
    '''
    Classe para criar os botões e checkbuttons na interface gráfica.
    Esta classe contém métodos para criar os botões e checkbuttons
    que serão exibidos na parte inferior da interface gráfica.
    Os botões serão utilizados para manipular as dobras e a interface
    de forma interativa.
    '''
    def __init__(self, root, app):
        '''
        Cria os botões e checkbuttons no frame inferior.

        Args:
            root (tk.Frame): Frame onde os botões serão adicionados.
            app (AppUI): Referência para a aplicação principal.
        '''
        self.frame = tk.Frame(root)
        self.app = app
        self.root = root

        self.valores_w = [1]  # Valores iniciais para a largura das dobras
        self.expandir_v = tk.IntVar()
        self.expandir_h = tk.IntVar()

        # Configurar grid
        for i in range(2):
            self.frame.columnconfigure(i, weight=1)
            self.frame.rowconfigure(i, weight=1)

        # Criar os widgets
        self.criar_widgets()

    def criar_widgets(self):
        '''
        Cria todos os widgets da interface de botões.
        '''
        # Checkbutton para expandir verticalmente
        tk.Checkbutton(
            self.frame,
            text="Expandir Vertical",
            variable=self.expandir_v,
            width=1,
            height=1,
            command=self.expandir_v_handler
        ).grid(row=0, column=0, sticky='we')

        # Checkbutton para expandir horizontalmente
        tk.Checkbutton(
            self.frame,
            text="Expandir Horizontal",
            variable=self.expandir_h,
            width=1,
            height=1,
            command=self.expandir_h_handler
        ).grid(row=0, column=1, sticky='we')

        # Botão para limpar valores de dobras
        tk.Button(
            self.frame,
            text="Limpar Dobras",
            command=limpar_dobras,
            width=15,
            bg='yellow'
        ).grid(row=1, column=0, sticky='we', padx=2)

        # Botão para limpar todos os valores
        tk.Button(
            self.frame,
            text="Limpar Tudo",
            command=limpar_tudo,
            width=15,
            bg='red'
        ).grid(row=1, column=1, sticky='we', padx=2)

        # Adicionar tooltips
        self.adicionar_tooltips()

    def adicionar_tooltips(self):
        '''
        Adiciona tooltips aos widgets.
        '''
        widgets = {
            (0, 0): "Expande a interface verticalmente",
            (0, 1): "Expande a interface horizontalmente",
            (1, 0): "Limpa as dobras",
            (1, 1): "Limpa todos os valores"
        }

        for (row, col), text in widgets.items():
            widget = self.frame.grid_slaves(row=row, column=col)
            if widget:
                tp.ToolTip(widget[0], text=text)

    def expandir_h_handler(self):
        '''
        Manipula a expansão horizontal da interface.
        '''
        try:
            altura_atual = self.app.janela_principal.winfo_height()
            
            if self.expandir_h.get() == 1:
                # Expandir horizontalmente
                self.app.janela_principal.geometry(f'680x{altura_atual}')
                self.valores_w = [1, 2]
            else:
                # Contrair horizontalmente
                self.app.janela_principal.geometry(f'340x{altura_atual}')
                self.valores_w = [1]
            
            # Recarregar interface
            self.app.carregar_interface()
            
        except Exception as e:
            print(f"Erro ao expandir horizontalmente: {e}")

    def expandir_v_handler(self):
        '''
        Manipula a expansão vertical da interface.
        '''
        try:
            largura_atual = self.app.janela_principal.winfo_width()

            if self.expandir_v.get() == 1:
                # Expandir verticalmente
                self.app.janela_principal.geometry(f"{largura_atual}x500")
            else:
                # Contrair verticalmente
                self.app.janela_principal.geometry(f"{largura_atual}x400")
            
            # Recarregar interface
            self.app.carregar_interface()
            
        except Exception as e:
            print(f"Erro ao expandir verticalmente: {e}")

    def get_numero_dobras(self):
        '''
        Retorna o número de dobras baseado no estado de expansão vertical.
        '''
        return 11 if self.expandir_v.get() == 1 else 6

    def get_valores_w(self):
        '''
        Retorna os valores de largura atual.
        '''
        return self.valores_w