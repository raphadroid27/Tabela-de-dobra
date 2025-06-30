"""
Este módulo contém funções auxiliares para o aplicativo de cálculo de dobras.

As funções incluem a atualização de widgets, manipulação de valores de dobras,
restauração de valores, e outras operações relacionadas ao funcionamento do
aplicativo de cálculo de dobras.
"""
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


def _atualizar_material():
    """Atualiza os valores do combobox de materiais."""
    if g.MAT_COMB and g.MAT_COMB.winfo_exists():
        materiais = [m.nome for m in session.query(Material).order_by(Material.nome)]
        g.MAT_COMB.configure(values=materiais)

    # Verifica se o combobox de dedução de material existe e atualiza seus valores
    if g.DED_MATER_COMB and g.DED_MATER_COMB.winfo_exists():
        g.DED_MATER_COMB.configure(values=[m.nome for m in session
                                           .query(Material)
                                           .order_by(Material.nome).all()])


def _atualizar_espessura():
    """Atualiza os valores do combobox de espessuras."""
    if not g.MAT_COMB or not hasattr(g.MAT_COMB, 'get'):
        return

    material_nome = g.MAT_COMB.get()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()
    if material_obj:
        espessuras = session.query(Espessura).join(Deducao).filter(
            Deducao.material_id == material_obj.id
        ).order_by(Espessura.valor)

        if g.ESP_COMB and hasattr(g.ESP_COMB, 'configure'):
            g.ESP_COMB.configure(values=[str(e.valor) for e in espessuras])

    # Verifica se o combobox de dedução de espessura existe e atualiza seus valores
    if g.DED_ESPES_COMB and g.DED_ESPES_COMB.winfo_exists():
        valores_espessura = session.query(Espessura.valor).distinct().all()
        valores_limpos = [float(valor[0]) for valor in valores_espessura
                          if valor[0] is not None]
        g.DED_ESPES_COMB.configure(values=sorted(valores_limpos))


def _atualizar_canal():
    """Atualiza os valores do combobox de canais."""
    if (not g.ESP_COMB or not hasattr(g.ESP_COMB, 'get') or
            not g.MAT_COMB or not hasattr(g.MAT_COMB, 'get')):
        return

    espessura_valor = g.ESP_COMB.get()
    material_nome = g.MAT_COMB.get()
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
        if g.CANAL_COMB and hasattr(g.CANAL_COMB, 'configure'):
            g.CANAL_COMB.configure(values=canais_valores)

    # Verifica se o combobox de dedução de canal existe e atualiza seus valores
    if g.DED_CANAL_COMB and g.DED_CANAL_COMB.winfo_exists():
        valores_canal = session.query(Canal.valor).distinct().all()
        valores_canal_limpos = [str(valor[0]) for valor in valores_canal
                                if valor[0] is not None]
        g.DED_CANAL_COMB.configure(values=sorted(valores_canal_limpos))


def _atualizar_deducao():
    """Atualiza os valores de dedução com base nos widgets selecionados."""
    # Verificar se todos os widgets necessários estão disponíveis
    widgets_requeridos = [
        (g.ESP_COMB, 'get'),
        (g.MAT_COMB, 'get'),
        (g.CANAL_COMB, 'get')
    ]

    for widget, metodo in widgets_requeridos:
        if not widget or not hasattr(widget, metodo):
            return

    espessura_valor = g.ESP_COMB.get()
    material_nome = g.MAT_COMB.get()
    canal_valor = g.CANAL_COMB.get()

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
            if g.DED_LBL and hasattr(g.DED_LBL, 'config'):
                g.DED_LBL.config(text=deducao_obj.valor, fg="black")
            observacao = deducao_obj.observacao or 'Observações não encontradas'
            if g.OBS_LBL and hasattr(g.OBS_LBL, 'config'):
                g.OBS_LBL.config(text=f'{observacao}')
        else:
            if g.DED_LBL and hasattr(g.DED_LBL, 'config'):
                g.DED_LBL.config(text='N/A', fg="red")
            if g.OBS_LBL and hasattr(g.OBS_LBL, 'config'):
                g.OBS_LBL.config(text='Observações não encontradas')

    for tipo in ['material', 'espessura', 'canal']:
        atualizar_widgets(tipo)


def atualizar_widgets(tipo):
    """
    Atualiza os valores de comboboxes com base no tipo especificado.

    Args:
        tipo (str): O tipo de combobox a ser atualizado.
    """
    # Mapeamento de tipos para funções
    acoes = {
        'material': _atualizar_material,
        'espessura': _atualizar_espessura,
        'canal': _atualizar_canal,
        'dedução': _atualizar_deducao
    }

    # Executa a ação correspondente ao tipo
    if tipo in acoes:
        acoes[tipo]()


