"""
Script simples para testar o sistema de auto-update.
"""

import json
import os
from datetime import datetime


def obter_caminho_updates_local():
    """Retorna o caminho da pasta updates relativa ao projeto."""
    projeto_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(projeto_root, "updates")


def criar_teste_rapido():
    """Cria uma versão de teste rapidamente."""
    # Usar pasta 'updates' relativa ao projeto
    update_dir = obter_caminho_updates_local()
    os.makedirs(update_dir, exist_ok=True)
    print(f"📁 Usando diretório: {update_dir}")

    # Versão de teste simples
    version_info = {
        "version": "1.0.2",
        "filename": "Cálculo de Dobra_new.exe",
        "mandatory": False,
        "changelog": "🧪 VERSÃO DE TESTE\n- Teste do sistema de auto-update\n- Verificação manual funcionando",
        "release_date": datetime.now().strftime("%Y-%m-%d")
    }

    # Salvar
    version_file = os.path.join(update_dir, "version.json")
    with open(version_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=4, ensure_ascii=False)

    print(f"✅ Teste criado: {version_file}")
    print(f"📋 Versão: {version_info['version']}")
    print(f"🔧 Obrigatória: {'Sim' if version_info['mandatory'] else 'Não'}")
    print("\n🚀 Para testar:")
    print("1. Execute o aplicativo")
    print("2. Menu: Utilidades → Verificar Atualizações")


def limpar_teste():
    """Remove teste."""
    # Usar a mesma função para obter o caminho
    update_dir = obter_caminho_updates_local()

    if os.path.exists(update_dir):
        import shutil
        try:
            shutil.rmtree(update_dir)
            print(f"✅ Removido: {update_dir}")
            return
        except OSError as e:
            print(f"⚠️ Erro ao remover {update_dir}: {e}")

    print("ℹ️ Nenhum diretório de teste encontrado")


if __name__ == "__main__":
    print("🧪 Teste Rápido do Auto-Update")
    print("1. Criar teste")
    print("2. Limpar teste")

    opcao = input("Opção [1]: ").strip() or "1"

    if opcao == "1":
        criar_teste_rapido()
    elif opcao == "2":
        limpar_teste()
    else:
        print("❌ Opção inválida")
