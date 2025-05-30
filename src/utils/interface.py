'''
Este módulo contém funções auxiliares para o aplicativo de cálculo de dobras.

As funções incluem a atualização de widgets, manipulação de valores de dobras,
restauração de valores, e outras operações relacionadas ao funcionamento do
aplicativo de cálculo de dobras.
'''
import tkinter as tk
from tkinter import ttk
import re
import pyperclip
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.banco_dados import session, obter_configuracoes
from src.utils.calculos import (calcular_dobra,
                                calcular_k_offset,
                                aba_minima_externa,
                                z_minimo_externo,
                                razao_ri_espessura
                                )
from src.config import globals as g
import src.utils.classes.tooltip as tp

def atualizar_widgets(cabecalho_ui, tipo):
    '''
    Atualiza os valores de comboboxes com base no tipo especificado.

    Args:
        tipo (str): O tipo de combobox a ser atualizado.
    '''
    def atualizar_material():
        if cabecalho_ui.material_widget and cabecalho_ui.material_widget.winfo_exists():
            materiais = [m.nome for m in session.query(Material).order_by(Material.nome)]
            cabecalho_ui.material_widget.configure(values=materiais)

        # Verifica se o combobox de dedução de material existe e atualiza seus valores
        if g.DED_MATER_COMB and g.DED_MATER_COMB.winfo_exists():
            g.DED_MATER_COMB.configure(values=[m.nome for m in session
                                               .query(Material)
                                               .order_by(Material.nome).all()])

    def atualizar_espessura():
        material_nome = cabecalho_ui.material_widget.get()
        material_obj = session.query(Material).filter_by(nome=material_nome).first()
        if material_obj:
            espessuras = session.query(Espessura).join(Deducao).filter(
                Deducao.material_id == material_obj.id
            ).order_by(Espessura.valor)
            cabecalho_ui.espessura_widget.configure(values=[str(e.valor) for e in espessuras])

        # Verifica se o combobox de dedução de espessura existe e atualiza seus valores
        if g.DED_ESPES_COMB and g.DED_ESPES_COMB.winfo_exists():
            g.DED_ESPES_COMB.configure(values=sorted([e.valor for e in session
                                                      .query(Espessura).all()]))

    def atualizar_canal():
        espessura_valor = cabecalho_ui.espessura_widget.get()
        material_nome = cabecalho_ui.material_widget.get()
        espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
        material_obj = session.query(Material).filter_by(nome=material_nome).first()

        if espessura_obj and material_obj:
            canais = session.query(Canal).join(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id
            ).order_by(Canal.valor)
            canais_valores = sorted(
                [str(c.valor) for c in canais],
                key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0])
            )
            cabecalho_ui.canal_widget.configure(values=canais_valores)

        # Verifica se o combobox de dedução de canal existe e atualiza seus valores
        if g.DED_CANAL_COMB and g.DED_CANAL_COMB.winfo_exists():
            g.DED_CANAL_COMB.configure(values=sorted([c.valor for c in session.query(Canal).all()]))

    def atualizar_deducao():
        espessura_valor = cabecalho_ui.espessura_widget.get()
        material_nome = cabecalho_ui.material_widget.get()
        canal_valor = cabecalho_ui.canal_widget.get()

        espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
        material_obj = session.query(Material).filter_by(nome=material_nome).first()
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if espessura_obj and material_obj and canal_obj:
            deducao_obj = session.query(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id,
                Deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj:
                cabecalho_ui.deducao_widget.config(text=deducao_obj.valor, fg="black")
                observacao = deducao_obj.observacao or 'Observações não encontradas'
                cabecalho_ui.observacoes_widget.config(text=f'{observacao}')
            else:
                cabecalho_ui.deducao_widget.config(text='N/A', fg="red")
                cabecalho_ui.observacoes_widget.config(text='Observações não encontradas')

        for tipo in ['material', 'espessura', 'canal']:
            atualizar_widgets(cabecalho_ui, tipo)


    # Mapeamento de tipos para funções
    acoes = {
        'material': atualizar_material,
        'espessura': atualizar_espessura,
        'canal': atualizar_canal,
        'dedução': atualizar_deducao

    }

    # Executa a ação correspondente ao tipo
    if tipo in acoes:
        acoes[tipo]()

def canal_tooltip(cabecalho_ui):
    '''
    Atualiza o tooltip do combobox de canais com as
    observações e comprimento total do canal selecionado.
    '''
    if cabecalho_ui.canal_widget.get() == "":
        cabecalho_ui.canal_widget.set("")
        tp.ToolTip(cabecalho_ui.canal_widget, "Selecione o canal de dobra.")
    else:
        canal_obj = session.query(Canal).filter_by(valor=cabecalho_ui.canal_widget.get()).first()
        if canal_obj:
            canal_obs = canal_obj.observacao if canal_obj.observacao else "N/A."
            canal_comprimento_total = (canal_obj.comprimento_total
                                       if canal_obj.comprimento_total else "N/A.")

            tp.ToolTip(cabecalho_ui.canal_widget,
                       f'Obs: {canal_obs}\n'
                       f'Comprimento total: {canal_comprimento_total}',
                       delay=0)

def atualizar_toneladas_m(cabecalho_ui):
    '''
    Atualiza o valor de toneladas por metro com base no comprimento e na dedução selecionada.
    '''
    comprimento = cabecalho_ui.comprimento_widget.get()
    espessura_valor = cabecalho_ui.espessura_widget.get()
    material_nome = cabecalho_ui.material_widget.get()
    canal_valor = cabecalho_ui.canal_widget.get()

    espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()
    canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

    if espessura_obj and material_obj and canal_obj:
        deducao_obj = session.query(Deducao).filter(
            Deducao.espessura_id == espessura_obj.id,
            Deducao.material_id == material_obj.id,
            Deducao.canal_id == canal_obj.id
        ).first()

        if deducao_obj and deducao_obj.forca is not None:
            toneladas_m = ((deducao_obj.forca * float(comprimento)) / 1000
                           if comprimento else deducao_obj.forca)
            cabecalho_ui.ton_m_widget.config(text=f'{toneladas_m:.0f}', fg="black")
        else:
            cabecalho_ui.ton_m_widget.config(text='N/A', fg="red")

    # Verificar se o comprimento é menor que o comprimento total do canal
    canal_obj = session.query(Canal).filter_by(valor=cabecalho_ui.canal_widget.get()).first()
    comprimento_total = canal_obj.comprimento_total if canal_obj else None
    comprimento = float(comprimento) if comprimento else None

    if canal_obj and comprimento and comprimento_total:
        if comprimento < comprimento_total:
            cabecalho_ui.comprimento_widget.config(fg="black")
        elif comprimento >= comprimento_total:
            cabecalho_ui.comprimento_widget.config(fg="red")

def restaurar_valores_dobra(dobras_ui, w):
    '''
    Restaura os valores das dobras para a coluna específica w
    a partir de g.DOBRAS_VALORES.
    '''
    # Verificar se g.DOBRAS_VALORES foi inicializada
    if not hasattr(g, 'DOBRAS_VALORES') or g.DOBRAS_VALORES is None:
        print("DOBRAS_VALORES não foi inicializada ou está vazia")
        return

    try:
        # Restaurar os valores das dobras apenas para a coluna w
        for i in range(1, dobras_ui.n):
            # Verificar se existem dados para esta linha e coluna
            if (i - 1 < len(g.DOBRAS_VALORES) and 
                w - 1 < len(g.DOBRAS_VALORES[i - 1])):
                valor = g.DOBRAS_VALORES[i - 1][w - 1]
                entry = getattr(dobras_ui, f'aba{i}_entry_{w}', None)
                if entry and hasattr(entry, 'winfo_exists') and entry.winfo_exists():
                    entry.delete(0, tk.END)
                    entry.insert(0, valor)
                    print(f"Valor restaurado para aba{i}_entry_{w}: {valor}")
                else:
                    print(f"Widget aba{i}_entry_{w} não existe ou foi destruído")
            else:
                print(f"Não há dados salvos para aba{i}_entry_{w}")
    except Exception as e:
        print(f"Erro ao restaurar valores das dobras: {e}")

def salvar_valores_cabecalho(cabecalho_ui):
    '''
    Salva os valores atuais dos widgets no cabeçalho em g.CABECALHO_VALORES.
    '''
    if not hasattr(g, 'CABECALHO_VALORES') or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}

    try:
        g.CABECALHO_VALORES = {
            'material': cabecalho_ui.material_widget.get() if hasattr(cabecalho_ui, 'material_widget') and cabecalho_ui.material_widget else '',
            'espessura': cabecalho_ui.espessura_widget.get() if hasattr(cabecalho_ui, 'espessura_widget') and cabecalho_ui.espessura_widget else '',
            'canal': cabecalho_ui.canal_widget.get() if hasattr(cabecalho_ui, 'canal_widget') and cabecalho_ui.canal_widget else '',
            'comprimento': cabecalho_ui.comprimento_widget.get() if hasattr(cabecalho_ui, 'comprimento_widget') and cabecalho_ui.comprimento_widget else '',
            'raio_interno': cabecalho_ui.raio_interno_widget.get() if hasattr(cabecalho_ui, 'raio_interno_widget') and cabecalho_ui.raio_interno_widget else '',
            'deducao_especifica': cabecalho_ui.deducao_especifica_widget.get() if hasattr(cabecalho_ui, 'deducao_especifica_widget') and cabecalho_ui.deducao_especifica_widget else '',
        }
        print("Valores salvos:", g.CABECALHO_VALORES)
    except Exception as e:
        print(f"Erro ao salvar valores do cabeçalho: {e}")
        g.CABECALHO_VALORES = {}

