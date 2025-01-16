import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import espessura, material, canal, deducao
from head import *
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

def atualizar_deducao():
        espessura_valor = g.espessura_combobox.get()
        material_valor = g.material_combobox.get()
        canal_valor = g.canal_combobox.get()

        espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
        material_obj = session.query(material).filter_by(nome=material_valor).first()
        canal_obj = session.query(canal).filter_by(valor=canal_valor).first()

        if espessura_obj and material_obj and canal_obj:
            deducao_obj = session.query(deducao).join(espessura).join(material).join(canal).filter(
                deducao.espessura_id == espessura_obj.id,
                deducao.material_id == material_obj.id,
                deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj:
                atualizar_medida(g.deducao_entry, deducao_obj.valor)
            else:
                atualizar_medida(g.deducao_entry, "Não encontrada")

def calcular_fatork():
        if g.raio_interno_valor.get() == "":
            atualizar_medida(g.fator_k_entry, "")
            print('Raio interno vazio')
            return
        else:
            deducao_valor = float(g.deducao_entry.get())
            espessura_valor = g.espessura_combobox.get()
            espessura_obj = session.query(espessura).filter_by(valor=espessura_valor).first()
            g.espessura_valor = espessura_obj.valor
            raio_interno = float(g.raio_interno_valor.get().replace(',', '.'))

            g.fator_k = (4 * (g.espessura_valor - (deducao_valor / 2) + raio_interno) - (3.14159 * raio_interno)) / (3.14159 * g.espessura_valor)

            atualizar_medida(g.fator_k_entry, f"{g.fator_k:.2f}")

            print("Espessura: ",g.espessura_valor)
            print("fator K: ",g.fator_k)

def calcular_offset():
     
    if g.fator_k_entry.get() == "":
          print('Fator K não informado')
          return
          
    else:
         
         offset = float(g.fator_k_entry.get()) * g.espessura_valor
         atualizar_medida(g.offset_entry, f"{offset:.2f}")
        
def calcular_dobra():
        if g.deducao_espec_entry.get() == "":
            g.deducao_entry.config(state='normal')
            deducao_valor = float(g.deducao_entry.get())
            g.deducao_entry.config(state='readonly')
        else:
            deducao_valor = float(g.deducao_espec_entry.get())    

        if deducao_valor is None:
            print('Dedução não informada')
            return
        else:
            #deducao_valor = g.deducao_valor
            print("valor da dedução ",deducao_valor)

            # Calculo da medida da linha de dobra 1
            if g.dobra1.get() == "":
                atualizar_medida(g.medidadobra1_entry, "")
                atualizar_medida(g.metadedobra1_entry, "")
                return
            else:
                medidadobra1 = float(g.dobra1.get()) - (deducao_valor / 2)
                atualizar_medida(g.medidadobra1_entry, medidadobra1)

            # Calculo da medida da linha de dobra 2
            if g.dobra2.get() == "":
                atualizar_medida(g.medidadobra2_entry, "")
                atualizar_medida(g.metadedobra2_entry, "")
                return
            else:
                if g.dobra3.get() == "":
                    medidadobra2 = float(g.dobra2.get()) - (deducao_valor / 2)
                else:
                    medidadobra2 = float(g.dobra2.get()) - deducao_valor
                atualizar_medida(g.medidadobra2_entry, medidadobra2)

            # Calculo da medida da linha de dobra 3
            if g.dobra3.get() == "":
                atualizar_medida(g.medidadobra3_entry, "")
                atualizar_medida(g.metadedobra3_entry, "")
                return
            else:
                if g.dobra4.get() == "":
                    medidadobra3 = float(g.dobra3.get()) - (deducao_valor / 2)
                else:
                    medidadobra3 = float(g.dobra3.get()) - deducao_valor
                atualizar_medida(g.medidadobra3_entry, medidadobra3)

            # Calculo da medida da linha de dobra 4
            if g.dobra4.get() == "":
                atualizar_medida(g.medidadobra4_entry, "")
                atualizar_medida(g.metadedobra4_entry, "")
                return
            else:
                if g.dobra5.get() == "":
                    medidadobra4 = float(g.dobra4.get()) - (deducao_valor / 2)
                else:
                    medidadobra4 = float(g.dobra4.get()) - deducao_valor
                atualizar_medida(g.medidadobra4_entry, medidadobra4)

            # Calculo da medida da linha de dobra 5
            if g.dobra5.get() == "":
                atualizar_medida(g.medidadobra5_entry, "")
                atualizar_medida(g.metadedobra5_entry, "")
                return
            else:
                medidadobra5 = float(g.dobra5.get()) - (deducao_valor / 2)
                atualizar_medida(g.medidadobra5_entry, medidadobra5)

def calcular_metade_dobra():
        entradas = [
            (g.medidadobra1_entry, g.metadedobra1_entry),
            (g.medidadobra2_entry, g.metadedobra2_entry),
            (g.medidadobra3_entry, g.metadedobra3_entry),
            (g.medidadobra4_entry, g.metadedobra4_entry),
            (g.medidadobra5_entry, g.metadedobra5_entry)
        ]

        for medidadobra_entry, metadedobra_entry in entradas:
            medidadobra_entry.config(state='normal')
            try:
                medidadobra = float(medidadobra_entry.get())
                metadedobra = medidadobra / 2
                atualizar_medida(metadedobra_entry, metadedobra)
            except ValueError:
                return
            finally:
                medidadobra_entry.config(state='readonly')


def limpar_dobras():
        limpar_dobras = [g.dobra1, g.dobra2, g.dobra3, g.dobra4, g.dobra5]
        limpar_medidas = [g.medidadobra1_entry, g.medidadobra2_entry, g.medidadobra3_entry, g.medidadobra4_entry, g.medidadobra5_entry]
        limpar_metades = [g.metadedobra1_entry, g.metadedobra2_entry, g.metadedobra3_entry, g.metadedobra4_entry, g.metadedobra5_entry]

        for limpar_dobras in limpar_dobras:
            limpar_dobras.delete(0, tk.END)

        for limpar_medidas in limpar_medidas:
            limpar_medidas.config(state='normal')
            limpar_medidas.delete(0, tk.END)
            limpar_medidas.config(state='readonly')

        for limpar_metades in limpar_metades:
            limpar_metades.config(state='normal')
            limpar_metades.delete(0, tk.END)
            limpar_metades.config(state='readonly')

def limpar_tudo():

        # Limpar widgets de head.py
        g.material_combobox.set('')
        g.espessura_combobox.set('')
        g.canal_combobox.set('')
        g.raio_interno_valor.delete(0, tk.END)
        atualizar_medida(g.fator_k_entry, "")
        atualizar_medida(g.deducao_entry, "")
        atualizar_medida(g.offset_entry, "")

def todas_funcoes():
        atualizar_espessura()
        atualizar_canal()
        atualizar_deducao()
        calcular_fatork()
        calcular_offset()
        calcular_dobra()
        calcular_metade_dobra()
        print(g.deducao_valor)