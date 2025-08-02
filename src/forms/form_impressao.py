"""
Formulário de Impressão com QGridLayout

Este módulo contém a implementação do formulário de impressão em lote,
que permite selecionar um diretório e uma lista de arquivos PDF para impressão.
O formulário é construído usando QGridLayout para melhor organização e controle.
"""

import os
import subprocess
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.config import globals as g
from src.utils.estilo import aplicar_estilo_botao, obter_tema_atual
from src.utils.janelas import (
    aplicar_no_topo,
    desabilitar_janelas,
    habilitar_janelas,
    posicionar_janela,
)
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# Constantes para configuração
TIMEOUT_IMPRESSAO = 30
ALTURA_FORM_IMPRESSAO = 500
LARGURA_FORM_IMPRESSAO = 500
MARGEM_LAYOUT_PRINCIPAL = 10
ALTURA_MAXIMA_LISTA = 100
ALTURA_MAXIMA_LISTA_WIDGET = 120

# Métodos de impressão em ordem de prioridade
METODOS_IMPRESSAO = ["foxit", "impressora_padrao", "adobe"]

# Strings de interface
STYLE_LABEL_BOLD = "font-weight: bold; font-size: 10pt;"
PLACEHOLDER_LISTA_ARQUIVOS = (
    "Digite os nomes dos arquivos, um por linha.\nExemplo:\n010464516\n010464519"
)

# Caminhos dos programas PDF
FOXIT_PATH = (
    "C:\\Program Files (x86)\\Foxit Software\\Foxit PDF Reader\\FoxitPDFReader.exe"
)
ADOBE_PATHS = [
    "C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe",
    "C:\\Program Files (x86)\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe",
    "C:\\Program Files\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe",
]