def canal_tooltip():
    """
    Atualiza o tooltip do combobox de canais com as
    observações e comprimento total do canal selecionado.
    """
    if not g.CANAL_COMB or not hasattr(g.CANAL_COMB, 'get'):
        return

    if g.CANAL_COMB.get() == "":
        if hasattr(g.CANAL_COMB, 'set'):
            g.CANAL_COMB.set("")
        tp.ToolTip(g.CANAL_COMB, "Selecione o canal de dobra.")
    else:
        canal_obj = session.query(Canal).filter_by(valor=g.CANAL_COMB.get()).first()
        if canal_obj:
            canal_obs = getattr(canal_obj, 'observacao', None) or "N/A."
            canal_comprimento_total = getattr(canal_obj, 'comprimento_total', None) or "N/A."

            tp.ToolTip(g.CANAL_COMB,
                       f'Obs: {canal_obs}\n'
                       f'Comprimento total: {canal_comprimento_total}',
                       delay=0)


def atualizar_toneladas_m():
    """
    Atualiza o valor de toneladas por metro com base no comprimento e na dedução selecionada.
    """
    # Verificar se todos os widgets necessários estão disponíveis
    widgets_requeridos = [
        (g.COMPR_ENTRY, 'get'),
        (g.ESP_COMB, 'get'),
        (g.MAT_COMB, 'get'),
        (g.CANAL_COMB, 'get')
    ]

    for widget, metodo in widgets_requeridos:
        if not widget or not hasattr(widget, metodo):
            return

    comprimento = g.COMPR_ENTRY.get()
    espessura_valor = g.ESP_COMB.get()
    material_nome = g.MAT_COMB.get()
    canal_valor = g.CANAL_COMB.get()

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
            if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'config'):
                g.FORCA_LBL.config(text=f'{toneladas_m:.0f}', fg="black")
        else:
            if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'config'):
                g.FORCA_LBL.config(text='N/A', fg="red")

    # Verificar se o comprimento é menor que o comprimento total do canal
    if g.CANAL_COMB and hasattr(g.CANAL_COMB, 'get'):
        canal_obj = session.query(Canal).filter_by(valor=g.CANAL_COMB.get()).first()
        comprimento_total = getattr(canal_obj, 'comprimento_total', None) if canal_obj else None
        comprimento = float(comprimento) if comprimento else None

        if canal_obj and comprimento and comprimento_total:
            if comprimento < comprimento_total:
                if g.COMPR_ENTRY and hasattr(g.COMPR_ENTRY, 'config'):
                    g.COMPR_ENTRY.config(fg="black")
            elif comprimento >= comprimento_total:
                if g.COMPR_ENTRY and hasattr(g.COMPR_ENTRY, 'config'):
                    g.COMPR_ENTRY.config(fg="red")


def restaurar_valores_dobra(w):
    """
    Restaura os valores das dobras e os campos de cabeçalho
    a partir de g.DOBRAS_VALORES e g.CABECALHO_VALORES.
    """
    # Verificar se g.DOBRAS_VALORES foi inicializada
    if not hasattr(g, 'DOBRAS_VALORES') or g.DOBRAS_VALORES is None:
        return

    # Restaurar os valores das dobras
    for i in range(1, g.N):
        for col in range(1, w + 1):
            if i - 1 < len(g.DOBRAS_VALORES) and col - 1 < len(g.DOBRAS_VALORES[i - 1]):
                valor = g.DOBRAS_VALORES[i - 1][col - 1]
                print(f"Restaurando valor para aba{i}_entry_{col}: {valor}")
                entry = getattr(g, f'aba{i}_entry_{col}', None)
                if entry:
                    entry.delete(0, tk.END)
                    entry.insert(0, valor)


def salvar_valores_cabecalho():
    """
    Salva os valores atuais dos widgets no cabeçalho em g.CABECALHO_VALORES.
    """
    if not hasattr(g, 'CABECALHO_VALORES') or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}

    g.CABECALHO_VALORES = {
        'MAT_COMB': g.MAT_COMB.get() if g.MAT_COMB else '',
        'ESP_COMB': g.ESP_COMB.get() if g.ESP_COMB else '',
        'CANAL_COMB': g.CANAL_COMB.get() if g.CANAL_COMB else '',
        'COMPR_ENTRY': g.COMPR_ENTRY.get() if g.COMPR_ENTRY else '',
        'RI_ENTRY': g.RI_ENTRY.get() if g.RI_ENTRY else '',
        'DED_ESPEC_ENTRY': g.DED_ESPEC_ENTRY.get() if g.DED_ESPEC_ENTRY else '',
    }
    print("Valores salvos:", g.CABECALHO_VALORES)


def restaurar_valores_cabecalho():
    """
    Restaura os valores dos widgets no cabeçalho
    com base nos valores armazenados em g.CABECALHO_VALORES.
    """
    # Verifica se g.CABECALHO_VALORES já foi inicializado como um dicionário
    if not hasattr(g, 'CABECALHO_VALORES') or not isinstance(g.CABECALHO_VALORES, dict):
        g.CABECALHO_VALORES = {}

    # Restaura os valores nos widgets
    for widget_name, valor in g.CABECALHO_VALORES.items():
        widget = getattr(g, widget_name, None)
        if widget and isinstance(widget, (tk.Entry, ttk.Combobox)):
            try:
                if isinstance(widget, tk.Entry):
                    widget.delete(0, tk.END)
                    widget.insert(0, valor)
                elif isinstance(widget, ttk.Combobox):
                    widget.set(valor)
            except Exception as e:
                print(f"Erro ao restaurar valor para {widget_name}: {e}")
                raise

    print("Valores restaurados:", g.CABECALHO_VALORES)


