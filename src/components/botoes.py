'''
Módulo para criar os botões e checkbuttons na interface gráfica.
'''
import tkinter as tk
from src.utils.interface import limpar_dobras, limpar_tudo
import src.utils.classes.tooltip as tp

def criar_botoes(parent, app_principal):
    '''
    Cria os botões e checkbuttons no frame inferior.
    
    Args:
        parent (tk.Frame): Frame onde os botões serão adicionados.
        app_principal (AppUI): Referência para a aplicação principal.
    
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
        variable=app_principal.expandir_v,
        width=1,
        height=1,
        command=lambda: expandir_v_handler(app_principal)
    )
    chk_v.grid(row=0, column=0, sticky='we')
    
    # Checkbutton para expandir horizontalmente
    chk_h = tk.Checkbutton(
        frame,
        text="Expandir Horizontal",
        variable=app_principal.expandir_h,
        width=1,
        height=1,
        command=lambda: expandir_h_handler(app_principal)
    )
    chk_h.grid(row=0, column=1, sticky='we')      # Botão para limpar valores de dobras
    btn_limpar_dobras = tk.Button(
        frame,
        text="Limpar Dobras",
        command=lambda: limpar_dobras_todas_colunas(app_principal) if hasattr(app_principal, 'cabecalho_ui') else None,
        width=15,
        bg='yellow'
    )
    btn_limpar_dobras.grid(row=1, column=0, sticky='we', padx=2)
      
    # Botão para limpar todos os valores
    btn_limpar_tudo = tk.Button(
        frame,
        text="Limpar Tudo",
        command=lambda: limpar_tudo_todas_colunas(app_principal) if hasattr(app_principal, 'cabecalho_ui') else None,
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

def expandir_h_handler(app_principal):
    '''
    Manipula a expansão horizontal da interface.
    '''
    try:
        altura_atual = app_principal.janela_principal.winfo_height()
        
        if app_principal.expandir_h.get() == 1:
            # Expandir horizontalmente - adicionar segunda coluna
            app_principal.janela_principal.geometry(f'680x{altura_atual}')
            app_principal.valores_w = [1, 2]
        else:
            # Contrair horizontalmente - uma coluna apenas
            app_principal.janela_principal.geometry(f'340x{altura_atual}')
            app_principal.valores_w = [1]
        
        # Recarregar interface
        import src.app as app_module
        app_module.carregar_interface(app_principal)
        
    except ValueError as e:
        print(f"Erro ao expandir horizontalmente: {e}")

def expandir_v_handler(app_principal):
    '''
    Manipula a expansão vertical da interface.
    '''
    try:
        largura_atual = app_principal.janela_principal.winfo_width()

        if app_principal.expandir_v.get() == 1:
            # Expandir verticalmente - 11 linhas de dobra
            app_principal.janela_principal.geometry(f"{largura_atual}x500")
        else:
            # Contrair verticalmente - 6 linhas de dobra
            app_principal.janela_principal.geometry(f"{largura_atual}x400")
          # Recarregar interface
        import src.app as app_module
        app_module.carregar_interface(app_principal)
        
    except ValueError as e:
        print(f"Erro ao expandir verticalmente: {e}")

def limpar_dobras_todas_colunas(app_principal):
    '''
    Limpa dobras em todas as colunas disponíveis.
    '''
    if hasattr(app_principal, 'cabecalho_ui') and hasattr(app_principal, 'dobras_ui') and app_principal.dobras_ui:
        # Limpar entradas de todas as colunas
        for w in app_principal.valores_w:
            if w in app_principal.dobras_ui:
                dobras_ui = app_principal.dobras_ui[w]
                
                # Limpar entradas de dobras para esta coluna específica
                for i in range(1, dobras_ui.n):
                    entry = getattr(dobras_ui, f'aba{i}_entry_{w}', None)
                    if entry:
                        entry.delete(0, tk.END)
                        entry.config(bg="white")
                
                # Limpar labels de medidas, metades e blanks para esta coluna
                for i in range(1, dobras_ui.n):
                    for prefixo in ['medidadobra', 'metadedobra']:
                        label = getattr(dobras_ui, f'{prefixo}{i}_label_{w}', None)
                        if label:
                            label.config(text="")
                
                # Limpar blanks
                for suffix in ['medida_blank_label', 'metade_blank_label']:
                    label = getattr(dobras_ui, f'{suffix}_{w}', None)
                    if label:
                        label.config(text="")
          # Limpar dedução específica
        if hasattr(app_principal.cabecalho_ui, 'deducao_especifica_widget') and app_principal.cabecalho_ui.deducao_especifica_widget:
            app_principal.cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)
        
        # Resetar valores globais
        import src.config.globals as g
        g.DOBRAS_VALORES = []
        
        # Focar no primeiro campo
        if 1 in app_principal.dobras_ui:
            aba1_entry = getattr(app_principal.dobras_ui[1], "aba1_entry_1", None)
            if aba1_entry:
                aba1_entry.focus_set()

def limpar_tudo_todas_colunas(app_principal):
    '''
    Limpa tudo em todas as colunas disponíveis.
    '''
    if hasattr(app_principal, 'cabecalho_ui') and hasattr(app_principal, 'dobras_ui') and app_principal.dobras_ui:
        # Limpar campos do cabeçalho
        cabecalho_ui = app_principal.cabecalho_ui
        if hasattr(cabecalho_ui, 'material_widget') and cabecalho_ui.material_widget:
            cabecalho_ui.material_widget.set('')
        if hasattr(cabecalho_ui, 'espessura_widget') and cabecalho_ui.espessura_widget:
            cabecalho_ui.espessura_widget.set('')
            cabecalho_ui.espessura_widget.configure(values=[])
        if hasattr(cabecalho_ui, 'canal_widget') and cabecalho_ui.canal_widget:
            cabecalho_ui.canal_widget.set('')
            cabecalho_ui.canal_widget.configure(values=[])
        
        # Limpar entradas
        if hasattr(cabecalho_ui, 'raio_interno_widget') and cabecalho_ui.raio_interno_widget:
            cabecalho_ui.raio_interno_widget.delete(0, tk.END)
        if hasattr(cabecalho_ui, 'comprimento_widget') and cabecalho_ui.comprimento_widget:
            cabecalho_ui.comprimento_widget.delete(0, tk.END)
        if hasattr(cabecalho_ui, 'deducao_especifica_widget') and cabecalho_ui.deducao_especifica_widget:
            cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)

        # Limpar etiquetas
        etiquetas_widgets = [
            ('fator_k_widget', ''),
            ('deducao_widget', ''),
            ('offset_widget', ''),
            ('observacoes_widget', ''),
            ('ton_m_widget', ''),
            ('aba_minima_widget', ''),
            ('z90_widget', '')
        ]
        
        for widget_name, texto in etiquetas_widgets:
            if hasattr(cabecalho_ui, widget_name):
                widget = getattr(cabecalho_ui, widget_name)
                if widget:
                    widget.config(text=texto)
          # Limpar dobras
        limpar_dobras_todas_colunas(app_principal)
        
        # Executar todas as funções para cada coluna
        from src.utils.interface import todas_funcoes
        for w in app_principal.valores_w:
            if w in app_principal.dobras_ui:
                todas_funcoes(app_principal.cabecalho_ui, app_principal.dobras_ui[w])

        # Focar no combobox de material
        if hasattr(cabecalho_ui, 'material_widget') and cabecalho_ui.material_widget:
            cabecalho_ui.material_widget.focus_set()