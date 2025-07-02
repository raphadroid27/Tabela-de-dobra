"""
# Formulário de Impressão
# Este módulo contém a implementação do formulário de impressão em lote,
# que permite selecionar um diretório e uma lista de arquivos PDF para impressão.
# O formulário é construído usando a biblioteca PySide6 e segue o padrão
# dos demais formulários do aplicativo.
"""
import os
import subprocess
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QListWidget, QFrame, 
                               QGroupBox, QScrollArea, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utils.janelas import (aplicar_no_topo,
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
            g.IMPRESSAO_RESULTADO_TEXT.clear()
            g.IMPRESSAO_RESULTADO_TEXT.setText(resultado)

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
                current_text = g.IMPRESSAO_RESULTADO_TEXT.toPlainText()
                g.IMPRESSAO_RESULTADO_TEXT.setText(current_text + resultado_impressao)

            QMessageBox.information(
                g.IMPRESSAO_FORM,
                "Impressão",
                f"Processo de impressão iniciado para {len(arquivos_encontrados)} arquivo(s)!\n"
                "Verifique os detalhes no campo 'Resultado da Impressão'."
            )
        else:
            QMessageBox.warning(g.IMPRESSAO_FORM, "Aviso", "Nenhum arquivo foi encontrado para impressão.")

    except (OSError, PermissionError, FileNotFoundError, ValueError) as e:
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", f"Erro ao processar impressão: {str(e)}")


def selecionar_diretorio():
    """
    Abre o diálogo para seleção de diretório.
    """
    desabilitar_janelas()  # Desabilita ANTES de abrir o diálogo

    diretorio = QFileDialog.getExistingDirectory(
        g.IMPRESSAO_FORM, "Selecionar Diretório dos PDFs")

    habilitar_janelas()  # Sempre habilita DEPOIS que o diálogo for fechado

    if diretorio:  # Se selecionou um diretório, atualiza o campo
        if hasattr(g, 'IMPRESSAO_DIRETORIO_ENTRY') and g.IMPRESSAO_DIRETORIO_ENTRY:
            g.IMPRESSAO_DIRETORIO_ENTRY.clear()
            g.IMPRESSAO_DIRETORIO_ENTRY.setText(diretorio)
    else:
        habilitar_janelas()


def adicionar_arquivo():
    """
    Adiciona um arquivo à lista de arquivos para impressão.
    """
    if not (hasattr(g, 'IMPRESSAO_ARQUIVO_ENTRY') and g.IMPRESSAO_ARQUIVO_ENTRY):
        return

    arquivo = g.IMPRESSAO_ARQUIVO_ENTRY.text().strip()
    if arquivo and hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS:
        g.IMPRESSAO_LISTA_ARQUIVOS.addItem(arquivo)
        g.IMPRESSAO_ARQUIVO_ENTRY.clear()


def adicionar_lista_arquivos():
    """
    Adiciona múltiplos arquivos à lista a partir do campo de texto.
    """
    if not (hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT):
        return

    texto = g.IMPRESSAO_LISTA_TEXT.toPlainText().strip()
    if texto:
        # Divide o texto por quebras de linha e remove linhas vazias
        if texto and isinstance(texto, str):
            linhas = texto.split('\n')
        else:
            linhas = []  # ou trate o erro conforme necessário

        # Filtrar linhas que não são placeholder
        placeholder_text = "Exemplo:\n010464516\n010464519"
        if texto != placeholder_text:
            arquivos = [linha.strip() for linha in linhas if linha.strip() and not linha.startswith("Exemplo:")]

            # Adiciona cada arquivo à lista
            if hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS and arquivos:
                for arquivo in arquivos:
                    g.IMPRESSAO_LISTA_ARQUIVOS.addItem(arquivo)

                # Limpa o campo de texto
                g.IMPRESSAO_LISTA_TEXT.clear()

                QMessageBox.information(g.IMPRESSAO_FORM, "Sucesso", f"{len(arquivos)} arquivo(s) adicionado(s) à lista!")


def remover_arquivo():
    """
    Remove o arquivo selecionado da lista.
    """
    if not (hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS):
        return

    current_row = g.IMPRESSAO_LISTA_ARQUIVOS.currentRow()
    if current_row >= 0:
        g.IMPRESSAO_LISTA_ARQUIVOS.takeItem(current_row)


def limpar_lista():
    """
    Limpa toda a lista de arquivos.
    """
    if hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS:
        g.IMPRESSAO_LISTA_ARQUIVOS.clear()


def limpar_texto_placeholder():
    """Limpa o campo de texto e restaura o placeholder."""
    if hasattr(g, 'IMPRESSAO_LISTA_TEXT') and g.IMPRESSAO_LISTA_TEXT:
        placeholder_text = "Exemplo:\n010464516\n010464519"
        g.IMPRESSAO_LISTA_TEXT.clear()
        g.IMPRESSAO_LISTA_TEXT.setPlainText(placeholder_text)


def executar_impressao():
    """
    Executa a impressão dos arquivos selecionados.
    """
    if not (hasattr(g, 'IMPRESSAO_DIRETORIO_ENTRY') and g.IMPRESSAO_DIRETORIO_ENTRY):
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", "Interface não inicializada corretamente.")
        return

    diretorio = g.IMPRESSAO_DIRETORIO_ENTRY.text().strip()
    if not diretorio:
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", "Por favor, selecione um diretório.")
        return

    if not os.path.exists(diretorio):
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", "O diretório selecionado não existe.")
        return

    if not (hasattr(g, 'IMPRESSAO_LISTA_ARQUIVOS') and g.IMPRESSAO_LISTA_ARQUIVOS):
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", "Interface não inicializada corretamente.")
        return

    lista_arquivos = []
    for i in range(g.IMPRESSAO_LISTA_ARQUIVOS.count()):
        lista_arquivos.append(g.IMPRESSAO_LISTA_ARQUIVOS.item(i).text())
        
    if not lista_arquivos:
        QMessageBox.critical(g.IMPRESSAO_FORM, "Erro", "Por favor, adicione pelo menos um arquivo à lista.")
        return

    imprimir_pdf(diretorio, lista_arquivos)


def main(root):
    """
    Inicializa e exibe o formulário de impressão em lote.
    """
    if hasattr(g, 'IMPRESSAO_FORM') and g.IMPRESSAO_FORM:
        g.IMPRESSAO_FORM.close()

    g.IMPRESSAO_FORM = QDialog(root)
    g.IMPRESSAO_FORM.setWindowTitle("Impressão em Lote de PDFs")
    g.IMPRESSAO_FORM.setFixedSize(500, 420)

    icone_path = obter_caminho_icone()
    g.IMPRESSAO_FORM.setWindowIcon(QIcon(icone_path))

    aplicar_no_topo(g.IMPRESSAO_FORM)
    posicionar_janela(g.IMPRESSAO_FORM, None)

    # Layout principal
    main_layout = QVBoxLayout()
    g.IMPRESSAO_FORM.setLayout(main_layout)

    # Frame do diretório
    frame_diretorio = QGroupBox('Diretório dos PDFs')
    dir_layout = QHBoxLayout()
    frame_diretorio.setLayout(dir_layout)

    g.IMPRESSAO_DIRETORIO_ENTRY = QLineEdit()
    dir_layout.addWidget(g.IMPRESSAO_DIRETORIO_ENTRY)

    procurar_btn = QPushButton("📁 Procurar")
    procurar_btn.setStyleSheet("""
        QPushButton {
            background-color: #9e9e9e;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #757575;
        }
        QPushButton:pressed {
            background-color: #616161;
        }
    """)
    procurar_btn.clicked.connect(selecionar_diretorio)
    dir_layout.addWidget(procurar_btn)

    main_layout.addWidget(frame_diretorio)

    # Frame dos arquivos
    frame_arquivos = QGroupBox('Lista de Arquivos para Impressão')
    arquivos_layout = QVBoxLayout()
    frame_arquivos.setLayout(arquivos_layout)

    # Campo de texto para múltiplos arquivos
    lista_label = QLabel("Lista de arquivos (um por linha):")
    lista_label.setStyleSheet("font-weight: bold; font-size: 8pt;")
    arquivos_layout.addWidget(lista_label)

    # Layout horizontal para texto e botões
    text_layout = QHBoxLayout()
    
    g.IMPRESSAO_LISTA_TEXT = QTextEdit()
    g.IMPRESSAO_LISTA_TEXT.setMaximumHeight(100)
    placeholder_text = "Exemplo:\n010464516\n010464519"
    g.IMPRESSAO_LISTA_TEXT.setPlainText(placeholder_text)
    text_layout.addWidget(g.IMPRESSAO_LISTA_TEXT)

    # Botões ao lado do texto
    text_buttons_layout = QVBoxLayout()
    
    adicionar_btn = QPushButton("➕ Adicionar")
    adicionar_btn.setStyleSheet("""
        QPushButton {
            background-color: #2196f3;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #1976d2;
        }
        QPushButton:pressed {
            background-color: #1565c0;
        }
    """)
    adicionar_btn.clicked.connect(adicionar_lista_arquivos)
    text_buttons_layout.addWidget(adicionar_btn)

    limpar_text_btn = QPushButton("🧹 Limpar")
    limpar_text_btn.setStyleSheet("""
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """)
    limpar_text_btn.clicked.connect(limpar_texto_placeholder)
    text_buttons_layout.addWidget(limpar_text_btn)

    text_layout.addLayout(text_buttons_layout)
    arquivos_layout.addLayout(text_layout)

    # Lista de arquivos
    lista_arquivos_label = QLabel("Arquivos na lista:")
    lista_arquivos_label.setStyleSheet("font-weight: bold; font-size: 8pt;")
    arquivos_layout.addWidget(lista_arquivos_label)

    # Layout horizontal para lista e botões
    lista_layout = QHBoxLayout()

    g.IMPRESSAO_LISTA_ARQUIVOS = QListWidget()
    g.IMPRESSAO_LISTA_ARQUIVOS.setMaximumHeight(120)
    lista_layout.addWidget(g.IMPRESSAO_LISTA_ARQUIVOS)

    # Botões ao lado da lista
    lista_buttons_layout = QVBoxLayout()

    remover_btn = QPushButton("🗑️ Remover")
    remover_btn.setStyleSheet("""
        QPushButton {
            background-color: #ff6b6b;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ff5252;
        }
        QPushButton:pressed {
            background-color: #e53935;
        }
    """)
    remover_btn.clicked.connect(remover_arquivo)
    lista_buttons_layout.addWidget(remover_btn)

    limpar_lista_btn = QPushButton("🧹 Limpar")
    limpar_lista_btn.setStyleSheet("""
        QPushButton {
            background-color: #ffd93d;
            color: #333;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #ffcc02;
        }
        QPushButton:pressed {
            background-color: #e6b800;
        }
    """)
    limpar_lista_btn.clicked.connect(limpar_lista)
    lista_buttons_layout.addWidget(limpar_lista_btn)

    imprimir_btn = QPushButton("🖨️ Imprimir")
    imprimir_btn.setStyleSheet("""
        QPushButton {
            background-color: #4caf50;
            color: white;
            border: none;
            padding: 4px 8px;
            font-weight: bold;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
    """)
    imprimir_btn.clicked.connect(executar_impressao)
    lista_buttons_layout.addWidget(imprimir_btn)

    lista_layout.addLayout(lista_buttons_layout)
    arquivos_layout.addLayout(lista_layout)

    main_layout.addWidget(frame_arquivos)

    # Frame do resultado
    frame_resultado = QGroupBox('Resultado da Impressão')
    resultado_layout = QVBoxLayout()
    frame_resultado.setLayout(resultado_layout)

    g.IMPRESSAO_RESULTADO_TEXT = QTextEdit()
    g.IMPRESSAO_RESULTADO_TEXT.setMaximumHeight(100)
    resultado_layout.addWidget(g.IMPRESSAO_RESULTADO_TEXT)

    main_layout.addWidget(frame_resultado)


if __name__ == "__main__":
    main(None)
