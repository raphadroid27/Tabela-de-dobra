import tkinter as tk
from tkinter import messagebox, simpledialog
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Espessura, Material, Canal, Deducao, Usuario, Log
import globals as g
import re
import hashlib
import tooltip as tp
import placeholder as ph

engine = create_engine('sqlite:///tabela_de_dobra.db')
session = sessionmaker(bind=engine)
session = session()

# App
def carregar_variaveis_globais():
    g.espessura_valor = float(g.espessura_combobox.get()) if g.espessura_combobox.get() else None
    g.canal_valor = float(re.findall(r'\d+\.?\d*', g.canal_combobox.get())[0]) if g.canal_combobox.get() else None
    g.raio_interno = float(re.findall(r'\d+\.?\d*', g.raio_interno_entry.get().replace(',', '.'))[0]) if g.raio_interno_entry.get() else None
    g.deducao_espec = float(re.findall(r'\d+\.?\d*',g.deducao_espec_entry.get().replace(',', '.'))[0]) if g.deducao_espec_entry.get() else None
    
    print(f'{g.canal_valor} {g.espessura_valor} {g.deducao_valor}')

def atualizar_material():
    g.material_combobox['values'] = [m.nome for m in session.query(Material).order_by(Material.nome).all()]

def atualizar_espessura():
    material_nome = g.material_combobox.get()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()
    if material_obj:
        espessuras_valores = [str(e.valor) for e in session.query(Espessura).join(Deducao).filter(Deducao.material_id == material_obj.id).order_by(Espessura.valor).all()]
        g.espessura_combobox['values'] = espessuras_valores

def atualizar_canal():
    espessura_valor = g.espessura_combobox.get()
    material_nome = g.material_combobox.get()
    espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
    material_obj = session.query(Material).filter_by(nome=material_nome).first()

    # Inicializar canais_valores como uma lista vazia
    canais_valores = []    
    
    if espessura_obj:
        canais_valores = sorted(
            [str(c.valor) for c in session.query(Canal).join(Deducao)
             .filter(Deducao.espessura_id == espessura_obj.id)
             .filter(Deducao.material_id == material_obj.id)
             .order_by(Canal.valor).all()],
            key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0]) if re.search(r'\d+\.?\d*', x) else float('inf')
        )
        
    g.canal_combobox['values'] = canais_valores

def canal_tooltip():
    # Verificar se o combobox está vazio
    if g.canal_combobox.get() == "":
        g.canal_combobox.set("")
        tp.ToolTip(g.canal_combobox, "Selecione o canal de dobra.")
    else:
        canal_obj = session.query(Canal).filter_by(valor=g.canal_combobox.get()).first()
        if canal_obj:
                canal_obs = canal_obj.observacao if canal_obj.observacao else "N/A."
                canal_comprimento_total = canal_obj.comprimento_total if canal_obj.comprimento_total else "N/A."

                tp.ToolTip(g.canal_combobox, f'Obs: {canal_obs}\nComprimento total: {canal_comprimento_total}', delay=0)

def atualizar_deducao_e_obs():
    espessura_valor = g.espessura_combobox.get()
    material_nome = g.material_combobox.get()
    canal_valor = g.canal_combobox.get()

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
            g.deducao_label.config(text=deducao_obj.valor, fg="black")
            g.obs_label.config(text=f'Observações: {deducao_obj.observacao}' if deducao_obj.observacao else 'Observações não encontradas')
        else:
            g.deducao_label.config(text='N/A', fg="red")
            g.obs_label.config(text='Observações não encontradas')
    
        g.deducao_valor = deducao_obj.valor if deducao_obj else None
        g.largura_canal = canal_obj.largura if deducao_obj else None

def atualizar_toneladas_m():
    comprimento = g.comprimento_entry.get()
    deducao_obj = session.query(Deducao).filter_by(valor=g.deducao_valor).first()

    if g.material_combobox.get() != "" and g.espessura_combobox.get() != "" and g.canal_combobox.get() != "":
        if deducao_obj and deducao_obj.forca is not None:
            toneladas_m = (deducao_obj.forca * float(comprimento)) / 1000 if comprimento else deducao_obj.forca
            g.ton_m_label.config(text=f'{toneladas_m:.0f}', fg="black")
        else:
            g.ton_m_label.config(text='N/A', fg="red") 
    
    # Verificar se o comprimento é menor que o comprimento total do canal
    canal_obj = session.query(Canal).filter_by(valor=g.canal_combobox.get()).first()
    comprimento_total = canal_obj.comprimento_total if canal_obj else None
    comprimento = float(comprimento) if comprimento else None

    if canal_obj and comprimento and comprimento_total:
        if comprimento < comprimento_total:
            g.comprimento_entry.config(fg="black")
        elif comprimento >= comprimento_total:
            g.comprimento_entry.config(fg="red")
        
