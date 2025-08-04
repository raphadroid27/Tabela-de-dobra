"""
Script para análise completa de qualidade de código.
Executa múltiplas ferramentas de análise e formatação.
Gera relatórios em TXT e aplica formatações automaticamente.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_arguments():
    """Analisa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Análise completa de qualidade de código com formatação automática"
    )
    parser.add_argument(
        "--src",
        default="src",
        help="Diretório do código fonte (padrão: src)"
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Não aplicar formatações automáticas"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Não gerar relatório em arquivo"
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="Apenas aplicar formatações, sem análise"
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        help="Executar apenas ferramentas específicas (ex: --tools pylint flake8)"
    )
    return parser.parse_args()


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


def run_command(cmd, description, timeout=120, save_to_report=True, report_file=None):
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

        output = ""
        if result.stdout:
            output += result.stdout
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            error_msg = f"❌ Erros:\n{result.stderr}"
            output += f"\n{error_msg}"
            print(error_msg)

        # Salvar no relatório se solicitado
        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"🔍 {description}\n")
                f.write(f"{'='*60}\n")
                f.write(f"Comando: {cmd}\n")
                f.write(
                    f"Status: {'✅ Sucesso' if result.returncode == 0 else '❌ Erro'}\n")
                f.write(f"Código de retorno: {result.returncode}\n")
                if output:
                    f.write(f"\nSaída:\n{output}\n")
                f.write("\n")

        return result.returncode == 0
    except subprocess.TimeoutExpired:
        error_msg = f"⏰ Comando excedeu o tempo limite de {timeout}s"
        print(error_msg)
        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{description}: {error_msg}\n")
        return False
    except (subprocess.SubprocessError, OSError) as e:
        error_msg = f"❌ Erro ao executar: {e}"
        print(error_msg)
        if save_to_report and report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"\n{description}: {error_msg}\n")
        return False
    except KeyboardInterrupt:
        print("🛑 Comando interrompido pelo usuário")
        return False


def apply_auto_formatting(tools, src_path, report_file):
    """Aplica formatações automáticas no código."""
    print("\n🎨 APLICANDO FORMATAÇÕES AUTOMÁTICAS")

    formatting_results = []

    # 1. Remover imports não utilizados
    if tools['autoflake']:
        success = run_command(
            f"python -m autoflake --remove-all-unused-imports "
            f"--remove-unused-variables --in-place --recursive {src_path}/",
            "Removendo imports e variáveis não utilizados", 60, True, report_file
        )
        formatting_results.append(("Autoflake", success))

    # 2. Organizar imports
    if tools['isort']:
        success = run_command(
            f"python -m isort {src_path}/ --profile black",
            "Organizando imports com isort", 30, True, report_file
        )
        formatting_results.append(("Isort", success))

    # 3. Formatação com black (se disponível)
    if tools.get('black'):
        success = run_command(
            f"python -m black {src_path}/ --line-length=88",
            "Formatando código com Black", 60, True, report_file
        )
        formatting_results.append(("Black", success))

    return formatting_results


