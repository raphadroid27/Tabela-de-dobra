'''
Funções auxiliares para o aplicativo de cálculo de dobras.
'''
import tkinter as tk
from tkinter import messagebox, simpledialog
from math import pi
import re
import hashlib
import pyperclip
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, OperationalError
from models import Espessura, Material, Canal, Deducao, Usuario, Log
import globals as g
import tooltip as tp

engine = create_engine('sqlite:///tabela_de_dobra.db')
session = sessionmaker(bind=engine)
session = session()

# App
def carregar_variaveis_globais():
    '''
    Carrega as variáveis globais necessárias para o funcionamento do aplicativo.
    '''
    g.ESP_VALOR = float(g.ESP_COMB.get()) if g.ESP_COMB.get() else None
    g.CANAL_VALOR = (float(re.findall(r'\d+\.?\d*', g.CANAL_COMB.get())[0])
                      if g.CANAL_COMB.get() else None)
    g.R_INT = (float(re.findall(r'\d+\.?\d*', g.RI_ENTRY.get().replace(',', '.'))[0])
               if g.RI_ENTRY.get() else None)
    g.DED_ESPEC = (float(re.findall(r'\d+\.?\d*',g.DED_ESPEC_ENTRY.get().replace(',', '.'))[0])
                   if g.DED_ESPEC_ENTRY.get() else None)

    print(f'{g.CANAL_VALOR} {g.ESP_VALOR} {g.DED_VALOR}')

def atualizar_combobox(tipo):
    """
    Atualiza os valores dos comboboxes ou labels com base no tipo especificado.

    Args:
        tipo (str): O tipo de atualização a ser realizada. Pode ser:
            - 'material': Atualiza o combobox de materiais.
            - 'espessura': Atualiza o combobox de espessuras.
            - 'canal': Atualiza o combobox de canais.
            - 'dedução': Atualiza dedução e observações.
    """
    if tipo == 'material':
        if g.MAT_COMB and g.MAT_COMB.winfo_exists():
            materiais = [m.nome for m in session.query(Material).order_by(Material.id)]
            g.MAT_COMB.configure(values=materiais)

    elif tipo == 'espessura':
        material_nome = g.MAT_COMB.get()
        material_obj = session.query(Material).filter_by(nome=material_nome).first()
        if material_obj:
            espessuras = session.query(Espessura).join(Deducao).filter(
                Deducao.material_id == material_obj.id
            ).order_by(Espessura.valor)
            g.ESP_COMB.configure(values=[str(e.valor) for e in espessuras])

    elif tipo == 'canal':
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
            g.CANAL_COMB.configure(values=canais_valores)

    elif tipo == 'dedução':
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
                g.DED_LBL.config(text=deducao_obj.valor, fg="black")
                observacao = deducao_obj.observacao or 'Observações não encontradas'
                g.OBS_LBL.config(text=f'Observações: {observacao}')
            else:
                g.DED_LBL.config(text='N/A', fg="red")
                g.OBS_LBL.config(text='Observações não encontradas')

            g.DED_VALOR = deducao_obj.valor if deducao_obj else None
            g.LARG_CANAL = canal_obj.largura if deducao_obj else None

def canal_tooltip():
    '''
    Atualiza o tooltip do combobox de canais com as
    observações e comprimento total do canal selecionado.
    '''
    if g.CANAL_COMB.get() == "":
        g.CANAL_COMB.set("")
        tp.ToolTip(g.CANAL_COMB, "Selecione o canal de dobra.")
    else:
        canal_obj = session.query(Canal).filter_by(valor=g.CANAL_COMB.get()).first()
        if canal_obj:
            canal_obs = canal_obj.observacao if canal_obj.observacao else "N/A."
            canal_comprimento_total = (canal_obj.comprimento_total
                                       if canal_obj.comprimento_total else "N/A.")

            tp.ToolTip(g.CANAL_COMB,
                       f'Obs: {canal_obs}\n'
                       f'Comprimento total: {canal_comprimento_total}',
                       delay=0)

def atualizar_toneladas_m():
    '''
    Atualiza o valor de toneladas por metro com base no comprimento e na dedução selecionada.
    '''
    comprimento = g.COMPR_ENTRY.get()
    deducao_obj = session.query(Deducao).filter_by(valor=g.DED_VALOR).first()

    if g.MAT_COMB.get() != "" and g.ESP_COMB.get() != "" and g.CANAL_COMB.get() != "":
        if deducao_obj and deducao_obj.forca is not None:
            toneladas_m = ((deducao_obj.forca * float(comprimento)) / 1000
            if comprimento else deducao_obj.forca)
            g.FORCA_LBL.config(text=f'{toneladas_m:.0f}', fg="black")
        else:
            g.FORCA_LBL.config(text='N/A', fg="red")

    # Verificar se o comprimento é menor que o comprimento total do canal
    canal_obj = session.query(Canal).filter_by(valor=g.CANAL_COMB.get()).first()
    comprimento_total = canal_obj.comprimento_total if canal_obj else None
    comprimento = float(comprimento) if comprimento else None

    if canal_obj and comprimento and comprimento_total:
        if comprimento < comprimento_total:
            g.COMPR_ENTRY.config(fg="black")
        elif comprimento >= comprimento_total:
            g.COMPR_ENTRY.config(fg="red")

