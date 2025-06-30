"""
# Formulário de Impressão
# Este módulo contém a implementação do formulário de impressão em lote,
# que permite selecionar um diretório e uma lista de arquivos PDF para impressão.
# O formulário é construído usando a biblioteca tkinter e segue o padrão
# dos demais formulários do aplicativo.
"""
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from src.utils.janelas import (no_topo,
                               posicionar_janela,
                               habilitar_janelas,
                               desabilitar_janelas)
from src.utils.utilitarios import obter_caminho_icone
from src.config import globals as g


def imprimir_pdf(diretorio, lista_arquivos):
    """
    Imprime os PDFs usando diferentes métodos disponíveis.
    """
    try:
        arquivos_encontrados = []
        arquivos_nao_encontrados = []

        # Procurar pelos arquivos no diretório
        for arquivo in lista_arquivos:
            # Extrair a parte principal do nome (antes de " - ")
            nome_base = arquivo.split(' - ')[0].strip() if ' - ' in arquivo else arquivo

            # Buscar arquivos que contenham esse nome base
            pesquisa = [f for f in os.listdir(diretorio)
                        if nome_base.lower() in f.lower() and f.endswith('.pdf')]
            nome_do_arquivo = pesquisa[0] if pesquisa else None

            if pesquisa:
                arquivos_encontrados.append(nome_do_arquivo)
            else:
                arquivos_nao_encontrados.append(arquivo)

        # Mostrar resultado na interface
        resultado = ""
        if arquivos_encontrados:
            resultado += f"Arquivos encontrados ({len(arquivos_encontrados)}):\n"
            for arquivo in arquivos_encontrados:
                resultado += f"  • {arquivo}\n"

        if arquivos_nao_encontrados:
            resultado += f"\nArquivos não encontrados ({len(arquivos_nao_encontrados)}):\n"
            for arquivo in arquivos_nao_encontrados:
                resultado += f"  • {arquivo}\n"

        # Verificar se o widget existe antes de usar
        if hasattr(g, 'IMPRESSAO_RESULTADO_TEXT') and g.IMPRESSAO_RESULTADO_TEXT:
            g.IMPRESSAO_RESULTADO_TEXT.delete(1.0, tk.END)
            g.IMPRESSAO_RESULTADO_TEXT.insert(1.0, resultado)

        if arquivos_encontrados:
            resultado_impressao = "\n\nTentando imprimir arquivos...\n"

            # Tentar diferentes métodos de impressão
            for nome_arquivo in arquivos_encontrados:
                caminho_completo = f"{diretorio}\\{nome_arquivo}"
                sucesso = False

                # Método 1: Foxit PDF Reader
                foxit_path = (
                    "C:\\Program Files (x86)\\Foxit Software\\Foxit PDF Reader\\FoxitPDFReader.exe"
                )
                if os.path.exists(foxit_path):
                    try:
                        resultado_impressao += f"Imprimindo {nome_arquivo} com Foxit...\n"
                        subprocess.run([foxit_path, "/p", caminho_completo], check=True, timeout=30)
                        resultado_impressao += "  ✓ Sucesso com Foxit\n"
                        sucesso = True
                    except (subprocess.TimeoutExpired,
                            subprocess.CalledProcessError,
                            FileNotFoundError) as e:
                        resultado_impressao += f"  ✗ Erro com Foxit: {str(e)}\n"

                # Método 2: Imprimir usando Windows (startfile com print)
                if not sucesso:
                    try:
                        resultado_impressao += (
                            f"Imprimindo {nome_arquivo} com impressora padrão...\n"
                        )
                        os.startfile(caminho_completo, "print")
                        resultado_impressao += "  ✓ Sucesso com impressora padrão\n"
                        sucesso = True
                    except (OSError, PermissionError, FileNotFoundError) as e:
                        resultado_impressao += f"  ✗ Erro com impressora padrão: {str(e)}\n"

                # Método 3: Adobe Reader (se disponível)
                if not sucesso:
                    adobe_paths = [
                        "C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe",
                        "C:\\Program Files (x86)\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe",
                        "C:\\Program Files\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe"
                    ]

                    for adobe_path in adobe_paths:
                        if os.path.exists(adobe_path):
                            try:
                                resultado_impressao += f"Imprimindo {nome_arquivo} com Adobe...\n"
                                subprocess.run([adobe_path, "/p", caminho_completo],
                                               check=True, timeout=30)
                                resultado_impressao += "  ✓ Sucesso com Adobe\n"
                                sucesso = True
                                break
                            except (subprocess.TimeoutExpired,
                                    subprocess.CalledProcessError,
                                    FileNotFoundError) as e:
                                resultado_impressao += f"  ✗ Erro com Adobe: {str(e)}\n"

                if not sucesso:
                    resultado_impressao += f"  ✗ Falha ao imprimir {nome_arquivo}\n"

            # Atualizar o campo de resultado com os detalhes da impressão
            if hasattr(g, 'IMPRESSAO_RESULTADO_TEXT') and g.IMPRESSAO_RESULTADO_TEXT:
                g.IMPRESSAO_RESULTADO_TEXT.insert(tk.END, resultado_impressao)

            messagebox.showinfo(
                "Impressão",
                f"Processo de impressão iniciado para {len(arquivos_encontrados)} arquivo(s)!\n"
                "Verifique os detalhes no campo 'Resultado da Impressão'."
            )
        else:
            messagebox.showwarning("Aviso", "Nenhum arquivo foi encontrado para impressão.")

    except (OSError, PermissionError, FileNotFoundError, ValueError) as e:
        messagebox.showerror("Erro", f"Erro ao processar impressão: {str(e)}")


