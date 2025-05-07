'''
Atualiza a versão do projeto, gera changelog e cria tag Git.
Este script automatiza o processo de atualização de versão,
geração de changelog e criação de tags Git para um projeto Python.
Ele lê as mensagens de commit desde a última tag, atualiza os
arquivos relevantes com a nova versão e gera um changelog formatado.
Além disso, permite ao usuário criar uma nova tag Git para a versão
atualizada.
'''
import subprocess
import re
import os
import datetime
from pathlib import Path

def get_latest_tag():
    '''Obtém a tag mais recente do repositório Git.'''
    try:
        tags_raw = subprocess.check_output(
            ["git", "tag", "--sort=-v:refname"], text=True
        ).strip()
        if not tags_raw:
            return "v0.0.0"  # Se não existir tag, começa do zero

        tags = tags_raw.split('\n')
        latest_tag = tags[0]
        print(f"Tag mais recente encontrada: {latest_tag}")
        return latest_tag
    except ValueError as e:
        print(f"Erro ao obter tags: {e}")
        return "v0.0.0"

def parse_version(version_str):
    '''Converte uma string de versão em tupla (major, minor, patch).'''
    match = re.search(r'v?(\d+)\.(\d+)\.(\d+)(?:-.*)?', version_str)
    if match:
        return tuple(map(int, match.groups()))
    return (0, 0, 0)

def generate_next_version(auto_increment="patch"):
    '''
    Gera a próxima versão com base na tag mais recente.
    
    Parâmetro auto_increment pode ser "major", "minor" ou "patch" para 
    definir qual número incrementar automaticamente.
    '''
    latest_tag = get_latest_tag()
    major, minor, patch = parse_version(latest_tag)

    if auto_increment == "major":
        major += 1
        minor = 0
        patch = 0
    elif auto_increment == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"

def get_commit_messages_since_last_tag():
    '''Obtém as mensagens de commit desde a última tag, sem número do commit e autor.'''
    try:
        latest_tag = get_latest_tag()
        output = subprocess.check_output(
            ["git", "log", f"{latest_tag}..HEAD", "--pretty=format:%s"], text=True
        ).strip()  # Apenas a mensagem do commit

        if not output:
            return ["Não há commits desde a última tag."]

        return output.split('\n')
    except ValueError as e:
        print(f"Erro ao obter mensagens de commit: {e}")
        return ["Erro ao obter mensagens de commit."]

def create_git_tag(version, message=None):
    '''Cria uma nova tag Git com a versão especificada.'''
    if not message:
        message = f"Versão {version}"

    version_tag = f"v{version}"
    try:
        subprocess.run(["git", "tag", "-a", version_tag, "-m", message], check=True)
        print(f"Tag {version_tag} criada com sucesso!")

        # Perguntar se deseja enviar a tag para o repositório remoto
        push = input("Deseja enviar a tag para o repositório remoto? (s/n): ")
        if push.lower() == 's':
            subprocess.run(["git", "push", "origin", version_tag], check=True)
            print(f"Tag {version_tag} enviada para o repositório remoto.")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao criar tag Git: {e}")
        return False