def calcular_fatork():
    '''
    Calcula o fator K com base nos valores de espessura, dedução e raio interno.
    Atualiza o label correspondente com o valor calculado.
    '''
    if g.DED_ESPEC:
        g.DED_VALOR = g.DED_ESPEC

    if not g.R_INT or not g.ESP_VALOR or not g.DED_VALOR or g.DED_VALOR == 'N/A':
        return

    g.FATOR_K = (4 * (g.ESP_VALOR - (g.DED_VALOR / 2) + g.R_INT) -
                 (pi * g.R_INT)) / (pi * g.ESP_VALOR)

    g.FATOR_K = min(g.FATOR_K, 0.5)

    g.K_LBL.config(text=f"{g.FATOR_K:.2f}", fg="blue"
                   if g.DED_VALOR == g.DED_ESPEC else "black")

def calcular_offset():
    '''
    Calcula o offset com base no fator K e na espessura.
    '''
    if not g.FATOR_K or not g.ESP_VALOR:
        print('Fator K não informado')
        return

    offset = g.FATOR_K * g.ESP_VALOR
    g.OFFSET_LBL.config(text=f"{offset:.2f}", fg="blue" if g.DED_VALOR == g.DED_ESPEC else "black")

def aba_minima_externa():
    '''
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Atualiza o label correspondente com o valor calculado.
    '''
    if g.CANAL_VALOR:
        aba_minima_valor = g.CANAL_VALOR / 2 + g.ESP_VALOR + 2
        g.ABA_EXT_LBL.config(text=f"{aba_minima_valor:.0f}")

def z_minimo_externo():
    '''
    Calcula o valor mínimo externo com base na espessura, dedução e largura do canal.
    Atualiza o label correspondente com o valor calculado.
    '''
    if g.MAT_COMB.get() != "" and g.ESP_COMB.get() != "" and g.CANAL_COMB.get() != "":
        if not g.LARG_CANAL:
            g.Z_EXT_LBL.config(text="N/A", fg="red")
            return
        if g.CANAL_VALOR and g.DED_VALOR:
            valor_z_min_ext = g.ESP_VALOR + (g.DED_VALOR / 2) + (g.LARG_CANAL / 2) + 2
            g.Z_EXT_LBL.config(text=f'{valor_z_min_ext:.0f}', fg="black")

def restaurar_dobras(w):
    '''
    Restaura os valores das dobras a partir de g.DOBRAS_VALORES.
    '''
     # Verificar se g.DOBRAS_VALORES foi inicializada
    if not hasattr(g, 'DOBRAS_VALORES') or g.DOBRAS_VALORES is None:
        return

    for i in range(1, g.N):
        for col in range(1, w + 1):
            if i - 1 < len(g.DOBRAS_VALORES) and col - 1 < len(g.DOBRAS_VALORES[i - 1]):
                valor = g.DOBRAS_VALORES[i - 1][col - 1]
                print(f"Restaurando valor para aba{i}_entry_{col}: {valor}")
                entry = getattr(g, f'aba{i}_entry_{col}', None)
                if entry:
                    entry.delete(0, tk.END)
                    entry.insert(0, valor)

    calcular_dobra(w)

def calcular_dobra(w):
    '''
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    '''
    # Criar uma lista de listas para armazenar os valores de linha i e coluna w
    g.DOBRAS_VALORES = [
        [
            getattr(g, f'aba{i}_entry_{col}').get() or ''  # Substitui valores vazios por '0'
            for col in range(1, w + 1)
        ]
        for i in range(1, g.N)
    ]

    # Exibir a matriz de valores para depuração
    print("Matriz de dobras (g.dobras_get):")
    for linha in g.DOBRAS_VALORES:
        print(linha)

    # Determinar o valor da dedução
    if g.DED_LBL.cget('text') == "" or g.DED_LBL.cget('text') == 'N/A':
        if g.DED_ESPEC_ENTRY.get() == "":
            return

        deducao_valor = g.DED_ESPEC
    else:
        deducao_valor = g.DED_VALOR
        if g.DED_ESPEC_ENTRY.get() != "":
            deducao_valor = g.DED_ESPEC

    # Função auxiliar para calcular medidas
    def calcular_medida(deducao_valor, i, w):
        dobra = g.DOBRAS_VALORES[i - 1][w - 1].replace(',', '.')

        if dobra == "":
            getattr(g, f'medidadobra{i}_label_{w}').config(text="")
            getattr(g, f'metadedobra{i}_label_{w}').config(text="")
        else:
            if i in (1, g.N - 1):
                medidadobra = float(dobra) - deducao_valor / 2
            else:
                if g.DOBRAS_VALORES[i][w - 1] == "":
                    medidadobra = float(dobra) - deducao_valor / 2
                else:
                    medidadobra = float(dobra) - deducao_valor

            metade_dobra = medidadobra / 2

            # Atualizar os widgets com os valores calculados
            getattr(g, f'medidadobra{i}_label_{w}').config(text=f'{medidadobra:.2f}', fg="black")
            getattr(g, f'metadedobra{i}_label_{w}').config(text=f'{metade_dobra:.2f}', fg="black")

        blank = sum(
        float(getattr(g, f'medidadobra{i}_label_{w}').cget('text').replace(' Copiado!', ''))
        for i in range(1, g.N)
        if getattr(g, f'medidadobra{i}_label_{w}').cget('text')
    )

        metade_blank = blank / 2

        # Atualizar os widgets com os valores calculados
        label = getattr(g, f'medida_blank_label_{w}')
        if blank:
            label.config(text=f"{blank:.2f}", fg="black")
        else:
            label.config(text="")

        label = getattr(g, f'metade_blank_label_{w}')
        if metade_blank:
            label.config(text=f"{metade_blank:.2f}", fg="black")
        else:
            label.config(text="")

    # Iterar pelas linhas e colunas para calcular as medidas
    for i in range(1, g.N):
        for col in range(1, w + 1):
            calcular_medida(deducao_valor, i, col)

