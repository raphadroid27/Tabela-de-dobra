import tkinter as tk
from tkinter import messagebox, simpledialog
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao, usuario
import globals as g
import re
import hashlib

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
    g.material_combobox['values'] = [m.nome for m in session.query(material).all()]

def atualizar_espessura():
    material_nome = g.material_combobox.get()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    if material_obj:
        espessuras_valores = [str(e.valor) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).order_by(espessura.valor).all()]
        g.espessura_combobox['values'] = espessuras_valores

def atualizar_canal():
    espessura_valor = g.espessura_combobox.get()
    material_nome = g.material_combobox.get()
    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    if espessura_obj:
        canais_valores = sorted(
            [str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).filter(deducao.material_id==material_obj.id).all()])
        
        g.canal_combobox['values'] = canais_valores

def atualizar_deducao_e_obs():
    espessura_valor = g.espessura_combobox.get()
    material_nome = g.material_combobox.get()
    canal_valor = g.canal_combobox.get()

    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    canal_obj = session.query(canal).filter_by(valor=canal_valor).first()

    if espessura_obj and material_obj and canal_obj:
        deducao_obj = session.query(deducao).filter(
            deducao.espessura_id == espessura_obj.id,
            deducao.material_id == material_obj.id,
            deducao.canal_id == canal_obj.id
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
    deducao_obj = session.query(deducao).filter_by(valor=g.deducao_valor).first()

    if g.material_combobox.get() != "" and g.espessura_combobox.get() != "" and g.canal_combobox.get() != "":
        if deducao_obj and deducao_obj.forca is not None:
            toneladas_m = (deducao_obj.forca * float(comprimento)) / 1000 if comprimento else deducao_obj.forca
            g.ton_m_label.config(text=f'{toneladas_m:.0f}', fg="black")
        else:
            g.ton_m_label.config(text='N/A', fg="red")        

def calcular_fatork():
    if g.deducao_espec:
        g.deducao_valor = g.deducao_espec

    if not g.raio_interno or not g.espessura_valor or not g.deducao_valor or g.deducao_valor == 'N/A':
        return

    g.fator_k = (4 * (g.espessura_valor - (g.deducao_valor / 2) + g.raio_interno) - (pi * g.raio_interno)) / (pi * g.espessura_valor)    
    g.fator_k_label.config(text=f"{g.fator_k:.2f}", fg="red" if g.deducao_valor == g.deducao_espec else "black")

def calcular_offset():
    if not g.fator_k or not g.espessura_valor:
        print('Fator K não informado')
        return

    offset = g.fator_k * g.espessura_valor
    g.offset_label.config(text=f"{offset:.2f}", fg="red" if g.deducao_valor == g.deducao_espec else "black")

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

def calcular_dobra():

    dobra1 = g.aba1_entry.get().replace(',', '.')
    dobra2 = g.aba2_entry.get().replace(',', '.')
    dobra3 = g.aba3_entry.get().replace(',', '.')
    dobra4 = g.aba4_entry.get().replace(',', '.')
    dobra5 = g.aba5_entry.get().replace(',', '.')

    if g.deducao_label['text'] == "" or g.deducao_label['text'] == 'N/A':
        if g.deducao_espec_entry.get() == "":
            return
        else:
            deducao_valor = g.deducao_espec
    else:
        deducao_valor = g.deducao_valor
        if g.deducao_espec_entry.get() != "":
            deducao_valor = g.deducao_espec

    def calcular_medida(deducao_valor):
        if dobra1 == "":
            g.medidadobra1_label.config(text="")
        else:
            medidadobra1 = float(dobra1) - (deducao_valor / 2)
            g.medidadobra1_label.config(text=f'{medidadobra1:.2f}', fg="black")

        if dobra2 == "":
            g.medidadobra2_label.config(text="")
        else:
            if dobra3 == "":
                medidadobra2 = float(dobra2) - (deducao_valor / 2)
            else:
                medidadobra2 = float(dobra2) - deducao_valor
            g.medidadobra2_label.config(text=f'{medidadobra2:.2f}', fg="black")

        if dobra3 == "":
            g.medidadobra3_label.config(text="")
        else:
            if dobra4 == "":
                medidadobra3 = float(dobra3) - (deducao_valor / 2)
            else:
                medidadobra3 = float(dobra3) - deducao_valor
            g.medidadobra3_label.config(text=f'{medidadobra3:.2f}', fg="black")

        if dobra4 == "":
            g.medidadobra4_label.config(text="")
        else:
            if dobra5 == "":
                medidadobra4 = float(dobra4) - (deducao_valor / 2)
            else:
                medidadobra4 = float(dobra4) - deducao_valor
            g.medidadobra4_label.config(text=f'{medidadobra4:.2f}', fg="black")

        if dobra5 == "":
            g.medidadobra5_label.config(text="")
        else:
            medidadobra5 = float(dobra5) - (deducao_valor / 2)
            g.medidadobra5_label.config(text=f'{medidadobra5:.2f}', fg="black")

    calcular_medida(deducao_valor)

def calcular_blank():
    medidas = [g.medidadobra1_label, g.medidadobra2_label, g.medidadobra3_label, g.medidadobra4_label, g.medidadobra5_label]
    medidas_validas = [float(medida['text']) for medida in medidas if medida['text']]

    if medidas_validas:
        blank = sum(medidas_validas)
        metade_blank = blank / 2
        g.medida_blank_label.config(text=f"{blank:.2f}", fg="black")
        g.metade_blank_label.config(text=f"{metade_blank:.2f}", fg="black")

def calcular_metade_dobra():
    entradas = [
        (g.medidadobra1_label, g.metadedobra1_label),
        (g.medidadobra2_label, g.metadedobra2_label),
        (g.medidadobra3_label, g.metadedobra3_label),
        (g.medidadobra4_label, g.metadedobra4_label),
        (g.medidadobra5_label, g.metadedobra5_label)
    ]

    for medidadobra_entry, metadedobra_entry in entradas:
        try:
            medidadobra = float(medidadobra_entry['text'])
            metadedobra = medidadobra / 2
            metadedobra_entry.config(text=f'{metadedobra:.2f}', fg="black")
        except ValueError:
            metadedobra_entry.config(text="")

def razao_raio_esp():
    if g.raio_interno is not None and g.espessura_valor is not None:
        try:
            razao_raio_esp_valor = g.raio_interno / g.espessura_valor
            g.razao_raio_esp_label.config(text=f'{razao_raio_esp_valor:.2f}')
        except ValueError:
            return

def copiar(tipo, numero=None):
    configuracoes = {
        'deducao': {
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
            'label': lambda numero: getattr(g, f'medidadobra{numero}_label'),
            'funcao_calculo': calcular_dobra
        },
        'metade_dobra': {
            'label': lambda numero: getattr(g, f'metadedobra{numero}_label'),
            'funcao_calculo': lambda: (calcular_dobra(), calcular_metade_dobra())
        },
        'blank': {
            'label': g.medida_blank_label,
            'funcao_calculo': lambda: (calcular_dobra(), calcular_metade_dobra(), calcular_blank())
        },
        'metade_blank': {
            'label': g.metade_blank_label,
            'funcao_calculo': lambda: (calcular_dobra(), calcular_metade_dobra(), calcular_blank())
        }
    }

    config = configuracoes[tipo]

    label = config['label'](numero) if callable(config['label']) else config['label']
    funcao_calculo = config['funcao_calculo']

    if label['text']:
        funcao_calculo()
        pyperclip.copy(label['text'])
        print(f'Valor copiado {label["text"]}')
        label.config(text=f'{label["text"]} Copiado!', fg="green")

def limpar_dobras():
    dobras = [g.aba1_entry, g.aba2_entry, g.aba3_entry, g.aba4_entry, g.aba5_entry]
    medidas = [g.medidadobra1_label, g.medidadobra2_label, g.medidadobra3_label, g.medidadobra4_label, g.medidadobra5_label]
    metades = [g.metadedobra1_label, g.metadedobra2_label, g.metadedobra3_label, g.metadedobra4_label, g.metadedobra5_label]

    for dobra in dobras:
        dobra.delete(0, tk.END)

    for medida in medidas:
        medida.config(text="")

    for metade in metades:
        metade.config(text="")

    g.deducao_espec_entry.delete(0, tk.END)
    g.medida_blank_label.config(text="")
    g.metade_blank_label.config(text="")

def limpar_tudo():
    limpar_dobras()
    g.material_combobox.set('')
    g.espessura_combobox.set('')
    g.canal_combobox.set('')
    g.raio_interno_entry.delete(0, tk.END)
    g.fator_k_label.config(text="")
    g.deducao_label.config(text="")
    g.offset_label.config(text="")
    g.obs_label.config(text="Observações:")
    g.ton_m_label.config(text="")
    g.comprimento_entry.delete(0, tk.END)
    g.aba_min_externa_label.config(text="")
    g.z_min_externa_label.config(text="")

def todas_funcoes():
    carregar_variaveis_globais()
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_toneladas_m()
    calcular_fatork()
    calcular_offset()
    aba_minima_externa()
    z_minimo_externo()
    calcular_dobra()
    calcular_blank()
    calcular_metade_dobra()
    razao_raio_esp()

# Manipulação de dados
def obter_configuracoes():
    return {
        'dedução': {
            'lista': g.lista_deducao,
            'modelo': deducao,
            'campos': {
                'valor': g.deducao_valor_entry,
                'observacao': g.deducao_obs_entry,
                'forca': g.deducao_forca_entry
            },
            'item_id': deducao.id,
            'valores': g.valores_deducao,
            'ordem': deducao.valor,
            'entries': {
                'material_combo': g.deducao_material_combobox,
                'espessura_combo': g.deducao_espessura_combobox,
                'canal_combo': g.deducao_canal_combobox
            }
        },
        'material': {
            'lista': g.lista_material,
            'modelo': material,
            'campos': {
                'nome': g.material_nome_entry,
                'densidade': g.material_densidade_entry,
                'escoamento': g.material_escoamento_entry,
                'elasticidade': g.material_elasticidade_entry
            },
            'item_id': deducao.material_id,
            'valores': g.valores_material,
            'ordem': material.nome,
            'entry': g.material_nome_entry,
            'busca': g.material_busca_entry,
            'campo_busca': material.nome
        },
        'espessura': {
            'lista': g.lista_espessura,
            'modelo': espessura,
            'valores': g.valores_espessura,
            'ordem': espessura.valor,
            'entry': g.espessura_valor_entry,
            'busca': g.espessura_busca_entry,
            'campo_busca': espessura.valor
        },
        'canal': {
            'lista': g.lista_canal,
            'modelo': canal,
            'campos': {
                'valor': g.canal_valor_entry,
                'largura': g.canal_largura_entry,
                'altura': g.canal_altura_entry,
                'comprimento_total': g.canal_comprimento_entry,
                'observacao': g.canal_observacao_entry
            },
            'item_id': deducao.canal_id,
            'valores': g.valores_canal,
            'ordem': canal.valor,
            'entry': g.canal_valor_entry,
            'busca': g.canal_busca_entry,
            'campo_busca': canal.valor
        },
        'usuario': {
            'lista': g.lista_usuario,
            'modelo': usuario,
            'valores': g.valores_usuario,
            'ordem': usuario.nome,
            'entry': g.usuario_valor_entry,
            'campo_busca': usuario.nome
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

    def filtrar_deducoes(material_nome, espessura_valor, canal_valor):
        query = session.query(deducao).join(material).join(espessura).join(canal)
        
        if material_nome:
            query = query.filter(material.nome == material_nome)
        if espessura_valor:
            query = query.filter(espessura.valor == espessura_valor)
        if canal_valor:
            query = query.filter(canal.valor == canal_valor)
        
        return query.all()

    if tipo == 'dedução':
        material_nome = config['entries']['material_combo'].get()
        espessura_valor = config['entries']['espessura_combo'].get()
        canal_valor = config['entries']['canal_combo'].get()
        itens = filtrar_deducoes(material_nome, espessura_valor, canal_valor)
    else:
        item = config['busca'].get().replace(',', '.')
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
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        canal_obj = session.query(canal).filter_by(valor=canal_valor).first()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        nova_observacao_valor = g.deducao_obs_entry.get()
        nova_forca_valor = g.deducao_forca_entry.get()
        
        if g.deducao_valor_entry.get() == "" or material_nome == "" or espessura_valor == "" or canal_valor == "":
            messagebox.showerror("Erro", "Material, espessura, canal e valor da dedução são obrigatórios.")
            return
        else:
            nova_deducao_valor = float(g.deducao_valor_entry.get().replace(',', '.'))

        # Verificar se a dedução já existe
        deducao_existente = session.query(deducao).filter_by(
            espessura_id=espessura_obj.id,
            canal_id=canal_obj.id,
            material_id=material_obj.id
        ).first()
        
        if not deducao_existente:
            if nova_forca_valor == '':
                nova_forca_valor = None

            nova_deducao = deducao(
                espessura_id=espessura_obj.id,
                canal_id=canal_obj.id,
                material_id=material_obj.id,
                valor=nova_deducao_valor,
                observacao=nova_observacao_valor,
                forca=nova_forca_valor
            )
            session.add(nova_deducao)
            session.commit()

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
        espessura_existente = session.query(espessura).filter_by(valor=espessura_valor).first()
        
        if not re.match(r'^\d+(\.\d+)?$', espessura_valor):
           messagebox.showwarning("Atenção!", "A espessura deve conter apenas números ou números decimais.")
           g.espessura_valor_entry.delete(0, tk.END)
           return

        if not espessura_existente:
            nova_espessura = espessura(valor=espessura_valor)
            session.add(nova_espessura)
            session.commit()
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
        
        material_existente = session.query(material).filter_by(nome=nome_material).first()
        if not material_existente:
            novo_material = material(
                nome=nome_material, 
                densidade=float(densidade_material) if densidade_material else None, 
                escoamento=float(escoamento_material) if escoamento_material else None, 
                elasticidade=float(elasticidade_material) if elasticidade_material else None
            )
            session.add(novo_material)
            session.commit()

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
        
        canal_existente = session.query(canal).filter_by(valor=valor_canal).first()
        if not canal_existente:
            novo_canal = canal(
                valor=valor_canal,
                largura=float(largura_canal) if largura_canal else None,
                altura=float(altura_canal) if altura_canal else None,
                comprimento_total=float(comprimento_total_canal) if comprimento_total_canal else None,
                observacao=observacao_canal if observacao_canal else None
            )
            session.add(novo_canal)
            session.commit()
            g.canal_valor_entry.delete(0, tk.END)
            g.canal_largura_entry.delete(0, tk.END)
            g.canal_altura_entry.delete(0, tk.END)
            g.canal_comprimento_entry.delete(0, tk.END)
            g.canal_observacao_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Novo canal adicionado com sucesso!")
        else:
            messagebox.showerror("Erro", "Canal já existe no banco de dados.")

    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    listar(tipo)

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

def atualizar(tipo):
    if not admin(tipo):
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
        for campo, entry in config['campos'].items():
            valor = entry.get() if entry.get() else getattr(obj, campo)
            if valor is not None:
                valor = valor.replace(',', '.') if isinstance(valor, str) else valor
                setattr(obj, campo, float(valor) if isinstance(valor, str) and valor.replace('.', '', 1).isdigit() else valor)
        session.commit()

        messagebox.showinfo("Sucesso", f"{tipo.capitalize()} editado(a) com sucesso!")

        for entry in config['campos'].values():
            entry.delete(0, tk.END)
    else:
        messagebox.showerror("Erro", f"{tipo.capitalize()} não encontrado(a).")

    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    listar('dedução'), listar('material'), listar('espessura'), listar('canal'), listar('usuario')

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

    deducao_objs = session.query(deducao).filter(config['item_id']==obj.id).all()
    for d in deducao_objs:
        session.delete(d)

    session.delete(obj)
    session.commit()
    config['lista'].delete(selected_item)
    messagebox.showinfo("Sucesso", f"{tipo.capitalize()} excluído(a) com sucesso!")

    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_combobox_deducao()
    listar('dedução'), listar('material'), listar('espessura'), listar('canal')

def atualizar_combobox_deducao():
    if g.deducao_material_combobox:
        g.deducao_material_combobox['values'] = [m.nome for m in session.query(material).all()] 
    if g.deducao_espessura_combobox:
        g.deducao_espessura_combobox['values'] = sorted([e.valor for e in session.query(espessura).all()])
    if g.deducao_canal_combobox:
        g.deducao_canal_combobox['values'] = sorted([c.valor for c in session.query(canal).all()],key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0]))

# Manipulação de usuarios
def novo_usuario():
    novo_usuario_nome = g.usuario_entry.get()
    novo_usuario_senha = g.senha_entry.get()
    senha_hash = hashlib.sha256(novo_usuario_senha.encode()).hexdigest()
    if novo_usuario_nome == "" or novo_usuario_senha == "":
        messagebox.showerror("Erro", "Preencha todos os campos.", parent=g.aut_form)
        return
    
    usuario_obj = session.query(usuario).filter_by(nome=novo_usuario_nome).first()
    if usuario_obj:
        messagebox.showerror("Erro", "Usuário já existente.", parent=g.aut_form)
        return
    else:
        novo_usuario = usuario(nome=novo_usuario_nome, senha=senha_hash, admin=g.admin_var.get())
        session.add(novo_usuario)
        session.commit()
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso.", parent=g.aut_form)
        g.aut_form.destroy()
    
    habilitar_janelas()

def login():
    usuario_nome = g.usuario_entry.get()
    usuario_senha = g.senha_entry.get()
    
    usuario_obj = session.query(usuario).filter_by(nome=usuario_nome).first()

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
    usuario_obj = session.query(usuario).filter_by(id=g.usuario_id).first()
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
    usuario_obj = session.query(usuario).filter_by(id=user_id).first()
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
    obj = session.query(usuario).filter_by(id=obj_id).first()
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

    if posicao is None:
        if posicao_x > largura_monitor / 2:
            posicao = 'esquerda'
        else:
            posicao = 'direita'

    if posicao == 'centro':
        x = g.principal_form.winfo_x() + ((g.principal_form.winfo_width() - form.winfo_width()) // 2)
        y = g.principal_form.winfo_y() + ((g.principal_form.winfo_height() - form.winfo_height()) // 2)
    elif posicao == 'direita':
        x = g.principal_form.winfo_x() + g.principal_form.winfo_width() + 10
        y = g.principal_form.winfo_y()
    elif posicao == 'esquerda':
        x = g.principal_form.winfo_x() - form.winfo_width() - 10
        y = g.principal_form.winfo_y()
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