def update_version_info(version):
    '''Atualiza o arquivo version_info.txt com a nova versão.'''
    version_info_path = "version_info.txt"
    try:
        with open(version_info_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(version_info_path, "w", encoding="utf-8") as f:
            for line in lines:
                if "filevers=" in line:
                    # Tratamento para versão em formato de tupla (filevers)
                    if "-beta" in version:
                        version_parts = version.split("-beta")[0].split(".")
                        version_tuple = f"{','.join(version_parts)},0"
                    else:
                        version_tuple = f"{version.replace('.', ',')},0"
                    f.write(
                        f"        filevers=({version_tuple}),  # Versão do arquivo ({version})\n"
                    )
                elif "prodvers=" in line:
                    # Garantir que prodvers também seja atualizado
                    if "-beta" in version:
                        version_parts = version.split("-beta")[0].split(".")
                        version_tuple = f"{','.join(version_parts)},0"
                    else:
                        version_tuple = f"{version.replace('.', ',')},0"
                    f.write(
                        f"        prodvers=({version_tuple}),  # Versão do produto ({version})\n"
                    )
                elif "StringStruct(u'FileVersion'" in line:
                    f.write(
                        f"                        StringStruct(u'FileVersion', u'{version}'),\n"
                    )
                elif "StringStruct(u'ProductVersion'" in line:
                    f.write(
                        f"                        StringStruct(u'ProductVersion', u'{version}'),\n"
                    )
                else:
                    f.write(line)

        print(f"Arquivo version_info.txt atualizado com a versão: {version}")
        return True
    except ValueError as e:
        print(f"Erro ao atualizar o arquivo version_info.txt: {e}")
        return False

def generate_changelog(version):
    '''Gera ou atualiza o arquivo CHANGELOG.md com as alterações da nova versão.'''
    commits = get_commit_messages_since_last_tag()
    changelog_path = os.path.join("docs", "CHANGELOG.md")
    today = datetime.datetime.now().strftime("%d/%m/%Y")

    # Corrigir caracteres especiais nos commits
    def corrigir_caracteres_especiais(texto):
        return texto.encode('latin1').decode('utf-8')

    # Cabeçalho da nova versão
    new_version_content = f"## {version} ({today})\n\n"
    for commit in commits:
        commit_corrigido = corrigir_caracteres_especiais(commit)
        new_version_content += f"- {commit_corrigido}\n"

    # Adiciona uma linha em branco após a última atualização
    new_version_content += "\n"

    # Verifica se o arquivo já existe
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Verifica se o arquivo tem o cabeçalho principal
        if "# Changelog" in existing_content:
            # Verifica se já tem a descrição
            if "Histórico de mudanças do aplicativo Cálculo de Dobras" in existing_content:
                # Adiciona a nova versão após o cabeçalho com descrição
                updated_content = re.sub(
                    r'# Changelog\n\nHistórico de mudanças do aplicativo Cálculo de Dobras\n\n', 
                    f'# Changelog\n\nHistórico de mudanças do aplicativo Cálculo de Dobras\n\n'
                    f'{new_version_content}',
                    existing_content
                )
            else:
                # Adiciona descrição e nova versão após o cabeçalho
                updated_content = re.sub(
                    r'# Changelog\n\n', 
                    f'# Changelog\n\nHistórico de mudanças do aplicativo Cálculo de Dobras\n\n'
                    f'{new_version_content}',
                    existing_content
                )
        else:
            # Adiciona cabeçalho, descrição e a nova versão
            updated_content = (
                f"# Changelog\n\nHistórico de mudanças do aplicativo Cálculo de Dobras\n\n"
                f"{new_version_content}{existing_content}"
            )
    else:
        # Cria um novo arquivo changelog
        updated_content = (
            f"# Changelog\n\nHistórico de mudanças do aplicativo Cálculo de Dobras\n\n"
            f"{new_version_content}"
        )

    try:
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Arquivo CHANGELOG.md atualizado com a versão {version}")
        return True
    except ValueError as e:
        print(f"Erro ao atualizar o arquivo CHANGELOG.md: {e}")
        return False

def main():
    '''Função principal que executa todo o processo de atualização de versão.'''
    print("=== Atualizador de Versão ===")

    # Obtém a próxima versão
    auto_increment = input("Incrementar [p]atch, [m]inor ou [M]ajor? (p/m/M) [p]: ").lower()

    if auto_increment == 'm':
        increment_type = "minor"
    elif auto_increment == 'M':
        increment_type = "major"
    else:
        increment_type = "patch"

    next_version = generate_next_version(increment_type)

    # Permite que o usuário confirme ou altere a versão sugerida
    custom_version = input(
        f"Próxima versão será {next_version}. "
        f"Pressione Enter para aceitar ou digite uma versão personalizada: "
    )
    if custom_version.strip():
        version = custom_version.strip()
    else:
        version = next_version

    # Confirma se deseja continuar
    confirm = input(f"Confirma atualização para versão {version}? (s/n): ").lower()
    if confirm != 's':
        print("Atualização de versão cancelada.")
        return

    # Atualiza o arquivo __init__.py
    init_file_path = "src/__init__.py"
    Path("src").mkdir(exist_ok=True)  # Cria o diretório src se não existir

    try:
        with open(init_file_path, "w", encoding="utf-8") as f:
            f.write(f'__version__ = "{version}"\n')
        print(f"Arquivo __init__.py atualizado com a versão: {version}")
    except ValueError as e:
        print(f"Erro ao atualizar o arquivo __init__.py: {e}")

    # Atualiza os outros arquivos
    update_version_info(version)

    # Gera o changelog
    generate_changelog(version)

    # Pergunta se deseja criar uma tag git
    create_tag = input("Deseja criar uma tag Git para esta versão? (s/n): ").lower()
    if create_tag == 's':
        tag_message = input("Digite uma mensagem para a tag (opcional): ")
        create_git_tag(version, tag_message if tag_message else None)

    print(f"\n✅ Processo de atualização para versão {version} concluído com sucesso!")

if __name__ == "__main__":
    main()