def copiar(tipo, numero=None, w=None):
    '''
    Copia o valor do label correspondente ao tipo e 
    número especificados para a área de transferência.
    '''
    configuracoes = {
        'dedução': {
            'label': g.DED_LBL,
            'funcao_calculo': lambda: (atualizar_combobox('dedução'), 
                                       calcular_fatork(),
                                       calcular_offset())
        },
        'fator_k': {
            'label': g.K_LBL,
            'funcao_calculo': lambda: (atualizar_combobox('dedução'), 
                                       calcular_fatork(),
                                       calcular_offset())
        },
        'offset': {
            'label': g.OFFSET_LBL,
            'funcao_calculo': lambda: (atualizar_combobox('dedução'), 
                                       calcular_fatork(),
                                       calcular_offset())
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

    if label.cget('text') == "":
        return

    if hasattr(label, 'cget') and 'text' in label.keys():
        config['funcao_calculo']()
        pyperclip.copy(label.cget('text'))
        print(f'Valor copiado {label.cget("text")}')
        label.config(text=f'{label.cget("text")} Copiado!', fg="green")
    else:
        print(f"Erro: O label para o tipo '{tipo}' não possui o atributo 'text'.")

def limpar_dobras(w):
    '''
    Limpa os valores das dobras e atualiza os labels correspondentes.
    '''
    def obter_atributos(prefixo):
        return [
            getattr(g, f'{prefixo}{i}_label_{col}', None)
            for i in range(1, g.N)
            for col in range(1, w + 1)
        ]

    dobras = [getattr(g, f'aba{i}_entry_{col}', None)
              for i in range(1, g.N)
              for col in range(1, w + 1)]
    medidas = obter_atributos('medidadobra')
    metades = obter_atributos('metadedobra')

    g.DOBRAS_VALORES = []

    for dobra in dobras:
        if dobra:
            dobra.delete(0, tk.END)

    for medida in medidas:
        if medida:
            medida.config(text="")

    for metade in metades:
        if metade:
            metade.config(text="")

    g.DED_ESPEC_ENTRY.delete(0, tk.END)

    label = getattr(g, f'medida_blank_label_{w}', None)
    if label:
        label.config(text="")

    label = getattr(g, f'metade_blank_label_{w}', None)
    if label:
        label.config(text="")

def limpar_tudo():
    '''
    Limpa todos os campos e labels do aplicativo.
    '''
    campos = [
        g.MAT_COMB, g.ESP_COMB, g.CANAL_COMB
    ]
    for campo in campos:
        campo.set('')  # Limpa o valor selecionado
        if campo != g.MAT_COMB:
            campo.configure(values=[])  # Limpa os valores disponíveis

    entradas = [
        g.RI_ENTRY, g.COMPR_ENTRY
    ]
    for entrada in entradas:
        entrada.delete(0, tk.END)

    etiquetas = {
        g.K_LBL: "",
        g.DED_LBL: "",
        g.OFFSET_LBL: "",
        g.OBS_LBL: "Observações:",
        g.FORCA_LBL: "",
        g.ABA_EXT_LBL: "",
        g.Z_EXT_LBL: ""
    }
    for etiqueta, texto in etiquetas.items():
        etiqueta.config(text=texto)

    for w in g.VALORES_W:
        limpar_dobras(w)
        todas_funcoes(w)

def todas_funcoes(w):
    '''
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.
    '''
    carregar_variaveis_globais()
    atualizar_combobox('espessura')
    atualizar_combobox('canal')
    atualizar_combobox('dedução')
    atualizar_toneladas_m()
    calcular_fatork()
    calcular_offset()
    aba_minima_externa()
    z_minimo_externo()
    calcular_dobra(w)

    # Atualizar tooltips
    canal_tooltip()

# Manipulação de dados
def obter_configuracoes():
    '''
    Retorna um dicionário com as configurações de cada tipo de item.
    '''
    return {
        'dedução': {
            'lista': g.LIST_DED,
            'modelo': Deducao,
            'campos': {
                'valor': g.DED_VALOR_ENTRY,
                'observacao': g.DED_OBSER_ENTRY,
                'forca': g.DED_FORCA_ENTRY
            },
            'item_id': Deducao.id,
            'valores': g.valores_deducao,
            'ordem': Deducao.valor,
            'entries': {
                'material_combo': g.DED_MATER_COMB,
                'espessura_combo': g.DED_ESPES_COMB,
                'canal_combo': g.DED_CANAL_COMB
            }
        },
        'material': {
            'lista': g.LIST_MAT,
            'modelo': Material,
            'campos': {
                'nome': g.MAT_NOME_ENTRY,
                'densidade': g.MAT_DENS_ENTRY,
                'escoamento': g.MAT_ESCO_ENTRY,
                'elasticidade': g.MAT_ELAS_ENTRY
            },
            'item_id': Material.id,  # Corrigido de Deducao.material_id
            'valores': g.valores_material,
            'ordem': Material.id,
            'entry': g.MAT_NOME_ENTRY,
            'busca': g.MAT_BUSCA_ENTRY,
            'campo_busca': Material.nome
        },
        'espessura': {
            'lista': g.LIST_ESP,
            'modelo': Espessura,
            'item_id': Espessura.id,  # Corrigido de Deducao.espessura_id
            'valores': g.valores_espessura,
            'ordem': Espessura.valor,
            'entry': g.ESP_VALOR_ENTRY,
            'busca': g.ESP_BUSCA_ENTRY,
            'campo_busca': Espessura.valor  # Corrigido de espessura.valor
        },
        'canal': {
            'lista': g.LIST_CANAL,
            'modelo': Canal,  # Corrigido de canal
            'campos': {
                'valor': g.CANAL_VALOR_ENTRY,
                'largura': g.CANAL_LARGU_ENTRY,
                'altura': g.CANAL_ALTUR_ENTRY,
                'comprimento_total': g.CANAL_COMPR_ENTRY,
                'observacao': g.CANAL_OBSER_ENTRY
            },
            'item_id': Canal.id,  # Corrigido de deducao.canal_id
            'valores': g.valores_canal,
            'ordem': Canal.valor,  # Corrigido de canal.valor
            'entry': g.CANAL_VALOR_ENTRY,
            'busca': g.CANAL_BUSCA_ENTRY,
            'campo_busca': Canal.valor  # Corrigido de canal.valor
        },
        'usuario': {
            'lista': g.LIST_USUARIO,
            'modelo': Usuario,  # Corrigido de usuario
            'valores': g.valores_usuario,
            'ordem': Usuario.nome,  # Corrigido de usuario.nome
            'entry': g.USUARIO_BUSCA_ENTRY,
            'campo_busca': Usuario.nome  # Corrigido de usuario.nome
        }
    }

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

    if tipo == 'canal':
        itens = sorted(itens, key=lambda x: float(re.findall(r'\d+\.?\d*', x.valor)[0]))

    for item in itens:
        if tipo == 'dedução':
            if item.material is None or item.espessura is None or item.canal is None:
                continue
        config['lista'].insert("", "end", values=config['valores'](item))

def buscar(tipo):
    '''
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    try:
        config = configuracoes[tipo]
    except KeyError:
        messagebox.showerror("Erro", f"Tipo '{tipo}' não encontrado nas configurações.")
        return

    if tipo != 'dedução' and (config.get('busca') is None or not config['busca'].winfo_exists()):
        return

    if config['lista'] is None or not config['lista'].winfo_exists():
        return

    def filtrar_deducoes(material_nome, espessura_valor, canal_valor):
        query = session.query(Deducao).join(Material).join(Espessura).join(Canal)

        if material_nome:
            query = query.filter(Material.nome == material_nome)
        if espessura_valor:
            query = query.filter(Espessura.valor == espessura_valor)
        if canal_valor:
            query = query.filter(Canal.valor == canal_valor)

        return query.all()

    if tipo == 'dedução':
        material_nome = config['entries']['material_combo'].get()
        espessura_valor = config['entries']['espessura_combo'].get()
        canal_valor = config['entries']['canal_combo'].get()
        itens = filtrar_deducoes(material_nome, espessura_valor, canal_valor)
    else:
        item = config['busca'].get().replace(',', '.') if config['busca'] else ""
        itens = session.query(config['modelo']).filter(config['campo_busca'].like(f"{item}%"))

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    for item in itens:
        config['lista'].insert("", "end", values=config['valores'](item))

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

def adicionar(tipo):
    '''
    Adiciona um novo item ao banco de dados com base no tipo especificado.
    '''
    if not logado(tipo):
        return

    if tipo == 'dedução':
        adicionar_deducao()
    elif tipo == 'espessura':
        adicionar_espessura()
    elif tipo == 'material':
        adicionar_material()
    elif tipo == 'canal':
        adicionar_canal()

    limpar_campos(tipo)
    listar(tipo)

def adicionar_deducao():
    '''
    Lógica para adicionar uma nova dedução.
    '''
    espessura_valor = g.DED_ESPES_COMB.get()
    canal_valor = g.DED_CANAL_COMB.get()
    material_nome = g.DED_MATER_COMB.get()
    nova_observacao_valor = g.DED_OBSER_ENTRY.get()
    nova_forca_valor = g.DED_FORCA_ENTRY.get()

    if not all([espessura_valor, canal_valor, material_nome, g.DED_VALOR_ENTRY.get()]):
        messagebox.showerror("Erro",
                             "Material, espessura, canal e valor da dedução são obrigatórios.")
        return

    nova_deducao_valor = float(g.DED_VALOR_ENTRY.get().replace(',', '.'))
    espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
    canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()

    deducao_existente = session.query(Deducao).filter_by(
        espessura_id=espessura_obj.id,
        canal_id=canal_obj.id,
        material_id=material_obj.id
    ).first()

    if deducao_existente:
        messagebox.showerror("Erro", "Dedução já existe no banco de dados.")
        return

    nova_deducao = Deducao(
        espessura_id=espessura_obj.id,
        canal_id=canal_obj.id,
        material_id=material_obj.id,
        valor=nova_deducao_valor,
        observacao=nova_observacao_valor,
        forca=nova_forca_valor if nova_forca_valor else None
    )
    salvar_no_banco(nova_deducao, 'dedução',
                    f'espessura: {espessura_valor}, '
                    f'canal: {canal_valor}, '
                    f'material: {material_nome}, '
                    f'valor: {nova_deducao_valor}')

def adicionar_espessura():
    '''
    Lógica para adicionar uma nova espessura.
    '''
    espessura_valor = g.ESP_VALOR_ENTRY.get().replace(',', '.')
    if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
        messagebox.showwarning("Atenção!",
                               "A espessura deve conter apenas números ou números decimais.")
        g.ESP_VALOR_ENTRY.delete(0, tk.END)
        return

    espessura_existente = session.query(Espessura).filter_by(valor=espessura_valor).first()
    if espessura_existente:
        messagebox.showerror("Erro", "Espessura já existe no banco de dados.")
        return

    nova_espessura = Espessura(valor=espessura_valor)
    salvar_no_banco(nova_espessura, 'espessura', f'valor: {espessura_valor}')

def adicionar_material():
    '''
    Lógica para adicionar um novo material.
    '''
    nome_material = g.MAT_NOME_ENTRY.get()
    densidade_material = g.MAT_DENS_ENTRY.get()
    escoamento_material = g.MAT_ESCO_ENTRY.get()
    elasticidade_material = g.MAT_ELAS_ENTRY.get()

    if not nome_material:
        messagebox.showerror("Erro", "O campo Material é obrigatório.")
        return

    material_existente = session.query(Material).filter_by(nome=nome_material).first()
    if material_existente:
        messagebox.showerror("Erro", "Material já existe no banco de dados.")
        return

    novo_material = Material(
        nome=nome_material,
        densidade=float(densidade_material) if densidade_material else None,
        escoamento=float(escoamento_material) if escoamento_material else None,
        elasticidade=float(elasticidade_material) if elasticidade_material else None
    )
    salvar_no_banco(novo_material,
                    'material',
                    f'nome: {nome_material}, '
                    f'densidade: {densidade_material}, '
                    f'escoamento: {escoamento_material}, '
                    f'elasticidade: {elasticidade_material}')

def adicionar_canal():
    '''
    Lógica para adicionar um novo canal.
    '''
    valor_canal = g.CANAL_VALOR_ENTRY.get()
    largura_canal = g.CANAL_LARGU_ENTRY.get()
    altura_canal = g.CANAL_ALTUR_ENTRY.get()
    comprimento_total_canal = g.CANAL_COMPR_ENTRY.get()
    observacao_canal = g.CANAL_OBSER_ENTRY.get()

    if not valor_canal:
        messagebox.showerror("Erro", "O campo Canal é obrigatório.")
        return

    canal_existente = session.query(Canal).filter_by(valor=valor_canal).first()
    if canal_existente:
        messagebox.showerror("Erro", "Canal já existe no banco de dados.")
        return

    novo_canal = Canal(
        valor=valor_canal,
        largura=float(largura_canal) if largura_canal else None,
        altura=float(altura_canal) if altura_canal else None,
        comprimento_total=float(comprimento_total_canal) if comprimento_total_canal else None,
        observacao=observacao_canal if observacao_canal else None
    )
    salvar_no_banco(novo_canal,
                    'canal',
                    f'valor: {valor_canal}, '
                    f'largura: {largura_canal}, '
                    f'altura: {altura_canal}, '
                    f'comprimento_total: {comprimento_total_canal}, '
                    f'observacao: {observacao_canal}')

def salvar_no_banco(obj, tipo, detalhes):
    '''
    Salva um objeto no banco de dados e registra o log.
    '''
    session.add(obj)
    try:
        session.commit()
        registrar_log(g.USUARIO_NOME, 'adicionar', tipo, obj.id, detalhes)
        messagebox.showinfo("Sucesso", f"Novo(a) {tipo} adicionado(a) com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise

def editar(tipo):
    '''
    Edita um item existente no banco de dados com base no tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao('editor'):  # Permitir que editores realizem esta ação
        return

    if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = item_selecionado(tipo)
    obj_id = obj.id
    if obj:
        alteracoes = []  # Lista para armazenar as alterações
        for campo, entry in config['campos'].items():
            valor_novo = entry.get().strip()
            if valor_novo == "":
                valor_novo = None
            else:
                try:
                    if campo in ["largura", "altura", "comprimento_total"]:
                        valor_novo = float(valor_novo.replace(",", "."))
                except ValueError:
                    messagebox.showerror("Erro", f"Valor inválido para o campo '{campo}'.")
                    return

            valor_antigo = getattr(obj, campo)
            if valor_antigo != valor_novo:  # Verifica se houve alteração
                alteracoes.append(f"{tipo} {campo}: '{valor_antigo}' -> '{valor_novo}'")
                setattr(obj, campo, valor_novo)

        try:
            session.commit()
            print("Operação realizada com sucesso!")
        except IntegrityError as e:
            session.rollback()
            print(f"Erro de integridade no banco de dados: {e}")
        except OperationalError as e:
            session.rollback()
            print(f"Erro operacional no banco de dados: {e}")
        except Exception as e:
            session.rollback()
            print(f"Erro inesperado: {e}")
            raise
        detalhes = "; ".join(alteracoes)  # Concatena as alterações em uma string
        # Registrar a edição com detalhes
        registrar_log(g.USUARIO_NOME, "editar", tipo, obj_id, detalhes)
        messagebox.showinfo("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")
    else:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a).")

    # Limpar os campos após a edição
    for entry in config['campos'].values():
        entry.delete(0, tk.END)

    # Atualizar as listas e comboboxes
    atualizar_combobox('material')
    atualizar_combobox('espessura')
    atualizar_combobox('canal')
    atualizar_combobox('dedução')
    atualizar_combobox_deducao()
    for tipo_item in configuracoes:
        listar(tipo_item)
        buscar(tipo_item)

def item_selecionado(tipo):
    '''
    Retorna o objeto selecionado na lista correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return None

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()

    return obj

def excluir(tipo):
    '''
    Exclui um item do banco de dados com base no tipo especificado.
    Os tipos disponíveis são:]
    - dedução
    - espessura
    - material
    - canal
    '''
    if not tem_permissao('editor'):  # Permitir que editores realizem esta ação
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if config['lista'] is None:
        return

    aviso = messagebox.askyesno("Atenção!",
                                f"Ao excluir um(a) {tipo} todas as deduções relacionadas "
                                f"serão excluídas também, 'deseja continuar?")
    if not aviso:
        return

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a).")
        return

    deducao_objs = (
        session.query(Deducao)
        .join(Canal, Deducao.canal_id == Canal.id)  # Junção explícita entre Deducao e Canal
        .filter(Canal.id == obj.id)  # Filtrar pelo ID do objeto selecionado
        .all()
    )

    for d in deducao_objs:
        session.delete(d)

    session.delete(obj)
    try:
        session.commit()
        print("Operação realizada com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise
    # Registrar a exclusão
    registrar_log(g.USUARIO_NOME,
                  "excluir",
                  tipo,
                  obj_id,
                  f"Excluído(a) {tipo} {(obj.nome) if tipo =='material' else obj.valor}")
    config['lista'].delete(selected_item)
    messagebox.showinfo("Sucesso", f"{tipo.capitalize()} excluído(a) com sucesso!")

    limpar_campos(tipo)
    listar(tipo)

def limpar_campos(tipo):
    '''
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    for entry in config['campos'].values():
        entry.delete(0, tk.END)