class PrintManager:
    """Gerencia as operações de impressão de PDFs."""

    def __init__(self):
        self.arquivos_encontrados: List[str] = []
        self.arquivos_nao_encontrados: List[str] = []
        self.resultado_impressao: str = ""

    def _validar_metodos_disponiveis(self) -> List[str]:
        """Valida quais métodos de impressão estão disponíveis."""
        metodos_disponiveis = []

        # Verificar Foxit
        if os.path.exists(FOXIT_PATH):
            metodos_disponiveis.append("foxit")

        # Verificar impressora padrão (Windows)
        if hasattr(os, "startfile"):
            metodos_disponiveis.append("impressora_padrao")

        # Verificar Adobe
        for adobe_path in ADOBE_PATHS:
            if os.path.exists(adobe_path):
                metodos_disponiveis.append("adobe")
                break

        return metodos_disponiveis

    def buscar_arquivos(self, diretorio: str, lista_arquivos: List[str]) -> None:
        """Busca os arquivos no diretório especificado."""
        self.arquivos_encontrados.clear()
        self.arquivos_nao_encontrados.clear()

        for arquivo in lista_arquivos:
            nome_base = self._extrair_nome_base(arquivo)
            arquivo_encontrado = self._procurar_arquivo(diretorio, nome_base)

            if arquivo_encontrado:
                self.arquivos_encontrados.append(arquivo_encontrado)
            else:
                self.arquivos_nao_encontrados.append(arquivo)

    def _extrair_nome_base(self, arquivo):
        """Extrai a parte principal do nome do arquivo."""
        if not arquivo or not isinstance(arquivo, str):
            return ""
        return arquivo.split(" - ")[0].strip() if " - " in arquivo else arquivo.strip()

    def _procurar_arquivo(self, diretorio, nome_base):
        """Procura um arquivo específico no diretório."""
        if not diretorio or not nome_base:
            return None

        try:
            # Normalizar o caminho para evitar problemas de segurança
            diretorio = os.path.normpath(diretorio)

            # Verificar se o diretório existe
            if not os.path.exists(diretorio) or not os.path.isdir(diretorio):
                return None

            arquivos_pdf = [
                f
                for f in os.listdir(diretorio)
                if nome_base.lower() in f.lower() and f.lower().endswith(".pdf")
            ]
            return arquivos_pdf[0] if arquivos_pdf else None
        except (OSError, PermissionError, ValueError):
            return None

    def gerar_relatorio_busca(self) -> str:
        """Gera relatório dos arquivos encontrados e não encontrados."""
        resultado = ""

        if self.arquivos_encontrados:
            resultado += f"Arquivos encontrados ({len(self.arquivos_encontrados)}):\n"
            for arquivo in self.arquivos_encontrados:
                resultado += f" • {arquivo}\n"

        if self.arquivos_nao_encontrados:
            resultado += (
                f"\nArquivos não encontrados ({len(self.arquivos_nao_encontrados)}):\n"
            )
            for arquivo in self.arquivos_nao_encontrados:
                resultado += f" • {arquivo}\n"

        return resultado

    def executar_impressao(self, diretorio: str) -> str:
        """Executa a impressão dos arquivos encontrados."""
        if not self.arquivos_encontrados:
            return "Nenhum arquivo foi encontrado para impressão."

        self.resultado_impressao = "\n\nTentando imprimir arquivos...\n"

        for nome_arquivo in self.arquivos_encontrados:
            caminho_completo = os.path.join(diretorio, nome_arquivo)
            self._imprimir_arquivo_individual(nome_arquivo, caminho_completo)

        return self.resultado_impressao

    def _imprimir_arquivo_individual(self, nome_arquivo: str, caminho_completo: str) -> None:
        """Imprime um arquivo individual usando diferentes métodos."""
        sucesso = False

        for metodo in METODOS_IMPRESSAO:
            if metodo == "foxit":
                sucesso = self._tentar_foxit(nome_arquivo, caminho_completo)
            elif metodo == "impressora_padrao":
                sucesso = self._tentar_impressora_padrao(nome_arquivo, caminho_completo)
            elif metodo == "adobe":
                sucesso = self._tentar_adobe(nome_arquivo, caminho_completo)

            if sucesso:
                break

        if not sucesso:
            self.resultado_impressao += f" ✗ Falha ao imprimir {nome_arquivo}\n"

    def _tentar_foxit(self, nome_arquivo: str, caminho_completo: str) -> bool:
        """Tenta imprimir usando Foxit PDF Reader."""
        if not os.path.exists(FOXIT_PATH):
            return False

        # Validar se o arquivo existe antes de tentar imprimir
        if not os.path.exists(caminho_completo):
            self.resultado_impressao += f" ✗ Arquivo não encontrado: {caminho_completo}\n"
            return False

        try:
            self.resultado_impressao += f"Imprimindo {nome_arquivo} com Foxit...\n"
            subprocess.run(
                [FOXIT_PATH, "/p", caminho_completo],
                check=True,
                timeout=TIMEOUT_IMPRESSAO,
                shell=False,  # Explicitamente desabilitar shell para segurança
            )
            self.resultado_impressao += " ✓ Sucesso com Foxit\n"
            return True
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            self.resultado_impressao += f" ✗ Erro com Foxit: {str(e)}\n"
            return False

    def _tentar_impressora_padrao(self, nome_arquivo: str, caminho_completo: str) -> bool:
        """Tenta imprimir usando a impressora padrão do Windows."""
        try:
            self.resultado_impressao += (
                f"Imprimindo {nome_arquivo} com impressora padrão...\n"
            )

            # Verificar se startfile está disponível (Windows)
            if hasattr(os, "startfile"):
                os.startfile(caminho_completo, "print")
                self.resultado_impressao += " ✓ Sucesso com impressora padrão\n"
                return True

            self.resultado_impressao += " ✗ startfile não disponível nesta plataforma\n"
            return False
        except (OSError, PermissionError, FileNotFoundError) as e:
            self.resultado_impressao += f" ✗ Erro com impressora padrão: {str(e)}\n"
            return False

    def _tentar_adobe(self, nome_arquivo: str, caminho_completo: str) -> bool:
        """Tenta imprimir usando Adobe Reader."""
        # Validar se o arquivo existe antes de tentar imprimir
        if not os.path.exists(caminho_completo):
            self.resultado_impressao += f" ✗ Arquivo não encontrado: {caminho_completo}\n"
            return False

        for adobe_path in ADOBE_PATHS:
            if os.path.exists(adobe_path):
                try:
                    self.resultado_impressao += (
                        f"Imprimindo {nome_arquivo} com Adobe...\n"
                    )
                    subprocess.run(
                        [adobe_path, "/p", caminho_completo],
                        check=True,
                        timeout=TIMEOUT_IMPRESSAO,
                        shell=False,  # Explicitamente desabilitar shell para segurança
                    )
                    self.resultado_impressao += " ✓ Sucesso com Adobe\n"
                    return True
                except (
                    subprocess.TimeoutExpired,
                    subprocess.CalledProcessError,
                    FileNotFoundError,
                ) as e:
                    self.resultado_impressao += f" ✗ Erro com Adobe: {str(e)}\n"

        return False


