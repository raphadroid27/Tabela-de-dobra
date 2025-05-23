'''
Formulário para o cálculo de Spring Back
'''
import tkinter as tk
from tkinter import ttk
from src.models.models import Material
from src.utils.banco_dados import session
from src.config import globals as g

# Configuração do banco de dados

spring_back_form = tk.Tk()
spring_back_form.title("Cálculo de Spring Back")

frame = tk.Frame(spring_back_form)
frame.pack(pady=5, padx=5, fill='both', expand=True)

# Obtém os nomes dos materiais como strings a partir da consulta
materiais = [str(material.nome) for material in session.query(Material).all()]

tk.Label(frame, text="Material:").grid(row=0, column=0)
g.MAT_COMB = ttk.Combobox(frame, values=materiais)
g.MAT_COMB.grid(row=1, column=0)

spring_back_form.mainloop()
