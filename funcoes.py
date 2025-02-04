import tkinter as tk
from tkinter import messagebox
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao
import globals as g
import re

def configuracao_do_banco_de_dados():
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    return Session()

session = configuracao_do_banco_de_dados()

def atualizar_espessura():
    material_nome = g.material_combobox.get()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    if material_obj:
        espessuras_valores = sorted([str(e.valor) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).all()], key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0]))
        g.espessura_combobox['values'] = espessuras_valores

def atualizar_canal():
    espessura_valor = g.espessura_combobox.get()
    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    if espessura_obj:
        canais_valores = sorted([str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).all()], key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0]))
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

def atualizar_toneladas_m():
    comprimento = g.comprimento_entry.get()
    deducao_valor = g.deducao_label['text']
    deducao_obj = session.query(deducao).filter_by(valor=deducao_valor).first()

    if deducao_obj and deducao_obj.forca is not None:
        toneladas_m = (deducao_obj.forca * float(comprimento)) / 1000 if comprimento else deducao_obj.forca
        g.ton_m_label.config(text=f'{toneladas_m:.0f}', fg="black")
    else:
        g.ton_m_label.config(text='N/A', fg="red")

def calcular_fatork():
    raio_interno = g.raio_interno_entry.get().replace(',', '.')
    espessura_valor = g.espessura_combobox.get()
    deducao_valor = g.deducao_label['text']

    if not raio_interno or not espessura_valor or not deducao_valor or deducao_valor == 'N/A':
        return

    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    espessura_valor = float(re.findall(r'\d+\.?\d*', espessura_obj.valor)[0])

    fator_k = (4 * (espessura_valor - (float(deducao_valor) / 2) + float(raio_interno)) - (pi * float(raio_interno))) / (pi * espessura_valor)
    g.fator_k_label.config(text=f"{fator_k:.2f}", fg="black")

def calcular_offset():
    fator_k = g.fator_k_label['text']
    espessura = g.espessura_combobox.get()

    if not fator_k or not espessura:
        print('Fator K não informado')
        return

    fator_k = float(g.fator_k_label['text'])
    espessura = float(re.findall(r'\d+\.?\d*', g.espessura_combobox.get())[0])

    offset = fator_k * espessura
    g.offset_label.config(text=f"{offset:.2f}", fg="black")

def calcular_dobra():
    deducao_valor = g.deducao_label['text']
    deducao_espec = g.deducao_espec_entry.get()
    dobra1 = g.aba1_entry.get().replace(',', '.')
    dobra2 = g.aba2_entry.get().replace(',', '.')
    dobra3 = g.aba3_entry.get().replace(',', '.')
    dobra4 = g.aba4_entry.get().replace(',', '.')
    dobra5 = g.aba5_entry.get().replace(',', '.')

    if deducao_valor == "" or deducao_valor == 'N/A':
        if deducao_espec == "":
            return
        else:
            deducao_valor = float(deducao_espec)
    else:
        deducao_valor = float(deducao_valor)
        if deducao_espec != "":
            deducao_valor = float(deducao_espec)

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
    metades = [g.metadedobra1_label, g.metadedobra2_label, g.metadedobra3_label, g.metadedobra4_label, g.metadedobra5_label]

    medidas_validas = [float(medida['text']) for medida in medidas if medida['text']]
    metades_validas = [float(metade['text']) for metade in metades if metade['text']]

    if medidas_validas:
        g.medida_blank_label.config(text=f"{sum(medidas_validas):.2f}", fg="black")
    if metades_validas:
        g.metade_blank_label.config(text=f"{sum(metades_validas):.2f}", fg="black")

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
    espessura_valor = g.espessura_combobox.get()

    if g.raio_interno_entry is None or espessura_valor is None:
        return

    try:
        raio_interno = float(g.raio_interno_entry.get().replace(',', '.'))
        espessura_valor = float(re.findall(r'\d+\.?\d*', g.espessura_combobox.get())[0])
        razao_raio_esp_valor = raio_interno / espessura_valor
        g.razao_raio_esp_label.config(text=f'{razao_raio_esp_valor:.2f}')
    except ValueError:
        return

def copiar_valor(label, funcao_calculo):
    if label['text'] == '':
        return
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

def todas_funcoes():
    atualizar_espessura()
    atualizar_canal()
    atualizar_deducao_e_obs()
    atualizar_toneladas_m()
    calcular_fatork()
    calcular_offset()
    calcular_dobra()
    calcular_blank()
    calcular_metade_dobra()
    razao_raio_esp()

def adicionar_deducao_e_observacao():
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
            messagebox.showinfo("Sucesso", "Nova dedução adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Dedução já existe no banco de dados.")

        g.deducao_espessura_combobox.set('')
        g.deducao_canal_combobox.set('')
        g.deducao_material_combobox.set('')
        g.deducao_valor_entry.delete(0, tk.END)
        g.deducao_obs_entry.delete(0, tk.END)
        g.deducao_forca_entry.delete(0, tk.END)

def adicionar_espessura():
        valor_espessura = float(g.espessura_valor_entry.get().replace(',', '.'))
        espessura_existente = session.query(espessura).filter_by(valor=valor_espessura).first()
        if not espessura_existente:
            nova_espessura = espessura(valor=valor_espessura)
            session.add(nova_espessura)
            session.commit()
            g.espessura_valor_entry.delete(0, tk.END)
            messagebox.showinfo("Sucesso", "Nova espessura adicionada com sucesso!")
        else:
            messagebox.showerror("Erro", "Espessura já existe no banco de dados.")

def carregar_deducoes():
        deducoes = session.query(deducao).all()
        for d in deducoes:
            g.tree.insert("", "end", values=(d.material.nome,d.espessura.valor, d.canal.valor, d.valor, d.observacao,d.forca))
            
def editar_deducao():
    selected_item = g.tree.selection()[0]
    item = g.tree.item(selected_item)
    deducao_valor = item['values'][3]
    deducao_obj = session.query(deducao).filter_by(valor=deducao_valor).first()    

    deducao_obj.valor = float(g.deducao_valor_entry.get().replace(',', '.')) if g.deducao_valor_entry.get() else deducao_obj.valor
    deducao_obj.observacao = g.deducao_obs_entry.get() if g.deducao_obs_entry.get() else deducao_obj.observacao
    deducao_obj.forca = float(g.deducao_forca_entry.get().replace(',', '.')) if g.deducao_forca_entry.get() else deducao_obj.forca
    session.commit()

    messagebox.showinfo("Sucesso", "Dedução editada com sucesso!")
    g.tree.item(selected_item, values=(deducao_obj.material.nome, deducao_obj.espessura.valor, deducao_obj.canal.valor, deducao_obj.valor, deducao_obj.observacao,deducao_obj.forca))
    g.deducao_valor_entry.delete(0, tk.END)
    g.deducao_obs_entry.delete(0, tk.END)
    g.deducao_forca_entry.delete(0, tk.END)

def excluir_deducao():
        selected_item = g.tree.selection()[0]
        item = g.tree.item(selected_item)
        deducao_valor = item['values'][3]
        deducao_obj = session.query(deducao).filter_by(valor=deducao_valor).first()
        session.delete(deducao_obj)
        session.commit()
        g.tree.delete(selected_item)
        messagebox.showinfo("Sucesso", "Dedução excluída com sucesso!")    