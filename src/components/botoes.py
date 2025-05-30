'''
Módulo para criar os botões e checkbuttons na interface gráfica.
'''
import tkinter as tk
from src.utils.interface import limpar_dobras, limpar_tudo
import src.utils.classes.tooltip as tp

def criar_botoes(parent, app):
    '''
    Cria os botões e checkbuttons no frame inferior.
    
    Args:
        parent (tk.Frame): Frame onde os botões serão adicionados.
        app (AppUI): Referência para a aplicação principal.
    
    Returns:
        tk.Frame: Frame contendo os botões
    '''
    frame = tk.Frame(parent)
    
    # Configurar grid
    for i in range(2):
        frame.columnconfigure(i, weight=1)
        frame.rowconfigure(i, weight=1)
    
    # Checkbutton para expandir verticalmente
    chk_v = tk.Checkbutton(
        frame,
        text="Expandir Vertical",
        variable=app.expandir_v,
        width=1,
        height=1,
        command=lambda: expandir_v_handler(app)
    )
    chk_v.grid(row=0, column=0, sticky='we')
    
    # Checkbutton para expandir horizontalmente
    chk_h = tk.Checkbutton(
        frame,
        text="Expandir Horizontal",
        variable=app.expandir_h,
        width=1,
        height=1,
        command=lambda: expandir_h_handler(app)
    )
    chk_h.grid(row=0, column=1, sticky='we')
    
    # Botão para limpar valores de dobras
    btn_limpar_dobras = tk.Button(
        frame,
        text="Limpar Dobras",
        command=limpar_dobras,
        width=15,
        bg='yellow'
    )
    btn_limpar_dobras.grid(row=1, column=0, sticky='we', padx=2)
    
    # Botão para limpar todos os valores
    btn_limpar_tudo = tk.Button(
        frame,
        text="Limpar Tudo",
        command=limpar_tudo,
        width=15,
        bg='red'
    )
    btn_limpar_tudo.grid(row=1, column=1, sticky='we', padx=2)
    
    # Adicionar tooltips
    tp.ToolTip(chk_v, text="Expande a interface verticalmente")
    tp.ToolTip(chk_h, text="Expande a interface horizontalmente")
    tp.ToolTip(btn_limpar_dobras, text="Limpa as dobras")
    tp.ToolTip(btn_limpar_tudo, text="Limpa todos os valores")
    
    return frame

def expandir_h_handler(app):
    '''
    Manipula a expansão horizontal da interface.
    '''
    try:
        altura_atual = app.janela_principal.winfo_height()
        
        if app.expandir_h.get() == 1:
            # Expandir horizontalmente - adicionar segunda coluna
            app.janela_principal.geometry(f'680x{altura_atual}')
            app.valores_w = [1, 2]
        else:
            # Contrair horizontalmente - uma coluna apenas
            app.janela_principal.geometry(f'340x{altura_atual}')
            app.valores_w = [1]
        
        # Recarregar interface
        import src.app as app_module
        app_module.carregar_interface(app)
        
    except ValueError as e:
        print(f"Erro ao expandir horizontalmente: {e}")

def expandir_v_handler(app):
    '''
    Manipula a expansão vertical da interface.
    '''
    try:
        largura_atual = app.janela_principal.winfo_width()

        if app.expandir_v.get() == 1:
            # Expandir verticalmente - 11 linhas de dobra
            app.janela_principal.geometry(f"{largura_atual}x500")
        else:
            # Contrair verticalmente - 6 linhas de dobra
            app.janela_principal.geometry(f"{largura_atual}x400")
          # Recarregar interface
        import src.app as app_module
        app_module.carregar_interface(app)
        
    except ValueError as e:
        print(f"Erro ao expandir verticalmente: {e}")