def selecionar_diretorio():
    """
    Abre o diálogo para seleção de diretório.
    """
    desabilitar_janelas()  # Desabilita ANTES de abrir o diálogo

    diretorio = filedialog.askdirectory(
        title="Selecionar Diretório dos PDFs", parent=g.IMPRESSAO_FORM)

    habilitar_janelas()  # Sempre habilita DEPOIS que o diálogo for fechado

    if diretorio:  # Se selecionou um diretório, atualiza o campo
        if hasattr(g, 'IMPRESSAO_DIRETORIO_ENTRY') and g.IMPRESSAO_DIRETORIO_ENTRY:
            g.IMPRESSAO_DIRETORIO_ENTRY.delete(0, tk.END)
            g.IMPRESSAO_DIRETORIO_ENTRY.insert(0, diretorio)
    else:
        habilitar_janelas()


def adicionar_arquivo():
    """
    Adiciona um arquivo à lista de arquivos para impressão.
    """
    if not (hasattr(g, 'IMPRESSAO_ARQUIVO_ENTRY') and g.IMPRESSAO_ARQUIVO_ENTRY):
        return

    arquivo = g.IMPRESSAO_ARQUIVO_ENTRY.get().strip()
    if arquivo and hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS:
        g.IMPRESSAO_LISTA_ARQUIVOS.insert(tk.END, arquivo)
        g.IMPRESSAO_ARQUIVO_ENTRY.delete(0, tk.END)


def adicionar_lista_arquivos():
    """
    Adiciona múltiplos arquivos à lista a partir do campo de texto.
    """
    if not (hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT):
        return

    texto = g.IMPRESSAO_LISTA_TEXT.get(1.0, tk.END).strip()
    if texto:
        # Divide o texto por quebras de linha e remove linhas vazias
        if texto and isinstance(texto, str):
            linhas = texto.split('\n')
        else:
            linhas = []  # ou trate o erro conforme necessário

        arquivos = [linha.strip() for linha in linhas if linha.strip()]

        # Adiciona cada arquivo à lista
        if hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS:
            for arquivo in arquivos:
                g.IMPRESSAO_LISTA_ARQUIVOS.insert(tk.END, arquivo)

        # Limpa o campo de texto
        g.IMPRESSAO_LISTA_TEXT.delete(1.0, tk.END)

        messagebox.showinfo("Sucesso", f"{len(arquivos)} arquivo(s) adicionado(s) à lista!")