def calcular_fatork():
    if g.deducao_espec:
        g.deducao_valor = g.deducao_espec

    if not g.raio_interno or not g.espessura_valor or not g.deducao_valor or g.deducao_valor == 'N/A':
        return

    g.fator_k = (4 * (g.espessura_valor - (g.deducao_valor / 2) + g.raio_interno) - (pi * g.raio_interno)) / (pi * g.espessura_valor)  

    if g.fator_k > 0.5:
        g.fator_k = 0.5

    g.fator_k_label.config(text=f"{g.fator_k:.2f}", fg="blue" if g.deducao_valor == g.deducao_espec else "black")

def calcular_offset():
    if not g.fator_k or not g.espessura_valor:
        print('Fator K não informado')
        return

    offset = g.fator_k * g.espessura_valor
    g.offset_label.config(text=f"{offset:.2f}", fg="blue" if g.deducao_valor == g.deducao_espec else "black")

def aba_minima_externa():
    if g.canal_valor:
        aba_minima_valor = g.canal_valor / 2 + g.espessura_valor + 2
        g.aba_min_externa_label.config(text=f"{aba_minima_valor:.0f}")

def z_minimo_externo():
    if g.material_combobox.get() != "" and g.espessura_combobox.get() != "" and g.canal_combobox.get() != "":
        if not g.largura_canal:
            g.z_min_externa_label.config(text="N/A", fg="red")
            return
        if g.canal_valor and g.deducao_valor:
            z_minimo_externo = g.espessura_valor + (g.deducao_valor / 2) + (g.largura_canal / 2) + 2
            g.z_min_externa_label.config(text=f'{z_minimo_externo:.0f}', fg="black")

def restaurar_dobras(w):
     # Verificar se g.dobras_get foi inicializada
    if not hasattr(g, 'dobras_get') or g.dobras_get is None:
        print("Erro: g.dobras_get não foi inicializada.")
        return

    for i in range(1, g.n):
        for col in range(1, w + 1):
            if i - 1 < len(g.dobras_get) and col - 1 < len(g.dobras_get[i - 1]):
                valor = g.dobras_get[i - 1][col - 1]
                print(f"Restaurando valor para aba{i}_entry_{col}: {valor}")
                entry = getattr(g, f'aba{i}_entry_{col}', None)
                if entry:
                    entry.delete(0, tk.END)
                    entry.insert(0, valor)

    calcular_dobra(w)

def calcular_dobra(w):
    # Criar uma lista de listas para armazenar os valores de linha i e coluna w
    g.dobras_get = [
        [
            getattr(g, f'aba{i}_entry_{col}').get() or ''  # Substitui valores vazios por '0'
            for col in range(1, w + 1)
        ]
        for i in range(1, g.n)
    ]

    # Exibir a matriz de valores para depuração
    print("Matriz de dobras (g.dobras_get):")
    for linha in g.dobras_get:
        print(linha)

    # Determinar o valor da dedução
    if g.deducao_label['text'] == "" or g.deducao_label['text'] == 'N/A':
        if g.deducao_espec_entry.get() == "":
            return
        else:
            deducao_valor = g.deducao_espec
    else:
        deducao_valor = g.deducao_valor
        if g.deducao_espec_entry.get() != "":
            deducao_valor = g.deducao_espec

    # Função auxiliar para calcular medidas
    def calcular_medida(deducao_valor, i, w):
        dobra = g.dobras_get[i - 1][w - 1].replace(',', '.')

        if dobra == "":
            getattr(g, f'medidadobra{i}_label_{w}').config(text="")
            getattr(g, f'metadedobra{i}_label_{w}').config(text="")
        else:
            if i == 1 or i == g.n - 1:
                medidadobra = float(dobra) - deducao_valor / 2
            else:
                if g.dobras_get[i][w - 1] == "":
                    medidadobra = float(dobra) - deducao_valor / 2
                else:
                    medidadobra = float(dobra) - deducao_valor

            metade_dobra = medidadobra / 2

            # Atualizar os widgets com os valores calculados
            getattr(g, f'medidadobra{i}_label_{w}').config(text=f'{medidadobra:.2f}', fg="black")
            getattr(g, f'metadedobra{i}_label_{w}').config(text=f'{metade_dobra:.2f}', fg="black")
        
        blank = sum([
        float(getattr(g, f'medidadobra{i}_label_{w}').cget('text').replace(' Copiado!', ''))
        for i in range(1, g.n)
        if getattr(g, f'medidadobra{i}_label_{w}').cget('text')
        ])
        
        metade_blank = blank / 2

        # Atualizar os widgets com os valores calculados
        getattr(g, f'medida_blank_label_{w}').config(text=f"{blank:.2f}", fg="black") if blank else getattr(g, f'medida_blank_label_{w}').config(text="")
        getattr(g, f'metade_blank_label_{w}').config(text=f"{metade_blank:.2f}", fg="black") if metade_blank else getattr(g, f'metade_blank_label_{w}').config(text="")

    # Iterar pelas linhas e colunas para calcular as medidas
    for i in range(1, g.n):
        for col in range(1, w + 1):
            calcular_medida(deducao_valor, i, col)
    
