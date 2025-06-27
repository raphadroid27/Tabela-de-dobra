"""
Funções utilitárias para o aplicativo de cálculo de dobras.
"""
import os
import sys

def obter_caminho_icone():
    """
    Retorna o caminho correto para o arquivo de ícone, 
    considerando o modo de execução (normal ou empacotado).
    """
    if getattr(sys, 'frozen', False):  # Verifica se está empacotado
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    else:
        base_path = os.path.abspath(".")  # Diretório atual no modo normal

    return os.path.join(base_path, "assets", "icone.ico")