def remover_arquivo():
    """
    Remove o arquivo selecionado da lista.
    """
    if not (hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS):
        return

    selection = g.IMPRESSAO_LISTA_ARQUIVOS.curselection()
    if selection:
        g.IMPRESSAO_LISTA_ARQUIVOS.delete(selection[0])


def limpar_lista():
    """
    Limpa toda a lista de arquivos.
    """
    if hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS:
        g.IMPRESSAO_LISTA_ARQUIVOS.delete(0, tk.END)


def executar_impressao():
    """
    Executa a impressão dos arquivos selecionados.
    """
    if not (hasattr(g, 'IMPRESSAO_DIRETORIO_ENTRY') and g.IMPRESSAO_DIRETORIO_ENTRY):
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    diretorio = g.IMPRESSAO_DIRETORIO_ENTRY.get().strip()
    if not diretorio:
        messagebox.showerror("Erro", "Por favor, selecione um diretório.")
        return

    if not os.path.exists(diretorio):
        messagebox.showerror("Erro", "O diretório selecionado não existe.")
        return

    if not (hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS):
        messagebox.showerror("Erro", "Interface não inicializada corretamente.")
        return

    lista_arquivos = list(g.IMPRESSAO_LISTA_ARQUIVOS.get(0, tk.END))
    if not lista_arquivos:
        messagebox.showerror("Erro", "Por favor, adicione pelo menos um arquivo à lista.")
        return

    imprimir_pdf(diretorio, lista_arquivos)


def configurar_janela(root):
    """
    Configura a janela principal do formulário de impressão.
    """
    if hasattr(g, 'IMPRESSAO_FORM') and g.IMPRESSAO_FORM:
        g.IMPRESSAO_FORM.destroy()

    g.IMPRESSAO_FORM = tk.Toplevel(root)
    g.IMPRESSAO_FORM.title("Impressão em Lote de PDFs")
    g.IMPRESSAO_FORM.geometry("500x420")
    g.IMPRESSAO_FORM.resizable(False, False)

    icone_path = obter_caminho_icone()
    g.IMPRESSAO_FORM.iconbitmap(icone_path)

    no_topo(g.IMPRESSAO_FORM)
    posicionar_janela(g.IMPRESSAO_FORM, None)


def criar_frame_diretorio(main_frame):
    """
    Cria o frame para seleção do diretório.
    """
    frame_diretorio = tk.LabelFrame(main_frame, text='Diretório dos PDFs', pady=2)
    frame_diretorio.grid(row=0, column=0, padx=3, pady=2, sticky="ew")

    frame_diretorio.columnconfigure(0, weight=1)

    g.IMPRESSAO_DIRETORIO_ENTRY = tk.Entry(frame_diretorio)
    g.IMPRESSAO_DIRETORIO_ENTRY.grid(row=0, column=0, padx=3, pady=3, sticky="ew")

    tk.Button(frame_diretorio,
              text="Procurar",
              command=selecionar_diretorio).grid(row=0, column=1, padx=3, pady=3)