def imprimir_pdf(diretorio: str, lista_arquivos: List[str]) -> None:
    """Imprime os PDFs usando diferentes métodos disponíveis."""
    try:
        print_manager = PrintManager()
        print_manager.buscar_arquivos(diretorio, lista_arquivos)

        # Mostrar resultado da busca
        resultado_busca = print_manager.gerar_relatorio_busca()
        _atualizar_resultado_interface(resultado_busca)

        if print_manager.arquivos_encontrados:
            resultado_impressao = print_manager.executar_impressao(diretorio)
            _atualizar_resultado_interface(resultado_busca + resultado_impressao)
            _mostrar_sucesso_impressao(len(print_manager.arquivos_encontrados))
        else:
            _mostrar_aviso_sem_arquivos()

    except (OSError, PermissionError, FileNotFoundError, ValueError) as e:
        _mostrar_erro_impressao(str(e))


def _atualizar_resultado_interface(texto):
    """Atualiza o campo de resultado na interface."""
    if hasattr(g, "IMPRESSAO_RESULTADO_TEXT") and g.IMPRESSAO_RESULTADO_TEXT:
        g.IMPRESSAO_RESULTADO_TEXT.clear()
        g.IMPRESSAO_RESULTADO_TEXT.setText(texto)


def _mostrar_sucesso_impressao(num_arquivos):
    """Mostra mensagem de sucesso da impressão."""
    QMessageBox.information(
        g.IMPRESSAO_FORM,
        "Impressão",
        f"Processo de impressão iniciado para {num_arquivos} arquivo(s)!\n"
        "Verifique os detalhes no campo 'Resultado da Impressão'.",
    )


def _mostrar_aviso_sem_arquivos():
    """Mostra aviso quando nenhum arquivo é encontrado."""
    QMessageBox.warning(
        g.IMPRESSAO_FORM, "Aviso", "Nenhum arquivo foi encontrado para impressão."
    )


def _mostrar_erro_impressao(erro):
    """Mostra erro durante a impressão."""
    QMessageBox.critical(
        g.IMPRESSAO_FORM, "Erro", f"Erro ao processar impressão: {erro}"
    )


def selecionar_diretorio():
    """Abre o diálogo para seleção de diretório."""
    try:
        if callable(desabilitar_janelas):
            desabilitar_janelas()

        diretorio = QFileDialog.getExistingDirectory(
            g.IMPRESSAO_FORM, "Selecionar Diretório dos PDFs"
        )

        if diretorio and _validar_interface_entry():
            g.IMPRESSAO_DIRETORIO_ENTRY.clear()
            g.IMPRESSAO_DIRETORIO_ENTRY.setText(diretorio)

    finally:
        if callable(habilitar_janelas):
            habilitar_janelas()


def _validar_interface_entry():
    """Valida se o campo de diretório está disponível."""
    return (hasattr(g, "IMPRESSAO_DIRETORIO_ENTRY")
            and g.IMPRESSAO_DIRETORIO_ENTRY is not None)


# Função adicionar_arquivo() removida - não utilizada no projeto


def adicionar_lista_arquivos():
    """Adiciona múltiplos arquivos à lista a partir do campo de texto."""
    if not (hasattr(g, "IMPRESSAO_LISTA_TEXT") and g.IMPRESSAO_LISTA_TEXT):
        return

    texto = g.IMPRESSAO_LISTA_TEXT.toPlainText().strip()
    if not texto:
        return

    arquivos = _processar_texto_arquivos(texto)
    _adicionar_arquivos_a_lista(arquivos)


