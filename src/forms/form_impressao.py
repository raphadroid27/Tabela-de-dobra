"""
Formulário de Impressão com QGridLayout

Este módulo contém a implementação do formulário de impressão em lote,
que permite selecionar um diretório e uma lista de arquivos PDF para impressão.
O formulário é construído usando QGridLayout para melhor organização e controle.

Refatorado para usar uma abordagem baseada em classes, eliminando variáveis globais
e adicionando um worker thread para impressão controlada, evitando sobrecarga do spooler.
"""

import os
import subprocess  # nosec B404
import sys
import time
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
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

# Supondo que esses módulos existam na estrutura do seu projeto.
# Se não, você precisará adaptá-los ou remover as chamadas.
from src.components.barra_titulo import BarraTitulo
from src.utils.estilo import aplicar_estilo_botao, obter_tema_atual
from src.utils.janelas import Janela
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# --- Constantes de Configuração ---
TIMEOUT_IMPRESSAO = 30
PAUSA_ENTRE_IMPRESSOES_SEGUNDOS = 2  # Pausa para não sobrecarregar o spooler
ALTURA_FORM_IMPRESSAO = 510
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
    """Gerencia as operações de busca e validação de arquivos PDF."""

    def __init__(self):
        self.arquivos_encontrados: List[str] = []
        self.arquivos_nao_encontrados: List[str] = []

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

    def _extrair_nome_base(self, arquivo: str) -> str:
        """Extrai a parte principal do nome do arquivo."""
        if not arquivo or not isinstance(arquivo, str):
            return ""
        return arquivo.split(" - ")[0].strip() if " - " in arquivo else arquivo.strip()

    def _procurar_arquivo(self, diretorio: str, nome_base: str) -> Optional[str]:
        """Procura um arquivo específico no diretório."""
        if not diretorio or not nome_base:
            return None
        try:
            diretorio = os.path.normpath(diretorio)
            if not os.path.isdir(diretorio):
                return None
            arquivos_pdf = [
                f
                for f in os.listdir(diretorio)
                if nome_base.lower() in f.lower() and f.lower().endswith(".pdf")
            ]
            return arquivos_pdf[0] if arquivos_pdf else None
        except (OSError, PermissionError):
            return None

    def gerar_relatorio_busca(self) -> str:
        """Gera relatório dos arquivos encontrados e não encontrados."""
        resultado = "Relatório da Verificação de Arquivos:\n\n"
        if self.arquivos_encontrados:
            resultado += f"Arquivos encontrados ({len(self.arquivos_encontrados)}):\n"
            resultado += "".join(f" • {arq}\n" for arq in self.arquivos_encontrados)
        if self.arquivos_nao_encontrados:
            msg = (
                f"\nArquivos não encontrados ({len(self.arquivos_nao_encontrados)}):\n"
            )
            resultado += msg
            resultado += "".join(f" • {arq}\n" for arq in self.arquivos_nao_encontrados)
        if not self.arquivos_encontrados and not self.arquivos_nao_encontrados:
            resultado += "Nenhum arquivo para verificar."
        return resultado


