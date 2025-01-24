import tkinter as tk
import pyperclip
from math import pi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao
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

    if espessura_obj and material_obj and canal_obj:
        deducao_obj = session.query(deducao).filter(
            deducao.espessura_id == espessura_obj.id,
            deducao.material_id == material_obj.id,
            deducao.canal_id == canal_obj.id
        ).first()

        if deducao_obj:
            g.deducao_label.config(text=deducao_obj.valor, fg="black")
            if deducao_obj.observacao:
                g.obs_label.config(text=f'Observações: {deducao_obj.observacao}')
            else:
                g.obs_label.config(text='Observações não encontradas')
        else:
            g.deducao_label.config(text='Não encontrada', fg="red")
            g.obs_label.config(text='Observações não encontradas')      

def atualizar_toneladas_m():
    comprimento = g.comprimento_entry.get()
    deducao_valor = g.deducao_label['text']
    deducao.obj = session.query(deducao).filter_by(valor=deducao_valor).first()

    if deducao.obj:
        if comprimento =="":
            g.ton_m_label.config(text=f'{deducao.obj.forca:.0f}', fg="black")
        else:
            toneladas_m = (deducao.obj.forca * float(comprimento))/1000
            g.ton_m_label.config(text=f'{toneladas_m:.0f}', fg="black")
    
def calcular_fatork():
    raio_interno = g.raio_interno_entry.get().replace(',', '.')
    espessura_valor = g.espessura_combobox.get()
    deducao_valor = g.deducao_label['text']

    if not raio_interno or not espessura_valor or not deducao_valor or deducao_valor == 'Não encontrada':
        return
    else:
        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        g.espessura_valor = espessura_obj.valor

        fator_k = (4 * (g.espessura_valor - (float(deducao_valor) / 2) + float(raio_interno)) - (pi * float(raio_interno))) / (pi * g.espessura_valor)

        g.fator_k_label.config(text=f"{fator_k:.2f}",fg="black")

def calcular_offset():

    fator_k = g.fator_k_label['text']
    espessura = g.espessura_combobox.get()
     
    if not fator_k or not espessura:
          print('Fator K não informado')
          return         
    else:
         offset = float(fator_k) * float(espessura)
         g.offset_label.config (text=f"{offset:.2f}",fg="black")
         
def calcular_dobra():
    deducao_valor = g.deducao_label['text']
    deducao_espec = g.deducao_espec_entry.get()
    dobra1 = g.aba1_entry.get().replace(',', '.')
    dobra2 = g.aba2_entry.get().replace(',', '.')
    dobra3 = g.aba3_entry.get().replace(',', '.')
    dobra4 = g.aba4_entry.get().replace(',', '.')
    dobra5 = g.aba5_entry.get().replace(',', '.')

    if deducao_valor == "" or deducao_valor == 'Não encontrada':
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
    medidas = [
        g.medidadobra1_label['text'],
        g.medidadobra2_label['text'],
        g.medidadobra3_label['text'],
        g.medidadobra4_label['text'],
        g.medidadobra5_label['text']
    ]

    metades = [
        g.metadedobra1_label['text'],
        g.metadedobra2_label['text'],
        g.metadedobra3_label['text'],
        g.metadedobra4_label['text'],
        g.metadedobra5_label['text']
    ]

    # Filtra apenas as medidas que não estão vazias e converte para float
    medidas_validas = [float(medida) for medida in medidas if medida != ""]

    if not medidas_validas:
        return
    else:
        blank = sum(medidas_validas)
        g.medida_blank_label.config(text=f"{blank:.2f}",fg="black")

    metades_validas = [float(metade) for metade in metades if metade != ""]

    if not metades_validas:
        return
    else:
        blank = sum(metades_validas)
        g.metade_blank_label.config(text=f"{blank:.2f}",fg="black")

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
                metadedobra_entry.config(text=f'{metadedobra:.2f}',fg="black")
            except ValueError:
                metadedobra_entry.config(text="")
                return
                    
def calcular_dobra_ang():
    distancia = float(g.dist1_entry.get())
    angulo = float(g.angulo1_entry.get())
    raio = float(g.raio_interno_entry.get())
    offset = float(g.offset_label.get())

    dobra = distancia + (angulo*(raio + offset)*pi/360)

    atualizar_medida(g.linha_dobra1_label, f"{dobra:.1f}")

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
    if g.deducao_label['text'] == 'Não encotrada' or g.deducao_label['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.deducao_label['text'])
        print(f'Valor de dedução copiado {g.deducao_label["text"]}')
        g.deducao_label.config(text=f'{g.deducao_label["text"]} Copiado!',fg="green")

def copiar_fatork():
    if g.fator_k_label['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.fator_k_label['text'])
        print(f'Valor de fator k copiado {g.fator_k_label["text"]}')
        g.fator_k_label.config(text=f'{g.fator_k_label["text"]} Copiado!',fg="green")

def copiar_offset():
    if g.offset_label['text'] == '':
        return
    else:
        atualizar_deducao_e_obs()
        calcular_fatork()
        calcular_offset()
        pyperclip.copy(g.offset_label['text'])
        print(f'Valor de offset copiado {g.offset_label["text"]}')
        g.offset_label.config(text=f'{g.offset_label["text"]} Copiado!',fg="green")

def copiar_medidadobra(numero):
    
    medida_dobra_label = getattr(g, f'medidadobra{numero}_label')
    if medida_dobra_label['text'] == '':
        return
    else:
        calcular_dobra()
        pyperclip.copy(medida_dobra_label['text'])
        print(f'Valor de medida de dobra {numero} copiado {medida_dobra_label["text"]}')
        medida_dobra_label.config(text=f'{medida_dobra_label["text"]} Copiado!', fg="green")

def copiar_metadedobra(numero):
    metade_dobra_label = getattr(g, f'metadedobra{numero}_label')
    if metade_dobra_label['text'] == '':
        return
    else:
        calcular_dobra()
        calcular_metade_dobra()
        pyperclip.copy(metade_dobra_label['text'])
        print(f'Valor de metade de dobra {numero} copiado {metade_dobra_label["text"]}')
        metade_dobra_label.config(text=f'{metade_dobra_label["text"]} Copiado!', fg="green")        

def copiar_blank():
    if g.medida_blank_label['text'] == '':
        return
    else:
        calcular_blank()
        pyperclip.copy(g.medida_blank_label['text'])
        print(f'Valor de medida blank copiado {g.medida_blank_label["text"]}')
        g.medida_blank_label.config(text=f'{g.medida_blank_label["text"]} Copiado!', fg="green")

def limpar_dobras():
        limpar_dobras = [g.aba1_entry, g.aba2_entry, g.aba3_entry, g.aba4_entry, g.aba5_entry]
        limpar_medidas = [g.medidadobra1_label, g.medidadobra2_label, g.medidadobra3_label, g.medidadobra4_label, g.medidadobra5_label]
        limpar_metades = [g.metadedobra1_label, g.metadedobra2_label, g.metadedobra3_label, g.metadedobra4_label, g.metadedobra5_label]

        for limpar_dobras in limpar_dobras:
            limpar_dobras.delete(0, tk.END)

        for limpar_medidas in limpar_medidas:
            limpar_medidas.config(text="")

        for limpar_metades in limpar_metades:
            limpar_metades.config(text="")

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
        #calcular_dobra_ang()
        razao_raio_esp()
        