'''
Funções utilitárias para o aplicativo de cálculo de dobras.
'''
import os
import sys
from src.config import globals as g
from src.utils.calculos import (calcular_dobra,
                                calcular_k_offset,
                                aba_minima_externa,
                                z_minimo_externo
                                )
from src.utils.interface import (atualizar_widgets,
                                 atualizar_toneladas_m,
                                 canal_tooltip
                                 )

def obter_caminho_icone():
    '''
    Retorna o caminho correto para o arquivo de ícone, 
    considerando o modo de execução (normal ou empacotado).
    '''
    if getattr(sys, 'frozen', False):  # Verifica se está empacotado
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone.ico")

def todas_funcoes():
    '''
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.
    '''
    for tipo in ['espessura', 'canal', 'dedução']:
        atualizar_widgets(tipo)

    atualizar_toneladas_m()
    calcular_k_offset()
    aba_minima_externa()
    z_minimo_externo()
    for w in g.VALORES_W:
        calcular_dobra(w)

    # Atualizar tooltips
    canal_tooltip()
