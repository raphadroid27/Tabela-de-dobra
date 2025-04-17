import tkinter as tk
from tkinter import ttk
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Canal, Material, Deducao, Espessura
from crud import item_selecionado, adicionar, atualizar, excluir
import globals as g
import re
from styles import configurar_estilos
from funcoes import atualizar_combobox

engine = create_engine('sqlite:///tabela_de_dobra.db')
session = sessionmaker(bind=engine)
session = session()

g.CONFIGURACOES = {
    'material': {
        'entradas': {
            'nome': 'MAT_NOME_ENTRY',
            'densidade': 'MAT_DENS_ENTRY',
            'escoamento': 'MAT_ESCO_ENTRY',
            'elasticidade': 'MAT_ELAS_ENTRY'
        },
        'busca': 'MAT_BUSCA_ENTRY',
        'modelo': Material,
        'ordem': Material.nome,
        'valores': lambda x: (x.id, x.nome, x.densidade, x.escoamento, x.elasticidade),
        'lista': 'MAT_LIST',
        'colunas': ['ID', 'Nome', 'Densidade', 'Escoamento', 'Elasticidade'],
        'campo_busca': Material.nome,
        'nomes_entradas': {
            'nome': 'Nome',
            'densidade': 'Densidade',
            'escoamento': 'Escoamento',
            'elasticidade': 'Elasticidade'
        }
    },
    'canal': {
        'entradas': {
            'valor': 'CANAL_VALOR_ENTRY',
            'largura': 'CANAL_LARGU_ENTRY',
            'altura': 'CANAL_ALTUR_ENTRY',
            'comprimento_total': 'CANAL_COMPR_ENTRY',
            'observacao': 'CANAL_OBSER_ENTRY'
        },
        'busca': 'CANAL_BUSCA_ENTRY',
        'modelo': Canal,
        'ordem': Canal.valor,
        'valores': lambda x: (x.id, x.valor, x.largura, x.altura, x.comprimento_total, x.observacao),
        'lista': 'CANAL_LIST',
        'colunas': ['ID', 'Valor', 'Largura', 'Altura', 'Comprimento Total', 'Observação'],
        'campo_busca': Canal.valor,
        'nomes_entradas': {
            'valor': 'Valor',
            'largura': 'Largura',
            'altura': 'Altura',
            'comprimento_total': 'Compr.',
            'observacao': 'Obs.'
        }
    },
    'espessura': {
        'entradas': {
            'valor': 'ESP_VALOR_ENTRY'
        },
        'busca': 'ESP_BUSCA_ENTRY',
        'modelo': Espessura,
        'ordem': Espessura.valor,
        'valores': lambda x: (x.id, x.valor),
        'lista': 'ESP_LIST',
        'colunas': ['ID', 'Valor'],
        'campo_busca': Espessura.valor,
        'nomes_entradas': {
            'valor': 'Valor'
        }
    },
    'dedução': {
        'entradas': {
            'valor': 'DED_VALOR_ENTRY',
            'observacao': 'DED_OBSER_ENTRY',
            'forca': 'DED_FORCA_ENTRY'
        },
        'busca': {
            'material': 'DED_MATER_COMB',
            'espessura': 'DED_ESPES_COMB',
            'canal': 'DED_CANAL_COMB'
        },
        'modelo': Deducao,
        'ordem': Deducao.id,
        'valores': lambda x: (x.id, x.material.nome, x.espessura.valor, x.canal.valor, x.valor, x.observacao),
        'lista': None,
        'colunas': ['ID', 'Material', 'Espessura', 'Canal', 'Valor', 'Observação'],
        'campo_busca': None,
        'nomes_entradas': {
            'valor': 'Valor',
            'observacao': 'Observação',
            'forca': 'Força'
        }
    }
}

def listar(tipo):
    '''
    Lista os itens do banco de dados na interface gráfica.
    '''

    config = g.CONFIGURACOES[tipo]

    if config['lista'] is None or not config['lista'].winfo_exists():
        return

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    itens = session.query(config['modelo']).order_by(config['ordem']).all()

    if tipo == 'canal':
        itens = sorted(itens, key=lambda x: float(re.findall(r'\d+\.?\d*', x.valor)[0]))

    for item in itens:
        if tipo == 'dedução':
            if item.material is None or item.espessura is None or item.canal is None:
                continue
        config['lista'].insert("", "end", values=config['valores'](item))

def buscar(tipo):
    '''
    Realiza a busca de itens no banco de dados com base nos critérios especificados.
    '''
    config = g.CONFIGURACOES[tipo]

    if config['lista'] is None or not config['lista'].winfo_exists():
        return

    item = config['busca'].get().replace(',', '.') if config['busca'] else ""
    itens = session.query(config['modelo']).filter(config['campo_busca'].like(f"{item}%"))

    for item in config['lista'].get_children():
        config['lista'].delete(item)

    for item in itens:
        config['lista'].insert("", "end", values=config['valores'](item))

def limpar_busca(tipo):
    '''
    Limpa os campos de busca e atualiza a lista correspondente.
    '''
    config = g.CONFIGURACOES[tipo]

    config['busca'].delete(0, tk.END)

    listar(tipo)

def limpar_campos(tipo):
    '''
    Limpa os campos de entrada na aba correspondente ao tipo especificado.
    Os tipos disponíveis são:
    - dedução
    - espessura
    - material
    - canal
    '''
    config = g.CONFIGURACOES[tipo]

    for entry in config['campos'].values():
        entry.delete(0, tk.END)

