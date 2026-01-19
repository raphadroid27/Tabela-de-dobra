"""Variáveis globais usadas em diferentes partes da aplicação."""

from typing import Any, Dict, List, Optional

# Variáveis globais
VALORES_W: List[int] = [1, 2]
EXP_V: Optional[bool] = None
EXP_H: Optional[bool] = None
USUARIO_ID: Optional[int] = None
USUARIO_NOME: Optional[str] = None
TEMA_ATUAL: Optional[str] = None
SESSION_ID: Optional[str] = None
UPDATE_INFO: Optional[Dict[str, Any]] = None
UPDATE_ACTION: Optional[str] = None

# Largura (px) abaixo da qual os menus de topo ficam em modo compacto (icone-only)
MENU_COMPACT_WIDTH: int = 450

# Flag para controlar quando a interface está sendo recarregada
INTERFACE_RELOADING: bool = False

# Referências a widgets globais (para atualização dinâmica)
AVISOS_WIDGET: Any = None

# Função para carregar interface (definida dinamicamente para evitar importação cíclica)
CARREGAR_INTERFACE_FUNC: Any = None

# Layout principal da interface (para redimensionamento)
MAIN_LAYOUT: Any = None

# head.py widgets
MAT_COMB: Any = None
ESP_COMB: Any = None
CANAL_COMB: Any = None
OFFSET_LBL: Any = None
OBS_LBL: Any = None
COMPR_ENTRY: Any = None
RI_ENTRY: Any = None
K_LBL: Any = None
DED_LBL: Any = None
ABA_EXT_LBL: Any = None
Z_EXT_LBL: Any = None
FORCA_LBL: Any = None

N: int = 6
DED_ESPEC_ENTRY: Any = None
FRAME_DOBRA: Any = None
RAZAO_RIE_LBL: Any = None

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
    10.0: 0.50,
}

# nova_espessura.py widgets
ESP_VALOR_ENTRY: Any = None
LIST_ESP: Any = None
ESP_BUSCA_ENTRY: Any = None

# deducao_form.py widgets
DED_MATER_COMB: Any = None
DED_ESPES_COMB: Any = None
DED_CANAL_COMB: Any = None
DED_VALOR_ENTRY: Any = None
DED_OBSER_ENTRY: Any = None
DED_FORCA_ENTRY: Any = None
LIST_DED: Any = None

# material_form.py widgets
MAT_NOME_ENTRY: Any = None
MAT_DENS_ENTRY: Any = None
MAT_ESCO_ENTRY: Any = None
MAT_ELAS_ENTRY: Any = None
LIST_MAT: Any = None
MAT_BUSCA_ENTRY: Any = None

# canal_form.py widgets
CANAL_VALOR_ENTRY: Any = None
CANAL_LARGU_ENTRY: Any = None
CANAL_ALTUR_ENTRY: Any = None
CANAL_COMPR_ENTRY: Any = None
CANAL_OBSER_ENTRY: Any = None
LIST_CANAL: Any = None
CANAL_BUSCA_ENTRY: Any = None

# form_autenticacao.py widgets
USUARIO_ENTRY: Any = None
SENHA_ENTRY: Any = None
ADMIN_VAR: Any = None
LOGIN: Any = None

# form_usuario.py widgets
USUARIO_BUSCA_ENTRY: Any = None
LIST_USUARIO: Any = None


# formularios
PRINC_FORM: Any = None
DEDUC_FORM: Any = None
MATER_FORM: Any = None
CANAL_FORM: Any = None
ESPES_FORM: Any = None
AUTEN_FORM: Any = None
USUAR_FORM: Any = None