def razao_raio_esp():
    if g.raio_interno is not None and g.espessura_valor is not None:
        try:
            razao_raio_esp_valor = g.raio_interno / g.espessura_valor
            g.razao_raio_esp_label.config(text=f'{razao_raio_esp_valor:.2f}')
        except ValueError:
            return

def copiar(tipo, numero=None, w=None):
    configuracoes = {
        'dedução': {
            'label': g.deducao_label,
            'funcao_calculo': lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset())
        },
        'fator_k': {
            'label': g.fator_k_label,
            'funcao_calculo': lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset())
        },
        'offset': {
            'label': g.offset_label,
            'funcao_calculo': lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset())
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
    def obter_atributos(prefixo):
        return [
            getattr(g, f'{prefixo}{i}_label_{col}', None)
            for i in range(1, g.n)
            for col in range(1, w + 1)
        ]

    dobras = [getattr(g, f'aba{i}_entry_{col}', None) for i in range(1, g.n) for col in range(1, w + 1)]
    medidas = obter_atributos('medidadobra')
    metades = obter_atributos('metadedobra')

    g.dobras_get = []

    for dobra in dobras:
        if dobra:
            dobra.delete(0, tk.END)

    for medida in medidas:
        if medida:
            medida.config(text="")

    for metade in metades:
        if metade:
            metade.config(text="")

    g.deducao_espec_entry.delete(0, tk.END)
    getattr(g, f'medida_blank_label_{w}', None).config(text="") if getattr(g, f'medida_blank_label_{w}', None) else None
    getattr(g, f'metade_blank_label_{w}', None).config(text="") if getattr(g, f'metade_blank_label_{w}', None) else None

def limpar_tudo():
    campos = [
        g.material_combobox, g.espessura_combobox, g.canal_combobox
    ]
    for campo in campos:
        campo.set('')
        if campo != g.material_combobox:
            campo['values'] = []

    entradas = [
        g.raio_interno_entry, g.comprimento_entry
    ]
    for entrada in entradas:
        entrada.delete(0, tk.END)

    etiquetas = {
        g.fator_k_label: "",
        g.deducao_label: "",
        g.offset_label: "",
        g.obs_label: "Observações:",
        g.ton_m_label: "",
        g.aba_min_externa_label: "",
        g.z_min_externa_label: ""
    }
    for etiqueta, texto in etiquetas.items():
        etiqueta.config(text=texto)

    for w in g.valores_w:
        limpar_dobras(w)
        todas_funcoes(w)

def todas_funcoes(w):
    carregar_variaveis_globais()
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_toneladas_m()
    #atualizar_comprimento_total()
    calcular_fatork()
    calcular_offset()
    aba_minima_externa()
    z_minimo_externo()
    calcular_dobra(w)

    # Atualizar tooltips
    canal_tooltip()

