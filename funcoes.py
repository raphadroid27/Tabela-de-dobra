import tkinter as tk
from tkinter import messagebox
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao
import globals as g
import re

engine = create_engine('sqlite:///tabela_de_dobra.db')
Session = sessionmaker(bind=engine)
session = Session()

# App principal (app.py)
def carregar_variaveis_globais():
    g.espessura_valor = float(re.findall(r'\d+\.?\d*', g.espessura_combobox.get())[0]) if g.espessura_combobox.get() else None
    g.canal_valor = float(re.findall(r'\d+\.?\d*', g.canal_combobox.get())[0]) if g.canal_combobox.get() else None
    g.raio_interno = float(re.findall(r'\d+\.?\d*', g.raio_interno_entry.get().replace(',', '.'))[0]) if g.raio_interno_entry.get() else None
    g.deducao_espec = float(g.deducao_espec_entry.get().replace(',', '.')) if g.deducao_espec_entry.get() else None
    
    print(f'{g.canal_valor} {g.espessura_valor} {g.deducao_valor}')

def atualizar_material():
    g.material_combobox['values'] = [m.nome for m in session.query(material).all()]

def atualizar_espessura():
    material_nome = g.material_combobox.get()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    if material_obj:
        espessuras_valores = sorted(
            [str(e.valor) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).all()],
            key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0])
        )
        g.espessura_combobox['values'] = espessuras_valores

def atualizar_canal():
    espessura_valor = g.espessura_combobox.get()
    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    if espessura_obj:
        canais_valores = sorted(
            [str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).all()],
            key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0])
        )
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

def copiar_valor(label, funcao_calculo):
    if label['text']:
        funcao_calculo()
        pyperclip.copy(label['text'])
        print(f'Valor copiado {label["text"]}')
        label.config(text=f'{label["text"]} Copiado!', fg="green")

def copiar_deducao():
    copiar_valor(g.deducao_label, lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset()))

def copiar_fatork():
    copiar_valor(g.fator_k_label, lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset()))

def copiar_offset():
    copiar_valor(g.offset_label, lambda: (atualizar_deducao_e_obs(), calcular_fatork(), calcular_offset()))

def copiar_medidadobra(numero):
    medida_dobra_label = getattr(g, f'medidadobra{numero}_label')
    copiar_valor(medida_dobra_label, calcular_dobra)

def copiar_metadedobra(numero):
    metade_dobra_label = getattr(g, f'metadedobra{numero}_label')
    copiar_valor(metade_dobra_label, lambda: (calcular_dobra(), calcular_metade_dobra()))

def copiar_blank():
    copiar_valor(g.medida_blank_label, lambda: (calcular_dobra(), calcular_metade_dobra(), calcular_blank()))

def copiar_metade_blank():
    copiar_valor(g.metade_blank_label, lambda: (calcular_dobra(), calcular_metade_dobra(), calcular_blank()))

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

# Manipulação de dados de Dedução (deducao_form.py)
def carregar_deducoes():
        
    for item in g.lista_deducao.get_children():
        g.lista_deducao.delete(item)
        
    deducoes = session.query(deducao).all()
    for d in deducoes:
        g.lista_deducao.insert("", "end", values=(d.material.nome,d.espessura.valor, d.canal.valor, d.valor, d.observacao,d.forca))

def filtrar_deducoes(material_nome, espessura_valor, canal_valor):
    query = session.query(deducao).join(material).join(espessura).join(canal)
    
    if material_nome:
        query = query.filter(material.nome == material_nome)
    if espessura_valor:
        query = query.filter(espessura.valor == espessura_valor)
    if canal_valor:
        query = query.filter(canal.valor == canal_valor)
    
    return query.all()

def buscar_deducoes():
    material_nome = g.deducao_material_combobox.get()
    espessura_valor = g.deducao_espessura_combobox.get()
    canal_valor = g.deducao_canal_combobox.get()
    
    deducoes = filtrar_deducoes(material_nome, espessura_valor, canal_valor)
    
    for item in g.lista_deducao.get_children():
        g.lista_deducao.delete(item)
    
    for d in deducoes:
        g.lista_deducao.insert("", "end", values=(d.material.nome, d.espessura.valor, d.canal.valor, d.valor, d.observacao, d.forca))

def limpar_busca_deducao():
    g.deducao_material_combobox.set('')
    g.deducao_espessura_combobox.set('')
    g.deducao_canal_combobox.set('')
    carregar_deducoes()

def nova_deducao():
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

        atualizar_espessura()
        atualizar_canal()
        atualizar_deducao_e_obs()
        carregar_deducoes()

def editar_deducao():
    item_selecionado = g.lista_deducao.selection()[0]
    item = g.lista_deducao.item(item_selecionado)
    deducao_valor = item['values'][3]
    deducao_obj = session.query(deducao).filter_by(valor=deducao_valor).first()    

    deducao_obj.valor = float(g.deducao_valor_entry.get().replace(',', '.')) if g.deducao_valor_entry.get() else deducao_obj.valor
    deducao_obj.observacao = g.deducao_obs_entry.get() if g.deducao_obs_entry.get() else deducao_obj.observacao
    deducao_obj.forca = float(g.deducao_forca_entry.get().replace(',', '.')) if g.deducao_forca_entry.get() else deducao_obj.forca
    session.commit()

    messagebox.showinfo("Sucesso", "Dedução editada com sucesso!")
    g.lista_deducao.item(item_selecionado, values=(deducao_obj.material.nome, deducao_obj.espessura.valor, deducao_obj.canal.valor, deducao_obj.valor, deducao_obj.observacao,deducao_obj.forca))
    g.deducao_valor_entry.delete(0, tk.END)
    g.deducao_obs_entry.delete(0, tk.END)
    g.deducao_forca_entry.delete(0, tk.END)