def preencher_campos(tipo):
    '''
    Preenche os campos de entrada com os dados do item selecionado na lista.
    '''
    config = g.CONFIGURACOES[tipo]

    obj = item_selecionado(tipo)

    if obj:
        for campo, entry in config['entradas'].items():
            entry.delete(0, tk.END)
            if getattr(obj, campo) is not None:
                entry.insert(0, getattr(obj, campo))
            else:
                entry.insert(0, '')

def form_gen(acao,tipo, root):
    """
    Inicializa e exibe o formulário de gerenciamento de canais.
    Configura a interface gráfica para adicionar, editar e excluir canais.
    """


    config = g.CONFIGURACOES[tipo]

    form_generico = tk.Toplevel(root)
    form_generico.geometry('340x420')
    form_generico.resizable(False, False)

    main_frame = tk.Frame(form_generico)
    main_frame.pack(pady=5, padx=5, fill='both', expand=True)

    main_frame.columnconfigure(0, weight=1)
    for i in range(4):
        main_frame.rowconfigure(i, weight=1 if i == 1 else 0)

    # Criação do frame de busca
    frame_busca = ttk.Labelframe(main_frame, text=f'Buscar {tipo.capitalize()}')
    frame_busca.grid(row=0, column=0, ipadx=5, ipady=5, sticky='ew')

    # Criar o campo de busca diretamente
    if tipo == 'dedução':
        atualizar_combobox('material')
        atualizar_combobox('espessura')
        atualizar_combobox('canal')
        form_generico.geometry('500x420')
        row = 1
        col = 3
        for i in range(4):
            frame_busca.columnconfigure(i, weight=1)

        for idx, (texto, _) in enumerate(config['busca'].items()):
            ttk.Label(frame_busca, text=f"{texto.capitalize()}:").grid(row=0, column=idx, padx=2, sticky='sw')
            combobox = ttk.Combobox(frame_busca,width=20)
            combobox.grid(row=1, column=idx, padx=5, sticky="ew")
            combobox.bind("<<ComboboxSelected>>", lambda event, t='dedução': buscar(t))
            config['busca'][texto] = combobox

    else:
        row = 0
        col = 2
        for i in range(3):
            frame_busca.columnconfigure(i, weight=1 if i == 1 else 0)

        label_busca = ttk.Label(frame_busca, text=f"{tipo.capitalize()}:", anchor="w")
        label_busca.grid(row=0, column=0, padx=2, sticky='ew')
        entry_busca = ttk.Entry(frame_busca)
        entry_busca.grid(row=0, column=1, padx=2, sticky='ew')
        config['busca'] = entry_busca  # Atualiza o campo de busca no dicionário
        entry_busca.bind("<KeyRelease>", lambda event: buscar(tipo))

    limpar_busca_button = ttk.Button(frame_busca, text="Limpar", command=lambda: limpar_busca(tipo))
    limpar_busca_button.grid(row=row, column=col, padx=2, sticky="e")

    frame_lista = tk.Frame(main_frame)
    frame_lista.grid(row=1, column=0, ipadx=5, ipady=5, sticky='ew')

    colunas = config['colunas'][1:]  # Remove a primeira coluna "ID"
    lista = ttk.Treeview(frame_lista, columns=colunas, show="headings")
    config['lista'] = lista  # Atualiza a lista no dicionário
    for col in colunas:
        lista.heading(col, text=col)
        lista.column(col, anchor="center",width=65)
    lista.grid(row=0, column=0, sticky='ew')
    
    listar(tipo)

    frame_campos = ttk.Labelframe(main_frame, text=f'Cadastro de {tipo.capitalize()}')
    frame_campos.grid(row=2, column=0, ipadx=5, ipady=5, sticky='ew')

    for idx in range(len(config['entradas'])):
        frame_campos.columnconfigure(idx, weight=1)

    for idx, (campo, _) in enumerate(config['entradas'].items()):
        labels = ttk.Label(frame_campos, text=config['nomes_entradas'][campo] + ":", width=10)
        labels.grid(row=0, column=idx, padx=2, sticky='sw')
        campos_entry = ttk.Entry(frame_campos, width=10)
        campos_entry.grid(row=1, column=idx, padx=2, sticky='ew')
        config['entradas'][campo] = campos_entry
        globals()[config['entradas'][campo]] = campos_entry  # Torna acessível globalmente

    # Botões de ação
    frame_botoes = tk.Frame(main_frame)
    frame_botoes.grid(row=3, column=0, ipadx=5, ipady=5, sticky='ew')

    frame_botoes.columnconfigure(0, weight=1)
    frame_botoes.columnconfigure(1, weight=1)

    if acao == 'editar':
        form_generico.title(f'Editar {tipo.capitalize()}')
        lista.bind("<ButtonRelease-1>", lambda event: preencher_campos(tipo))
        botao_atualizar = ttk.Button(frame_botoes, text="Atualizar", command=lambda: (atualizar(tipo), listar(tipo), buscar(tipo)))
        botao_atualizar.grid(row=0, column=0, padx=5, pady=5, sticky='ew')

        botao_excluir = ttk.Button(frame_botoes, text="Excluir", command=lambda: (excluir(tipo), listar(tipo)))
        botao_excluir.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    
    if acao == 'adicionar':
        form_generico.title(f'Novo {tipo.capitalize()}')
        botao_adicionar = ttk.Button(frame_botoes, text="Adicionar", command=lambda: (adicionar(tipo), listar(tipo)))
        botao_adicionar.grid(row=0, column=0, padx=5, pady=5, sticky='ew',columnspan=2)

    form_generico.mainloop()
    
if __name__ == "__main__":
    form_gen()