# Manipulação de dados
def obter_configuracoes():
    return {
        'dedução': {
            'lista': g.lista_deducao,
            'modelo': Deducao,
            'campos': {
                'valor': g.deducao_valor_entry,
                'observacao': g.deducao_obs_entry,
                'forca': g.deducao_forca_entry
            },
            'item_id': Deducao.id,
            'valores': g.valores_deducao,
            'ordem': Deducao.valor,
            'entries': {
                'material_combo': g.deducao_material_combobox,
                'espessura_combo': g.deducao_espessura_combobox,
                'canal_combo': g.deducao_canal_combobox
            }
        },
        'material': {
            'lista': g.lista_material,
            'modelo': Material,
            'campos': {
                'nome': g.material_nome_entry,
                'densidade': g.material_densidade_entry,
                'escoamento': g.material_escoamento_entry,
                'elasticidade': g.material_elasticidade_entry
            },
            'item_id': Material.id,  # Corrigido de Deducao.material_id
            'valores': g.valores_material,
            'ordem': Material.nome,
            'entry': g.material_nome_entry,
            'busca': g.material_busca_entry,
            'campo_busca': Material.nome
        },
        'espessura': {
            'lista': g.lista_espessura,
            'modelo': Espessura,
            'item_id': Espessura.id,  # Corrigido de Deducao.espessura_id
            'valores': g.valores_espessura,
            'ordem': Espessura.valor,
            'entry': g.espessura_valor_entry,
            'busca': g.espessura_busca_entry,
            'campo_busca': Espessura.valor  # Corrigido de espessura.valor
        },
        'canal': {
            'lista': g.lista_canal,
            'modelo': Canal,  # Corrigido de canal
            'campos': {
                'valor': g.canal_valor_entry,
                'largura': g.canal_largura_entry,
                'altura': g.canal_altura_entry,
                'comprimento_total': g.canal_comprimento_entry,
                'observacao': g.canal_observacao_entry
            },
            'item_id': Canal.id,  # Corrigido de deducao.canal_id
            'valores': g.valores_canal,
            'ordem': Canal.valor,  # Corrigido de canal.valor
            'entry': g.canal_valor_entry,
            'busca': g.canal_busca_entry,
            'campo_busca': Canal.valor  # Corrigido de canal.valor
        },
        'usuario': {
            'lista': g.lista_usuario,
            'modelo': Usuario,  # Corrigido de usuario
            'valores': g.valores_usuario,
            'ordem': Usuario.nome,  # Corrigido de usuario.nome
            'entry': g.usuario_valor_entry,
            'campo_busca': Usuario.nome  # Corrigido de usuario.nome
        }
    }

