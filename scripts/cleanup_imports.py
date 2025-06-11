"""
Script para remover imports não utilizados e otimizar imports no projeto.
"""
import ast
import os
import sys
from typing import Set, List, Dict
from pathlib import Path

class ImportAnalyzer(ast.NodeVisitor):
    """Analisador AST para identificar imports utilizados."""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = set()
        self.used_names = set()
        
    def visit_Import(self, node):
        """Registra imports diretos."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Registra imports from."""
        if node.module:
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.from_imports.add(name)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Registra nomes utilizados no código."""
        self.used_names.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Registra atributos utilizados."""
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

def analyze_file(file_path: str) -> Dict[str, Set[str]]:
    """
    Analisa um arquivo Python e retorna imports utilizados e não utilizados.
    
    Args:
        file_path: Caminho para o arquivo Python
        
    Returns:
        Dict com imports utilizados e não utilizados
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        # Identificar imports não utilizados
        all_imports = analyzer.imports.union(analyzer.from_imports)
        unused_imports = all_imports - analyzer.used_names
        used_imports = all_imports.intersection(analyzer.used_names)
        
        return {
            'used': used_imports,
            'unused': unused_imports,
            'all_imports': all_imports,
            'used_names': analyzer.used_names
        }
        
    except Exception as e:
        print(f"Erro ao analisar {file_path}: {e}")
        return {'used': set(), 'unused': set(), 'all_imports': set(), 'used_names': set()}

def get_python_files(directory: str) -> List[str]:
    """Obtém lista de arquivos Python no diretório."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Ignorar diretórios cache
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def clean_imports_in_file(file_path: str, dry_run: bool = True) -> None:
    """
    Remove imports não utilizados de um arquivo.
    
    Args:
        file_path: Caminho para o arquivo
        dry_run: Se True, apenas mostra o que seria removido
    """
    analysis = analyze_file(file_path)
    unused = analysis['unused']
    
    if not unused:
        return
    
    print(f"\n📁 {file_path}")
    print(f"   Imports não utilizados: {', '.join(sorted(unused))}")
    
    if not dry_run:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filtrar linhas com imports não utilizados
            cleaned_lines = []
            for line in lines:
                should_keep = True
                line_stripped = line.strip()
                
                # Verificar se é uma linha de import não utilizado
                for unused_import in unused:
                    if (line_stripped.startswith(f'import {unused_import}') or
                        line_stripped.startswith(f'from {unused_import}') or
                        f'import {unused_import},' in line_stripped or
                        f', {unused_import}' in line_stripped):
                        should_keep = False
                        break
                
                if should_keep:
                    cleaned_lines.append(line)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
                
            print(f"   ✅ Imports removidos de {file_path}")
            
        except Exception as e:
            print(f"   ❌ Erro ao limpar {file_path}: {e}")

def optimize_imports_order(file_path: str) -> None:
    """
    Reorganiza imports seguindo PEP 8.
    
    Args:
        file_path: Caminho para o arquivo
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Separar imports por categoria
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        # Lista de módulos da biblioteca padrão (simplificada)
        stdlib_modules = {
            'os', 'sys', 'json', 'csv', 'datetime', 'time', 'math', 'random',
            'collections', 'itertools', 'functools', 're', 'typing', 'abc',
            'pathlib', 'sqlite3', 'tkinter', 'threading', 'subprocess'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in stdlib_modules:
                        stdlib_imports.append(f"import {alias.name}")
                    elif module_name.startswith('src.'):
                        local_imports.append(f"import {alias.name}")
                    else:
                        third_party_imports.append(f"import {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    import_items = ', '.join([alias.name for alias in node.names])
                    import_line = f"from {node.module} import {import_items}"
                    
                    if module_name in stdlib_modules:
                        stdlib_imports.append(import_line)
                    elif module_name.startswith('src.'):
                        local_imports.append(import_line)
                    else:
                        third_party_imports.append(import_line)
        
        # Construir seção de imports otimizada
        organized_imports = []
        
        if stdlib_imports:
            organized_imports.extend(sorted(set(stdlib_imports)))
            organized_imports.append('')
        
        if third_party_imports:
            organized_imports.extend(sorted(set(third_party_imports)))
            organized_imports.append('')
        
        if local_imports:
            organized_imports.extend(sorted(set(local_imports)))
            organized_imports.append('')
        
        print(f"   📋 Imports organizados em {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"   ❌ Erro ao organizar imports em {file_path}: {e}")

def main():
    """Função principal."""
    print("🧹 Script de Limpeza e Otimização de Imports")
    print("=" * 50)
    
    # Obter diretório do projeto
    project_dir = os.path.join(os.path.dirname(__file__), '..')
    src_dir = os.path.join(project_dir, 'src')
    
    if not os.path.exists(src_dir):
        print(f"❌ Diretório src não encontrado: {src_dir}")
        return
    
    # Obter arquivos Python
    python_files = get_python_files(src_dir)
    print(f"📂 Analisando {len(python_files)} arquivos Python...")
    
    # Modo de execução
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("🔍 Modo de análise (dry-run). Use --apply para aplicar mudanças.")
    else:
        print("⚡ Aplicando mudanças nos arquivos...")
    
    total_unused = 0
    files_with_unused = 0
    
    # Analisar cada arquivo
    for file_path in python_files:
        analysis = analyze_file(file_path)
        unused_count = len(analysis['unused'])
        
        if unused_count > 0:
            files_with_unused += 1
            total_unused += unused_count
            clean_imports_in_file(file_path, dry_run)
            
            if not dry_run:
                optimize_imports_order(file_path)
    
    # Relatório final
    print(f"\n📊 Relatório Final:")
    print(f"   Arquivos analisados: {len(python_files)}")
    print(f"   Arquivos com imports não utilizados: {files_with_unused}")
    print(f"   Total de imports não utilizados: {total_unused}")
    
    if dry_run and total_unused > 0:
        print(f"\n💡 Execute 'python scripts/cleanup_imports.py --apply' para aplicar as mudanças.")

if __name__ == "__main__":
    main()
