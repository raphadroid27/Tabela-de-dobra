"""
Utilitário para gerenciar caminhos de atualização de forma padronizada.
"""
import os
import sys


def normalizar_caminho(caminho):
    """
    Normaliza caminhos para evitar problemas de encoding.

    Args:
        caminho (str): Caminho a ser normalizado

    Returns:
        str: Caminho normalizado
    """
    if not caminho:
        return caminho

    try:
        # Primeiro normalizar o caminho
        normalized = os.path.normpath(caminho)

        # Verificar se contém caracteres problemáticos tentando codificar
        try:
            normalized.encode('cp1252')  # Encoding padrão do Windows
            return normalized
        except UnicodeEncodeError:
            pass

        # Se contém caracteres especiais, tentar obter nome curto do Windows
        if os.name == 'nt' and os.path.exists(normalized):
            try:
                import win32api
                short_path = win32api.GetShortPathName(normalized)
                print(f"Usando nome curto: {normalized} -> {short_path}")
                return short_path
            except (ImportError, Exception):
                # Fallback: usar comando DIR para obter nome curto
                try:
                    import subprocess
                    # Usar comando DIR /X para obter nomes curtos
                    parent_dir = os.path.dirname(normalized)
                    filename = os.path.basename(normalized)

                    result = subprocess.run(
                        ['cmd', '/c', 'dir', '/x', parent_dir],
                        capture_output=True,
                        text=True,
                        encoding='cp1252'
                    )

                    # Procurar pelo arquivo na saída
                    for line in result.stdout.split('\n'):
                        if filename in line and '~' in line:
                            parts = line.split()
                            for part in parts:
                                if '~' in part and part.upper().endswith('.EXE'):
                                    short_name = os.path.join(parent_dir, part)
                                    print(
                                        f"Nome curto encontrado via DIR: {normalized} -> {short_name}")
                                    return short_name
                            break
                except Exception as e:
                    print(f"Erro ao obter nome curto via DIR: {e}")

        # Se não conseguiu nome curto, usar estratégia de escape
        try:
            # Substituir caracteres problemáticos por equivalentes seguros
            safe_path = normalized.replace('ç', 'c').replace('Ç', 'C')
            safe_path = safe_path.replace('á', 'a').replace('Á', 'A')
            safe_path = safe_path.replace('à', 'a').replace('À', 'A')
            safe_path = safe_path.replace('ã', 'a').replace('Ã', 'A')
            safe_path = safe_path.replace('â', 'a').replace('Â', 'A')
            safe_path = safe_path.replace('é', 'e').replace('É', 'E')
            safe_path = safe_path.replace('ê', 'e').replace('Ê', 'E')
            safe_path = safe_path.replace('í', 'i').replace('Í', 'I')
            safe_path = safe_path.replace('ó', 'o').replace('Ó', 'O')
            safe_path = safe_path.replace('ô', 'o').replace('Ô', 'O')
            safe_path = safe_path.replace('õ', 'o').replace('Õ', 'O')
            safe_path = safe_path.replace('ú', 'u').replace('Ú', 'U')
            safe_path = safe_path.replace('ü', 'u').replace('Ü', 'U')

            if safe_path != normalized:
                print(
                    f"Usando versão sem acentos: {normalized} -> {safe_path}")
                return safe_path
        except Exception:
            pass

        # Último recurso: manter caminho original mas avisar
        print(
            f"Aviso: Mantendo caminho com caracteres especiais: {normalized}")
        return normalized

    except Exception as e:
        print(f"Erro ao normalizar caminho '{caminho}': {e}")
        return caminho


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

    updates_path = os.path.join(app_dir, "updates")
    return normalizar_caminho(updates_path)


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
