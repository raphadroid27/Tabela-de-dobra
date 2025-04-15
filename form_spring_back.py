"""
# Calculadora de Springback
# Este módulo implementa uma calculadora de springback para processos de conformação
# de chapas metálicas. Permite selecionar diferentes materiais, inserir parâmetros
# como espessura, raio final e ângulo final, e calcula o fator de springback, raio inicial
# e ângulo inicial necessários.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import math
from funcoes import no_topo, posicionar_janela

# Variáveis globais
SPRING_FORM = None
MATER_COMBO = None
ESPES_ENTRY = None
RAIO_FINAL_ENTRY = None
ANG_FINAL_ENTRY = None
KS_LABEL = None
RAIO_INICIAL_LABEL = None
ANG_INICIAL_LABEL = None
LIST_PROP = None
PROP_KS_VARS = []

# Dados de materiais
MATERIAIS = {
    "AISI 304": {"Y": 207, "E": 190000},
    "AISI 410": {"Y": 550, "E": 215000},
    "AL 5052-H32": {"Y": 195, "E": 70000},
    "AL 6061": {"Y": 55, "E": 69000},
    "CARBONO": {"Y": 220, "E": 210000},
    "LATÃO": {"Y": 240, "E": 100000},
    "SAE 1020": {"Y": 400, "E": 210000},
}

def calcular_springback():
    """Calcula o fator de springback, raio inicial e ângulo inicial"""
    try:
        material = MATER_COMBO.get()
        espessura = float(ESPES_ENTRY.get().replace(',', '.'))
        raio_final = float(RAIO_FINAL_ENTRY.get().replace(',', '.'))
        angulo_final = float(ANG_FINAL_ENTRY.get().replace(',', '.'))
        
        if espessura <= 0 or raio_final <= 0:
            raise ValueError("Espessura e raio final devem ser maiores que zero")
            
        if material not in MATERIAIS:
            raise ValueError("Material inválido")
            
        # Obter propriedades do material
        Y = MATERIAIS[material]["Y"]
        E = MATERIAIS[material]["E"]
        
        # Calcular Ks usando a fórmula: Ks = 1 - 3*(Y*Rf/E/T) + 4*(Y*Rf/E/T)^3
        termo = Y * raio_final / E / espessura
        ks = 1 - 3 * termo + 4 * (termo ** 3)
        
        # Calcular raio inicial: Ri = Ks*(Rf+T/2)-T/2
        raio_inicial = ks * (raio_final + espessura/2) - espessura/2
        
        # Calcular ângulo inicial: α1 = α2/Ks
        angulo_inicial = angulo_final / ks
        
        # Atualizar campos de resultado
        KS_LABEL.config(text=f"{ks:.4f}")
        RAIO_INICIAL_LABEL.config(text=f"{raio_inicial:.2f}")
        ANG_INICIAL_LABEL.config(text=f"{angulo_inicial:.2f}")
        
        # Atualizar valores de Ks na tabela para todos os materiais
        atualizar_tabela_ks(espessura, raio_final)
        
    except ValueError as e:
        messagebox.showerror("Erro", f"Erro de cálculo: {str(e)}")
    except ZeroDivisionError:
        messagebox.showerror("Erro", "Divisão por zero. Verifique os valores inseridos.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")

def atualizar_tabela_ks(espessura, raio_final):
    """Atualiza os valores de Ks na tabela de propriedades para todos os materiais"""
    for i, material in enumerate(MATERIAIS.keys()):
        Y = MATERIAIS[material]["Y"]
        E = MATERIAIS[material]["E"]
        
        # Calcular Ks para este material
        termo = Y * raio_final / E / espessura
        ks = 1 - 3 * termo + 4 * (termo ** 3)
        
        # Atualizar valor na tabela
        item_id = LIST_PROP.get_children()[i]
        LIST_PROP.set(item_id, 'ks', f"{ks:.4f}")

def limpar_campos():
    """Limpa os campos de entrada e resultados"""
    ESPES_ENTRY.delete(0, tk.END)
    RAIO_FINAL_ENTRY.delete(0, tk.END)
    ANG_FINAL_ENTRY.delete(0, tk.END)
    KS_LABEL.config(text="-")
    RAIO_INICIAL_LABEL.config(text="-")
    ANG_INICIAL_LABEL.config(text="-")
    
    # Limpar valores de Ks na tabela
    for item_id in LIST_PROP.get_children():
        LIST_PROP.set(item_id, 'ks', "-")

def main(root=None):
    """
    Função principal que inicializa e configura o formulário de cálculo de springback.
    """
    global SPRING_FORM, MATER_COMBO, ESPES_ENTRY, RAIO_FINAL_ENTRY, ANG_FINAL_ENTRY
    global KS_LABEL, RAIO_INICIAL_LABEL, ANG_INICIAL_LABEL, LIST_PROP
    
    # Criar janela principal se não for fornecida
    if root is None:
        root = tk.Tk()
        root.withdraw()
    
    # Verificar se a janela já está aberta
    if SPRING_FORM:
        SPRING_FORM.destroy()

    SPRING_FORM = tk.Toplevel(root)
    SPRING_FORM.title("Calculadora de Springback")
    SPRING_FORM.geometry("600x500")
    SPRING_FORM.resizable(False, False)

    no_topo(SPRING_FORM)
    posicionar_janela(SPRING_FORM, None)

    # Frame principal
    main_frame = tk.Frame(SPRING_FORM)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)
    main_frame.columnconfigure(0, weight=1)

    # Frame de entrada de dados
    frame_entrada = tk.LabelFrame(main_frame, text='Dados de Entrada', pady=5)
    frame_entrada.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    for i in range(2):
        frame_entrada.columnconfigure(i, weight=1)

    # Material
    tk.Label(frame_entrada, text="MATERIAL:").grid(row=0, column=0, padx=2, sticky='sw')
    MATER_COMBO = ttk.Combobox(frame_entrada, values=list(MATERIAIS.keys()))
    MATER_COMBO.grid(row=1, column=0, padx=5, sticky="ew")
    MATER_COMBO.current(0)  # AISI 304 como padrão

    # Espessura
    tk.Label(frame_entrada, text="ESPESSURA:").grid(row=0, column=1, padx=2, sticky='sw')
    ESPES_ENTRY = tk.Entry(frame_entrada)
    ESPES_ENTRY.grid(row=1, column=1, padx=5, sticky="ew")

    # Raio Final
    tk.Label(frame_entrada, text="RAIO FINAL (Rf):").grid(row=2, column=0, padx=2, sticky='sw')
    RAIO_FINAL_ENTRY = tk.Entry(frame_entrada)
    RAIO_FINAL_ENTRY.grid(row=3, column=0, padx=5, sticky="ew")

    # Ângulo Final
    tk.Label(frame_entrada, text="ÂNGULO FINAL (α2):").grid(row=2, column=1, padx=2, sticky='sw')
    ANG_FINAL_ENTRY = tk.Entry(frame_entrada)
    ANG_FINAL_ENTRY.grid(row=3, column=1, padx=5, sticky="ew")

    # Botões
    botoes_frame = tk.Frame(main_frame)
    botoes_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    botoes_frame.columnconfigure(0, weight=1)
    botoes_frame.columnconfigure(1, weight=1)

    tk.Button(botoes_frame, text="CALCULAR", bg="green", fg="white", 
              command=calcular_springback).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    tk.Button(botoes_frame, text="LIMPAR", bg="red", fg="white", 
              command=limpar_campos).grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Frame de resultados
    frame_resultados = tk.LabelFrame(main_frame, text='Resultados', pady=5)
    frame_resultados.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    for i in range(2):
        frame_resultados.columnconfigure(i, weight=1)

    # Ks
    tk.Label(frame_resultados, text="Ks:").grid(row=0, column=0, padx=2, sticky='sw')
    KS_LABEL = tk.Label(frame_resultados, text="-", relief="sunken", width=15, bg="#e6ffec")
    KS_LABEL.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    # Raio Inicial
    tk.Label(frame_resultados, text="RAIO INICIAL (Ri):").grid(row=1, column=0, padx=2, sticky='sw')
    RAIO_INICIAL_LABEL = tk.Label(frame_resultados, text="-", relief="sunken", width=15, bg="#e6ffec")
    RAIO_INICIAL_LABEL.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    # Ângulo Inicial
    tk.Label(frame_resultados, text="ÂNGULO INICIAL (α1):").grid(row=2, column=0, padx=2, sticky='sw')
    ANG_INICIAL_LABEL = tk.Label(frame_resultados, text="-", relief="sunken", width=15, bg="#e6ffec")
    ANG_INICIAL_LABEL.grid(row=2, column=1, padx=5, pady=5, sticky="w")

    # Tabela de propriedades
    frame_tabela = tk.LabelFrame(main_frame, text='Propriedades dos Materiais', pady=5)
    frame_tabela.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    # Criar tabela
    LIST_PROP = ttk.Treeview(frame_tabela, columns=("material", "Y", "E", "ks"), show="headings", height=7)
    LIST_PROP.pack(fill="both", expand=True)

    # Configurar colunas
    LIST_PROP.heading("material", text="MATERIAL")
    LIST_PROP.heading("Y", text="Y [N/mm²]")
    LIST_PROP.heading("E", text="E [N/mm²]")
    LIST_PROP.heading("ks", text="ks")
    
    LIST_PROP.column("material", width=100, anchor="center")
    LIST_PROP.column("Y", width=80, anchor="center")
    LIST_PROP.column("E", width=80, anchor="center")
    LIST_PROP.column("ks", width=80, anchor="center")

    # Preencher tabela com dados dos materiais
    for material, props in MATERIAIS.items():
        LIST_PROP.insert("", "end", values=(material, props["Y"], props["E"], "-"))

    # Rodapé com informações
    frame_info = tk.Frame(main_frame)
    frame_info.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
    
    tk.Label(frame_info, text="Y = Limite de escoamento [N/mm²]").pack(anchor="w")
    tk.Label(frame_info, text="E = Módulo de Elasticidade [N/mm²]").pack(anchor="w")
    tk.Label(frame_info, text="Ks = 1 - 3*(Y*Rf/E/T) + 4*(Y*Rf/E/T)^3").pack(anchor="w")
    
    # Referências
    frame_ref = tk.Frame(main_frame)
    frame_ref.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
    
    tk.Label(frame_ref, text="Fontes:", font=("Arial", 8, "bold")).pack(anchor="w")
    tk.Label(frame_ref, text="http://www.matweb.com/", font=("Arial", 8)).pack(anchor="w")
    tk.Label(frame_ref, text="https://steelselector.sij.si", font=("Arial", 8)).pack(anchor="w")
    tk.Label(frame_ref, text="http://li.mit.edu/Stuff/RHW/Upload/49.pdf SHEET METAL FORMING PROCESSES AND DIE DESIGN (pg. 64)", 
             font=("Arial", 8)).pack(anchor="w")

    SPRING_FORM.mainloop()

if __name__ == "__main__":
    main()