def _processar_texto_arquivos(texto: str) -> List[str]:
    """Processa o texto e retorna lista de arquivos."""
    if not texto or not isinstance(texto, str):
        return []

    linhas = texto.split("\n")
    return [linha.strip() for linha in linhas if linha.strip()]


def _adicionar_arquivos_a_lista(arquivos):
    """Adiciona arquivos à lista da interface."""
    if not arquivos or not _validar_lista_arquivos():
        return

    for arquivo in arquivos:
        g.IMPRESSAO_LISTA_ARQUIVOS.addItem(arquivo)

    _limpar_campo_texto()
    _mostrar_confirmacao_adicao(len(arquivos))


def _validar_lista_arquivos():
    """Valida se a lista de arquivos está disponível."""
    return (hasattr(g, "IMPRESSAO_LISTA_ARQUIVOS")
            and g.IMPRESSAO_LISTA_ARQUIVOS is not None)


def _limpar_campo_texto():
    """Limpa o campo de texto se disponível."""
    if hasattr(g, "IMPRESSAO_LISTA_TEXT") and g.IMPRESSAO_LISTA_TEXT:
        g.IMPRESSAO_LISTA_TEXT.clear()


def _mostrar_confirmacao_adicao(num_arquivos):
    """Mostra confirmação de adição de arquivos."""
    QMessageBox.information(
        g.IMPRESSAO_FORM,
        "Sucesso",
        f"{num_arquivos} arquivo(s) adicionado(s) à lista!",
    )


def remover_arquivo():
    """Remove o arquivo selecionado da lista."""
    if not (hasattr(g, "IMPRESSAO_LISTA_ARQUIVOS") and g.IMPRESSAO_LISTA_ARQUIVOS):
        return

    current_row = g.IMPRESSAO_LISTA_ARQUIVOS.currentRow()
    if current_row >= 0:
        g.IMPRESSAO_LISTA_ARQUIVOS.takeItem(current_row)


def limpar_lista():
    """Limpa toda a lista de arquivos."""
    if hasattr(g, "IMPRESSAO_LISTA_ARQUIVOS") and g.IMPRESSAO_LISTA_ARQUIVOS:
        g.IMPRESSAO_LISTA_ARQUIVOS.clear()


def limpar_texto_placeholder():
    """Limpa o campo de texto."""
    if hasattr(g, "IMPRESSAO_LISTA_TEXT") and g.IMPRESSAO_LISTA_TEXT:
        g.IMPRESSAO_LISTA_TEXT.clear()


def executar_impressao():
    """Executa a impressão dos arquivos selecionados."""
    # Validar interface
    if not _validar_interface_inicializada():
        return

    # Validar diretório
    diretorio = g.IMPRESSAO_DIRETORIO_ENTRY.text().strip()
    if not _validar_diretorio(diretorio):
        return

    # Obter lista de arquivos
    lista_arquivos = _obter_lista_arquivos()
    if not lista_arquivos:
        QMessageBox.critical(
            g.IMPRESSAO_FORM,
            "Erro",
            "Por favor, adicione pelo menos um arquivo à lista.",
        )
        return

    imprimir_pdf(diretorio, lista_arquivos)


def _validar_interface_inicializada():
    """Valida se a interface foi inicializada corretamente."""
    if not (hasattr(g, "IMPRESSAO_DIRETORIO_ENTRY") and g.IMPRESSAO_DIRETORIO_ENTRY):
        QMessageBox.critical(
            g.IMPRESSAO_FORM, "Erro", "Interface não inicializada corretamente."
        )
        return False
    return True


def _validar_diretorio(diretorio):
    """Valida o diretório selecionado."""
    if not diretorio:
        QMessageBox.critical(
            g.IMPRESSAO_FORM, "Erro", "Por favor, selecione um diretório."
        )
        return False

    if not os.path.exists(diretorio):
        QMessageBox.critical(
            g.IMPRESSAO_FORM, "Erro", "O diretório selecionado não existe."
        )
        return False

    return True