def preencher_campos(tipo):
    '''
    Preenche os campos de entrada com os dados do item selecionado na lista.
    '''
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    obj = item_selecionado(tipo)

    if obj:
        for campo, entry in config['campos'].items():
            entry.delete(0, tk.END)
            if getattr(obj, campo) is not None:
                entry.insert(0, getattr(obj, campo))
            else:
                entry.insert(0, '')

def atualizar_combobox_deducao():
    '''
    Atualiza os comboboxes de material, espessura e canal na aba de dedução.
    '''
    if g.DED_MATER_COMB and g.DED_MATER_COMB.winfo_exists():
        g.DED_MATER_COMB.configure(values=[m.nome for m in session
                                           .query(Material)
                                           .order_by(Material.id).all()])

    if g.DED_ESPES_COMB and g.DED_ESPES_COMB.winfo_exists():
        g.DED_ESPES_COMB.configure(values=sorted([e.valor for e in session.query(Espessura).all()]))

    if g.DED_CANAL_COMB and g.DED_CANAL_COMB.winfo_exists():
        g.DED_CANAL_COMB.configure(values=sorted(
            [c.valor for c in session.query(Canal).all()],
            key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0])
        ))

# Manipulação de usuarios
def novo_usuario():
    '''
    Cria um novo usuário com o nome e senha fornecidos.
    '''
    novo_usuario_nome = g.USUARIO_ENTRY.get()
    novo_usuario_senha = g.SENHA_ENTRY.get()
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()

    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.", parent=g.AUTEN_FORM)
        return

    # Verificar se o usuário já existe
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.", parent=g.AUTEN_FORM)
        return

    # Criar o novo usuário
    usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, role=g.ADMIN_VAR)
    session.add(usuario)
    try:
        session.commit()
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.", parent=g.AUTEN_FORM)
        g.AUTEN_FORM.destroy()
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise  # Relança a exceção para depuração

    habilitar_janelas()

