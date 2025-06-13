"""
Script para atualizar todas as referências de tp.DicaFerramenta para tp.DicaFerramenta
"""
import os
import re

def atualizar_referencias_tooltip(diretorio):
    """Atualiza todas as referências de tp.DicaFerramenta para tp.DicaFerramenta"""
    arquivos_alterados = []
    
    for root, dirs, files in os.walk(diretorio):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Substituir tp.DicaFerramenta por tp.DicaFerramenta
                    novo_content = content.replace('tp.DicaFerramenta', 'tp.DicaFerramenta')
                    
                    if content != novo_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(novo_content)
                        arquivos_alterados.append(filepath)
                        print(f"Atualizado: {filepath}")
                
                except Exception as e:
                    print(f"Erro ao processar {filepath}: {e}")
    
    return arquivos_alterados

if __name__ == "__main__":
    # Executar a partir do diretório src
    arquivos = atualizar_referencias_tooltip(".")
    print(f"\nTotal de arquivos atualizados: {len(arquivos)}")
