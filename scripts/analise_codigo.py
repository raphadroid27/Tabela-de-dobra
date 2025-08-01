#!/usr/bin/env python3
"""
Script para análise completa de qualidade de código.
Executa múltiplas ferramentas de análise e formatação.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"❌ Erros:\n{result.stderr}")
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError) as e:
        print(f"❌ Erro ao executar: {e}")
        return False

def main():
    """Executa análise completa do código."""
    src_path = "src"

    if not Path(src_path).exists():
        print(f"❌ Diretório {src_path} não encontrado!")
        sys.exit(1)

    print("🚀 Iniciando análise completa de qualidade de código...")

    # 1. Formatação automática (se disponível)
    print("\n🎨 FORMATAÇÃO AUTOMÁTICA")
    run_command("python -m isort src/ --profile black --check-only",
                "Verificação de imports com isort")

    # 2. Análise de qualidade core
    print("\n🔍 ANÁLISE DE QUALIDADE")
    run_command("python -m pylint src --disable=C0114,C0115,C0116 --reports=n --score=y",
                "Análise completa com Pylint")
    run_command("python -m flake8 src/", "Análise de estilo com Flake8")
    run_command("python -m vulture src/", "Detecção de código morto com Vulture")

    # 3. Análise avançada (se disponível)
    print("\n⚡ ANÁLISE AVANÇADA")
    run_command("python -m mypy src/ --ignore-missing-imports", "Verificação de tipos")
    run_command("python -m bandit -r src/ --format screen", "Análise de segurança")
    run_command("python -m radon cc src/ -a", "Complexidade ciclomática")
    run_command("python -m autoflake --check --remove-all-unused-imports --recursive src/",
                "Verificação de imports não utilizados")

    print(f"\n{'='*60}")
    print("✅ Análise completa finalizada!")
    print("📊 Revise os resultados acima para identificar melhorias.")
    print("💡 Para instalar ferramentas faltantes: pip install -r requirements-dev.txt")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