def listar(tipo):
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
    configuracoes = obter_configuracoes()
    if tipo == 'dedução':
        configuracoes[tipo]['entries']['material_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['espessura_combo'].delete(0, tk.END)
        configuracoes[tipo]['entries']['canal_combo'].delete(0, tk.END)
    else:
        configuracoes[tipo]['busca'].delete(0, tk.END)

    listar(tipo)

def adicionar(tipo):
    if not logado(tipo):
        return
       
    if tipo == 'dedução':
        espessura_valor = g.deducao_espessura_combobox.get()
        canal_valor = g.deducao_canal_combobox.get()
        material_nome = g.deducao_material_combobox.get()
        espessura_obj = session.query(Espessura).filter_by(valor=espessura_valor).first()
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()
        material_obj = session.query(Material).filter_by(nome=material_nome).first()
        nova_observacao_valor = g.deducao_obs_entry.get()
        nova_forca_valor = g.deducao_forca_entry.get()
        
        if g.deducao_valor_entry.get() == "" or material_nome == "" or espessura_valor == "" or canal_valor == "":
            messagebox.showerror("Erro", "Material, espessura, canal e valor da dedução são obrigatórios.")
            return
        else:
            nova_deducao_valor = float(g.deducao_valor_entry.get().replace(',', '.'))

        # Verificar se a dedução já existe
        deducao_existente = session.query(Deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id
        ).first()
        
        if not deducao_existente:
            if nova_forca_valor == '':
                nova_forca_valor = None

            nova_deducao = Deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=nova_deducao_valor,
                observacao=nova_observacao_valor,
                forca=nova_forca_valor
            )
            session.add(nova_deducao)
            session.commit()
            registrar_log(g.usuario_id, 'adicionar', 'dedução',nova_deducao.id,f'espessura: {espessura_valor}, canal: {canal_valor}, material: {material_nome}, valor: {nova_deducao_valor}, forca: {nova_forca_valor}, obs: {nova_observacao_valor}')

            g.deducao_espessura_combobox.set('')
            g.deducao_canal_combobox.set('')
            g.deducao_material_combobox.set('')
            g.deducao_valor_entry.delete(0, tk.END)
            g.deducao_obs_entry.delete(0, tk.END)
            g.deducao_forca_entry.delete(0, tk.END)

            messagebox.showinfo("Sucesso", "Nova dedução adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Dedução já existe no banco de dados.")

    if tipo == 'espessura':
   
        espessura_valor = g.espessura_valor_entry.get().replace(',', '.')
        espessura_existente = session.query(Espessura).filter_by(valor=espessura_valor).first()
        
        if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
           messagebox.showwarning("Atenção!", "A espessura deve conter apenas números ou números decimais.")
           g.espessura_valor_entry.delete(0, tk.END)
           return

        if not espessura_existente:
            nova_espessura = Espessura(valor=espessura_valor)
            session.add(nova_espessura)
            session.commit()
            registrar_log(g.usuario_id, 'adicionar', 'espessura', nova_espessura.id, f'valor: {espessura_valor}')
            messagebox.showinfo("Sucesso", "Nova espessura adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Espessura já existe no banco de dados.")

    if tipo == 'material':
  
        nome_material = g.material_nome_entry.get()
        densidade_material = g.material_densidade_entry.get()
        escoamento_material = g.material_escoamento_entry.get()
        elasticidade_material = g.material_elasticidade_entry.get()
        
        if not nome_material:
            messagebox.showerror("Erro", "O campo Material é obrigatório.")
            return
        
        material_existente = session.query(Material).filter_by(nome=nome_material).first()
        if not material_existente:
            novo_material = Material(
                nome=nome_material, 
                densidade=float(densidade_material) if densidade_material else None, 
                escoamento=float(escoamento_material) if escoamento_material else None, 
                elasticidade=float(elasticidade_material) if elasticidade_material else None
            )
            session.add(novo_material)
            session.commit()
            registrar_log(g.usuario_id, 'adicionar', 'material', novo_material.id, f'nome: {nome_material}, densidade: {(densidade_material) if densidade_material else "N/A"}, escoamento: {escoamento_material}, elasticidade: {elasticidade_material}')

            g.material_nome_entry.delete(0, tk.END)
            g.material_densidade_entry.delete(0, tk.END)
            g.material_escoamento_entry.delete(0, tk.END)
            g.material_elasticidade_entry.delete(0, tk.END)

    if tipo == 'canal':
        valor_canal = g.canal_valor_entry.get()
        largura_canal = g.canal_largura_entry.get()
        altura_canal = g.canal_altura_entry.get()
        comprimento_total_canal = g.canal_comprimento_entry.get()
        observacao_canal = g.canal_observacao_entry.get()

        if valor_canal.isalpha():
            messagebox.showwarning("Atenção!", "O canal deve conter números ou números e letras.")
            return

        if not valor_canal:
            messagebox.showerror("Erro", "O campo Canal é obrigatório.")
            return
        
        canal_existente = session.query(Canal).filter_by(valor=valor_canal).first()
        if not canal_existente:
            novo_canal = Canal(
                valor=valor_canal,
                largura=float(largura_canal) if largura_canal else None,
                altura=float(altura_canal) if altura_canal else None,
                comprimento_total=float(comprimento_total_canal) if comprimento_total_canal else None,
                observacao=observacao_canal if observacao_canal else None
            )
            session.add(novo_canal)
            session.commit()
            registrar_log(g.usuario_id, 'adicionar', 'canal', novo_canal.id, f'valor: {valor_canal}, largura: {largura_canal}, altura: {altura_canal}, comprimento_total: {comprimento_total_canal}, observacao: {observacao_canal}')

            g.canal_valor_entry.delete(0, tk.END)
            g.canal_largura_entry.delete(0, tk.END)
            g.canal_altura_entry.delete(0, tk.END)
            g.canal_comprimento_entry.delete(0, tk.END)
            g.canal_observacao_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Novo canal adicionado com sucesso!")
        else:
            messagebox.showerror("Erro", "Canal já existe no banco de dados.")

    atualizar_material()
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    listar(tipo)

