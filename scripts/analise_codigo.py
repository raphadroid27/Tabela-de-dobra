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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"❌ Erros:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")
        return False

def main():
    """Executa análise completa do código."""
    src_path = "src"
    
    if not Path(src_path).exists():
        print(f"❌ Diretório {src_path} não encontrado!")
        sys.exit(1)
    
    print("🚀 Iniciando análise completa de qualidade de código...")
    
    # 1. Formatação automática
    run_command("python -m black src/", "Formatação com Black")
    run_command("python -m isort src/ --profile black", "Organização de imports com isort")
    
    # 2. Análise de qualidade
    run_command("python -m pylint src --disable=C0114,C0115,C0116 --reports=n --score=y", 
                "Análise com Pylint")
    run_command("python -m flake8 src/", "Análise com Flake8")
    run_command("python -m vulture src/", "Detecção de código morto com Vulture")
    
    # 3. Análise de segurança
    run_command("python -m bandit -r src/", "Análise de segurança com Bandit")
    
    # 4. Análise de complexidade
    run_command("python -m radon cc src/ -a", "Complexidade ciclomática com Radon")
    run_command("python -m radon mi src/", "Índice de manutenibilidade com Radon")
    
    # 5. Verificação de tipos
    run_command("python -m mypy src/ --ignore-missing-imports", "Verificação de tipos com MyPy")
    
    # 6. Imports não utilizados
    run_command("python -m unimport --check src/", "Verificação de imports com Unimport")
    
    print(f"\n{'='*60}")
    print("✅ Análise completa finalizada!")
    print("📊 Revise os resultados acima para identificar melhorias.")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
