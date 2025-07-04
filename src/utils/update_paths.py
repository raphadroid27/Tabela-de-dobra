"""
Utilitário para gerenciar caminhos de atualização de forma padronizada.
"""
import os
import sys


def obter_caminho_updates():
    """
    Retorna o caminho da pasta de updates relativa ao executável.

    Returns:
        str: Caminho absoluto para a pasta updates
    """
    if getattr(sys, 'frozen', False):
        # Aplicativo compilado (executável)
        app_dir = os.path.dirname(sys.executable)
    else:
        # Executando do código fonte - usar raiz do projeto
        current_file = os.path.abspath(__file__)
        # Subir 2 níveis: src/utils -> src -> raiz do projeto
        app_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(current_file)))

    return os.path.join(app_dir, "updates")


def criar_pasta_updates():
    """
    Cria a pasta updates se não existir.

    Returns:
        str: Caminho absoluto para a pasta updates criada
    """
    updates_path = obter_caminho_updates()
    os.makedirs(updates_path, exist_ok=True)
    return updates_path


def obter_caminho_executavel():
    """
    Retorna o caminho do executável atual.

    Returns:
        str: Caminho absoluto do executável
    """
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        # Durante desenvolvimento, simular caminho do executável
        projeto_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(projeto_root, "Cálculo de Dobra.exe")


def obter_diretorio_aplicativo():
    """
    Retorna o diretório onde está localizado o aplicativo.

    Returns:
        str: Caminho absoluto do diretório do aplicativo
    """
    return os.path.dirname(obter_caminho_executavel())
