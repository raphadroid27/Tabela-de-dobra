"""
Este módulo implementa a interface principal do aplicativo Tabela de Dobra.
"""

import tkinter as tk
from models import Usuario
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import json
import os
from dobra_90 import form_dobra, dobras
from cabecalho import cabecalho
from avisos import avisos
import form_espessura
import globals as g
from funcoes import *
import form_deducao
import form_material
import form_canal
import form_sobre 
import form_aut
import form_usuario

# Configuração do banco de dados
engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

DOCUMENTS_DIR = os.path.join(os.environ["USERPROFILE"], "Documents")  
CONFIG_DIR = os.path.join(DOCUMENTS_DIR, "Tabela de Dobra") 
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json") 

def verificar_admin_existente():
    """
    Verifica se existe um administrador cadastrado no banco de dados.
    Caso contrário, abre a tela de autenticação para criar um.
    """
    admin_existente = session.query(Usuario).filter(Usuario.role == "admin").first()
    if not admin_existente:
        form_aut.main(g.PRINC_FORM)

def carregar_configuracao():
    """
    Carrega a configuração do aplicativo a partir de um arquivo JSON.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_configuracao(config):
    '''
    Salva a configuração do aplicativo em um arquivo JSON.
    '''
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f)

def form_true(form, editar_attr, root):
    '''
    Abre o formulário de edição de um item específico (dedução, material, espessura ou canal).
    '''

    setattr(g, editar_attr, True)
    form.main(root)

def form_false(form, editar_attr, root):
    '''
    Fecha o formulário de edição de um item específico (dedução, material, espessura ou canal).
    '''
    setattr(g, editar_attr, False)
    form.main(root)

def main():
    """
    Função principal que inicializa a interface gráfica do aplicativo.
    """
    config = carregar_configuracao()
    g.PRINC_FORM = tk.Tk()
    g.PRINC_FORM.title("Cálculo de Dobra")
    g.PRINC_FORM.geometry('340x400')
    if 'geometry' in config:
        g.PRINC_FORM.geometry(config['geometry'])
    g.PRINC_FORM.resizable(False, False)
    g.PRINC_FORM.update_idletasks() 

    def on_closing():
        geometry = g.PRINC_FORM.geometry()
        # Extrair apenas a posição da string de geometria
        position = geometry.split('+')[1:]
        config['geometry'] = f"+{position[0]}+{position[1]}"
        salvar_configuracao(config)
        g.PRINC_FORM.destroy()

    g.PRINC_FORM.protocol("WM_DELETE_WINDOW", on_closing)  

    # Criando o menu superior
    menu_bar = tk.Menu(g.PRINC_FORM)
    g.PRINC_FORM.config(menu=menu_bar)

    # Adicionando menus
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Arquivo", menu=file_menu)
    file_menu.add_command(label="Nova Dedução", command=lambda: form_false(form_deducao, 'editar_deducao', g.PRINC_FORM))
    file_menu.add_command(label="Novo Material", command=lambda: form_false(form_material, 'editar_material', g.PRINC_FORM))
    file_menu.add_command(label="Nova Espessura", command=lambda: form_false(form_espessura, 'editar_espessura', g.PRINC_FORM))
    file_menu.add_command(label="Novo Canal", command=lambda: form_false(form_canal, 'editar_canal', g.PRINC_FORM))
    file_menu.add_separator()
    file_menu.add_command(label="Sair", command=on_closing)

    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Editar", menu=edit_menu)
    edit_menu.add_command(label="Editar Dedução", command=lambda: form_true(form_deducao, 'editar_deducao', g.PRINC_FORM))
    edit_menu.add_command(label="Editar Material", command=lambda: form_true(form_material, 'editar_material', g.PRINC_FORM))
    edit_menu.add_command(label="Editar Espessura", command=lambda: form_true(form_espessura, 'editar_espessura', g.PRINC_FORM))
    edit_menu.add_command(label="Editar Canal", command=lambda: form_true(form_canal, 'editar_canal', g.PRINC_FORM))

    opcoes_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Opções", menu=opcoes_menu)
    g.NO_TOPO_VAR = tk.IntVar()
    opcoes_menu.add_checkbutton(label="No topo", 
                                variable=g.NO_TOPO_VAR, 
                                ommand=lambda: no_topo(g.PRINC_FORM))

    usuario_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Usuário", menu=usuario_menu)
    usuario_menu.add_command(label="Login", 
                             command=lambda: form_true(form_aut,"login",g.AUTEN_FORM))
    
    usuario_menu.add_command(label="Novo Usuário", 
                             command=lambda: form_false(form_aut,"login",g.AUTEN_FORM))
    
    usuario_menu.add_command(label="Gerenciar Usuários", 
                             command=lambda: form_usuario.main(g.PRINC_FORM))
    
    usuario_menu.add_separator()
    usuario_menu.add_command(label="Sair", command=logout)

    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Ajuda", menu=help_menu)
    help_menu.add_command(label="Sobre", command=lambda: form_sobre.main(g.PRINC_FORM))

    frame_superior = tk.Frame(g.PRINC_FORM)
    frame_superior.pack(fill='both', expand=True, padx=10)

    frame_superior.columnconfigure(0, weight=1)
    frame_superior.columnconfigure(1, weight=1)
    
    def carregar_cabecalho(var):
        """
        Atualiza o cabeçalho no frame_superior com base no valor de var.
        
        Args:
            var (int): Define o layout do cabeçalho. 
                       1 para apenas o cabeçalho principal.
                       2 para cabeçalho com avisos.
        """
        # Remove widgets existentes
        for widget in frame_superior.winfo_children():
            widget.destroy()

        # Adiciona o cabeçalho principal
        cabecalho(frame_superior).grid(row=0, column=0, sticky='we', padx=2, pady=2)

        # Adiciona avisos se var for 2
        if var == 2:
            avisos(frame_superior).grid(row=0, column=1, sticky='we', padx=2, pady=2)

    # Chamada inicial
    carregar_cabecalho(1)

    frame_teste = tk.Frame(g.PRINC_FORM)
    frame_teste.pack(fill='both', expand=True, padx=10)
    
    def carregar_form_dobra():
        # Limpar widgets antigos
        for widget in frame_teste.winfo_children():
            widget.destroy()

        # Redefinir as configurações de colunas
        for col in range(frame_teste.grid_size()[0]):  # Obtém o número de colunas configuradas
            frame_teste.columnconfigure(col, weight=0)  # Redefine o peso para 0

        # Recriar as configurações de colunas
        for col in range(len(g.VALORES_W)):
            frame_teste.columnconfigure(col, weight=1)

        # Recriar os widgets no frame
        for w in g.VALORES_W:
            form_dobra(frame_teste, w).grid(row=1, column=w-1, sticky='we', padx=2, pady=2)
        
    g.VALORES_W = [1]

    carregar_form_dobra()
    g.EXP_V = tk.IntVar()
    g.EXP_H = tk.IntVar()

    def expandir_v():
        largura_atual = g.PRINC_FORM.winfo_width() 
        if g.EXP_V.get() == 1:
            g.PRINC_FORM.geometry(f"{largura_atual}x500")
            for w in g.VALORES_W:
                dobras(11, w)
            carregar_form_dobra()
        else:
            g.PRINC_FORM.geometry(f"{largura_atual}x400")
            for w in g.VALORES_W:
                dobras(6, w)
            carregar_form_dobra()
        restaurar_dobras(w)

    def expandir_h():
        altura_atual = g.PRINC_FORM.winfo_height()
        if g.EXP_H.get() == 1:
            g.PRINC_FORM.geometry(f'680x{altura_atual}')  # Define a altura atual e a nova largura
            g.VALORES_W = [1,2]
            carregar_cabecalho(2)
            carregar_form_dobra() 
        else:
            g.PRINC_FORM.geometry(f'340x{altura_atual}')  # Define a altura atual e a nova largura
            g.VALORES_W = [1]
            carregar_cabecalho(1)
            carregar_form_dobra()
        for w in g.VALORES_W:
            restaurar_dobras(w)

    frame_inferior = tk.Frame(g.PRINC_FORM)
    frame_inferior.pack(fill='both', expand=True)

    frame_inferior.columnconfigure(0, weight=1)
    frame_inferior.columnconfigure(1, weight=1)

    tk.Checkbutton(
        frame_inferior,
        text="Expandir Vertical",
        variable=g.EXP_V,
        width=1,
        height=1,
        command=expandir_v
    ).grid(row=0, column=0, sticky='we')

    tk.Checkbutton(
        frame_inferior,
        text="Expandir Horizontal",
        variable=g.EXP_H,
        width=1,
        height=1,
        command=expandir_h
    ).grid(row=0, column=1, sticky='we')

    frame_botoes = tk.Frame(g.PRINC_FORM, width=200)
    frame_botoes.pack(expand=True)

    frame_botoes.columnconfigure(0, weight=1)
    frame_botoes.columnconfigure(1, weight=1)

    # Botão para limpar valores de dobras
    tk.Button(frame_botoes, text="Limpar Dobras", command=lambda : [limpar_dobras(w) for w in g.VALORES_W], width=15, bg='yellow').grid(row=0, column=0, sticky='we', padx=2)

    # Botão para limpar todos os valores
    tk.Button(frame_botoes, text="Limpar Tudo", command=limpar_tudo, width=15, bg='red').grid(row=0, column=1, sticky='we', padx=2)

    # Exemplo de uso para g.comprimento_entry
    verificar_admin_existente()
    g.PRINC_FORM.mainloop()

if __name__ == "__main__":
    main()
