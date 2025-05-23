"""
Este script lista os commits de um branch específico de um repositório Git e salva as informações
em um arquivo. Ele permite configurar filtros como autor, intervalo de datas e formato de saída,
além de exibir detalhes das modificações.
"""
import subprocess
import argparse
import sys
import os
from datetime import datetime

def listar_commits(branch="main", arquivo_saida=None,
                  mostrar_modificacoes="stat", limite=None,
                  formato="completo", author=None, desde=None, ate=None,
                  linhas_contexto=3):
    '''
    Lista os commits de um branch específico e salva em um arquivo.
    
    Args:
        branch (str): Nome do branch para listar commits
        arquivo_saida (str): Nome do arquivo onde salvar a saída
        mostrar_modificacoes (str): Nível de detalhes das modificações (stat, patch, nenhum)
        limite (int): Número máximo de commits a listar
        formato (str): Formato da saída (completo, oneline, custom)
        author (str): Filtrar commits por autor
        desde (str): Data inicial para filtrar commits (formato YYYY-MM-DD)
        ate (str): Data final para filtrar commits (formato YYYY-MM-DD)
        linhas_contexto (int): Número de linhas de contexto ao mostrar diffs (padrão: 3)
    '''
    try:
        # Define o nome do arquivo de saída padrão
        if arquivo_saida is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_saida = f"commits_{branch}_{timestamp}.txt"

        # Configura os parâmetros do comando git log
        comando = ["git", "log", branch]

        # Adiciona opção para mostrar modificações
        if mostrar_modificacoes == "stat":
            comando.append("--stat")  # Estatísticas resumidas
        elif mostrar_modificacoes == "patch":
            comando.append("-p")      # Diff completo (patch)
            comando.append(f"--unified={linhas_contexto}")  # Configura número de linhas de contexto

        # Configura o formato de saída
        if formato == "oneline":
            comando.append("--oneline")
        elif formato == "custom":
            comando.append("--pretty=format:%h - %an, %ar : %s")

        # Filtro por autor
        if author:
            comando.extend(["--author", author])

        # Filtro por data
        if desde:
            comando.extend(["--since", desde])
        if ate:
            comando.extend(["--until", ate])

        # Limita o número de commits se especificado
        if limite:
            comando.extend(["-n", str(limite)])

        # Executa o comando com configuração explícita de codificação
        processo = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace'  # Substitui caracteres problemáticos em vez de falhar
        )
        resultado, erro = processo.communicate()

        if processo.returncode != 0:
            print(f"Erro ao executar git log: {erro}")
            return

        # Prepara o cabeçalho com informações do comando
        cabeçalho = f"Commits e modificações do branch '{branch}':\n"
        cabeçalho += f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        cabeçalho += f"Comando executado: {' '.join(comando)}\n\n"

        # Salva os commits e modificações em um arquivo
        with open(arquivo_saida, "w", encoding="utf-8", errors='replace') as arquivo:
            arquivo.write(cabeçalho)
            arquivo.write(resultado)

        print(f"Lista de commits e modificações salva em '{os.path.abspath(arquivo_saida)}'.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar commits: {e}")
    except FileNotFoundError:
        print("Git não está instalado ou não foi encontrado no PATH.")
    except PermissionError:
        print(f"Erro de permissão ao tentar escrever no arquivo '{arquivo_saida}'.")
    except ValueError as e:
        print(f"Erro de valor: {e}")
    except OSError as e:
        print(f"Erro do sistema operacional: {e}")

    return False

if __name__ == "__main__":
    # Configura argumentos da linha de comando
    parser = argparse.ArgumentParser(description="Lista commits e suas modificações")
    parser.add_argument("--branch", "-b", default="main", help="Nome do branch")
    parser.add_argument("--output", "-o", help="Arquivo de saída (padrão: commits_BRANCH_DATA.txt)")
    parser.add_argument("--mode", "-m", choices=["stat", "patch", "nenhum"], default="stat",
                      help="Modo de exibição: 'stat' para estatísticas resumidas, 'patch' para diff "  # pylint: disable=C0301
                           "completo, 'nenhum' para apenas commits")
    parser.add_argument("--format", "-f", choices=["completo", "oneline", "custom"],
                        default="completo",
                      help="Formato da saída: 'completo', 'oneline' ou 'custom'")
    parser.add_argument("--context", "-c", type=int, default=3,
                      help="Número de linhas de contexto ao mostrar diffs (padrão: 3)")
    parser.add_argument("--limit", "-l", type=int, help="Limitar número de commits")
    parser.add_argument("--author", "-a", help="Filtrar por autor (nome ou email)")
    parser.add_argument("--since", "-s", help="Incluir commits desde data (YYYY-MM-DD)")
    parser.add_argument("--until", "-u", help="Incluir commits até data (YYYY-MM-DD)")

    args = parser.parse_args()

    # Executa a função com os argumentos fornecidos
    sucesso = listar_commits(
        branch=args.branch,
        arquivo_saida=args.output,
        mostrar_modificacoes=args.mode,
        limite=args.limit,
        formato=args.format,
        author=args.author,
        desde=args.since,
        ate=args.until,
        linhas_contexto=args.context
    )

    # Define o código de saída
    sys.exit(0 if sucesso else 1)
