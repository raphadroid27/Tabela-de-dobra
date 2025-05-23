'''
# Formulário de Autenticação
# Este módulo implementa uma interface gráfica para autenticação de usuários no sistema.
# As funcionalidades incluem login de usuários existentes e criação de novos usuários,
# com a possibilidade de definir permissões administrativas. A interface é construída
# com a biblioteca tkinter, utilizando o módulo globals para variáveis globais e o
# módulo funcoes para operações auxiliares. O banco de dados é gerenciado com SQLAlchemy.
'''
import tkinter as tk
from src.utils.banco_dados import session
from src.models import Usuario
from src.utils.usuarios import login, novo_usuario
from src.utils.janelas import (desabilitar_janelas,
                              habilitar_janelas,
                              posicionar_janela
                              )
from src.config import globals as g

def main(root):
    '''
    Função principal que cria a janela de autenticação.
    Se a janela já existir, ela é destruída antes de criar uma nova.
    A janela é configurada com campos para usuário e senha, e um botão para login ou
    criação de novo usuário, dependendo do estado atual do sistema.
    '''

    if g.AUTEN_FORM:
        g.AUTEN_FORM.destroy()

    g.AUTEN_FORM = tk.Toplevel(root)
    g.AUTEN_FORM.geometry("200x120")
    g.AUTEN_FORM.resizable(False, False)
    g.AUTEN_FORM.attributes('-toolwindow', True)
    g.AUTEN_FORM.attributes("-topmost", True)
    g.AUTEN_FORM.focus()
    desabilitar_janelas()
    g.AUTEN_FORM.protocol("WM_DELETE_WINDOW", lambda: [habilitar_janelas(), g.AUTEN_FORM.destroy()])

    posicionar_janela(g.AUTEN_FORM, 'centro')

    main_frame = tk.Frame(g.AUTEN_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)

    main_frame.rowconfigure(0,weight=0)
    main_frame.rowconfigure(1,weight=0)
    main_frame.rowconfigure(2,weight=1)
    main_frame.rowconfigure(3,weight=1)

    tk.Label(main_frame, text="Usuário:").grid(row=0, column=0,padx=5, pady=5)
    g.USUARIO_ENTRY = tk.Entry(main_frame)
    g.USUARIO_ENTRY.focus()
    g.USUARIO_ENTRY.grid(row=0, column=1,padx=5, pady=5)
    tk.Label(main_frame, text="Senha:").grid(row=1, column=0,padx=5, pady=5)
    g.SENHA_ENTRY = tk.Entry(main_frame, show="*")
    g.SENHA_ENTRY.grid(row=1, column=1,padx=5, pady=5)

    admin_existente = session.query(Usuario).filter(Usuario.role == 'admin').first()

    g.ADMIN_VAR = tk.StringVar()

    if g.LOGIN:
        g.AUTEN_FORM.title("Login")
        tk.Button(main_frame,
                text="Login",
                command=login).grid(row=3, column=0, columnspan=2,padx=5, pady=5)
    else:
        if not admin_existente:
            g.AUTEN_FORM.geometry("200x150")
            tk.Label(main_frame, text="Admin:").grid(row=2, column=0, padx=5, pady=5)
            # Definir o valor inicial e os valores on/off
            g.ADMIN_VAR.set('viewer') # Valor padrão quando desmarcado
            admin_checkbox = tk.Checkbutton(main_frame,
                                            variable=g.ADMIN_VAR,
                                            onvalue='admin',
                                            offvalue='viewer')
            admin_checkbox.grid(row=2, column=1, padx=5, pady=5)
        else:
            # Se já existe admin, o novo usuário não pode ser admin
            g.ADMIN_VAR.set('viewer')

        g.AUTEN_FORM.title("Novo Usuário")
        tk.Button(main_frame,
                text="Salvar",
                # Na função novo_usuario, use g.ADMIN_VAR.get() para obter o valor
                command=novo_usuario).grid(row=3, column=0, columnspan=2,padx=5, pady=5)

if __name__ == "__main__":
    main(None)
