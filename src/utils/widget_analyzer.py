"""
Utilitário para análise e otimização do uso de widgets globais.
"""
import os
import sys
from typing import Set, Dict, List, Tuple

# Adicionar o diretório raiz ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)


class WidgetUsageAnalyzer:
    """
    Analisador para identificar widgets globais não utilizados e padrões de uso.
    """

    def __init__(self, root_path: str):
        self.project_root = root_path
        self.src_path = os.path.join(root_path, 'src')
        self.widget_assignments = set()
        self.widget_usages = set()

    def get_all_global_widgets(self) -> Set[str]:
        """
        Obtém todos os widgets definidos no módulo globals.

        Returns:
            Conjunto com nomes de todos os widgets globais
        """
        widgets = set()

        # Obter widgets do arquivo globals.py
        globals_path = os.path.join(self.src_path, 'config', 'globals.py')
        if os.path.exists(globals_path):
            with open(globals_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Buscar definições de widgets (variáveis com valor None)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if '=' in line and 'None' in line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    if var_name.isupper():  # Convenção para constantes/widgets
                        widgets.add(var_name)

        return widgets

    def scan_python_file(self, file_path: str) -> Tuple[Set[str], Set[str]]:
        """
        Escaneia um arquivo Python procurando por usos de widgets globais.

        Args:
            file_path: Caminho para o arquivo Python

        Returns:
            Tupla (widget_assignments, widget_usages)
        """
        assignments = set()
        usages = set()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Buscar padrões comuns de uso
            lines = content.split('\n')
            for line in lines:
                line = line.strip()

                # Atribuições: setattr(g, 'WIDGET_NAME', ...)
                if 'setattr(g,' in line:
                    parts = line.split("'")
                    if len(parts) >= 2:
                        widget_name = parts[1]
                        assignments.add(widget_name)

                # Usos diretos: g.WIDGET_NAME
                if 'g.' in line and not line.startswith('#'):
                    words = line.split()
                    for word in words:
                        if word.startswith('g.') and len(word) > 2:
                            # Extrair nome do widget (remover símbolos)
                            widget_name = word[2:].split('(')[0].split('[')[0].split('.')[
                                0].split(',')[0].split(')')[0]
                            if widget_name.isupper():
                                usages.add(widget_name)

                # getattr(g, 'WIDGET_NAME', ...)
                if 'getattr(g,' in line:
                    parts = line.split("'")
                    if len(parts) >= 2:
                        widget_name = parts[1]
                        usages.add(widget_name)

        except (OSError, IOError) as e:
            print(f"Erro ao analisar {file_path}: {e}")

        return assignments, usages

    def scan_project(self) -> Dict[str, Dict]:
        """
        Escaneia todo o projeto em busca de uso de widgets.

        Returns:
            Dicionário com estatísticas de uso
        """
        all_assignments = set()
        all_usages = set()
        file_stats = {}

        # Escanear todos os arquivos Python
        for root, dirs, files in os.walk(self.src_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_root)

                    assignments, usages = self.scan_python_file(file_path)
                    all_assignments.update(assignments)
                    all_usages.update(usages)

                    if assignments or usages:
                        file_stats[rel_path] = {
                            'assignments': assignments,
                            'usages': usages
                        }

        self.widget_assignments = all_assignments
        self.widget_usages = all_usages

        return file_stats

    def analyze_usage(self) -> Dict[str, List[str]]:
        """
        Analisa o uso dos widgets e identifica problemas.

        Returns:
            Dicionário com categorias de widgets e suas listas
        """
        all_globals = self.get_all_global_widgets()

        # Widgets atribuídos mas nunca usados
        assigned_not_used = self.widget_assignments - self.widget_usages

        # Widgets usados mas nunca atribuídos (possível problema)
        used_not_assigned = self.widget_usages - self.widget_assignments

        # Widgets definidos mas nunca atribuídos nem usados
        never_used = all_globals - self.widget_assignments - self.widget_usages

        # Widgets com uso normal
        properly_used = self.widget_assignments & self.widget_usages

        return {
            'assigned_not_used': sorted(list(assigned_not_used)),
            'used_not_assigned': sorted(list(used_not_assigned)),
            'never_used': sorted(list(never_used)),
            'properly_used': sorted(list(properly_used)),
            'all_globals': sorted(list(all_globals))
        }

    def get_widgets_by_category(self) -> Dict[str, List[str]]:
        """
        Categoriza widgets por tipo/funcionalidade.

        Returns:
            Dicionário com widgets categorizados
        """
        all_globals = self.get_all_global_widgets()

        categories = {
            'cabecalho': [],
            'dobras': [],
            'formularios': [],
            'deducao_form': [],
            'material_form': [],
            'canal_form': [],
            'espessura_form': [],
            'usuario_form': [],
            'impressao_form': [],
            'outros': []
        }

        for widget in all_globals:
            if any(prefix in widget for prefix in [
                'MAT_COMB', 'ESP_COMB', 'CANAL_COMB', 'DED_LBL', 'RI_ENTRY',
                'K_LBL', 'OFFSET_LBL', 'OBS_LBL', 'FORCA_LBL', 'COMPR_ENTRY',
                'ABA_EXT_LBL', 'Z_EXT_LBL'
            ]):
                categories['cabecalho'].append(widget)
            elif any(
                prefix in widget
                for prefix in ['aba', 'medidadobra', 'metadedobra', 'blank', 'FRAME_DOBRA']
            ):
                categories['dobras'].append(widget)
            elif widget.endswith('_FORM'):
                categories['formularios'].append(widget)
            elif widget.startswith('DED_'):
                categories['deducao_form'].append(widget)
            elif widget.startswith('MAT_'):
                categories['material_form'].append(widget)
            elif widget.startswith('CANAL_'):
                categories['canal_form'].append(widget)
            elif widget.startswith('ESP_'):
                categories['espessura_form'].append(widget)
            elif widget.startswith('USUARIO_') or widget.startswith('SENHA_'):
                categories['usuario_form'].append(widget)
            elif widget.startswith('IMPRESSAO_'):
                categories['impressao_form'].append(widget)
            else:
                categories['outros'].append(widget)

        return categories

    def generate_report(self) -> str:
        """
        Gera um relatório completo da análise de widgets.

        Returns:
            String com o relatório formatado
        """
        print("Analisando uso de widgets...")
        file_stats = self.scan_project()
        usage_analysis = self.analyze_usage()
        categories = self.get_widgets_by_category()

        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE ANÁLISE DE WIDGETS")
        report.append("=" * 80)

        # Estatísticas gerais
        report.append("\nESTATÍSTICAS GERAIS:")
        report.append(
            "- Total de widgets globais definidos: {len(usage_analysis['all_globals'])}")
        report.append(
            "- Widgets propriamente utilizados: {len(usage_analysis['properly_used'])}")
        report.append(
            "- Widgets atribuídos mas não usados: {len(usage_analysis['assigned_not_used'])}")
        report.append(
            "- Widgets usados mas não atribuídos: {len(usage_analysis['used_not_assigned'])}")
        report.append(
            "- Widgets nunca utilizados: {len(usage_analysis['never_used'])}")

        # Widgets por categoria
        report.append("\nWIDGETS POR CATEGORIA:")
        for category, widgets in categories.items():
            if widgets:
                report.append(f"- {category.title()}: {len(widgets)} widgets")

        # Possíveis otimizações
        report.append("\nOPORTUNIDADES DE OTIMIZAÇÃO:")

        if usage_analysis['never_used']:
            report.append(
                f"\n1. WIDGETS NUNCA UTILIZADOS ({len(usage_analysis['never_used'])}):")
            report.append(
                "   Estes widgets podem ser removidos do globals.py:")
            for widget in usage_analysis['never_used']:
                report.append(f"   - {widget}")

        if usage_analysis['assigned_not_used']:
            report.append(
                f"\n2. WIDGETS ATRIBUÍDOS MAS NÃO USADOS "
                f"({len(usage_analysis['assigned_not_used'])}):"
            )
            report.append("   Estes widgets são criados mas nunca utilizados:")
            for widget in usage_analysis['assigned_not_used']:
                report.append(f"   - {widget}")

        if usage_analysis['used_not_assigned']:
            report.append(
                f"\n3. POSSÍVEIS PROBLEMAS ({len(usage_analysis['used_not_assigned'])}):")
            report.append(
                "   Estes widgets são usados mas podem não estar sendo atribuídos:")
            for widget in usage_analysis['used_not_assigned']:
                report.append(f"   - {widget}")

        # Sugestões de melhoria
        report.append("\nSUGESTÕES DE MELHORIA:")
        report.append(
            "1. Considere criar widgets sob demanda ao invés de globalmente")
        report.append(
            "2. Agrupe widgets relacionados em classes ou estruturas")
        report.append(
            "3. Use factory patterns para criação de formulários similares")
        report.append("4. Implemente lazy loading para widgets não críticos")

        # Detalhes por arquivo
        report.append("\nUSO POR ARQUIVO:")
        for file_path, stats in file_stats.items():
            if stats['assignments'] or stats['usages']:
                report.append(f"\n{file_path}:")
                if stats['assignments']:
                    report.append(
                        f"  Atribuições: {', '.join(sorted(stats['assignments']))}")
                if stats['usages']:
                    report.append(
                        f"  Usos: {', '.join(sorted(stats['usages']))}")

        return '\n'.join(report)


def analyze_project_widgets(root_path: str = None) -> str:
    """
    Função utilitária para analisar o uso de widgets no projeto.

    Args:
        root_path: Caminho raiz do projeto (usa o diretório atual se None)

    Returns:
        Relatório de análise formatado
    """
    if root_path is None:
        root_path = os.getcwd()

    analyzer = WidgetUsageAnalyzer(root_path)
    return analyzer.generate_report()


if __name__ == "__main__":
    # Executar análise se o script for chamado diretamente
    print(analyze_project_widgets())
