"""
Este módulo define variáveis globais para uso em diferentes partes da aplicação.
"""
from typing import Optional
import tkinter as tk
from tkinter import ttk
# Variáveis globais
NO_TOPO_VAR: Optional[tk.IntVar] = None
TRANSP_VAR: Optional[tk.StringVar] = None
DOBRAS_VALORES = None
CABECALHO_VALORES = None
VALORES_W = [1,2]
EXP_V: Optional[tk.StringVar] = None
EXP_H: Optional[tk.StringVar] = None
USUARIO_ID = None
USUARIO_NOME = None

# Função para carregar interface (definida dinamicamente para evitar importação cíclica)
CARREGAR_INTERFACE_FUNC = None

# head.py widgets
MAT_COMB: Optional[ttk.Combobox] = None
ESP_COMB: Optional[ttk.Combobox] = None
CANAL_COMB: Optional[ttk.Combobox] = None
DED_LBL: Optional[tk.Label] = None
RI_ENTRY: Optional[tk.Entry] = None
K_LBL: Optional[tk.Label] = None
OFFSET_LBL: Optional[tk.Label] = None
OBS_LBL: Optional[tk.Label] = None
FORCA_LBL: Optional[tk.Label] = None
COMPR_ENTRY: Optional[tk.Entry] = None
ABA_EXT_LBL: Optional[tk.Label] = None
Z_EXT_LBL: Optional[tk.Label] = None

# aba1.py widgets
W = None
N = 6
for i in range(1, N):
    globals()[f'aba{i}_entry_{W}'] = None
    globals()[f'medidadobra{i}_label_{W}'] = None
    globals()[f'metadedobra{i}_label_{W}'] = None
DED_ESPEC_ENTRY: Optional[tk.Entry] = None
FRAME_DOBRA: Optional[tk.Frame] = None  # Verificar se é necessário

# aba3.py widgets
RAZAO_RIE_LBL: Optional[tk.Label] = None

# Dicionário de valores de raio interno
RAIO_K = {
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
ESP_VALOR_ENTRY: Optional[tk.Entry] = None
LIST_ESP: Optional[ttk.Treeview] = None
EDIT_ESP: Optional[tk.Button] = None
ESP_BUSCA_ENTRY: Optional[tk.Entry] = None

# deducao_form.py widgets
DED_MATER_COMB: Optional[ttk.Combobox] = None
DED_ESPES_COMB: Optional[ttk.Combobox] = None
DED_CANAL_COMB: Optional[ttk.Combobox] = None
DED_VALOR_ENTRY: Optional[tk.Entry] = None
DED_OBSER_ENTRY: Optional[tk.Entry] = None
DED_FORCA_ENTRY: Optional[tk.Entry] = None
LIST_DED: Optional[ttk.Treeview] = None
EDIT_DED: Optional[tk.Button] = None

# material_form.py widgets
MAT_NOME_ENTRY: Optional[tk.Entry] = None
MAT_DENS_ENTRY: Optional[tk.Entry] = None
MAT_ESCO_ENTRY: Optional[tk.Entry] = None
MAT_ELAS_ENTRY: Optional[tk.Entry] = None
LIST_MAT: Optional[ttk.Treeview] = None
EDIT_MAT: Optional[tk.Button] = None
MAT_BUSCA_ENTRY: Optional[tk.Entry] = None

# canal_form.py widgets
CANAL_VALOR_ENTRY: Optional[tk.Entry] = None
CANAL_LARGU_ENTRY: Optional[tk.Entry] = None
CANAL_ALTUR_ENTRY: Optional[tk.Entry] = None
CANAL_COMPR_ENTRY: Optional[tk.Entry] = None
CANAL_OBSER_ENTRY: Optional[tk.Entry] = None
LIST_CANAL: Optional[ttk.Treeview] = None
EDIT_CANAL: Optional[tk.Button] = None
CANAL_BUSCA_ENTRY: Optional[tk.Entry] = None

# form_autenticacao.py widgets
USUARIO_ENTRY: Optional[tk.Entry] = None
SENHA_ENTRY: Optional[tk.Entry] = None
ADMIN_VAR: Optional[tk.StringVar] = None
LOGIN: Optional[tk.Toplevel] = None

# form_usuario.py widgets
USUARIO_BUSCA_ENTRY: Optional[tk.Entry] = None
LIST_USUARIO: Optional[ttk.Treeview] = None
EDIT_USUARIO: Optional[tk.Button] = None

# form_impressao.py widgets
IMPRESSAO_FORM: Optional[tk.Toplevel] = None
IMPRESSAO_DIRETORIO_ENTRY: Optional[tk.Entry] = None
IMPRESSAO_ARQUIVO_ENTRY: Optional[tk.Entry] = None
IMPRESSAO_LISTA_ARQUIVOS: Optional[tk.Listbox] = None
IMPRESSAO_LISTA_TEXT: Optional[tk.Text] = None
IMPRESSAO_RESULTADO_TEXT: Optional[tk.Text] = None

# formularios
PRINC_FORM: Optional[tk.Tk] = None
DEDUC_FORM: Optional[tk.Toplevel] = None
MATER_FORM: Optional[tk.Toplevel] = None
CANAL_FORM: Optional[tk.Toplevel] = None
ESPES_FORM: Optional[tk.Toplevel] = None
SOBRE_FORM: Optional[tk.Toplevel] = None
AUTEN_FORM: Optional[tk.Toplevel] = None
USUAR_FORM: Optional[tk.Toplevel] = None
RIE_FORM: Optional[tk.Toplevel] = None