def restaurar_valores_cabecalho(cabecalho_ui):
    '''
    Restaura os valores dos widgets no cabeçalho
    com base nos valores armazenados em g.CABECALHO_VALORES.
    '''
    # Verifica se g.CABECALHO_VALORES já foi inicializado como um dicionário
    if not hasattr(g, 'CABECALHO_VALORES') or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}
        return

    try:
        # Restaura os valores nos widgets
        for widget_name, valor in g.CABECALHO_VALORES.items():
            if hasattr(cabecalho_ui, f'{widget_name}_widget'):
                widget = getattr(cabecalho_ui, f'{widget_name}_widget')
                if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                    if isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, valor)
                    elif isinstance(widget, ttk.Combobox):
                        widget.set(valor)
                    print(f"Valor restaurado para {widget_name}: {valor}")
                else:
                    print(f"Widget {widget_name}_widget não existe ou foi destruído")
            else:
                print(f"Atributo {widget_name}_widget não encontrado em cabecalho_ui")

        print("Valores restaurados:", g.CABECALHO_VALORES)
    except Exception as e:
        print(f"Erro ao restaurar valores do cabeçalho: {e}")

def copiar(dobras_ui, cabecalho_ui, tipo, numero=None, w=None):
    '''
    Copia o valor do label correspondente ao tipo e 
    número especificados para a área de transferência.
    '''
    configuracoes = {
        'dedução': {
            'label': g.DED_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'), 
                                       calcular_k_offset())
        },
        'fator_k': {
            'label': g.K_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'), 
                                       calcular_k_offset())
        },
        'offset': {
            'label': g.OFFSET_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'), 
                                       calcular_k_offset())
        },
        'medida_dobra': {
            'label': lambda numero: getattr(g, f'medidadobra{numero}_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(cabecalho_ui, dobras_ui, w)
        },
        'metade_dobra': {
            'label': lambda numero: getattr(g, f'metadedobra{numero}_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(cabecalho_ui, dobras_ui, w)
        },
        'blank': {
            'label': getattr(g, f'medida_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(cabecalho_ui, dobras_ui, w)
        },
        'metade_blank': {
            'label': getattr(g, f'metade_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(cabecalho_ui, dobras_ui, w)
        }
    }

    config = configuracoes[tipo]

    label = config['label'](numero) if callable(config['label']) else config['label']
    if label is None:
        print(f"Erro: Label não encontrado para o tipo '{tipo}' com numero={numero} e w={w}.")
        return

    if label.cget('text') == "":
        return

    if hasattr(label, 'cget') and 'text' in label.keys():
        config['funcao_calculo']()
        pyperclip.copy(label.cget('text'))
        print(f'Valor copiado {label.cget("text")}')
        label.config(text=f'{label.cget("text")} Copiado!', fg="green")
    else:
        print(f"Erro: O label para o tipo '{tipo}' não possui o atributo 'text'.")

def limpar_dobras(cabecalho_ui, dobras_ui, app_principal):
    '''
    Limpa os valores das dobras e atualiza os labels correspondentes.
    '''
    def limpar_widgets(widgets, metodo, valor=""):
        '''
        Limpa ou redefine widgets com base no método fornecido.

        Args:
            widgets (list): Lista de widgets a serem limpos.
            metodo (str): Método a ser chamado no widget (ex.: 'delete', 'config').
            valor (str): Valor a ser usado no método (se aplicável).
        '''
        for widget in widgets:
            if widget:
                if metodo == "delete":
                    getattr(widget, metodo)(0, tk.END)
                else:
                    widget.config(text=valor)

    # Obter widgets dinamicamente
    def obter_widgets(prefixo):        return [
            getattr(dobras_ui, f"{prefixo}{i}_label_{col}", None)
            for i in range(1, dobras_ui.n)
            for col in app_principal.valores_w
        ]    # Limpar entradas e labels
    dobras = [getattr(dobras_ui, f"aba{i}_entry_{col}", None) for i in range(1, dobras_ui.n) for col in app_principal.valores_w]
    medidas = obter_widgets("medidadobra")
    metades = obter_widgets("metadedobra")
    blanks = [getattr(dobras_ui, f"medida_blank_label_{col}", None) for col in app_principal.valores_w]
    metades_blanks = [getattr(dobras_ui, f"metade_blank_label_{col}", None) for col in app_principal.valores_w]

    # Limpar widgets
    limpar_widgets(dobras, "delete")
    limpar_widgets(medidas + metades + blanks + metades_blanks, "config", "")

    # Limpar dedução específica
    if cabecalho_ui.deducao_especifica_widget:
        cabecalho_ui.deducao_especifica_widget.delete(0, tk.END)

    # Resetar valores globais
    g.DOBRAS_VALORES = []    # Alterar a cor de fundo das entradas de dobras para branco
    for i in range(1, dobras_ui.n):
        for col in app_principal.valores_w:
            entry = getattr(dobras_ui, f'aba{i}_entry_{col}', None)
            if entry:
                entry.config(bg="white")

    # Verifique se o atributo existe antes de usá-lo
    aba1_entry = getattr(dobras_ui, "aba1_entry_1", None)
    if aba1_entry:
        aba1_entry.focus_set()

def limpar_tudo(cabecalho_ui, dobras_ui, app_principal):
    '''
    Limpa todos os campos e labels do aplicativo.
    '''
    try:
        # Limpar campos do cabeçalho usando a instância cabecalho_ui
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
                if widget:                    widget.config(text=texto)        # Limpar dobras
        limpar_dobras(cabecalho_ui, dobras_ui, app_principal)
        
        # Executar todas as funções
        todas_funcoes(cabecalho_ui, dobras_ui)

        # Limpar razão R/E se existir
        if g.RAZAO_RIE_LBL and g.RAZAO_RIE_LBL.winfo_exists():
            g.RAZAO_RIE_LBL.config(text="")

        # Focar no combobox de material
        if hasattr(cabecalho_ui, 'material_widget') and cabecalho_ui.material_widget:
            cabecalho_ui.material_widget.focus_set()
            
    except Exception as e:
        print(f"Erro ao limpar todos os campos: {e}")

def limpar_busca(tipo):
    '''
    Limpa os campos de busca e atualiza a lista correspondente.
    '''
    configuracoes = obter_configuracoes()
    if tipo == 'dedução':
        configuracoes[tipo]['entries']['material_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['espessura_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['canal_combo'].delete(0, tk.END)
    else:
        configuracoes[tipo]['busca'].delete(0, tk.END)

    listar(tipo)

def focus_next_entry(current_index, w, dobras_ui):
    '''
    Move o foco para o próximo campo de entrada na aba atual.
    '''
    next_index = current_index + 1
    if next_index < dobras_ui.n:
        next_entry = getattr(dobras_ui, f'aba{next_index}_entry_{w}', None)
        if next_entry:
            next_entry.focus()

def focus_previous_entry(current_index, w, dobras_ui):
    '''
    Move o foco para o campo de entrada anterior na aba atual.
    '''
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(dobras_ui, f'aba{previous_index}_entry_{w}', None)
        if previous_entry:
            previous_entry.focus()

def listar(tipo):
    '''
    Lista os itens do banco de dados na interface gráfica.
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if config['lista'] is None or not config['lista'].winfo_exists():
        return

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    itens = session.query(config['modelo']).order_by(config['ordem']).all()

    if tipo == 'material':
        itens = sorted(itens, key=lambda x: x.nome)

    for item in itens:
        if tipo == 'dedução':
            if item.material is None or item.espessura is None or item.canal is None:
                continue
        config['lista'].insert("", "end", values=config['valores'](item))

def todas_funcoes(cabecalho_ui, dobras_ui=None, todas_colunas=False, app_principal=None):
    '''
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.
    
    Args:
        cabecalho_ui: Interface do cabeçalho
        dobras_ui: Interface de dobras específica (opcional)
        todas_colunas: Se True, recalcula todas as colunas ativas
        app_principal: Instância do app para acessar todas as colunas
    '''
    for tipo in ['material', 'espessura', 'canal', 'dedução']:
        atualizar_widgets(cabecalho_ui, tipo)

    atualizar_toneladas_m(cabecalho_ui)
    calcular_k_offset(cabecalho_ui)
    aba_minima_externa(cabecalho_ui)
    z_minimo_externo(cabecalho_ui)
    
    # Se deve recalcular todas as colunas e tem app_principal
    if todas_colunas and app_principal and hasattr(app_principal, 'dobras_ui'):
        for w in app_principal.valores_w:
            if w in app_principal.dobras_ui:
                calcular_dobra(cabecalho_ui, app_principal.dobras_ui[w], w)
    elif dobras_ui:
        # Calcular dobra apenas para a coluna específica passada como parâmetro
        if hasattr(dobras_ui, 'w'):
            w = dobras_ui.w
            calcular_dobra(cabecalho_ui, dobras_ui, w)

    razao_ri_espessura(cabecalho_ui)

    # Atualizar tooltips
    canal_tooltip(cabecalho_ui)

def configurar_main_frame(parent, rows=4):
    '''
    Configura o frame principal com colunas e linhas padrão.
    '''
    main_frame = tk.Frame(parent)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    for i in range(rows):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    return main_frame

def configurar_frame_edicoes(parent, text, columns=3, rows=4):
    '''
    Cria um frame de edições com configuração padrão.
    '''
    frame_edicoes = tk.LabelFrame(parent, text=text, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    for i in range(columns):
        frame_edicoes.columnconfigure(i, weight=1 if i < columns - 1 else 0)

    for i in range(rows):
        frame_edicoes.rowconfigure(i, weight=1)

    return frame_edicoes

def salvar_valores_dobra(dobras_ui, w):
    '''
    Salva os valores atuais das dobras da coluna específica w em g.DOBRAS_VALORES.
    '''
    try:
        if not hasattr(g, 'DOBRAS_VALORES') or g.DOBRAS_VALORES is None:
            g.DOBRAS_VALORES = []

        # Garantir que g.DOBRAS_VALORES tenha o tamanho necessário para as linhas
        while len(g.DOBRAS_VALORES) < dobras_ui.n - 1:
            g.DOBRAS_VALORES.append([])

        # Salvar os valores das dobras apenas para a coluna w
        for i in range(1, dobras_ui.n):
            # Garantir que cada linha tenha o tamanho necessário para conter até a coluna w
            while len(g.DOBRAS_VALORES[i - 1]) < w:
                g.DOBRAS_VALORES[i - 1].append("")

            # Salvar apenas a coluna específica w
            entry = getattr(dobras_ui, f'aba{i}_entry_{w}', None)
            if entry and hasattr(entry, 'winfo_exists') and entry.winfo_exists():
                valor = entry.get()
                g.DOBRAS_VALORES[i - 1][w - 1] = valor
                print(f"Valor salvo para aba{i}_entry_{w}: {valor}")
            else:
                g.DOBRAS_VALORES[i - 1][w - 1] = ""

        print(f"Valores de dobras salvos para coluna {w}:", g.DOBRAS_VALORES)
    except Exception as e:
        print(f"Erro ao salvar valores das dobras: {e}")
