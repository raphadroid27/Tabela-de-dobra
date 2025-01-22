import tkinter as tk
from tkinter import ttk

import globals as g


def main():
    
    root = tk.Tk()
    root.title("Tabela de dobra")
    root.geometry('480x400')

    borda = 20
    espaço = 10
    app_width = 480
    comprimento_1_linha = (app_width - 2 * (borda + espaço))/3
    print(comprimento_1_linha)
    altura = 20

    y1 = borda
    y2 = espaço + altura + espaço
    y3 = espaço + (2 * altura) + espaço
    y4 = espaço + (3 * altura) + espaço

    x1 = borda
    x2 = borda + comprimento_1_linha + espaço
    x3 = borda + 2 * (comprimento_1_linha + espaço)


    tk.Label(root, text="Material:").place(x=x1, y=y1)

    g.material_combobox = ttk.Combobox()
    g.material_combobox.place(x=x1, y=y2, width=comprimento_1_linha, height=altura)

    tk.Label(root, text="Espessura:").place(x=x2, y=y1)

    g.espessura_combobox = ttk.Combobox()
    g.espessura_combobox.place(x=x2, y=y2, width=comprimento_1_linha, height=altura)

    tk.Label(root, text="Canal:").place(x=x3, y=y1)

    g.canal_combobox = ttk.Combobox()
    g.canal_combobox.place(x=x3, y=y2, width=comprimento_1_linha, height=altura)

    segunda_linha=tk.Frame(root, bg='black')
    segunda_linha.place(x=borda, y=y3+espaço, width=200, height=4*altura)

    segunda_linha.columnconfigure(0, weight=1)
    segunda_linha.columnconfigure(1, weight=1)
    segunda_linha.columnconfigure(2, weight=1)
    segunda_linha.columnconfigure(3, weight=1)

    tk.Label(segunda_linha, text="Raio interno:").grid(row=0, column=0)
    
    g.raio_interno_entry = tk.Entry(segunda_linha)
    g.raio_interno_entry.grid(row=1, column=0, )

    tk.Label(segunda_linha, text="Raio externo:").grid(row=0, column=1)

    raio_externo_entry = tk.Entry(segunda_linha)
    raio_externo_entry.grid(row=1, column=1)

    tk.Label(segunda_linha, text="Largura:").grid(row=0, column=2)

    largura_entry = tk.Entry(segunda_linha)
    largura_entry.grid(row=1, column=2)

    tk.Label(segunda_linha, text="Comprimento:").grid(row=0, column=3)
    
    comprimento_entry = tk.Entry(segunda_linha)
    comprimento_entry.grid(row=1, column=3)


    root.mainloop() 

if __name__ == "__main__":
    main()