def login():
    '''
    Realiza o login do usuário com o nome e senha fornecidos.
    Se o usuário não existir, cria um novo usuário.
    '''
    g.USUARIO_NOME = g.USUARIO_ENTRY.get()
    usuario_senha = g.SENHA_ENTRY.get()

    usuario_obj = session.query(Usuario).filter_by(nome=g.USUARIO_NOME).first()

    if usuario_obj:
        if usuario_obj.senha == "nova_senha":
            nova_senha = simpledialog.askstring("Nova Senha",
                                                "Digite uma nova senha:",
                                                show="*",
                                                parent=g.AUTEN_FORM)
            if nova_senha:
                usuario_obj.senha = hashlib.sha256(nova_senha.encode()).hexdigest()
                try:
                    session.commit()
                    print("Operação realizada com sucesso!")
                except IntegrityError as e:
                    session.rollback()
                    print(f"Erro de integridade no banco de dados: {e}")
                except OperationalError as e:
                    session.rollback()
                    print(f"Erro operacional no banco de dados: {e}")
                except Exception as e:
                    session.rollback()
                    print(f"Erro inesperado: {e}")
                    raise
                messagebox.showinfo("Sucesso",
                                    "Senha alterada com sucesso. Faça login novamente.",
                                    parent=g.AUTEN_FORM)
                return
        elif usuario_obj.senha == hashlib.sha256(usuario_senha.encode()).hexdigest():
            messagebox.showinfo("Login", "Login efetuado com sucesso.", parent=g.AUTEN_FORM)
            g.USUARIO_ID = usuario_obj.id
            g.AUTEN_FORM.destroy()
            g.PRINC_FORM.title(f"Cálculo de Dobra - {usuario_obj.nome}")
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.AUTEN_FORM)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.AUTEN_FORM)

    habilitar_janelas()

