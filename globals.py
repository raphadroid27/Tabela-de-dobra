"""
Este módulo define variáveis globais para uso em diferentes partes da aplicação.
"""
#variáveis globais
FATOR_K = None
ESP_VALOR = None
DED_ESPEC = None
DED_VALOR = None
R_INT = None
CANAL_VALOR = None
LARG_CANAL = None
NO_TOPO_VAR = None
DOBRAS_VALORES = None
VALORES_W = [1,2]
EXP_V = None
EXP_H = None
USUARIO_ID = None
USUARIO_NOME = None

# head.py widgets
MAT_COMB = None
ESP_COMB = None
CANAL_COMB = None
DED_COMB = None
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
MED_BLANK_LBL = None
MET_BLANK_LBL = None
FRAME_DOBRA = None #Verificar se é necessário

#aba3.py widgets
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

#material_form.py widgets
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

# formularios
PRINC_FORM = None
DEDUC_FORM = None
MATER_FORM = None
CANAL_FORM = None
ESPES_FORM = None
SOBRE_FORM = None
AUTEN_FORM = None
USUAR_FORM = None

def valores_deducao(d):
    '''
    Retorna os valores de um objeto Deducao como uma tupla.
    Os valores retornados são:
    - ID da dedução
    - Nome do material
    - Valor da espessura
    - Valor do canal
    - Valor da dedução
    - Observação da dedução
    - Força da dedução
    '''
    return (
        d.id,
        d.material.nome,
        d.espessura.valor,
        d.canal.valor,
        d.valor,
        d.observacao,
        d.forca,
    )

def valores_material(m):
    '''
    Retorna os valores de um objeto Material como uma tupla.
    Os valores retornados são:
    - ID do material
    - Nome do material
    - Densidade do material
    - Escoamento do material
    - Elasticidade do material
    '''
    return (
        m.id,
        m.nome,
        m.densidade,
        m.escoamento,
        m.elasticidade,
    )

def valores_espessura(e):
    '''
    Retorna os valores de um objeto Espessura como uma tupla.
    Os valores retornados são:
    - ID da espessura
    - Valor da espessura
    '''
    return (
        e.id,
        e.valor,
    )

def valores_canal(c):
    '''
    Retorna os valores de um objeto Canal como uma tupla.
    Os valores retornados são:
    - ID do canal
    - Valor do canal
    - Largura do canal
    - Altura do canal
    - Comprimento total do canal
    - Observação do canal
    '''
    return (
        c.id,
        c.valor,
        c.largura,
        c.altura,
        c.comprimento_total,
        c.observacao,
    )

def valores_usuario(u):
    '''
    Retorna os valores de um objeto Usuario como uma tupla.
    Os valores retornados são:
    - ID do usuário
    - Nome do usuário
    - Senha do usuário
    - Papel do usuário (admin ou viewer)
    '''
    return (
        u.id,
        u.nome,
        u.role,
    )