def editar(tipo):
    if not admin(tipo):
        return

    if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja editar o(a) {tipo}?"):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()
    
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
                alteracoes.append(f"{campo}: '{valor_antigo}' -> '{valor_novo}'")
                setattr(obj, campo, valor_novo)

        try:
            session.commit()
            detalhes = "; ".join(alteracoes)  # Concatena as alterações em uma string
            registrar_log(g.usuario_id, "editar", tipo, obj_id, detalhes)  # Registrar a edição com detalhes
            messagebox.showinfo("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erro", f"Erro ao salvar no banco de dados: {e}")
    else:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a).")

    # Limpar os campos após a edição
    for entry in config['campos'].values():
        entry.delete(0, tk.END)

    # Atualizar as listas e comboboxes
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    for tipo in configuracoes:
        listar(tipo)
        buscar(tipo)

def excluir(tipo):
    if not admin(tipo):
        return

    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]
    
    if config['lista'] is None:
        return

    aviso = messagebox.askyesno("Atenção!", f"Ao excluir um(a) {tipo} todas as deduções relacionadas serão excluídas também, deseja continuar?")
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
    session.commit()
    registrar_log(g.usuario_id, "excluir", tipo, obj_id, f"Excluído(a) {tipo} com ID {obj_id}")  # Registrar a exclusão
    config['lista'].delete(selected_item)
    messagebox.showinfo("Sucesso", f"{tipo.capitalize()} excluído(a) com sucesso!")

    atualizar_material()
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    for tipo in configuracoes:
        listar(tipo)
        buscar(tipo)

def preencher_campos(tipo):
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    if not config['lista'].selection():
        messagebox.showerror("Erro", f"Nenhum {tipo} selecionado.")
        return

    selected_item = config['lista'].selection()[0]
    item = config['lista'].item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(config['modelo']).filter_by(id=obj_id).first()

    if obj:
        for campo, entry in config['campos'].items():
            entry.delete(0, tk.END)
            entry.insert(0, getattr(obj, campo)) if getattr(obj, campo) is not None else entry.insert(0, '')
    else:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a.")

def atualizar_combobox_deducao():
    if g.deducao_material_combobox and g.deducao_material_combobox.winfo_exists():
        g.deducao_material_combobox['values'] = [m.nome for m in session.query(Material).order_by(Material.nome).all()]
    if g.deducao_espessura_combobox and g.deducao_espessura_combobox.winfo_exists():
        g.deducao_espessura_combobox['values'] = sorted([e.valor for e in session.query(Espessura).all()])
    if g.deducao_canal_combobox and g.deducao_canal_combobox.winfo_exists():
        g.deducao_canal_combobox['values'] = sorted([c.valor for c in session.query(Canal).all()], key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0]))

# Manipulação de usuarios
def novo_usuario():
    novo_usuario_nome = g.usuario_entry.get()
    novo_usuario_senha = g.senha_entry.get()
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.", parent=g.aut_form)
        return
    
    usuario_obj = session.query(Usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.", parent=g.aut_form)
        return
    else:
        novo_usuario = Usuario(nome=novo_usuario_nome, senha=senha_hash, admin=g.admin_var.get())
        session.add(novo_usuario)
        session.commit()
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.", parent=g.aut_form)
        g.aut_form.destroy()
    
    habilitar_janelas()

def login():
    usuario_nome = g.usuario_entry.get()
    usuario_senha = g.senha_entry.get()
    
    usuario_obj = session.query(Usuario).filter_by(nome=usuario_nome).first()

    if usuario_obj:
        if usuario_obj.senha == "nova_senha":
            nova_senha = simpledialog.askstring("Nova Senha", "Digite uma nova senha:", show="*", parent=g.aut_form)
            if nova_senha:
                usuario_obj.senha = hashlib.sha256(nova_senha.encode()).hexdigest()
                session.commit()
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso. Faça login novamente.", parent=g.aut_form)
                return
        elif usuario_obj.senha == hashlib.sha256(usuario_senha.encode()).hexdigest():
            messagebox.showinfo("Login", "Login efetuado com sucesso.", parent=g.aut_form)
            g.usuario_id = usuario_obj.id
            g.aut_form.destroy()
            g.principal_form.title(f"Cálculo de Dobra - {usuario_obj.nome}")
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.aut_form)
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.", parent=g.aut_form)

    habilitar_janelas()

def logado(tipo):
    configuracoes = {
        'dedução': g.deducao_form,
        'espessura': g.espessura_form,
        'material': g.material_form,
        'canal': g.canal_form
    }

    if g.usuario_id is None:
        messagebox.showerror("Erro", "Login requerido.", parent=configuracoes[tipo])
        return False
    return True