def copiar(tipo, numero=None, w=None):
    """
    Copia o valor do label correspondente ao tipo e 
    número especificados para a área de transferência.
    """
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
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'metade_dobra': {
            'label': lambda numero: getattr(g, f'metadedobra{numero}_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'blank': {
            'label': getattr(g, f'medida_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'metade_blank': {
            'label': getattr(g, f'metade_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        }
    }

    config = configuracoes[tipo]

    label = config['label'](numero) if callable(config['label']) else config['label']
    if label is None:
        print(f"Erro: Label não encontrado para o tipo '{tipo}' com numero={numero} e w={w}.")
        return

    # Verificar se o label é um widget válido do tkinter
    if not hasattr(label, 'cget') or not hasattr(label, 'config'):
        print(f"Erro: O objeto para o tipo '{tipo}' não é um widget válido do tkinter.")
        return

    # Verificar se o texto está vazio
    try:
        texto_atual = getattr(label, 'cget')('text')
        # Converter para string para garantir compatibilidade
        texto_atual = str(texto_atual)
        if texto_atual == "":
            return
    except (tk.TclError, AttributeError):
        print(f"Erro: Não foi possível acessar o texto do widget para o tipo '{tipo}'.")
        return

    # Remover " Copiado!" se já estiver presente para evitar repetição
    if " Copiado!" in texto_atual:
        texto_original = texto_atual.replace(" Copiado!", "")
    else:
        texto_original = texto_atual

    config['funcao_calculo']()

    # Obter o texto atualizado após o cálculo
    try:
        texto_atualizado = getattr(label, 'cget')('text')
        # Converter para string e remover " Copiado!" se já estiver presente
        texto_atualizado = str(texto_atualizado)
        if " Copiado!" in texto_atualizado:
            texto_atualizado = texto_atualizado.replace(" Copiado!", "")
    except (tk.TclError, AttributeError):
        texto_atualizado = texto_original

    pyperclip.copy(texto_atualizado)
    print(f'Valor copiado {texto_atualizado}')
    getattr(label, 'config')(text=f'{texto_atualizado} Copiado!', fg="green")

    # Agendar a remoção do "Copiado!" após 2 segundos
    def remover_copiado():
        try:
            getattr(label, 'config')(text=texto_atualizado, fg="black")
        except (tk.TclError, AttributeError):
            pass

    if hasattr(label, 'after'):
        getattr(label, 'after')(2000, remover_copiado)


def limpar_busca(tipo):
    """
    Limpa os campos de busca e atualiza a lista correspondente.
    """
    configuracoes = obter_configuracoes()
    if tipo == 'dedução':
        configuracoes[tipo]['entries']['material_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['espessura_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['canal_combo'].delete(0, tk.END)
    else:
        configuracoes[tipo]['busca'].delete(0, tk.END)

    listar(tipo)


def focus_next_entry(current_index, w):
    """
    Move o foco para o próximo campo de entrada na aba atual.
    """
    next_index = current_index + 1
    if next_index < g.N:
        next_entry = getattr(g, f'aba{next_index}_entry_{w}', None)
        if next_entry:
            next_entry.focus()


def focus_previous_entry(current_index, w):
    """
    Move o foco para o campo de entrada anterior na aba atual.
    """
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(g, f'aba{previous_index}_entry_{w}', None)
        if previous_entry:
            previous_entry.focus()


def listar(tipo):
    """
    Lista os itens do banco de dados na interface gráfica.
    """
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


def todas_funcoes():
    """
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.
    """
    for tipo in ['espessura', 'canal', 'dedução']:
        atualizar_widgets(tipo)

    atualizar_toneladas_m()
    calcular_k_offset()
    aba_minima_externa()
    z_minimo_externo()
    for w in g.VALORES_W:
        calcular_dobra(w)

    razao_ri_espessura()

    # Atualizar tooltips
    canal_tooltip()


def configurar_main_frame(parent, rows=4):
    """
    Configura o frame principal com colunas e linhas padrão.
    """
    main_frame = tk.Frame(parent)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    for i in range(rows):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    return main_frame


def configurar_frame_edicoes(parent, text, columns=3, rows=4):
    """
    Cria um frame de edições com configuração padrão.
    """
    frame_edicoes = tk.LabelFrame(parent, text=text, pady=5)
    frame_edicoes.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    for i in range(columns):
        frame_edicoes.columnconfigure(i, weight=1 if i < columns - 1 else 0)

    for i in range(rows):
        frame_edicoes.rowconfigure(i, weight=1)

    return frame_edicoes
