'''
Formulário para o cálculo de Spring Back
'''
import tkinter as tk
from src.utils.janelas import (no_topo, posicionar_janela)
from src.utils.utilitarios import obter_caminho_icone
from src.config import globals as g

# Configuração do banco de dados

def main(root):
    '''
    Inicializa e exibe o formulário de cálculo de razão raio interno / espessura.
    Configura a interface gráfica para exibir os valores e fatores K correspondentes.
    '''
    if g.SPRING_BACK_FORM:
        g.SPRING_BACK_FORM.destroy()

    g.SPRING_BACK_FORM = tk.Toplevel(root)
    g.SPRING_BACK_FORM.title("Spring Back")
    g.SPRING_BACK_FORM.geometry("340x420")
    g.SPRING_BACK_FORM.resizable(False, False)

    # Define o ícone
    icone_path = obter_caminho_icone()
    g.SPRING_BACK_FORM.iconbitmap(icone_path)

    no_topo(g.SPRING_BACK_FORM)
    posicionar_janela(g.SPRING_BACK_FORM,None)

    main_frame = tk.Frame(g.SPRING_BACK_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

if __name__ == "__main__":
    main(None)
