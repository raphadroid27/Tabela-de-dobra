"""
Script unificado para gerenciar versões e atualizações.
Combina funcionalidades de update_version.py e manage_updates.py de forma simplificada.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Função para obter caminho das atualizações


def obter_caminho_updates_local():
    """Retorna o caminho da pasta updates relativa ao projeto."""
    projeto_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(projeto_root, "updates")


def obter_versao_atual():
    """Obtém a versão atual do arquivo src/__init__.py"""
    try:
        with open("src/__init__.py", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return "1.0.0"


def incrementar_versao(versao_atual, tipo="patch"):
    """Incrementa a versão baseado no tipo (major, minor, patch)"""
    try:
        partes = versao_atual.split('.')
        major, minor, patch = int(partes[0]), int(
            partes[1]), int(partes[2]) if len(partes) > 2 else 0

        if tipo == "major":
            major += 1
            minor = 0
            patch = 0
        elif tipo == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"
    except (ValueError, IndexError):
        return "1.0.0"


def atualizar_arquivos_locais(nova_versao):
    """Atualiza arquivos locais com a nova versão"""
    arquivos_atualizados = []

    # 1. Atualizar src/__init__.py
    init_file = "src/__init__.py"
    Path("src").mkdir(exist_ok=True)

    try:
        if os.path.exists(init_file):
            with open(init_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(init_file, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.startswith("__version__"):
                        f.write(f'__version__ = "{nova_versao}"\n')
                    else:
                        f.write(line)
        else:
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(f'__version__ = "{nova_versao}"\n')

        arquivos_atualizados.append(init_file)
    except Exception as e:
        print(f"⚠️ Erro ao atualizar {init_file}: {e}")

    # 2. Atualizar version_info.txt se existir
    version_info_file = "version_info.txt"
    if os.path.exists(version_info_file):
        try:
            with open(version_info_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(version_info_file, "w", encoding="utf-8") as f:
                for line in lines:
                    if "filevers=" in line or "prodvers=" in line:
                        version_tuple = nova_versao.replace('.', ',') + ",0"
                        if "filevers=" in line:
                            f.write(
                                f"        filevers=({version_tuple}),  # Versão do arquivo ({nova_versao})\n")
                        else:
                            f.write(
                                f"        prodvers=({version_tuple}),  # Versão do produto ({nova_versao})\n")
                    elif "StringStruct(u'FileVersion'" in line:
                        f.write(
                            f"                        StringStruct(u'FileVersion', u'{nova_versao}'),\n")
                    elif "StringStruct(u'ProductVersion'" in line:
                        f.write(
                            f"                        StringStruct(u'ProductVersion', u'{nova_versao}'),\n")
                    else:
                        f.write(line)

            arquivos_atualizados.append(version_info_file)
        except Exception as e:
            print(f"⚠️ Erro ao atualizar {version_info_file}: {e}")

    # 3. Atualizar app.py com a nova versão
    app_file = "src/app.py"
    if os.path.exists(app_file):
        try:
            with open(app_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Procurar e substituir APP_VERSION
            if 'APP_VERSION = ' in content:
                lines = content.split('\n')
                with open(app_file, "w", encoding="utf-8") as f:
                    for line in lines:
                        if line.startswith('APP_VERSION = '):
                            f.write(
                                f'APP_VERSION = "{nova_versao}"  # Versão atual do aplicativo\n')
                        else:
                            f.write(line + '\n')

                arquivos_atualizados.append(app_file)
        except Exception as e:
            print(f"⚠️ Erro ao atualizar {app_file}: {e}")

    return arquivos_atualizados


def criar_version_json_servidor(nova_versao, changelog, obrigatoria=False):
    """Cria/atualiza o version.json do servidor"""
    # Usar pasta 'updates' relativa ao projeto
    servidor_updates = obter_caminho_updates_local()

    # Criar a pasta se não existir
    os.makedirs(servidor_updates, exist_ok=True)
    print(f"📁 Usando diretório: {servidor_updates}")

    version_json_path = os.path.join(servidor_updates, "version.json")
    executavel_path = os.path.join(
        servidor_updates, "Cálculo de Dobra_new.exe")

    # Verificar tamanho do executável
    tamanho_mb = 0.0
    if os.path.exists(executavel_path):
        tamanho_mb = round(os.path.getsize(executavel_path) / (1024 * 1024), 1)

    # Dados do version.json
    version_data = {
        "version": nova_versao,
        "filename": "Cálculo de Dobra_new.exe",
        "mandatory": obrigatoria,
        "changelog": changelog,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "min_version": obter_versao_atual(),
        "download_url": None,
        "size_mb": tamanho_mb,
        "checksum": "auto_generated"
    }

    # Salvar
    with open(version_json_path, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=4, ensure_ascii=False)

    return version_json_path, executavel_path


def main():
    """Função principal - fluxo simplificado"""
    print("🚀 Gerenciador de Versões Simplificado")
    print("="*50)

    versao_atual = obter_versao_atual()
    print(f"📋 Versão atual: {versao_atual}")

    # 1. Escolher tipo de atualização
    print("\nTipo de atualização:")
    print("  [p] Patch (correções de bugs)")
    print("  [m] Minor (novas funcionalidades)")
    print("  [M] Major (mudanças significativas)")

    tipo = input("Escolha [p]: ").lower() or "p"
    tipo_map = {"p": "patch", "m": "minor", "M": "major"}
    nova_versao = incrementar_versao(versao_atual, tipo_map.get(tipo, "patch"))

    # 2. Confirmar versão
    versao_customizada = input(
        f"Nova versão: {nova_versao} (Enter para aceitar): ").strip()
    if versao_customizada:
        nova_versao = versao_customizada

    print(f"🆕 Versão: {nova_versao}")

    # 3. Changelog
    print("\n📝 Changelog (Enter em linha vazia para finalizar):")
    changelog_lines = []
    while True:
        linha = input("  - ")
        if not linha.strip():
            break
        changelog_lines.append(f"- {linha}")

    if not changelog_lines:
        changelog_lines = ["- Atualização de versão", "- Melhorias gerais"]

    changelog = "\n".join(changelog_lines)

    # 4. Configurações
    obrigatoria = input("Atualização obrigatória? (s/N): ").lower() == 's'
    atualizar_servidor = input(
        "Atualizar servidor de updates? (S/n): ").lower() != 'n'

    print(f"\n🔄 Processando...")

    # 5. Executar atualizações
    try:
        # Atualizar arquivos locais
        arquivos_atualizados = atualizar_arquivos_locais(nova_versao)
        print(f"✅ Arquivos locais atualizados: {len(arquivos_atualizados)}")
        for arquivo in arquivos_atualizados:
            print(f"   - {arquivo}")

        # Atualizar servidor se solicitado
        if atualizar_servidor:
            version_json_path, executavel_path = criar_version_json_servidor(
                nova_versao, changelog, obrigatoria
            )
            print(f"✅ Servidor atualizado: {version_json_path}")

            if not os.path.exists(executavel_path):
                print(f"⚠️  Executável não encontrado: {executavel_path}")
                print("   Não esqueça de copiar o novo executável!")

        print(f"\n🎉 Atualização para versão {nova_versao} concluída!")

        # Git tag opcional
        if input("Criar tag Git? (s/N): ").lower() == 's':
            try:
                version_tag = f"v{nova_versao}"
                subprocess.run(["git", "tag", "-a", version_tag,
                               "-m", f"Versão {nova_versao}"], check=True)
                print(f"✅ Tag Git criada: {version_tag}")

                if input("Push tag? (s/N): ").lower() == 's':
                    subprocess.run(
                        ["git", "push", "origin", version_tag], check=True)
                    print("✅ Tag enviada para repositório")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Erro com Git: {e}")

        print(f"\n📊 Resumo:")
        print(f"   Versão: {nova_versao}")
        print(f"   Obrigatória: {'Sim' if obrigatoria else 'Não'}")
        print(f"   Changelog: {len(changelog_lines)} item(s)")

    except Exception as e:
        print(f"❌ Erro durante atualização: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
