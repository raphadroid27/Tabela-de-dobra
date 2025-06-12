#!/usr/bin/env python3
"""
Script para corrigir automaticamente problemas do pylint no projeto.
"""

import os
import re
import glob


def remover_trailing_whitespace(file_path):
    """Remove espaços em branco no final das linhas."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove trailing whitespace
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cleaned_lines))
        
        print(f"Removido trailing whitespace de: {file_path}")
    except Exception as e:
        print(f"Erro ao processar {file_path}: {e}")


def corrigir_linhas_longas(file_path):
    """Quebra linhas muito longas quando possível."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        corrected_lines = []
        
        for line in lines:
            if len(line) > 100:
                # Verifica se é uma string longa que pode ser quebrada
                if '(' in line and ')' in line:
                    # Tenta quebrar em vírgulas dentro de parênteses
                    if ',' in line:
                        indent = len(line) - len(line.lstrip())
                        parts = line.split(',')
                        if len(parts) > 1:
                            new_line = parts[0] + ','
                            corrected_lines.append(new_line)
                            for part in parts[1:-1]:
                                corrected_lines.append(' ' * (indent + 4) + part.strip() + ',')
                            if parts[-1].strip():
                                corrected_lines.append(' ' * (indent + 4) + parts[-1].strip())
                            continue
                
                # Se não conseguiu quebrar, mantém a linha original
                corrected_lines.append(line)
            else:
                corrected_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(corrected_lines))
        
        print(f"Corrigidas linhas longas em: {file_path}")
    except Exception as e:
        print(f"Erro ao processar linhas longas em {file_path}: {e}")


def adicionar_docstrings(file_path):
    """Adiciona docstrings básicas para classes sem documentação."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        corrected_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            corrected_lines.append(line)
            
            # Verifica se é uma definição de classe sem docstring
            if line.strip().startswith('class ') and line.strip().endswith(':'):
                # Verifica se a próxima linha não é uma docstring
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not next_line.startswith('"""') and not next_line.startswith("'''"):
                        class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0]
                        indent = len(lines[i + 1]) - len(lines[i + 1].lstrip()) if i + 1 < len(lines) else 4
                        if indent == 0:
                            indent = 4
                        docstring = ' ' * indent + f'"""{class_name} class."""'
                        corrected_lines.append(docstring)
            
            i += 1
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(corrected_lines))
        
        print(f"Adicionadas docstrings em: {file_path}")
    except Exception as e:
        print(f"Erro ao adicionar docstrings em {file_path}: {e}")


def adicionar_final_newline(file_path):
    """Adiciona newline final se não existir."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content and not content.endswith('\n'):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content + '\n')
            print(f"Adicionado newline final em: {file_path}")
    except Exception as e:
        print(f"Erro ao adicionar newline final em {file_path}: {e}")


def processar_arquivo(file_path):
    """Processa um arquivo aplicando todas as correções."""
    print(f"\nProcessando: {file_path}")
    
    # Remove trailing whitespace
    remover_trailing_whitespace(file_path)
    
    # Adiciona newline final
    adicionar_final_newline(file_path)
    
    # Adiciona docstrings básicas
    adicionar_docstrings(file_path)
    
    # Corrige linhas longas (comentado por ser mais complexo)
    # corrigir_linhas_longas(file_path)


def main():
    """Função principal."""
    src_dir = "src"
    
    if not os.path.exists(src_dir):
        print(f"Diretório {src_dir} não encontrado!")
        return
    
    # Encontra todos os arquivos Python no diretório src
    python_files = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Encontrados {len(python_files)} arquivos Python para processar...")
    
    for file_path in python_files:
        processar_arquivo(file_path)
    
    print("\nCorreções automáticas concluídas!")
    print("Execute 'pylint src --output-format=text' novamente para verificar melhorias.")


if __name__ == "__main__":
    main()