class PrintWorker(QThread):
    """
    Worker thread para executar a impressão em segundo plano,
    evitando que a GUI congele e controlando a fila de impressão.
    """

    progress_update = Signal(str)
    # CORREÇÃO: Renomeado o sinal para evitar conflito com o QThread.finished
    processo_finalizado = Signal()

    def __init__(self, diretorio: str, arquivos_para_imprimir: List[str], parent=None):
        super().__init__(parent)
        self.diretorio = diretorio
        self.arquivos = arquivos_para_imprimir

    def run(self):
        """Executa o processo de impressão em segundo plano."""
        if not self.arquivos:
            self.processo_finalizado.emit()
            return

        self.progress_update.emit("\n--- Iniciando processo de impressão ---\n")

        for nome_arquivo in self.arquivos:
            caminho_completo = os.path.join(self.diretorio, nome_arquivo)
            self._imprimir_arquivo_individual(nome_arquivo, caminho_completo)

            time.sleep(PAUSA_ENTRE_IMPRESSOES_SEGUNDOS)

        final_message = "\n--- Processo de impressão finalizado. ---"
        self.progress_update.emit(final_message)
        # CORREÇÃO: Emitindo o sinal renomeado
        self.processo_finalizado.emit()

    def _imprimir_arquivo_individual(self, nome_arquivo: str, caminho_completo: str):
        """Imprime um arquivo individual usando diferentes métodos."""
        if not self._validar_caminho_arquivo(caminho_completo):
            return

        sucesso = any(
            self._tentar_metodo(metodo, nome_arquivo, caminho_completo)
            for metodo in METODOS_IMPRESSAO
        )
        if not sucesso:
            msg = f" ✗ Falha ao imprimir {nome_arquivo} por todos os métodos.\n"
            self.progress_update.emit(msg)

    def _tentar_metodo(self, metodo: str, nome_arquivo: str, caminho: str) -> bool:
        """Tenta imprimir um arquivo com um método específico."""
        metodos = {
            "foxit": self._tentar_foxit,
            "impressora_padrao": self._tentar_impressora_padrao,
            "adobe": self._tentar_adobe,
        }
        if metodo in metodos:
            return metodos[metodo](nome_arquivo, caminho)
        return False

    def _validar_caminho_arquivo(self, caminho_completo: str) -> bool:
        """Valida se o caminho do arquivo é seguro e existe."""
        try:
            caminho_normalizado = os.path.normpath(caminho_completo)
            if not os.path.isfile(caminho_normalizado):
                msg = f" ✗ Caminho inválido ou não é arquivo: {caminho_completo}\n"
                self.progress_update.emit(msg)
                return False
            if not caminho_normalizado.lower().endswith(".pdf"):
                msg = f" ✗ Arquivo não é PDF: {caminho_completo}\n"
                self.progress_update.emit(msg)
                return False
            return True
        except (OSError, ValueError):
            msg = f" ✗ Erro ao validar caminho: {caminho_completo}\n"
            self.progress_update.emit(msg)
            return False

    def _tentar_foxit(self, nome_arquivo: str, caminho: str) -> bool:
        """Tenta imprimir usando Foxit PDF Reader."""
        if not os.path.exists(FOXIT_PATH):
            return False
        msg = f"Tentando imprimir {nome_arquivo} com Foxit...\n"
        self.progress_update.emit(msg)
        try:
            subprocess.run(  # nosec B603
                [FOXIT_PATH, "/p", caminho],
                check=True,
                timeout=TIMEOUT_IMPRESSAO,
                shell=False,
            )
            result_msg = " ✓ Sucesso com Foxit\n"
            self.progress_update.emit(result_msg)
            return True
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ) as e:
            error_msg = f" ✗ Erro com Foxit: {e}\n"
            self.progress_update.emit(error_msg)
            return False

    def _tentar_impressora_padrao(self, nome_arquivo: str, caminho: str) -> bool:
        """Tenta imprimir usando a impressora padrão do Windows."""
        if not hasattr(os, "startfile"):
            return False
        msg = f"Tentando imprimir {nome_arquivo} com impressora padrão...\n"
        self.progress_update.emit(msg)
        try:
            os.startfile(caminho, "print")  # nosec B606
            result_msg = " ✓ Sucesso com impressora padrão\n"
            self.progress_update.emit(result_msg)
            return True
        except (OSError, PermissionError, FileNotFoundError) as e:
            error_msg = f" ✗ Erro com impressora padrão: {e}\n"
            self.progress_update.emit(error_msg)
            return False

    def _tentar_adobe(self, nome_arquivo: str, caminho: str) -> bool:
        """Tenta imprimir usando Adobe Reader."""
        for adobe_path in ADOBE_PATHS:
            if os.path.exists(adobe_path):
                base_name = os.path.basename(adobe_path)
                msg = f"Tentando imprimir {nome_arquivo} com Adobe ({base_name})...\n"
                self.progress_update.emit(msg)
                try:
                    subprocess.run(  # nosec B603
                        [adobe_path, "/p", caminho],
                        check=True,
                        timeout=TIMEOUT_IMPRESSAO,
                        shell=False,
                    )
                    result_msg = " ✓ Sucesso com Adobe\n"
                    self.progress_update.emit(result_msg)
                    return True
                except (
                    subprocess.TimeoutExpired,
                    subprocess.CalledProcessError,
                    FileNotFoundError,
                ) as e:
                    error_msg = f" ✗ Erro com Adobe: {e}\n"
                    self.progress_update.emit(error_msg)
        return False


