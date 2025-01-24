import tkinter as tk
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao, observacao
import globals as g

def configuracao_do_banco_de_dados():
    engine = create_engine('sqlite:///tabela_de_dobra.db')
    Session = sessionmaker(bind=engine)
    return Session()

session = configuracao_do_banco_de_dados()

def atualizar_medida(entry, valor):
    entry.config(state='normal')
    entry.delete(0, tk.END)
    entry.insert(0, valor)
    entry.config(state='readonly')

def atualizar_espessura():
        
        material_nome = g.material_combobox.get()
        material_obj = session.query(material).filter_by(nome=material_nome).first()
        if material_obj:
            espessuras_valores = [str(e.valor) for e in session.query(espessura).join(deducao).filter(deducao.material_id == material_obj.id).all()]
            g.espessura_combobox['values'] = espessuras_valores

def atualizar_canal():
        espessura_valor = g.espessura_combobox.get()
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        if espessura_obj:
            canais_valores = [str(c.valor) for c in session.query(canal).join(deducao).filter(deducao.espessura_id == espessura_obj.id).all()]
            g.canal_combobox['values'] = canais_valores

def atualizar_deducao_e_obs():
    espessura_valor = g.espessura_combobox.get()
    material_nome = g.material_combobox.get()
    canal_valor = g.canal_combobox.get()

    espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
    material_obj = session.query(material).filter_by(nome=material_nome).first()
    canal_obj = session.query(canal).filter_by(valor=canal_valor).first()

    obs_obj = None

    if espessura_obj and material_obj and canal_obj:
        deducao_obj = session.query(deducao).join(espessura).join(material).join(canal).filter(
            deducao.espessura_id == espessura_obj.id,
            deducao.material_id == material_obj.id,
            deducao.canal_id == canal_obj.id
        ).first()

        if deducao_obj:
            g.deducao_entry.config(text=deducao_obj.valor, fg="black")
            obs_obj = session.query(observacao).join(deducao).filter(deducao.obs_id == deducao_obj.id).first()
            
            if obs_obj:
                g.obs_label.config(text=f'Observações: {obs_obj.valor}')
            else:
                g.obs_label.config(text='Observações não encontradas')
        else:
            g.deducao_entry.config(text='Não encontrada', fg="red")
            g.obs_label.config(text='Observações não encontradas')
        
        if obs_obj:
            g.obs_label.config(text=f'Observações: {obs_obj.valor}')
        else:
            g.obs_label.config(text='Observações não encontradas')      
            
def calcular_fatork():
    raio_interno = g.raio_interno_entry.get().replace(',', '.')
    espessura_valor = g.espessura_combobox.get()
    deducao_valor = g.deducao_entry['text']

    if not raio_interno or not espessura_valor or not deducao_valor or deducao_valor == 'Não encontrada':
        return
    else:
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        g.espessura_valor = espessura_obj.valor

        fator_k = (4 * (g.espessura_valor - (float(deducao_valor) / 2) + float(raio_interno)) - (pi * float(raio_interno))) / (pi * g.espessura_valor)

        g.fator_k_entry.config(text=f"{fator_k:.2f}",fg="black")

def calcular_offset():

    fator_k = g.fator_k_entry['text']
    espessura = g.espessura_combobox.get()
     
    if not fator_k or not espessura:
          print('Fator K não informado')
          return         
    else:
         offset = float(fator_k) * float(espessura)
         g.offset_entry.config (text=f"{offset:.2f}",fg="black")
         
def calcular_dobra():
    deducao_valor = g.deducao_entry['text']
    deducao_espec = g.deducao_espec_entry.get()
    dobra1 = g.aba1_entry.get().replace(',', '.')
    dobra2 = g.aba2_entry.get().replace(',', '.')
    dobra3 = g.aba3_entry.get().replace(',', '.')
    dobra4 = g.aba4_entry.get().replace(',', '.')
    dobra5 = g.aba5_entry.get().replace(',', '.')

    if deducao_valor == "" or deducao_valor == 'Não encotrada':  
        return
    else:
        if deducao_espec == "":
            deducao_valor = float(g.deducao_entry['text'])
        else:
            deducao_valor = float(deducao_espec)
        
        if dobra1 == "":
                g.medidadobra1_entry.config(text="")
                return
        else:
                
                medidadobra1 = float(dobra1) - (deducao_valor / 2)
                g.medidadobra1_entry.config(text=medidadobra1,fg="black")

            # Calculo da medida da linha de dobra 2
        if dobra2 == "":
                g.medidadobra2_entry.config(text="")
                return
        else:
                if dobra3 == "":
                    medidadobra2 = float(dobra2) - (deducao_valor / 2)
                else:
                    medidadobra2 = float(dobra2) - deducao_valor
                g.medidadobra2_entry.config(text=medidadobra2,fg="black")

            # Calculo da medida da linha de dobra 3
        if dobra3 == "":
                g.medidadobra3_entry.config(text="")
                return
        else:
                if dobra4 == "":
                    medidadobra3 = float(dobra3) - (deducao_valor / 2)
                else:
                    medidadobra3 = float(dobra3) - deducao_valor
                g.medidadobra3_entry.config(text=medidadobra3,fg="black")

            # Calculo da medida da linha de dobra 4
        if dobra4 == "":
                g.medidadobra4_entry.config(text="")
                return
        else:
                if dobra5 == "":
                    medidadobra4 = float(dobra4) - (deducao_valor / 2)
                else:
                    medidadobra4 = float(dobra4) - deducao_valor
                g.medidadobra4_entry.config(text=medidadobra4,fg="black")

            # Calculo da medida da linha de dobra 5
        if dobra5 == "":
                g.medidadobra5_entry.config(text="")
                return
        else:
                medidadobra5 = float(dobra5) - (deducao_valor / 2)
                g.medidadobra5_entry.config(text=medidadobra5,fg="black")