def _obter_lista_arquivos():
    """Obtém a lista de arquivos da interface."""
    if not (hasattr(g, "IMPRESSAO_LISTA_ARQUIVOS") and g.IMPRESSAO_LISTA_ARQUIVOS):
        QMessageBox.critical(
            g.IMPRESSAO_FORM, "Erro", "Interface não inicializada corretamente."
        )
        return []

    lista_arquivos = []
    for i in range(g.IMPRESSAO_LISTA_ARQUIVOS.count()):
        lista_arquivos.append(g.IMPRESSAO_LISTA_ARQUIVOS.item(i).text())

    return lista_arquivos


# === SEÇÃO DE LAYOUT COM QGridLayout ===


def main(root):
    """Inicializa e exibe o formulário de impressão em lote."""
    _inicializar_formulario(root)
    _configurar_layout_grid()


def _inicializar_formulario(root):
    """Inicializa o formulário principal."""
    if hasattr(g, "IMPRESSAO_FORM") and g.IMPRESSAO_FORM:
        g.IMPRESSAO_FORM.close()

    g.IMPRESSAO_FORM = QDialog(root)
    g.IMPRESSAO_FORM.setWindowTitle("Impressão em Lote de PDFs")
    g.IMPRESSAO_FORM.setFixedSize(LARGURA_FORM_IMPRESSAO, ALTURA_FORM_IMPRESSAO)
    # Remover barra nativa
    g.IMPRESSAO_FORM.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

    g.IMPRESSAO_FORM.setWindowIcon(QIcon(ICON_PATH))

    aplicar_no_topo(g.IMPRESSAO_FORM)
    posicionar_janela(g.IMPRESSAO_FORM, None)


def _configurar_layout_grid():
    """Configura o layout principal usando QGridLayout."""
    # Layout vertical: barra de título customizada + conteúdo grid
    vlayout = QVBoxLayout(g.IMPRESSAO_FORM)
    vlayout.setContentsMargins(0, 0, 0, 0)
    vlayout.setSpacing(0)

    # Barra de título customizada
    barra = BarraTitulo(g.IMPRESSAO_FORM, tema=obter_tema_atual())
    barra.titulo.setText("Impressão em Lote de PDFs")
    vlayout.addWidget(barra)

    # Widget de conteúdo principal
    conteudo = QWidget()
    layout_principal = QGridLayout(conteudo)
    aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT_PRINCIPAL)

    layout_principal.setRowStretch(0, 0)
    layout_principal.setRowStretch(1, 1)
    layout_principal.setRowStretch(2, 0)

    frame_diretorio = _criar_secao_diretorio_grid()
    layout_principal.addWidget(frame_diretorio, 0, 0)

    # Linha 1: Seção de Arquivos
    frame_arquivos = _criar_secao_arquivos_grid()
    layout_principal.addWidget(frame_arquivos, 1, 0)

    # Linha 2: Seção de Resultado
    frame_resultado = _criar_secao_resultado_grid()
    layout_principal.addWidget(frame_resultado, 2, 0)

    vlayout.addWidget(conteudo)

    # Mostrar formulário
    g.IMPRESSAO_FORM.show()


def _criar_secao_diretorio_grid():
    """Cria a seção de seleção de diretório usando QGridLayout."""
    frame_diretorio = QGroupBox("Diretório dos PDFs")

    # Layout interno em grid
    dir_layout = QGridLayout()
    frame_diretorio.setLayout(dir_layout)
    aplicar_medida_borda_espaco(dir_layout)

    # Linha 0: Campo de diretório (coluna 0) + Botão procurar (coluna 1)
    g.IMPRESSAO_DIRETORIO_ENTRY = QLineEdit()
    dir_layout.addWidget(g.IMPRESSAO_DIRETORIO_ENTRY, 0, 0)

    procurar_btn = QPushButton("📁 Procurar")
    aplicar_estilo_botao(procurar_btn, "cinza")
    procurar_btn.clicked.connect(selecionar_diretorio)
    dir_layout.addWidget(procurar_btn, 0, 1)

    return frame_diretorio


