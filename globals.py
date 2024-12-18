import tkinter as tk
from tkinter import ttk

#variáveis globais

fator_k = None
espessura_valor = None
deducao_espec = None
deducao_valor = None
raio_interno = None
canal_valor = None

# head.py widgets
material_combobox = None
espessura_combobox = None
canal_combobox = None
deducao_label = None
raio_interno_entry = None
fator_k_label = None
offset_label = None
obs_label = None
ton_m_label = None
comprimento_entry = None
aba_min_externa_label = None
z_min_externa_label = None

# aba1.py widgets
aba1_entry = None
aba2_entry = None
aba3_entry = None
aba4_entry = None
aba5_entry = None
medidadobra1_label = None
medidadobra2_label = None
medidadobra3_label = None
medidadobra4_label = None
medidadobra5_label = None
metadedobra1_label = None
metadedobra2_label = None
metadedobra3_label = None
metadedobra4_label = None
metadedobra5_label = None
deducao_espec_entry = None
medida_blank_label = None
metade_blank_label = None

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
linha_dobra1_label = None
linha_dobra2_label = None
linha_dobra3_label = None
linha_dobra4_label = None
linha_dobra5_label = None

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

# nova_espessura.py widgets
espessura_valor_entry = None

# deducao_form.py widgets
deducao_material_combobox = None
deducao_espessura_combobox = None
deducao_canal_combobox = None
deducao_valor_entry = None
deducao_obs_entry = None
deducao_forca_entry = None
lista_deducao = None
editar_deducao = None

#material_form.py widgets
material_nome_entry = None
material_densidade_entry = None
material_escoamento_entry = None
material_elasticidade_entry = None
lista_material = None
editar_material = None

# canal_form.py widgets
canal_valor_entry = None
canal_largura_entry = None
canal_altura_entry = None
canal_comprimento_entry = None
canal_observacao_entry = None
lista_canal = None
editar_canal = None

# formularios
deducao_form = None
material_form = None
canal_form = None