def create_summary_report(report_file, tools, formatting_results, analysis_results):
    """Cria um resumo do relatório."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"RESUMO DA ANÁLISE DE CÓDIGO - {timestamp}\n")
        f.write(f"{'='*80}\n\n")

        # Status das ferramentas
        f.write("📋 STATUS DAS FERRAMENTAS:\n")
        f.write("-" * 40 + "\n")
        for tool, installed in tools.items():
            status = "✅ Instalada" if installed else "❌ Não instalada"
            f.write(f"{tool:<15}: {status}\n")

        # Resultados da formatação
        if formatting_results:
            f.write("\n🎨 RESULTADOS DA FORMATAÇÃO:\n")
            f.write("-" * 40 + "\n")
            for tool, success in formatting_results:
                status = "✅ Sucesso" if success else "❌ Falhou"
                f.write(f"{tool:<15}: {status}\n")

        # Resultados da análise
        if analysis_results:
            f.write("\n🔍 RESULTADOS DA ANÁLISE:\n")
            f.write("-" * 40 + "\n")
            for tool, success in analysis_results:
                status = "✅ Sucesso" if success else "❌ Falhou"
                f.write(f"{tool:<15}: {status}\n")

        f.write(f"\n{'='*80}\n")
        f.write("📊 Análise completa finalizada!\n")
        f.write("Revise os resultados acima para identificar melhorias.\n")
        f.write(f"{'='*80}\n")

# pylint: disable=R0912
# pylint: disable=R0915


def main():
    """Executa análise completa do código."""
    args = parse_arguments()

    src_path = args.src

    if not Path(src_path).exists():
        print(f"❌ Diretório {src_path} não encontrado!")
        sys.exit(1)

    # Configurar relatório
    report_file = None
    if not args.no_report:
        # Criar diretório de relatórios se não existir
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Nome do arquivo de relatório com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"analise_codigo_{timestamp}.txt"

    print("🚀 Iniciando análise completa de qualidade de código...")
    if report_file:
        print(f"📄 Relatório será salvo em: {report_file}")

    # Verificar ferramentas disponíveis
    all_tools = {
        'isort': check_tool_installed('isort'),
        'pylint': check_tool_installed('pylint'),
        'flake8': check_tool_installed('flake8'),
        'vulture': check_tool_installed('vulture'),
        'mypy': check_tool_installed('mypy'),
        'bandit': check_tool_installed('bandit'),
        'radon': check_tool_installed('radon'),
        'autoflake': check_tool_installed('autoflake'),
        'black': check_tool_installed('black')
    }

    # Filtrar ferramentas se especificado
    if args.tools:
        tools = {tool: all_tools.get(tool, False) for tool in args.tools}
        # Verificar se as ferramentas especificadas são válidas
        invalid_tools = [tool for tool in args.tools if tool not in all_tools]
        if invalid_tools:
            print(f"❌ Ferramentas inválidas: {', '.join(invalid_tools)}")
            print(f"🔧 Ferramentas disponíveis: {', '.join(all_tools.keys())}")
            sys.exit(1)
    else:
        tools = all_tools

    # Inicializar relatório
    if report_file:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE ANÁLISE DE QUALIDADE DE CÓDIGO\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Diretório analisado: {src_path}\n")
            f.write(f"Argumentos: {' '.join(sys.argv[1:])}\n")
            f.write("=" * 80 + "\n\n")

    missing_tools = [tool for tool, installed in tools.items() if not installed]
    if missing_tools:
        print(f"\n⚠️  Ferramentas não instaladas: {', '.join(missing_tools)}")
        print("💡 Para instalar: pip install -r requirements-dev.txt")

        # Adicionar ao relatório
        if report_file:
            with open(report_file, "a", encoding="utf-8") as f:
                f.write(f"⚠️  Ferramentas não instaladas: {', '.join(missing_tools)}\n")
                f.write("💡 Para instalar: pip install -r requirements-dev.txt\n\n")

    try:
        formatting_results = []
        analysis_results = []

        # Aplicar formatações automáticas (se não for --no-format)
        if not args.no_format:
            formatting_results = apply_auto_formatting(tools, src_path, report_file)

        # Executar análise (se não for --format-only)
        if not args.format_only:
            # Análise de qualidade
            print("\n🔍 EXECUTANDO ANÁLISE DE QUALIDADE")

            if tools.get('pylint'):
                success = run_command(
                    f"python -m pylint {src_path} --disable=C0114,C0115,C0116,R0903,R0913 "
                    f"--output-format=text --reports=n --score=y --jobs=0",
                    "Análise completa com Pylint", 300, not args.no_report, report_file
                )
                analysis_results.append(("Pylint", success))
            elif 'pylint' in tools:
                print("⏭️  Pulando pylint - não instalado")

            if tools.get('flake8'):
                success = run_command(
                    f"python -m flake8 {src_path}/ --max-line-length=88 --ignore=E203,W503",
                    "Análise de estilo com Flake8", 60, not args.no_report, report_file
                )
                analysis_results.append(("Flake8", success))
            elif 'flake8' in tools:
                print("⏭️  Pulando flake8 - não instalado")

            if tools.get('vulture'):
                success = run_command(
                    f"python -m vulture {src_path}/ --min-confidence 80",
                    "Detecção de código morto com Vulture", 60, not args.no_report, report_file
                )
                analysis_results.append(("Vulture", success))
            elif 'vulture' in tools:
                print("⏭️  Pulando vulture - não instalado")

            # Análise avançada
            print("\n⚡ ANÁLISE AVANÇADA")
            if tools.get('mypy'):
                success = run_command(
                    f"python -m mypy {src_path}/ --ignore-missing-imports --no-strict-optional",
                    "Verificação de tipos", 120, not args.no_report, report_file
                )
                analysis_results.append(("MyPy", success))
            elif 'mypy' in tools:
                print("⏭️  Pulando mypy - não instalado")

            if tools.get('bandit'):
                success = run_command(
                    f"python -m bandit -r {src_path}/ --format screen --skip B101",
                    "Análise de segurança", 90, not args.no_report, report_file
                )
                analysis_results.append(("Bandit", success))
            elif 'bandit' in tools:
                print("⏭️  Pulando bandit - não instalado")

            if tools.get('radon'):
                success = run_command(
                    f"python -m radon cc {src_path}/ -a --min=B",
                    "Complexidade ciclomática", 60, not args.no_report, report_file
                )
                analysis_results.append(("Radon", success))
            elif 'radon' in tools:
                print("⏭️  Pulando radon - não instalado")

        # Criar resumo final
        if report_file:
            create_summary_report(report_file, tools,
                                  formatting_results, analysis_results)

        print(f"\n{'='*60}")
        print("✅ Análise completa finalizada!")
        if report_file:
            print(f"📄 Relatório salvo em: {report_file}")
        print("📊 Revise os resultados para identificar melhorias.")
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
    try:
        main()
    except (subprocess.SubprocessError, OSError, RuntimeError) as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("\n📖 Exemplos de uso:")
        print("  python analise_codigo.py                    # Análise completa")
        print("  python analise_codigo.py --no-format        # Apenas análise, sem formatação")
        print("  python analise_codigo.py --format-only      # Apenas formatação")
        print("  python analise_codigo.py --tools pylint flake8  # Executar apenas pylint e flake8")
        print("  python analise_codigo.py --src meu_codigo    # Analisar diretório específico")
        print("  python analise_codigo.py --no-report        # Não gerar arquivo de relatório")
        sys.exit(1)