def logado(tipo):
    '''
    Verifica se o usuário está logado antes de permitir ações em formulários específicos.
    '''
    configuracoes = {
        'dedução': g.DEDUC_FORM,
        'espessura': g.ESPES_FORM,
        'material': g.MATER_FORM,
        'canal': g.CANAL_FORM
    }

    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Login requerido.", parent=configuracoes[tipo])
        return False
    return True

def tem_permissao(role_requerida):
    '''
    Verifica se o usuário tem permissão para realizar uma ação específica.
    '''
    usuario_obj = session.query(Usuario).filter_by(id=g.USUARIO_ID).first()
    if not usuario_obj:
        messagebox.showerror("Erro", "Você não tem permissão para acessar esta função.")
        return False
    # Permitir hierarquia de permissões
    roles_hierarquia = ["viewer", "editor", "admin"]
    if roles_hierarquia.index(usuario_obj.role) < roles_hierarquia.index(role_requerida):
        messagebox.showerror("Erro", f"Permissão '{role_requerida}' requerida.")
        return False
    return True

def logout():
    '''
    Realiza o logout do usuário atual.
    '''
    if g.USUARIO_ID is None:
        messagebox.showerror("Erro", "Nenhum usuário logado.")
        return
    g.USUARIO_ID = None
    g.PRINC_FORM.title("Cálculo de Dobra")
    messagebox.showinfo("Logout", "Logout efetuado com sucesso.")

