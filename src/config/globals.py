"""
Este módulo define variáveis globais para uso em diferentes partes da aplicação.
"""
# Variáveis globais
NO_TOPO_VAR = None
TRANSP_VAR = None
VALORES_W = [1, 2]
EXP_V = None
EXP_H = None
USUARIO_ID = None
USUARIO_NOME = None
TEMA_ATUAL = None
WIDGET_MIN_WIDTH = None
WIDGET_MAX_HEIGHT = None
BARRA_TITULO = None
MENU_CUSTOM = None
SESSION_ID = None

# Flag para controlar quando a interface está sendo recarregada
INTERFACE_RELOADING = False

# Flag para controlar quando os comboboxes de dedução estão sendo atualizados automaticamente
UPDATING_DEDUCAO_COMBOS = False

# Função para carregar interface (definida dinamicamente para evitar importação cíclica)
CARREGAR_INTERFACE_FUNC = None

# Layout principal da interface (para redimensionamento)
MAIN_LAYOUT = None

# head.py widgets
MAT_COMB = None
ESP_COMB = None
CANAL_COMB = None
DED_LBL = None
RI_ENTRY = None
K_LBL = None
OFFSET_LBL = None
OBS_LBL = None
FORCA_LBL = None
COMPR_ENTRY = None
ABA_EXT_LBL = None
Z_EXT_LBL = None

# aba1.py widgets
W = None
N = 6
for i in range(1, N):
    globals()[f'aba{i}_entry_{W}'] = None
    globals()[f'medidadobra{i}_label_{W}'] = None
    globals()[f'metadedobra{i}_label_{W}'] = None
DED_ESPEC_ENTRY = None
FRAME_DOBRA = None

# aba3.py widgets
RAZAO_RIE_LBL = None

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
ESP_VALOR_ENTRY = None
LIST_ESP = None
EDIT_ESP = None
ESP_BUSCA_ENTRY = None

# deducao_form.py widgets
DED_MATER_COMB = None
DED_ESPES_COMB = None
DED_CANAL_COMB = None
DED_VALOR_ENTRY = None
DED_OBSER_ENTRY = None
DED_FORCA_ENTRY = None
LIST_DED = None
EDIT_DED = None

# material_form.py widgets
MAT_NOME_ENTRY = None
MAT_DENS_ENTRY = None
MAT_ESCO_ENTRY = None
MAT_ELAS_ENTRY = None
LIST_MAT = None
EDIT_MAT = None
MAT_BUSCA_ENTRY = None

# canal_form.py widgets
CANAL_VALOR_ENTRY = None
CANAL_LARGU_ENTRY = None
CANAL_ALTUR_ENTRY = None
CANAL_COMPR_ENTRY = None
CANAL_OBSER_ENTRY = None
LIST_CANAL = None
EDIT_CANAL = None
CANAL_BUSCA_ENTRY = None

# form_autenticacao.py widgets
USUARIO_ENTRY = None
SENHA_ENTRY = None
ADMIN_VAR = None
LOGIN = None

# form_usuario.py widgets
USUARIO_BUSCA_ENTRY = None
LIST_USUARIO = None
EDIT_USUARIO = None

# form_impressao.py widgets
IMPRESSAO_FORM = None
IMPRESSAO_DIRETORIO_ENTRY = None
IMPRESSAO_ARQUIVO_ENTRY = None
IMPRESSAO_LISTA_ARQUIVOS = None
IMPRESSAO_LISTA_TEXT = None
IMPRESSAO_RESULTADO_TEXT = None

# formularios
PRINC_FORM = None
DEDUC_FORM = None
MATER_FORM = None
CANAL_FORM = None
ESPES_FORM = None
SOBRE_FORM = None
AUTEN_FORM = None
USUAR_FORM = None
RIE_FORM = None
