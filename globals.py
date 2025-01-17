import tkinter as tk
from tkinter import ttk

#variáveis globais
deducao_valor = None
fator_k = None
espessura_valor = None
deducao_espec = None

# head.py wigets
material_combobox = None
espessura_combobox = None
canal_combobox = None
deducao_entry = None
raio_interno_entry = None
fator_k_entry = None
offset_entry = None

# aba1.py widgets
dobra1 = None
dobra2 = None
dobra3 = None
dobra4 = None
dobra5 = None
medidadobra1_entry = None
medidadobra2_entry = None
medidadobra3_entry = None
medidadobra4_entry = None
medidadobra5_entry = None
metadedobra1_entry = None
metadedobra2_entry = None
metadedobra3_entry = None
metadedobra4_entry = None
metadedobra5_entry = None
deducao_espec_entry = None

#aba2.py widgets

dist1_entry = None
dist2_entry = None
dist3_entry = None
dist4_entry = None
dist5_entry = None
angulo1_entry = None
angulo2_entry = None
angulo3_entry = None
angulo4_entry = None
angulo5_entry = None
linha_dobra1_entry = None
linha_dobra2_entry = None
linha_dobra3_entry = None
linha_dobra4_entry = None
linha_dobra5_entry = None


#aba3.py widgets
razao_raio_esp_label = None

# Dicionário de valores de raio interno
raio_fator_k = {
    0.1: 0.23,
    0.2: 0.29,
    0.3: 0.32,
    0.4: 0.35,
    0.5: 0.37,
    0.6: 0.38,
    0.7: 0.39,
    0.8: 0.40,
    0.9: 0.41,
    1.0: 0.41,
    1.5: 0.44,
    2.0: 0.45,
    3.0: 0.46,
    4.0: 0.47,
    5.0: 0.48,
    6.0: 0.48,
    7.0: 0.49,
    8.0: 0.49,
    9.0: 0.50,
    10.0: 0.50
    }