def resetar_senha():
    '''
    Reseta a senha do usuário selecionado na lista de usuários.
    '''
    selected_item = g.LIST_USUARIO.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para resetar a senha.",
                                  parent=g.USUAR_FORM)
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0]
    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        usuario_obj.senha = novo_password
        try:
            session.commit()
            print("Operação realizada com sucesso!")
        except IntegrityError as e:
            session.rollback()
            print(f"Erro de integridade no banco de dados: {e}")
        except OperationalError as e:
            session.rollback()
            print(f"Erro operacional no banco de dados: {e}")
        except Exception as e:
            session.rollback()
            print(f"Erro inesperado: {e}")
            raise
        tk.messagebox.showinfo("Sucesso", "Senha resetada com sucesso.", parent=g.USUAR_FORM)
    else:
        tk.messagebox.showerror("Erro", "Usuário não encontrado.", parent=g.USUAR_FORM)

def excluir_usuario():
    '''
    Exclui o usuário selecionado na lista de usuários.
    '''
    if not tem_permissao("admin"):
        return

    if g.LIST_USUARIO is None:
        return

    selected_item = g.LIST_USUARIO.selection()[0]
    item = g.LIST_USUARIO.item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(Usuario).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro", "Usuário não encontrado.", parent=g.USUAR_FORM)
        return

    if obj.role == "admin":
        messagebox.showerror("Erro",
                             "Não é possível excluir um administrador.",
                             parent=g.USUAR_FORM)
        return

    aviso = messagebox.askyesno("Atenção!",
                                "Tem certeza que deseja excluir o usuário?",
                                parent=g.USUAR_FORM)
    if not aviso:
        return

    session.delete(obj)
    try:
        session.commit()
        print("Operação realizada com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise
    g.LIST_USUARIO.delete(selected_item)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!", parent=g.USUAR_FORM)

    listar('usuario')

def tornar_editor():
    '''
    Promove o usuário selecionado a editor.
    '''
    selected_item = g.LIST_USUARIO.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso",
                                  "Selecione um usuário para promover a editor.",
                                  parent=g.USUAR_FORM)
        return

    user_id = g.LIST_USUARIO.item(selected_item, "values")[0]
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()

    if usuario_obj:
        if usuario_obj.role == "admin":
            tk.messagebox.showerror("Erro",
                                    "O usuário já é um administrador.",
                                    parent=g.USUAR_FORM)
            return
        if usuario_obj.role == "editor":
            tk.messagebox.showinfo("Informação",
                                   "O usuário já é um editor.",
                                   parent=g.USUAR_FORM)
            return

        usuario_obj.role = "editor"
        try:
            session.commit()
            print("Operação realizada com sucesso!")
        except IntegrityError as e:
            session.rollback()
            print(f"Erro de integridade no banco de dados: {e}")
        except OperationalError as e:
            session.rollback()
            print(f"Erro operacional no banco de dados: {e}")
        except Exception as e:
            session.rollback()
            print(f"Erro inesperado: {e}")
            raise
        tk.messagebox.showinfo("Sucesso",
                               "Usuário promovido a editor com sucesso.",
                               parent=g.USUAR_FORM)
        listar('usuario')  # Atualiza a lista de usuários na interface
    else:
        tk.messagebox.showerror("Erro",
                                "Usuário não encontrado.",
                                parent=g.USUAR_FORM)