def excluir_deducao():
        selected_item = g.lista_deducao.selection()[0]
        item = g.lista_deducao.item(selected_item)
        deducao_valor = item['values'][3]
        deducao_obj = session.query(deducao).filter_by(valor=deducao_valor).first()
        session.delete(deducao_obj)
        session.commit()
        g.lista_deducao.delete(selected_item)
        messagebox.showinfo("Sucesso", "Dedução excluída com sucesso!")

# Manipulação de dados de materiais (material_form.py)
def carregar_lista_materiais():
        atualizar_material()
        for item in g.lista_material.get_children():
            g.lista_material.delete(item)

        materiais = session.query(material).all()
        for m in materiais:
            g.lista_material.insert("", "end", values=(m.nome, m.densidade, m.escoamento, m.elasticidade))

def novo_material():
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

            messagebox.showinfo("Sucesso", "Novo material adicionado com sucesso!")
        else:
            messagebox.showerror("Erro", "Material já existe no banco de dados.")
 
        
        carregar_lista_materiais()        

def editar_material():
        selected_item = g.lista_material.selection()[0]
        item = g.lista_material.item(selected_item)
        material_nome = item['values'][0]
        material_obj = session.query(material).filter_by(nome=material_nome).first()

        material_obj.nome = g.material_nome_entry.get() if g.material_nome_entry.get() else material_obj.nome
        material_obj.densidade = float(g.material_densidade_entry.get().replace(',', '.')) if g.material_densidade_entry.get() else material_obj.densidade
        material_obj.escoamento = float(g.material_escoamento_entry.get().replace(',', '.')) if g.material_escoamento_entry.get() else material_obj.escoamento
        material_obj.elasticidade = float(g.material_elasticidade_entry.get().replace(',', '.')) if g.material_elasticidade_entry.get() else material_obj.elasticidade
        session.commit()

        g.material_nome_entry.delete(0, tk.END)
        g.material_densidade_entry.delete(0, tk.END)
        g.material_escoamento_entry.delete(0, tk.END)
        g.material_elasticidade_entry.delete(0, tk.END)

        messagebox.showinfo("Sucesso", "Material editado com sucesso!")
        carregar_lista_materiais()

def excluir_material():
        item_selecionado = g.lista_material.selection()[0]
        item = g.lista_material.item(item_selecionado)
        material_nome = item['values'][0]
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        session.delete(material_obj)
        session.commit()
        g.lista_material.delete(item_selecionado)
        messagebox.showinfo("Sucesso", "Material excluído com sucesso!")
        atualizar_material()
        carregar_lista_materiais()

# Manipulação de dados de canais (Canal_form.py)
def carregar_lista_canais():
    for item in g.lista_canal.get_children():
        g.lista_canal.delete(item)

    canais = session.query(canal).all()
    for c in canais:
        g.lista_canal.insert("","end", values=(c.valor,c.largura,c.altura,c.comprimento_total,c.observacao))

def adicionar_canal():
        valor_canal = g.canal_valor_entry.get()
        largura_canal = g.canal_largura_entry.get()
        altura_canal = g.canal_altura_entry.get()
        comprimento_total_canal = g.canal_comprimento_entry.get()
        observacao_canal = g.canal_observacao_entry.get()
        
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

        carregar_lista_canais()

def editar_canal ():
    item_selecionado = g.lista_canal.selection()[0]
    item = g.lista_canal.item(item_selecionado)
    canal_valor= item['values'][0]
    canal_obj = session.query(canal).filter_by(valor=canal_valor).first()

    canal_obj.largura = float(g.canal_largura_entry.get()) if g.canal_largura_entry.get() else canal_obj.largura
    canal_obj.altura = float(g.canal_altura_entry.get()) if g.canal_altura_entry.get() else canal_obj.altura
    canal_obj.comprimento_total = float(g.canal_comprimento_entry.get()) if g.canal_comprimento_entry.get() else canal_obj.comprimento_total
    canal_obj.observacao = g.canal_observacao_entry.get() if g.canal_observacao_entry.get() else canal_obj.observacao
    session.commit() 
    messagebox.showinfo("Sucesso", "Canal editado com suceso!")
    carregar_lista_canais()

def excluir_canal():
    item_selecionado = g.lista_canal.selection()[0]
    item = g.lista_canal.item(item_selecionado)
    canal_valor = item['values'][0]
    canal_obj = session.query(canal).filter_by(valor=canal_valor).first()
    session.delete(canal_obj)
    session.commit()
    g.lista_canal.delete(item_selecionado)
    messagebox.showinfo("Sucesso", "Canal excluído com sucesso!")

# Manipulação de dados de espessuras (espessura_form.py)
def adicionar_espessura():
        espessura_valor = g.espessura_valor_entry.get().replace(',', '.')
        espessura_existente = session.query(espessura).filter_by(valor=espessura_valor).first()
        if not espessura_existente:
            nova_espessura = espessura(valor=espessura_valor)
            session.add(nova_espessura)
            session.commit()
            g.espessura_valor_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Nova espessura adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Espessura já existe no banco de dados.")

        atualizar_espessura()

def buscar_canais():
   
    canal_valor = g.canal_valor_entry.get()
    
    canais = session.query(canal).filter(canal.valor == canal_valor)
    
    for item in g.lista_canal.get_children():
        g.lista_canal.delete(item)
    
    for c in canais:
        g.lista_canal.insert("","end", values=(c.valor,c.largura,c.altura,c.comprimento_total,c.observacao))