def _criar_secao_arquivos_grid():
    """Cria a seção de gerenciamento de arquivos usando QGridLayout."""
    frame_arquivos = QGroupBox("Lista de Arquivos para Impressão")

    # Layout interno em grid
    arquivos_layout = QGridLayout()
    frame_arquivos.setLayout(arquivos_layout)
    aplicar_medida_borda_espaco(arquivos_layout)

    # === SUBSECÇÃO: CAMPO DE TEXTO MÚLTIPLO ===
    # Linha 0: Label
    lista_label = QLabel("Lista de arquivos (um por linha):")
    lista_label.setStyleSheet(STYLE_LABEL_BOLD)
    arquivos_layout.addWidget(lista_label, 0, 0, 1, 3)  # colspan=3

    # Linha 1-2: Campo de texto (coluna 0-1) + Botões (coluna 2)
    g.IMPRESSAO_LISTA_TEXT = QTextEdit()
    g.IMPRESSAO_LISTA_TEXT.setMaximumHeight(ALTURA_MAXIMA_LISTA)
    g.IMPRESSAO_LISTA_TEXT.setPlaceholderText(PLACEHOLDER_LISTA_ARQUIVOS)
    arquivos_layout.addWidget(
        g.IMPRESSAO_LISTA_TEXT, 1, 0, 2, 2
    )  # rowspan=2, colspan=2

    # Botões do campo de texto (coluna 2)
    adicionar_btn = QPushButton("➕ Adicionar")
    aplicar_estilo_botao(adicionar_btn, "azul")
    adicionar_btn.clicked.connect(adicionar_lista_arquivos)
    arquivos_layout.addWidget(adicionar_btn, 1, 2)

    limpar_text_btn = QPushButton("🧹 Limpar")
    aplicar_estilo_botao(limpar_text_btn, "amarelo")
    limpar_text_btn.clicked.connect(limpar_texto_placeholder)
    arquivos_layout.addWidget(limpar_text_btn, 2, 2)

    # === SUBSECÇÃO: LISTA DE ARQUIVOS ===
    # Linha 3: Label
    lista_arquivos_label = QLabel("Arquivos na lista:")
    lista_arquivos_label.setStyleSheet(STYLE_LABEL_BOLD)
    arquivos_layout.addWidget(lista_arquivos_label, 3, 0, 1, 3)  # colspan=3

    # Linha 4-6: Lista de arquivos (coluna 0-1) + Botões (coluna 2)
    g.IMPRESSAO_LISTA_ARQUIVOS = QListWidget()
    g.IMPRESSAO_LISTA_ARQUIVOS.setMaximumHeight(ALTURA_MAXIMA_LISTA_WIDGET)
    arquivos_layout.addWidget(
        g.IMPRESSAO_LISTA_ARQUIVOS, 4, 0, 3, 2
    )  # rowspan=3, colspan=2

    # Botões da lista (coluna 2)
    remover_btn = QPushButton("🗑️ Remover")
    aplicar_estilo_botao(remover_btn, "vermelho")
    remover_btn.clicked.connect(remover_arquivo)
    arquivos_layout.addWidget(remover_btn, 4, 2)

    limpar_lista_btn = QPushButton("🧹 Limpar")
    aplicar_estilo_botao(limpar_lista_btn, "amarelo")
    limpar_lista_btn.clicked.connect(limpar_lista)
    arquivos_layout.addWidget(limpar_lista_btn, 5, 2)

    imprimir_btn = QPushButton("🖨️ Imprimir")
    aplicar_estilo_botao(imprimir_btn, "verde")
    imprimir_btn.clicked.connect(executar_impressao)
    arquivos_layout.addWidget(imprimir_btn, 6, 2)

    return frame_arquivos


def _criar_secao_resultado_grid():
    """Cria a seção de resultado da impressão usando QGridLayout."""
    frame_resultado = QGroupBox("Resultado da Impressão")

    # Layout interno em grid
    resultado_layout = QGridLayout()
    frame_resultado.setLayout(resultado_layout)
    aplicar_medida_borda_espaco(resultado_layout)

    # Linha 0: Campo de resultado (ocupa toda a largura)
    g.IMPRESSAO_RESULTADO_TEXT = QTextBrowser()
    g.IMPRESSAO_RESULTADO_TEXT.setMaximumHeight(ALTURA_MAXIMA_LISTA)
    resultado_layout.addWidget(g.IMPRESSAO_RESULTADO_TEXT, 0, 0)

    return frame_resultado


if __name__ == "__main__":
    main(None)
