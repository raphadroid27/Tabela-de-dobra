#!/usr/bin/env python3
"""
Script para análise completa de qualidade de código.
Executa múltiplas ferramentas de análise e formatação.
"""

import subprocess
import sys
from pathlib import Path


def check_tool_installed(tool_name):
    """Verifica se uma ferramenta está instalada."""
    try:
        # Para algumas ferramentas, verificar se o módulo pode ser importado
        if tool_name == 'autoflake':
            subprocess.run([sys.executable, "-c", f"import {tool_name}"],
                           capture_output=True, check=True, timeout=10)
        else:
            subprocess.run([sys.executable, "-m", tool_name, "--version"],
                           capture_output=True, check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_command(cmd, description, timeout=120):
    """Executa um comando e exibe o resultado."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"❌ Erros:\n{result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ Comando excedeu o tempo limite de {timeout}s")
        return False
    except (subprocess.SubprocessError, OSError) as e:
        print(f"❌ Erro ao executar: {e}")
        return False
    except KeyboardInterrupt:
        print("🛑 Comando interrompido pelo usuário")
        return False


def main():
    """Executa análise completa do código."""
    src_path = "src"

    if not Path(src_path).exists():
        print(f"❌ Diretório {src_path} não encontrado!")
        sys.exit(1)

    print("🚀 Iniciando análise completa de qualidade de código...")

    # Verificar ferramentas disponíveis
    tools = {
        'isort': check_tool_installed('isort'),
        'pylint': check_tool_installed('pylint'),
        'flake8': check_tool_installed('flake8'),
        'vulture': check_tool_installed('vulture'),
        'mypy': check_tool_installed('mypy'),
        'bandit': check_tool_installed('bandit'),
        'radon': check_tool_installed('radon'),
        'autoflake': check_tool_installed('autoflake')
    }

    missing_tools = [tool for tool, installed in tools.items() if not installed]
    if missing_tools:
        print(f"\n⚠️  Ferramentas não instaladas: {', '.join(missing_tools)}")
        print("💡 Para instalar: pip install -r requirements-dev.txt")

    try:
        # 1. Formatação automática (se disponível)
        print("\n🎨 FORMATAÇÃO AUTOMÁTICA")
        if tools['isort']:
            run_command("python -m isort src/ --profile black --check-only",
                        "Verificação de imports com isort", 30)
        else:
            print("⏭️  Pulando isort - não instalado")

        # 2. Análise de qualidade core
        print("\n🔍 ANÁLISE DE QUALIDADE")
        if tools['pylint']:
            run_command("python -m pylint src --disable=C0114,C0115,C0116,R0903,R0913 --reports=n --score=y --jobs=0",
                        "Análise completa com Pylint", 300)
        else:
            print("⏭️  Pulando pylint - não instalado")

        if tools['flake8']:
            run_command("python -m flake8 src/ --max-line-length=100 --ignore=E203,W503",
                        "Análise de estilo com Flake8", 60)
        else:
            print("⏭️  Pulando flake8 - não instalado")

        if tools['vulture']:
            run_command("python -m vulture src/ --min-confidence 80",
                        "Detecção de código morto com Vulture", 60)
        else:
            print("⏭️  Pulando vulture - não instalado")

        # 3. Análise avançada (se disponível)
        print("\n⚡ ANÁLISE AVANÇADA")
        if tools['mypy']:
            run_command("python -m mypy src/ --ignore-missing-imports --no-strict-optional",
                        "Verificação de tipos", 120)
        else:
            print("⏭️  Pulando mypy - não instalado")

        if tools['bandit']:
            run_command("python -m bandit -r src/ --format screen --skip B101",
                        "Análise de segurança", 90)
        else:
            print("⏭️  Pulando bandit - não instalado")

        if tools['radon']:
            run_command("python -m radon cc src/ -a --min=B",
                        "Complexidade ciclomática", 60)
        else:
            print("⏭️  Pulando radon - não instalado")

        if tools['autoflake']:
            run_command("python -m autoflake --check --remove-all-unused-imports --recursive src/",
                        "Verificação de imports não utilizados", 60)
        else:
            print("⏭️  Pulando autoflake - não instalado")

        print(f"\n{'='*60}")
        print("✅ Análise completa finalizada!")
        print("📊 Revise os resultados acima para identificar melhorias.")
        if missing_tools:
            print(
                f"💡 Para instalar ferramentas faltantes: pip install {' '.join(missing_tools)}")
        print(f"{'='*60}")

    except KeyboardInterrupt:
        print("\n🛑 Análise interrompida pelo usuário")
        sys.exit(1)
    except (subprocess.SubprocessError, OSError, RuntimeError) as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
