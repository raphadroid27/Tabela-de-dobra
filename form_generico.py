import tkinter as tk
from tkinter import ttk
from funcoes import obter_configuracoes, limpar_busca, listar

def main(tipo, root):
    """
    Inicializa e exibe o formulário de gerenciamento de canais.
    Configura a interface gráfica para adicionar, editar e excluir canais.
    """
    configuracoes = obter_configuracoes()
    config = configuracoes[tipo]

    form_generico = tk.Tk(root)
    form_generico.title(f'Novo {tipo.capitalize()}')
    form_generico.geometry('340x400')
    form_generico.resizable(False, False)

    # Criação do frame de busca
    frame_busca = ttk.Labelframe(form_generico, text=f'Buscar {tipo.capitalize()}')
    frame_busca.pack(pady=5, padx=5, fill='x', expand=True)

    for i in range(3):
        frame_busca.columnconfigure(i, weight=1)

    label_busca = ttk.Label(frame_busca, text=f"{tipo.capitalize()}:")
    label_busca.grid(row=0, column=0, padx=2, sticky='sw')

    # Criar o campo de busca diretamente
    entry_busca = ttk.Entry(frame_busca, width=20)
    entry_busca.grid(row=0, column=1)
    config['busca'] = entry_busca  # Atualiza o campo de busca no dicionário

    limpar_busca_button = ttk.Button(frame_busca, text="Limpar", command=lambda: limpar_busca(tipo))
    limpar_busca_button.grid(row=0, column=2, padx=5, pady=5, sticky="e")

    frame_lista = tk.Frame(form_generico)
    frame_lista.pack(pady=5, padx=5, fill='both', expand=True)

    colunas = config['colunas']
    lista = ttk.Treeview(frame_lista, columns=colunas, show="headings")
    lista.grid(row=0, column=0, sticky='ew')
    config['lista'] = lista  # Atualiza a lista no dicionário
    for col in colunas:
        lista.heading(col, text=col)
        lista.column(col, anchor="center", width=60)
    
    listar(tipo)

    form_generico.mainloop()
    
if __name__ == "__main__":
    main('canal', None)