def admin(tipo):
    configuracoes = {
        'dedução': g.deducao_form,
        'espessura': g.espessura_form,
        'material': g.material_form,
        'canal': g.canal_form,
        'usuario': g.usuario_form
    }

    if g.usuario_id is None:
        messagebox.showerror("Erro", "Admin requerido.", parent=configuracoes[tipo])
        return False
    usuario_obj = session.query(Usuario).filter_by(id=g.usuario_id).first()
    if not usuario_obj.admin:
        messagebox.showerror("Erro", "Admin requerido.", parent=configuracoes[tipo])
        return False
    return True

def logout():
    if g.usuario_id is None:
        messagebox.showerror("Erro", "Nenhum usuário logado.")
        return
    g.usuario_id = None
    g.principal_form.title("Cálculo de Dobra")
    messagebox.showinfo("Logout", "Logout efetuado com sucesso.")

def resetar_senha():
    selected_item = g.lista_usuario.selection()
    if not selected_item:
        tk.messagebox.showwarning("Aviso", "Selecione um usuário para resetar a senha.")
        return

    user_id = g.lista_usuario.item(selected_item, "values")[0]
    novo_password = "nova_senha"  # Defina a nova senha padrão aqui
    usuario_obj = session.query(Usuario).filter_by(id=user_id).first()
    if usuario_obj:
        usuario_obj.senha = novo_password
        session.commit()
        tk.messagebox.showinfo("Sucesso", "Senha resetada com sucesso.")
    else:
        tk.messagebox.showerror("Erro", "Usuário não encontrado.")

def excluir_usuario():
    if not admin('usuario'):
        return

    if g.lista_usuario is None:
        return

    selected_item = g.lista_usuario.selection()[0]
    item = g.lista_usuario.item(selected_item)
    obj_id = item['values'][0]
    obj = session.query(Usuario).filter_by(id=obj_id).first()
    if obj is None:
        messagebox.showerror("Erro", "Usuário não encontrado.")
        return

    if obj.admin:
        messagebox.showerror("Erro", "Não é possível excluir o administrador.")
        return
    
    aviso = messagebox.askyesno("Atenção!", "Tem certeza que deseja excluir o usuário?")
    if not aviso:
        return

    session.delete(obj)
    session.commit()
    g.lista_usuario.delete(selected_item)
    messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")

    listar('usuario')

# Manipulação de formulários
def no_topo(form):
    def set_topmost(window, on_top):
        if window and window.winfo_exists():
            window.attributes("-topmost",on_top)

    on_top_valor = g.on_top_var.get() == 1
    set_topmost(form, on_top_valor)

def posicionar_janela(form, posicao=None):
    form.update_idletasks()
    g.principal_form.update_idletasks()
    largura_monitor = g.principal_form.winfo_screenwidth()
    posicao_x = g.principal_form.winfo_x()
    largura_janela = g.principal_form.winfo_width()
    largura_form = form.winfo_width()

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = g.principal_form.winfo_x() + ((g.principal_form.winfo_width() - largura_form) // 2)
        y = g.principal_form.winfo_y() + ((g.principal_form.winfo_height() - form.winfo_height()) // 2)
    elif posicao == 'direita':
        x = g.principal_form.winfo_x() + largura_janela + 10
        y = g.principal_form.winfo_y()
        if x + largura_form > largura_monitor:
            x = g.principal_form.winfo_x() - largura_form - 10
    elif posicao == 'esquerda':
        x = g.principal_form.winfo_x() - largura_form - 10
        y = g.principal_form.winfo_y()
        if x < 0:
            x = g.principal_form.winfo_x() + largura_janela + 10
    else:
        return

    form.geometry(f"+{x}+{y}")

def desabilitar_janelas():
    forms = [g.principal_form, g.deducao_form, g.espessura_form, g.material_form, g.canal_form]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', True)
            form.focus_force()

def habilitar_janelas():
    forms = [g.principal_form, g.deducao_form, g.espessura_form, g.material_form, g.canal_form]
    for form in forms:
        if form is not None and form.winfo_exists():
            form.attributes('-disabled', False)
            form.focus_force()

def registrar_log(usuario_id, acao, tabela, registro_id, detalhes=None):
    log = Log(
        usuario_id=usuario_id,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        detalhes=detalhes
    )
    session.add(log)
    session.commit()