class FormImpressao(QDialog):
    """Formulário de Impressão em Lote de PDFs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.print_manager = PrintManager()
        self.print_worker: Optional[PrintWorker] = None

        # Widgets
        self.diretorio_entry: Optional[QLineEdit] = None
        self.lista_text: Optional[QTextEdit] = None
        self.lista_arquivos_widget: Optional[QListWidget] = None
        self.resultado_text: Optional[QTextBrowser] = None
        self.imprimir_btn: Optional[QPushButton] = None

        self._inicializar_ui()

    def _inicializar_ui(self):
        """Inicializa a interface do usuário."""
        self.setWindowTitle("Impressão em Lote de PDFs")
        self.setFixedSize(LARGURA_FORM_IMPRESSAO, ALTURA_FORM_IMPRESSAO)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowIcon(QIcon(ICON_PATH))

        Janela.aplicar_no_topo(self)
        Janela.posicionar_janela(self, None)

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        barra = BarraTitulo(self, tema=obter_tema_atual())
        barra.titulo.setText("Impressão em Lote de PDFs")
        vlayout.addWidget(barra)

        conteudo = QWidget()
        layout_principal = QGridLayout(conteudo)
        aplicar_medida_borda_espaco(layout_principal, MARGEM_LAYOUT_PRINCIPAL)

        frame_diretorio = self._criar_secao_diretorio()
        layout_principal.addWidget(frame_diretorio, 0, 0)

        frame_arquivos = self._criar_secao_arquivos()
        layout_principal.addWidget(frame_arquivos, 1, 0)

        frame_resultado = self._criar_secao_resultado()
        layout_principal.addWidget(frame_resultado, 2, 0)

        layout_principal.setRowStretch(0, 0)
        layout_principal.setRowStretch(1, 1)
        layout_principal.setRowStretch(2, 0)

        vlayout.addWidget(conteudo)

    def _criar_secao_diretorio(self) -> QGroupBox:
        """Cria a seção de seleção de diretório."""
        frame = QGroupBox("Diretório dos PDFs")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)

        self.diretorio_entry = QLineEdit()
        layout.addWidget(self.diretorio_entry, 0, 0)

        procurar_btn = QPushButton("📁 Procurar")
        procurar_btn.clicked.connect(self.selecionar_diretorio)
        aplicar_estilo_botao(procurar_btn, "cinza")
        layout.addWidget(procurar_btn, 0, 1)
        return frame

    def _criar_secao_arquivos(self) -> QGroupBox:
        """Cria a seção de gerenciamento de arquivos."""
        frame = QGroupBox("Lista de Arquivos para Impressão")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)

        label_lista = QLabel("Lista de arquivos (um por linha):")
        label_lista.setStyleSheet(STYLE_LABEL_BOLD)
        layout.addWidget(label_lista, 0, 0, 1, 3)

        self.lista_text = QTextEdit(
            maximumHeight=ALTURA_MAXIMA_LISTA,
            placeholderText=PLACEHOLDER_LISTA_ARQUIVOS,
        )
        layout.addWidget(self.lista_text, 1, 0, 2, 2)

        adicionar_btn = QPushButton("➕ Adicionar")
        adicionar_btn.clicked.connect(self.adicionar_lista_arquivos)
        aplicar_estilo_botao(adicionar_btn, "azul")
        layout.addWidget(adicionar_btn, 1, 2)

        limpar_text_btn = QPushButton("🧹 Limpar Texto")
        limpar_text_btn.clicked.connect(self.lista_text.clear)
        aplicar_estilo_botao(limpar_text_btn, "amarelo")
        layout.addWidget(limpar_text_btn, 2, 2)

        label_arquivos = QLabel("Arquivos na lista:")
        label_arquivos.setStyleSheet(STYLE_LABEL_BOLD)
        layout.addWidget(label_arquivos, 3, 0, 1, 3)

        self.lista_arquivos_widget = QListWidget(
            maximumHeight=ALTURA_MAXIMA_LISTA_WIDGET
        )
        layout.addWidget(self.lista_arquivos_widget, 4, 0, 4, 2)

        remover_btn = QPushButton("🗑️ Remover")
        remover_btn.clicked.connect(self.remover_arquivo_selecionado)
        aplicar_estilo_botao(remover_btn, "vermelho")
        layout.addWidget(remover_btn, 4, 2)

        limpar_lista_btn = QPushButton("🧹 Limpar Lista")
        limpar_lista_btn.clicked.connect(self.lista_arquivos_widget.clear)
        aplicar_estilo_botao(limpar_lista_btn, "amarelo")
        layout.addWidget(limpar_lista_btn, 5, 2)

        verificar_btn = QPushButton("🔍 Verificar")
        verificar_btn.clicked.connect(self.verificar_arquivos_existentes)
        aplicar_estilo_botao(verificar_btn, "cinza")
        layout.addWidget(verificar_btn, 6, 2)

        self.imprimir_btn = QPushButton("🖨️ Imprimir")
        self.imprimir_btn.clicked.connect(self.executar_impressao)
        aplicar_estilo_botao(self.imprimir_btn, "verde")
        layout.addWidget(self.imprimir_btn, 7, 2)

        return frame

    def _criar_secao_resultado(self) -> QGroupBox:
        """Cria a seção de resultado da impressão."""
        frame = QGroupBox("Resultado da Impressão")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)
        self.resultado_text = QTextBrowser(maximumHeight=ALTURA_MAXIMA_LISTA)
        layout.addWidget(self.resultado_text, 0, 0)
        return frame

    def selecionar_diretorio(self):
        """Abre o diálogo para seleção de diretório."""
        try:
            Janela.estado_janelas(False)
            diretorio = QFileDialog.getExistingDirectory(
                self, "Selecionar Diretório dos PDFs"
            )
            if diretorio:
                self.diretorio_entry.setText(diretorio)
        finally:
            Janela.estado_janelas(True)

    def adicionar_lista_arquivos(self):
        """Adiciona múltiplos arquivos à lista a partir do campo de texto."""
        texto = self.lista_text.toPlainText().strip()
        if not texto:
            return
        arquivos = [linha.strip() for linha in texto.split("\n") if linha.strip()]
        if arquivos:
            self.lista_arquivos_widget.addItems(arquivos)
            self.lista_text.clear()
            msg = f"{len(arquivos)} arquivo(s) adicionado(s) à lista!"
            QMessageBox.information(self, "Sucesso", msg)

    def remover_arquivo_selecionado(self):
        """Remove o arquivo selecionado da lista."""
        item_selecionado = self.lista_arquivos_widget.currentItem()
        if item_selecionado:
            self.lista_arquivos_widget.takeItem(
                self.lista_arquivos_widget.row(item_selecionado)
            )

    def _obter_lista_arquivos_da_widget(self) -> List[str]:
        """Obtém a lista de arquivos da QListWidget."""
        return [
            self.lista_arquivos_widget.item(i).text()
            for i in range(self.lista_arquivos_widget.count())
        ]

    def _validar_entradas(self) -> bool:
        """Valida se o diretório e a lista de arquivos estão prontos."""
        if not self.diretorio_entry.text().strip():
            QMessageBox.critical(self, "Erro", "Por favor, selecione um diretório.")
            return False
        if not os.path.isdir(self.diretorio_entry.text().strip()):
            QMessageBox.critical(self, "Erro", "O diretório selecionado não existe.")
            return False
        if self.lista_arquivos_widget.count() == 0:
            QMessageBox.warning(
                self,
                "Aviso",
                "A lista de arquivos está vazia. Adicione arquivos para continuar.",
            )
            return False
        return True

    def verificar_arquivos_existentes(self):
        """Verifica se os arquivos da lista existem no diretório selecionado."""
        diretorio = self.diretorio_entry.text().strip()
        if not diretorio or not os.path.isdir(diretorio):
            QMessageBox.critical(
                self, "Erro", "Por favor, selecione um diretório válido."
            )
            return

        lista_arquivos = self._obter_lista_arquivos_da_widget()
        if not lista_arquivos:
            QMessageBox.warning(self, "Aviso", "A lista de arquivos está vazia.")
            return

        try:
            self.print_manager.buscar_arquivos(diretorio, lista_arquivos)
            resultado_busca = self.print_manager.gerar_relatorio_busca()
            self.resultado_text.setText(resultado_busca)

            msg = (
                f"Verificação finalizada.\n\n"
                f"Arquivos encontrados: {len(self.print_manager.arquivos_encontrados)}\n"
                f"Arquivos não encontrados: {len(self.print_manager.arquivos_nao_encontrados)}\n\n"
                "Confira os detalhes no campo 'Resultado da Impressão'."
            )
            QMessageBox.information(self, "Verificação Concluída", msg)
        except (OSError, ValueError) as e:
            QMessageBox.critical(
                self, "Erro", f"Ocorreu um erro durante a verificação: {e}"
            )

    def executar_impressao(self):
        """Inicia o processo de impressão em uma thread separada."""
        if not self._validar_entradas():
            return

        diretorio = self.diretorio_entry.text().strip()
        lista_arquivos = self._obter_lista_arquivos_da_widget()

        try:
            self.print_manager.buscar_arquivos(diretorio, lista_arquivos)
            resultado_busca = self.print_manager.gerar_relatorio_busca()
            self.resultado_text.setText(resultado_busca)

            if not self.print_manager.arquivos_encontrados:
                QMessageBox.warning(
                    self,
                    "Aviso",
                    "Nenhum arquivo válido foi encontrado para impressão.",
                )
                return

            self.imprimir_btn.setEnabled(False)
            self.imprimir_btn.setText("Imprimindo...")

            self.print_worker = PrintWorker(
                diretorio, self.print_manager.arquivos_encontrados
            )
            self.print_worker.progress_update.connect(self.atualizar_resultado)
            # CORREÇÃO: Conectando ao sinal renomeado
            self.print_worker.processo_finalizado.connect(self.impressao_finalizada)
            self.print_worker.start()

        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar impressão: {e}")
            self.imprimir_btn.setEnabled(True)
            self.imprimir_btn.setText("🖨️ Imprimir")

    def atualizar_resultado(self, mensagem: str):
        """Adiciona mensagens de progresso à caixa de texto de resultado."""
        self.resultado_text.append(mensagem)
        self.resultado_text.verticalScrollBar().setValue(
            self.resultado_text.verticalScrollBar().maximum()
        )

    def impressao_finalizada(self):
        """Chamado quando a thread de impressão termina."""
        QMessageBox.information(
            self, "Processo Concluído", "A impressão em lote foi finalizada."
        )
        self.imprimir_btn.setEnabled(True)
        self.imprimir_btn.setText("🖨️ Imprimir")
        self.print_worker = None


class FormManager:
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    _instance = None

    @classmethod
    def show_form(cls, parent=None):
        """Cria e exibe o formulário, garantindo uma única instância visível."""
        if cls._instance is None or not cls._instance.isVisible():
            cls._instance = FormImpressao(parent)
            cls._instance.show()
        else:
            cls._instance.activateWindow()
            cls._instance.raise_()


def main(parent=None):
    """Ponto de entrada para criar e exibir o formulário de impressão."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        main()
    except (ImportError, NameError) as e:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("Erro de Dependência")
        msg_box.setInformativeText(
            f"Não foi possível iniciar o aplicativo: {e}.\n"
            "Execute este formulário a partir do aplicativo principal."
        )
        msg_box.setWindowTitle("Erro")
        msg_box.exec()
        sys.exit(1)

    sys.exit(app.exec())