# Manipulação de formulários
def no_topo(form):
    '''
    Define se a janela deve ficar sempre no topo ou não.
    '''
    def set_topmost(window, on_top):
        if window and window.winfo_exists():
            window.attributes("-topmost",on_top)

    on_top_valor = g.NO_TOPO_VAR.get() == 1
    set_topmost(form, on_top_valor)

def posicionar_janela(form, posicao=None):
    '''
    Posiciona a janela em relação à janela principal.
    '''
    form.update_idletasks()
    g.PRINC_FORM.update_idletasks()
    largura_monitor = g.PRINC_FORM.winfo_screenwidth()
    posicao_x = g.PRINC_FORM.winfo_x()
    largura_janela = g.PRINC_FORM.winfo_width()
    largura_form = form.winfo_width()

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = g.PRINC_FORM.winfo_x() + ((g.PRINC_FORM.winfo_width() - largura_form) // 2)
        y = g.PRINC_FORM.winfo_y() + ((g.PRINC_FORM.winfo_height() - form.winfo_height()) // 2)
    elif posicao == 'direita':
        x = g.PRINC_FORM.winfo_x() + largura_janela + 10
        y = g.PRINC_FORM.winfo_y()
        if x + largura_form > largura_monitor:
            x = g.PRINC_FORM.winfo_x() - largura_form - 10
    elif posicao == 'esquerda':
        x = g.PRINC_FORM.winfo_x() - largura_form - 10
        y = g.PRINC_FORM.winfo_y()
        if x < 0:
            x = g.PRINC_FORM.winfo_x() + largura_janela + 10
    else:
        return

    form.geometry(f"+{x}+{y}")

def desabilitar_janelas():
    '''
    Desabilita todas as janelas do aplicativo.
    '''
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', True)
            form.focus_force()

def habilitar_janelas():
    '''
    Habilita todas as janelas do aplicativo.
    '''
    forms = [g.PRINC_FORM, g.DEDUC_FORM, g.ESPES_FORM, g.MATER_FORM, g.CANAL_FORM]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', False)
            form.focus_force()

def focus_next_entry(current_index, w):
    '''
    Move o foco para o próximo campo de entrada na aba atual.
    '''
    next_index = current_index + 1
    if next_index < g.N:
        next_entry = getattr(g, f'aba{next_index}_entry_{w}', None)
        if next_entry:
            next_entry.focus()

def focus_previous_entry(current_index, w):
    '''
    Move o foco para o campo de entrada anterior na aba atual.
    '''
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(g, f'aba{previous_index}_entry_{w}', None)
        if previous_entry:
            previous_entry.focus()

# Manipulação de logs
def registrar_log(usuario_nome, acao, tabela, registro_id, detalhes=None):
    '''
    Registra uma ação no banco de dados.
    '''
    log = Log(
        usuario_nome=usuario_nome,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes
    )
    session.add(log)
    try:
        session.commit()
        print("Operação realizada com sucesso!")
    except IntegrityError as e:
        session.rollback()
        print(f"Erro de integridade no banco de dados: {e}")
    except OperationalError as e:
        session.rollback()
        print(f"Erro operacional no banco de dados: {e}")
    except Exception as e:
        session.rollback()
        print(f"Erro inesperado: {e}")
        raise

# def atualizar_interface(configuracoes=None, tipo=None):
#     '''
#     Atualiza as listas e comboboxes na interface.
#     '''
#     if tipo:
#         listar(tipo)
#     elif configuracoes:
#         for tipo_item in configuracoes:
#             listar(tipo_item)
#             buscar(tipo_item)