def calcular_blank():
    medidas = [
        g.medidadobra1_entry['text'],
        g.medidadobra2_entry['text'],
        g.medidadobra3_entry['text'],
        g.medidadobra4_entry['text'],
        g.medidadobra5_entry['text']
    ]

    # Filtra apenas as medidas que não estão vazias e converte para float
    medidas_validas = [float(medida) for medida in medidas if medida != ""]

    if not medidas_validas:
        return
    else:
        blank = sum(medidas_validas)
        g.medida_blank_label.config(text=f"{blank:.2f}")


def calcular_metade_dobra():
        entradas = [
            (g.medidadobra1_entry, g.metadedobra1_entry),
            (g.medidadobra2_entry, g.metadedobra2_entry),
            (g.medidadobra3_entry, g.metadedobra3_entry),
            (g.medidadobra4_entry, g.metadedobra4_entry),
            (g.medidadobra5_entry, g.metadedobra5_entry)
        ]

        for medidadobra_entry, metadedobra_entry in entradas:
            try:
                medidadobra = float(medidadobra_entry['text'])
                metadedobra = medidadobra / 2
                metadedobra_entry.config(text=f'{metadedobra:.2f}')
            except ValueError:
                metadedobra_entry.config(text="")
                return
                    
def calcular_dobra_ang():
    distancia = float(g.dist1_entry.get())
    angulo = float(g.angulo1_entry.get())
    raio = float(g.raio_interno_entry.get())
    offset = float(g.offset_entry.get())

    dobra = distancia + (angulo*(raio + offset)*pi/360)

    atualizar_medida(g.linha_dobra1_entry, f"{dobra:.1f}")

    print(f'Essa é a dobra: {dobra:.1f}')


def razao_raio_esp():
    if g.raio_interno_entry is None or g.espessura_valor is None:
        return
    else:
        try:
            razao_raio_esp_valor = float(g.raio_interno_entry.get()) / g.espessura_valor
            if g.razao_raio_esp_label is not None:
                g.razao_raio_esp_label.config(text=f"{razao_raio_esp_valor:.1f}")
            
        except ValueError:
            return


def copiar_deducao():
    if g.deducao_entry['text'] == 'Não encotrada' or g.deducao_entry['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.deducao_entry['text'])
        print(f'Valor de dedução copiado {g.deducao_entry["text"]}')
        g.deducao_entry.config(text=f'{g.deducao_entry["text"]} Copiado!',fg="green")

def copiar_fatork():
    if g.fator_k_entry['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.fator_k_entry['text'])
        print(f'Valor de fator k copiado {g.fator_k_entry["text"]}')
        g.fator_k_entry.config(text=f'{g.fator_k_entry["text"]} Copiado!',fg="green")

def copiar_offset():
    if g.offset_entry['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.offset_entry['text'])
        print(f'Valor de offset copiado {g.offset_entry["text"]}')
        g.offset_entry.config(text=f'{g.offset_entry["text"]} Copiado!',fg="green")

def copiar_medidadobra(numero):
    entry = getattr(g, f'medidadobra{numero}_entry')
    if entry['text'] == '':
        return
    else:
        pyperclip.copy(entry['text'])
        print(f'Valor de medida de dobra {numero} copiado {entry["text"]}')
        entry.config(text=f'{entry["text"]} Copiado!', fg="green")

def copiar_metadedobra(numero):
    entry = getattr(g, f'metadedobra{numero}_entry')
    if entry['text'] == '':
        return
    else:
        pyperclip.copy(entry['text'])
        print(f'Valor de metade de dobra {numero} copiado {entry["text"]}')
        entry.config(text=f'{entry["text"]} Copiado!', fg="green")        

def copiar_blank():
    if g.medida_blank_label['text'] == '':
        return
    else:
        pyperclip.copy(g.medida_blank_label['text'])
        print(f'Valor de medida blank copiado {g.medida_blank_label["text"]}')
        g.medida_blank_label.config(text=f'{g.medida_blank_label["text"]} Copiado!', fg="green")


def limpar_dobras():
        limpar_dobras = [g.aba1_entry, g.aba2_entry, g.aba3_entry, g.aba4_entry, g.aba5_entry]
        limpar_medidas = [g.medidadobra1_entry, g.medidadobra2_entry, g.medidadobra3_entry, g.medidadobra4_entry, g.medidadobra5_entry]
        limpar_metades = [g.metadedobra1_entry, g.metadedobra2_entry, g.metadedobra3_entry, g.metadedobra4_entry, g.metadedobra5_entry]

        for limpar_dobras in limpar_dobras:
            limpar_dobras.delete(0, tk.END)

        for limpar_medidas in limpar_medidas:
            limpar_medidas.config(text="")

        for limpar_metades in limpar_metades:
            limpar_metades.config(text="")

        g.deducao_espec_entry.delete(0, tk.END)

def limpar_tudo():

        limpar_dobras()
        
        g.material_combobox.set('')
        g.espessura_combobox.set('')
        g.canal_combobox.set('')
        g.raio_interno_entry.delete(0, tk.END)
        g.fator_k_entry.config(text="")
        g.deducao_entry.config(text="")
        g.offset_entry.config(text="")

def todas_funcoes():
        atualizar_espessura()
        atualizar_canal()
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        calcular_dobra()
        calcular_blank()
        calcular_metade_dobra()
        #calcular_dobra_ang()
        razao_raio_esp()
        