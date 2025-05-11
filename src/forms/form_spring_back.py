'''
Formulário para o cálculo de Spring Back
'''
import tkinter as tk
from tkinter import ttk
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

    dados_frame = tk.LabelFrame(main_frame, text="Dados de Entrada")
    dados_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    dados_frame.columnconfigure(0, weight=0)
    dados_frame.columnconfigure(1, weight=1)

    tk.Label(dados_frame, text="Material:").grid(row=0, column=0, sticky='w')
    material_combo = ttk.Combobox(dados_frame, state="readonly")
    material_combo.grid(row=0, column=1, sticky='ew')

    tk.Label(dados_frame, text="Espessura:").grid(row=1, column=0, sticky='w')
    espessura_entry = ttk.Entry(dados_frame)
    espessura_entry.grid(row=1, column=1, sticky='ew')

    tk.Label(dados_frame, text="Raio Final:").grid(row=2, column=0, sticky='w')
    raio_entry = ttk.Entry(dados_frame)
    raio_entry.grid(row=2, column=1, sticky='ew')

    tk.Label(dados_frame, text="Ângulo Final:").grid(row=3, column=0, sticky='w')
    angulo_entry = ttk.Entry(dados_frame)
    angulo_entry.grid(row=3, column=1, sticky='ew')

    resultado_frame = tk.LabelFrame(main_frame, text="Resultados")
    resultado_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    resultado_frame.columnconfigure(0, weight=0)
    resultado_frame.columnconfigure(1, weight=1)

    tk.Label(resultado_frame, text="Ks:").grid(row=0, column=0, sticky='w')
    ks_label = tk.Label(resultado_frame, relief="sunken")
    ks_label.grid(row=0, column=1, sticky='ew')

    tk.Label(resultado_frame, text="Raio Inicial:").grid(row=1, column=0, sticky='w')
    raio_inicial_label = tk.Label(resultado_frame, relief="sunken")
    raio_inicial_label.grid(row=1, column=1, sticky='ew')

    tk.Label(resultado_frame, text="Ângulo Inicial:").grid(row=2, column=0, sticky='w')
    angulo_inicial_label = tk.Label(resultado_frame, relief="sunken")
    angulo_inicial_label.grid(row=2, column=1, sticky='ew')

if __name__ == "__main__":
    main(None)