def criar_frame_arquivos(main_frame):
    """
    Cria o frame para gerenciamento da lista de arquivos.
    """
    frame_arquivos = tk.LabelFrame(main_frame, text='Lista de Arquivos para Impressão', pady=2)
    frame_arquivos.grid(row=1, column=0, padx=3, pady=2, sticky="nsew")

    frame_arquivos.columnconfigure(0, weight=1)
    frame_arquivos.rowconfigure(0, weight=0)  # Label
    frame_arquivos.rowconfigure(1, weight=0)  # Campo de texto
    frame_arquivos.rowconfigure(2, weight=0)  # Entrada múltiplos
    frame_arquivos.rowconfigure(3, weight=1)  # Lista final

    # Frame para entrada de múltiplos arquivos
    frame_entrada_multiplos = tk.Frame(frame_arquivos)
    frame_entrada_multiplos.grid(row=2, column=0, sticky="ew", padx=3, pady=2)
    frame_entrada_multiplos.columnconfigure(0, weight=1)  # Campo de texto
    frame_entrada_multiplos.columnconfigure(1, weight=0)  # Botões
    frame_entrada_multiplos.rowconfigure(0, weight=0)     # Label
    frame_entrada_multiplos.rowconfigure(1, weight=1)     # Texto e botões

    tk.Label(frame_entrada_multiplos, text="Lista de arquivos (um por linha):",
             font=("Arial", 8, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

    # Frame para o campo de texto com scrollbar
    frame_text = tk.Frame(frame_entrada_multiplos)
    frame_text.grid(row=1, column=0, sticky="nsew", pady=(2, 0), padx=(0, 3))
    frame_text.columnconfigure(0, weight=1)
    frame_text.rowconfigure(0, weight=1)

    g.IMPRESSAO_LISTA_TEXT = tk.Text(frame_text, height=4, width=40, wrap=tk.WORD)
    g.IMPRESSAO_LISTA_TEXT.grid(row=0, column=0, sticky="nsew")

    scrollbar_text = tk.Scrollbar(frame_text, orient="vertical")
    scrollbar_text.grid(row=0, column=1, sticky="ns")
    g.IMPRESSAO_LISTA_TEXT.config(yscrollcommand=scrollbar_text.set)
    scrollbar_text.config(command=g.IMPRESSAO_LISTA_TEXT.yview)

    # Placeholder de exemplo
    placeholder_text = """Exemplo:
010464516
010464519"""
    g.IMPRESSAO_LISTA_TEXT.insert(1.0, placeholder_text)
    g.IMPRESSAO_LISTA_TEXT.config(fg="gray")

    def on_focus_in(event):
        if hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT:
            if g.IMPRESSAO_LISTA_TEXT.get(1.0, tk.END).strip() == placeholder_text:
                g.IMPRESSAO_LISTA_TEXT.delete(1.0, tk.END)
                g.IMPRESSAO_LISTA_TEXT.config(fg="black")

    def on_focus_out(event):
        if hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT:
            if not g.IMPRESSAO_LISTA_TEXT.get(1.0, tk.END).strip():
                g.IMPRESSAO_LISTA_TEXT.insert(1.0, placeholder_text)
                g.IMPRESSAO_LISTA_TEXT.config(fg="gray")

    def limpar_texto_placeholder():
        """Limpa o campo de texto e restaura o placeholder."""
        if hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT:
            g.IMPRESSAO_LISTA_TEXT.delete(1.0, tk.END)
            g.IMPRESSAO_LISTA_TEXT.insert(1.0, placeholder_text)
            g.IMPRESSAO_LISTA_TEXT.config(fg="gray")

    g.IMPRESSAO_LISTA_TEXT.bind("<FocusIn>", on_focus_in)
    g.IMPRESSAO_LISTA_TEXT.bind("<FocusOut>", on_focus_out)

    # Frame para botões ao lado do campo de texto
    frame_botoes_texto = tk.Frame(frame_entrada_multiplos)
    frame_botoes_texto.grid(row=1, column=1, sticky="ns", pady=(2, 0))

    # Botões para campo de múltiplos arquivos (verticais ao lado do texto)
    tk.Button(frame_botoes_texto,
              text="Adicionar",
              command=adicionar_lista_arquivos,
              bg="lightblue",
              width=10).grid(row=0, column=0, sticky="ew", pady=(0, 1))

    tk.Button(frame_botoes_texto,
              text="Limpar",
              width=10,
              bg="lightyellow",
              command=limpar_texto_placeholder).grid(row=1, column=0, sticky="ew", pady=(1, 0))

    # Frame para a lista final e botões de controle
    frame_lista = tk.Frame(frame_arquivos)
    frame_lista.grid(row=3, column=0, sticky="nsew", padx=3, pady=2)
    frame_lista.columnconfigure(0, weight=1)  # Lista
    frame_lista.columnconfigure(1, weight=0)  # Botões
    frame_lista.rowconfigure(0, weight=0)     # Label
    frame_lista.rowconfigure(1, weight=1)     # Lista e botões

    tk.Label(frame_lista, text="Arquivos na lista:", font=("Arial", 8, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))

    # Listbox com scrollbar
    frame_listbox = tk.Frame(frame_lista)
    frame_listbox.grid(row=1, column=0, sticky="nsew", pady=(0, 0), padx=(0, 3))
    frame_listbox.columnconfigure(0, weight=1)
    frame_listbox.rowconfigure(0, weight=1)

    g.IMPRESSAO_LISTA_ARQUIVOS = tk.Listbox(frame_listbox, height=6, width=40)
    g.IMPRESSAO_LISTA_ARQUIVOS.grid(row=0, column=0, sticky="nsew")

    scrollbar = tk.Scrollbar(frame_listbox, orient="vertical")
    scrollbar.grid(row=0, column=1, sticky="ns")
    g.IMPRESSAO_LISTA_ARQUIVOS.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=g.IMPRESSAO_LISTA_ARQUIVOS.yview)

    # Frame para botões ao lado da lista
    frame_botoes = tk.Frame(frame_lista)
    frame_botoes.grid(row=1, column=1, sticky="ns", pady=(0, 0))

    # Botões de controle da lista (verticais ao lado da lista)
    tk.Button(frame_botoes,
              text="Remover",
              width=10,
              bg="lightcoral",
              command=remover_arquivo).grid(row=0, column=0, sticky="ew", pady=(0, 1))

    tk.Button(frame_botoes,
              text="Limpar",
              width=10,
              bg="lightyellow",
              command=limpar_lista).grid(row=1, column=0, sticky="ew", pady=1)

    tk.Button(frame_botoes,
              text="Imprimir",
              width=10,
              command=executar_impressao,
              bg="lightgreen").grid(row=2, column=0, sticky="ew", pady=(1, 0))


def criar_frame_resultado(main_frame):
    """
    Cria o frame para exibir os resultados da impressão.
    """
    frame_resultado = tk.LabelFrame(main_frame, text='Resultado da Impressão', pady=2)
    frame_resultado.grid(row=2, column=0, padx=3, pady=2, sticky="ew")

    frame_resultado.columnconfigure(0, weight=1)

    g.IMPRESSAO_RESULTADO_TEXT = tk.Text(frame_resultado, height=5, wrap=tk.WORD)
    g.IMPRESSAO_RESULTADO_TEXT.grid(row=0, column=0, padx=3, pady=3, sticky="ew")

    scrollbar_resultado = tk.Scrollbar(frame_resultado, orient="vertical")
    scrollbar_resultado.grid(row=0, column=1, sticky="ns")
    g.IMPRESSAO_RESULTADO_TEXT.config(yscrollcommand=scrollbar_resultado.set)
    scrollbar_resultado.config(command=g.IMPRESSAO_RESULTADO_TEXT.yview)


def main(root):
    """
    Inicializa e exibe o formulário de impressão em lote.
    """
    configurar_janela(root)

    # Configurar o main frame com padding reduzido
    main_frame = tk.Frame(g.IMPRESSAO_FORM)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    main_frame.columnconfigure(0, weight=1)

    main_frame.rowconfigure(0, weight=0)  # Diretório - tamanho fixo
    main_frame.rowconfigure(1, weight=1)  # Lista de arquivos - expansível
    main_frame.rowconfigure(2, weight=0)  # Resultado - tamanho fixo

    criar_frame_diretorio(main_frame)
    criar_frame_arquivos(main_frame)
    criar_frame_resultado(main_frame)


if __name__ == "__main__":
    main(None)
