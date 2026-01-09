"""
Formulário de Impressão com QGridLayout.

Este módulo contém a implementação do formulário de impressão em lote,
que permite selecionar um diretório e uma lista de arquivos PDF para impressão.
O formulário é construído usando QGridLayout para melhor organização e controle.

Refatorado para usar uma abordagem baseada em classes, eliminando variáveis globais
e adicionando um worker thread para impressão controlada, evitando sobrecarga do spooler.
"""

import os
import re
import subprocess  # nosec B404
import sys
import time
from typing import Dict, List, Optional

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from src.forms.common import context_help
from src.forms.common.form_manager import BaseSingletonFormManager
from src.forms.common.ui_helpers import configurar_dialogo_padrao
from src.utils.estilo import aplicar_estilo_botao
from src.utils.janelas import Janela
from src.utils.themed_widgets import ThemedDialog
from src.utils.utilitarios import (
    ICON_PATH,
    aplicar_medida_borda_espaco,
    show_error,
    show_info,
    show_warning,
)

# --- Constantes de Configuração ---
TIMEOUT_IMPRESSAO = 30
PAUSA_ENTRE_IMPRESSOES_SEGUNDOS = 2  # Pausa para não sobrecarregar o spooler
ALTURA_FORM_IMPRESSAO = 510
LARGURA_FORM_IMPRESSAO = 500
MARGEM_LAYOUT_PRINCIPAL = 10

# Métodos de impressão em ordem de prioridade
METODOS_IMPRESSAO = ["foxit", "impressora_padrao", "adobe"]

# Strings de interface
PLACEHOLDER_LISTA_ARQUIVOS_1 = (
    "Digite os nomes dos arquivos, um por linha. Exemplo:\n010464516\n010464519"
)

TOOLTIP_LISTA_ARQUIVOS_2 = (
    "Lista de arquivos PDF para impressão\n"
    "Arraste PDFs aqui para adicionar à lista\n"
    "Clique para selecionar arquivos\n"
    "Use Ctrl+↑/↓ para mover item selecionado"
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
        """Inicializa listas de controle de arquivos encontrados e ausentes."""
        self.arquivos_encontrados: List[str] = []
        self.arquivos_nao_encontrados: List[str] = []

    def buscar_arquivos(self, diretorio: str, lista_arquivos: List[str]) -> None:
        """Busca os arquivos no diretório especificado."""
        self.arquivos_encontrados.clear()
        self.arquivos_nao_encontrados.clear()

        if not diretorio:
            self.arquivos_nao_encontrados.extend(lista_arquivos)
            return

        try:
            diretorio = os.path.normpath(diretorio)
            if not os.path.isdir(diretorio):
                self.arquivos_nao_encontrados.extend(lista_arquivos)
                return

            # OTIMIZAÇÃO: Ler o conteúdo do diretório apenas uma vez
            files_in_dir = [
                f for f in os.listdir(diretorio) if f.lower().endswith(".pdf")
            ]
            # Cria índice otimizado para busca rápida
            indice = self._construir_indice(files_in_dir)

        except (OSError, PermissionError):
            self.arquivos_nao_encontrados.extend(lista_arquivos)
            return

        for arquivo in lista_arquivos:
            nome_base = self._extrair_nome_base(arquivo)
            # Usa o índice para busca O(1) ou O(N_filtrado) em vez de iterar tudo sempre
            arquivo_encontrado = self._consultar_indice(indice, nome_base)

            if arquivo_encontrado:
                self.arquivos_encontrados.append(arquivo_encontrado)
            else:
                self.arquivos_nao_encontrados.append(arquivo)

    def _construir_indice(self, lista_arquivos: List[str]) -> Dict:
        """
        Constrói um índice para acelerar a busca de arquivos.
        Retorna um dicionário com mapas de busca rápida.
        """
        idx = {"exact": {}, "tokens": []}

        for f in lista_arquivos:
            nome_sem_ext = os.path.splitext(f)[0].lower()

            # Mapa reverso para busca exata (nome_limpo -> nome_real)
            idx["exact"][nome_sem_ext] = f

            # Prepara tokens para busca fuzzy
            # Separa por hífens, underlines, espaços e pontos
            tokens = [t for t in re.split(r"[-_\s\.]+", nome_sem_ext) if t]
            idx["tokens"].append({
                "real": f,
                "norm": nome_sem_ext,
                "tokens": tokens,
                "token_set": set(tokens)  # Set para verificação rápida de pertinência
            })

        return idx

    def _consultar_indice(self, indice: Dict, nome_buscado: str) -> Optional[str]:
        """Realiza a busca usando o índice pré-processado."""
        if not nome_buscado:
            return None

        nome_lower = nome_buscado.lower()

        # 1. Busca Exata (O(1))
        # Verifica se existe chave direta no mapa
        if nome_lower in indice["exact"]:
            return indice["exact"][nome_lower]

        # Prepara tokens da busca
        tokens_busca = [t for t in re.split(r"[-_\s\.]+", nome_lower) if t]

        # 2. Busca por Prefixo (Otimizada)
        # 3. Busca Flexível (Baseada em Tokens)
        candidatos = []

        for item in indice["tokens"]:
            f_real = item["real"]
            f_norm = item["norm"]
            f_tokens = item["tokens"]

            # Regra de Prefixo
            if f_norm.startswith(nome_lower):
                return f_real

            # Regra de Subsequência / Tokens
            # Verifica se os tokens do arquivo são um subconjunto ordenado
            # ou não dos tokens da busca
            # Cenário: Busca 'P1-123-50-R1', Arquivo 'P1-123-R1'
            # Tokens Busca: {P1, 123, 50, R1} -> Tokens Arq: {P1, 123, R1} -> É match!

            # Lógica refinada:
            # Se o arquivo presente é uma 'versão simplificada' da busca
            it = iter(tokens_busca)
            try:
                # Verifica se todos os tokens do arquivo aparecem na busca,
                # na ordem relativa correta
                if all(token in it for token in f_tokens):
                    # Score de prioridade: quanto mais tokens baterem, melhor,
                    # mas penalizando se o arquivo for muito curto (falso positivo)
                    candidatos.append(f_real)
            except TypeError:
                continue

        if candidatos:
            # Desempate:
            # 1. O que tiver mais 'partes' (mais específico)
            # 2. O nome mais longo
            candidatos.sort(
                key=lambda x: (len(re.split(r"[-_\s\.]+", x)), len(x)),
                reverse=True,
            )
            return candidatos[0]

        return None

    def _extrair_nome_base(self, arquivo: str) -> str:
        """Extrai a parte principal do nome do arquivo de forma robusta."""
        if not arquivo or not isinstance(arquivo, str):
            return ""

        # Normaliza diferentes tipos de hífens para o hífen padrão
        # e normaliza todos os tipos de espaços em excesso.
        temp_arquivo = arquivo.replace("–", "-").replace("—", "-")
        temp_arquivo = " ".join(temp_arquivo.split())

        # Prioriza a divisão por " - "
        if " - " in temp_arquivo:
            return temp_arquivo.split(" - ", maxsplit=1)[0].strip()

        # Caso contrário, divide pelo primeiro espaço
        return temp_arquivo.split(" ", maxsplit=1)[0].strip()

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
    """Executa a impressão em segundo plano.

    Evita travar a GUI e controla a fila de impressão.
    """

    progress_update = Signal(str)
    progress_percent = Signal(int)
    processo_finalizado = Signal()

    def __init__(self, diretorio: str, arquivos_para_imprimir: List[str], parent=None):
        """Guarda parâmetros e prepara a thread de impressão."""
        super().__init__(parent)
        self.diretorio = diretorio
        self.arquivos = arquivos_para_imprimir

    def run(self):
        """Executa o processo de impressão em segundo plano."""
        if not self.arquivos:
            self.processo_finalizado.emit()
            return

        self.progress_update.emit("\n--- Iniciando processo de impressão ---\n")

        total = len(self.arquivos)
        for idx, nome_arquivo in enumerate(self.arquivos, start=1):
            caminho_completo = os.path.join(self.diretorio, nome_arquivo)
            self._imprimir_arquivo_individual(nome_arquivo, caminho_completo)
            # Atualiza progresso
            percent = int((idx / total) * 100)
            self.progress_percent.emit(min(100, max(0, percent)))
            time.sleep(PAUSA_ENTRE_IMPRESSOES_SEGUNDOS)

        final_message = "\n--- Processo de impressão finalizado. ---"
        self.progress_update.emit(final_message)
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
            # pylint: disable=E1101
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


# pylint: disable=R0902


class FormImpressao(ThemedDialog):
    """Formulário de Impressão em Lote de PDFs."""

    def __init__(self, parent=None):
        """Inicializa widgets, estado e constrói a UI do formulário."""
        super().__init__(parent)
        self.print_manager = PrintManager()
        self.print_worker: Optional[PrintWorker] = None

        # Widgets (atributos de instância inicializados no __init__)
        self.diretorio_entry = None  # type: Optional[QLineEdit]
        self.lista_text = None  # type: Optional[QTextEdit]
        self.lista_arquivos_widget = None  # type: Optional[QListWidget]
        self.resultado_text = None  # type: Optional[QTextBrowser]
        self.imprimir_btn = None  # type: Optional[QPushButton]
        self.progress_bar = None  # type: Optional[QProgressBar]

        self._inicializar_ui()

        # Adicionar atalho F1 para ajuda
        shortcut = QShortcut(QKeySequence("F1"), self)
        shortcut.activated.connect(self._mostrar_ajuda)

    def _inicializar_ui(self):
        """Inicializa a interface do usuário."""
        self.setWindowTitle("Impressão em Lote de PDFs")
        self.resize(LARGURA_FORM_IMPRESSAO, ALTURA_FORM_IMPRESSAO)
        self.setMinimumSize(LARGURA_FORM_IMPRESSAO, ALTURA_FORM_IMPRESSAO)
        configurar_dialogo_padrao(self, ICON_PATH)

        Janela.posicionar_janela(self, None)

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

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
        layout_principal.setRowStretch(2, 1)

        vlayout.addWidget(conteudo)

    def _configurar_atalhos_lista(self):
        """Configura os atalhos de teclado para movimentação de itens na lista."""
        # Atalho para mover item para cima
        shortcut_up = QShortcut(QKeySequence("Ctrl+Up"), self.lista_arquivos_widget)
        shortcut_up.activated.connect(self.mover_item_para_cima)

        # Atalho para mover item para baixo
        shortcut_down = QShortcut(QKeySequence("Ctrl+Down"), self.lista_arquivos_widget)
        shortcut_down.activated.connect(self.mover_item_para_baixo)

    def mover_item_para_cima(self):
        """Move o item selecionado uma posição para cima."""
        if not self.lista_arquivos_widget:
            return

        current_row = self.lista_arquivos_widget.currentRow()
        if current_row <= 0:  # Já está no topo ou nenhum item selecionado
            return

        # Remove o item atual
        item = self.lista_arquivos_widget.takeItem(current_row)
        if item:
            # Insere uma posição acima
            self.lista_arquivos_widget.insertItem(current_row - 1, item)
            # Mantém a seleção no item movido
            self.lista_arquivos_widget.setCurrentRow(current_row - 1)

    def mover_item_para_baixo(self):
        """Move o item selecionado uma posição para baixo."""
        if not self.lista_arquivos_widget:
            return

        current_row = self.lista_arquivos_widget.currentRow()
        total_items = self.lista_arquivos_widget.count()

        if current_row < 0 or current_row >= total_items - 1:
            return

        # Remove o item atual
        item = self.lista_arquivos_widget.takeItem(current_row)
        if item:
            # Insere uma posição abaixo
            self.lista_arquivos_widget.insertItem(current_row + 1, item)
            # Mantém a seleção no item movido
            self.lista_arquivos_widget.setCurrentRow(current_row + 1)

    def _mostrar_ajuda(self) -> None:
        """Exibe o guia contextual desta janela."""
        context_help.show_help("impressao", parent=self)

    def _criar_secao_diretorio(self) -> QGroupBox:
        """Cria a seção de seleção de diretório."""
        frame = QGroupBox("Diretório dos PDFs")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)

        self.diretorio_entry = QLineEdit()
        self.diretorio_entry.setToolTip(
            "Caminho do diretório contendo os arquivos PDF para impressão"
        )
        self.diretorio_entry.setPlaceholderText("Selecione o diretório com os PDFs...")
        layout.addWidget(self.diretorio_entry, 0, 0)

        procurar_btn = QPushButton("📁 Procurar")
        procurar_btn.clicked.connect(self.selecionar_diretorio)
        procurar_btn.setShortcut(QKeySequence("Ctrl+O"))
        procurar_btn.setToolTip(
            "Abre o explorador para selecionar o diretório dos PDFs (Ctrl+O)"
        )
        aplicar_estilo_botao(procurar_btn, "cinza")
        layout.addWidget(procurar_btn, 0, 1)
        return frame

    # pylint: disable=R0915
    def _criar_secao_arquivos(self) -> QGroupBox:
        """Cria a seção de gerenciamento de arquivos."""
        frame = QGroupBox("Lista de Arquivos para Impressão")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)

        layout.setRowStretch(0, 0)  # título da lista (linha 0)
        layout.setRowStretch(1, 1)  # QTextEdit (parte 1)
        layout.setRowStretch(2, 1)  # QTextEdit (parte 2 - span)
        layout.setRowStretch(3, 0)  # label 'Arquivos na lista' (fixo)
        layout.setRowStretch(4, 2)  # QListWidget (recebe mais espaço)

        # Colunas: coluna 0 e 1 são conteúdo expansível; coluna 2 é coluna de botões fixa
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)

        label_lista = QLabel("Lista de arquivos (um por linha):")
        label_lista.setObjectName("label_titulo_negrito")
        layout.addWidget(label_lista, 0, 0, 1, 3)

        self.lista_text = QTextEdit()
        self.lista_text.setPlaceholderText(PLACEHOLDER_LISTA_ARQUIVOS_1)
        self.lista_text.setAcceptDrops(False)
        layout.addWidget(self.lista_text, 1, 0, 2, 2)

        adicionar_btn = QPushButton("➕ Adicionar")
        adicionar_btn.clicked.connect(self.adicionar_lista_arquivos)
        adicionar_btn.setShortcut(QKeySequence("Ctrl+Shift+A"))
        adicionar_btn.setToolTip(
            "Adiciona os nomes de arquivos do campo de texto à lista (Ctrl+Shift+A)"
        )
        aplicar_estilo_botao(adicionar_btn, "azul")
        layout.addWidget(adicionar_btn, 1, 2)

        limpar_text_btn = QPushButton("🧹 Limpar Texto")
        limpar_text_btn.clicked.connect(self.lista_text.clear)
        limpar_text_btn.setShortcut(QKeySequence("Ctrl+L"))
        limpar_text_btn.setToolTip("Limpa o campo de entrada de texto (Ctrl+L)")
        aplicar_estilo_botao(limpar_text_btn, "amarelo")
        layout.addWidget(limpar_text_btn, 2, 2)

        label_arquivos = QLabel("Arquivos na lista:")
        label_arquivos.setObjectName("label_titulo_negrito")
        layout.addWidget(label_arquivos, 3, 0, 1, 3)

        # Lista com suporte a arrastar/soltar arquivos PDF
        self.lista_arquivos_widget = QListWidget()
        self.lista_arquivos_widget.setToolTip(TOOLTIP_LISTA_ARQUIVOS_2)
        self.lista_arquivos_widget.setAcceptDrops(True)
        self.lista_arquivos_widget.setDragDropMode(
            QListWidget.DragDropMode.InternalMove
        )

        # Configurar atalhos de teclado para movimentação
        self._configurar_atalhos_lista()

        # Atribui handlers de DnD dinamicamente (ignora mypy quanto a atribuição de métodos)
        self.lista_arquivos_widget.dragEnterEvent = (  # type: ignore[method-assign]
            self._lista_drag_enter_event
        )
        self.lista_arquivos_widget.dragMoveEvent = (  # type: ignore[method-assign]
            self._lista_drag_move_event
        )
        self.lista_arquivos_widget.dropEvent = (  # type: ignore[method-assign]
            self._lista_drop_event
        )
        self.lista_arquivos_widget.setAccessibleName("lista_arquivos_para_impressao")

        layout.addWidget(self.lista_arquivos_widget, 4, 0, 4, 2)

        remover_btn = QPushButton("🗑️ Remover")
        remover_btn.clicked.connect(self.remover_arquivo_selecionado)
        remover_btn.setShortcut(QKeySequence("Delete"))
        remover_btn.setToolTip("Remove o arquivo selecionado da lista (Del)")
        aplicar_estilo_botao(remover_btn, "vermelho")
        layout.addWidget(remover_btn, 4, 2)

        limpar_lista_btn = QPushButton("🧹 Limpar Lista")
        limpar_lista_btn.clicked.connect(self.lista_arquivos_widget.clear)
        limpar_lista_btn.setShortcut(QKeySequence("Ctrl+Shift+L"))
        limpar_lista_btn.setToolTip("Remove todos os arquivos da lista (Ctrl+Shift+L)")
        aplicar_estilo_botao(limpar_lista_btn, "amarelo")
        layout.addWidget(limpar_lista_btn, 5, 2)

        verificar_btn = QPushButton("🔍 Verificar")
        verificar_btn.clicked.connect(self.verificar_arquivos_existentes)
        verificar_btn.setShortcut(QKeySequence("Ctrl+Shift+V"))
        verificar_btn.setToolTip(
            "Verifica se os arquivos da lista existem no diretório (Ctrl+Shift+V)"
        )
        aplicar_estilo_botao(verificar_btn, "cinza")
        layout.addWidget(verificar_btn, 6, 2)

        self.imprimir_btn = QPushButton("🖨️ Imprimir")
        self.imprimir_btn.clicked.connect(self.executar_impressao)
        self.imprimir_btn.setShortcut(QKeySequence("Ctrl+P"))
        self.imprimir_btn.setToolTip(
            "Inicia a impressão de todos os arquivos da lista (Ctrl+P)"
        )
        aplicar_estilo_botao(self.imprimir_btn, "verde")
        layout.addWidget(self.imprimir_btn, 7, 2)

        return frame

    def _criar_secao_resultado(self) -> QGroupBox:
        """Cria a seção de resultado da impressão."""
        frame = QGroupBox("Resultado da Impressão")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)
        self.resultado_text = QTextBrowser()
        self.resultado_text.setToolTip(
            "Exibe o progresso e resultado da impressão dos arquivos"
        )
        layout.addWidget(self.resultado_text, 0, 0)

        # Permitir expansão vertical do texto de resultado
        layout.setRowStretch(0, 1)

        # Barra de progresso da impressão
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setToolTip("Mostra o progresso da impressão dos arquivos")
        self.progress_bar.setVisible(False)  # Começa oculta
        layout.addWidget(self.progress_bar, 1, 0)
        return frame

    def selecionar_diretorio(self):
        """Abre o diálogo para seleção de diretório."""
        try:
            Janela.estado_janelas(False)
            diretorio = QFileDialog.getExistingDirectory(
                self, "Selecionar Diretório dos PDFs"
            )
            if diretorio and self.diretorio_entry is not None:
                self.diretorio_entry.setText(diretorio)
        finally:
            Janela.estado_janelas(True)

    def adicionar_lista_arquivos(self):
        """Adiciona múltiplos arquivos à lista a partir do campo de texto."""
        assert self.lista_text is not None
        texto = self.lista_text.toPlainText().strip()
        if not texto:
            return
        arquivos = [linha.strip() for linha in texto.split("\n") if linha.strip()]
        if arquivos:
            assert self.lista_arquivos_widget is not None
            self.lista_arquivos_widget.addItems(arquivos)
            self.lista_text.clear()

            msg = f"{len(arquivos)} arquivo(s) adicionado(s) à lista e ordenado(s) alfabeticamente!"
            show_info("Sucesso", msg, parent=self)

    def _ordenar_lista_alfabeticamente(self):
        """Ordena a lista alfabeticamente sem mostrar mensagem."""
        if not self.lista_arquivos_widget or self.lista_arquivos_widget.count() == 0:
            return

        # Coleta todos os textos dos itens
        items_text = []
        for i in range(self.lista_arquivos_widget.count()):
            item = self.lista_arquivos_widget.item(i)
            if item:
                items_text.append(item.text())

        # Ordena alfabeticamente (case-insensitive)
        items_text.sort(key=str.lower)

        # Limpa a lista e adiciona os itens ordenados
        self.lista_arquivos_widget.clear()
        self.lista_arquivos_widget.addItems(items_text)

    # Suporte a arrastar/soltar PDFs na lista
    def _lista_drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _lista_drag_move_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _lista_drop_event(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        # Coleta apenas PDFs
        pdf_paths = []
        for url in urls:
            try:
                p = url.toLocalFile()
            except Exception:  # pylint: disable=broad-except
                p = ""
            if p and p.lower().endswith(".pdf"):
                pdf_paths.append(p)

        if not pdf_paths:
            return

        # Define diretório automaticamente se todos forem do mesmo local
        dirs = {os.path.dirname(p) for p in pdf_paths}
        if len(dirs) == 1:
            dir_unico = next(iter(dirs))
            if self.diretorio_entry is not None:
                self.diretorio_entry.setText(dir_unico)
        else:
            # Múltiplos diretórios: informa o usuário e não altera o campo
            show_warning(
                "Aviso",
                (
                    "Arquivos de diretórios diferentes detectados. "
                    "O campo 'Diretório dos PDFs' não foi alterado."
                ),
                parent=self,
            )

        # Adiciona somente os nomes (sem extensão) à lista
        nomes_adicionados = []
        for p in pdf_paths:
            nome = os.path.splitext(os.path.basename(p))[0]
            assert self.lista_arquivos_widget is not None
            self.lista_arquivos_widget.addItem(nome)
            nomes_adicionados.append(nome)

        # Ordenar automaticamente após adicionar via drag & drop
        self._ordenar_lista_alfabeticamente()

        show_info(
            "Sucesso",
            f"{len(nomes_adicionados)} arquivo(s) adicionado(s) à lista e ordenado(s) alfabeticamente!",  # pylint: disable=line-too-long
            parent=self,
        )

    def remover_arquivo_selecionado(self):
        """Remove o arquivo selecionado da lista."""
        assert self.lista_arquivos_widget is not None
        item_selecionado = self.lista_arquivos_widget.currentItem()
        if item_selecionado:
            self.lista_arquivos_widget.takeItem(
                self.lista_arquivos_widget.row(item_selecionado)
            )

    def _obter_lista_arquivos_da_widget(self) -> List[str]:
        """Obtém a lista de arquivos da QListWidget."""
        assert self.lista_arquivos_widget is not None
        return [
            self.lista_arquivos_widget.item(i).text()
            for i in range(self.lista_arquivos_widget.count())
        ]

    def _validar_entradas(self) -> bool:
        """Valida se o diretório e a lista de arquivos estão prontos."""
        assert self.diretorio_entry is not None
        if not self.diretorio_entry.text().strip():
            show_error("Erro", "Por favor, selecione um diretório.", parent=self)
            return False
        if not os.path.isdir(self.diretorio_entry.text().strip()):
            show_error("Erro", "O diretório selecionado não existe.", parent=self)
            return False
        assert self.lista_arquivos_widget is not None
        if self.lista_arquivos_widget.count() == 0:
            # MODIFICADO: Uso da função show_warning centralizada
            show_warning(
                "Aviso",
                "A lista de arquivos está vazia. Adicione arquivos para continuar.",
                parent=self,
            )
            return False
        return True

    def verificar_arquivos_existentes(self):
        """Verifica se os arquivos da lista existem no diretório selecionado."""
        assert self.diretorio_entry is not None
        diretorio = self.diretorio_entry.text().strip()
        if not diretorio or not os.path.isdir(diretorio):
            show_error("Erro", "Por favor, selecione um diretório válido.", parent=self)
            return
        lista_arquivos = self._obter_lista_arquivos_da_widget()
        if not lista_arquivos:
            # MODIFICADO: Uso da função show_warning centralizada
            show_warning("Aviso", "A lista de arquivos está vazia.", parent=self)
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
            # MODIFICADO: Uso da função show_info centralizada
            show_info("Verificação Concluída", msg, parent=self)
        except (OSError, ValueError) as e:
            show_error(
                "Erro", f"Ocorreu um erro durante a verificação: {e}", parent=self
            )

    def executar_impressao(self):
        """Inicia o processo de impressão em uma thread separada."""
        if not self._validar_entradas():
            return

        assert self.diretorio_entry is not None
        diretorio = self.diretorio_entry.text().strip()
        lista_arquivos = self._obter_lista_arquivos_da_widget()

        try:
            self.print_manager.buscar_arquivos(diretorio, lista_arquivos)
            resultado_busca = self.print_manager.gerar_relatorio_busca()
            self.resultado_text.setText(resultado_busca)

            if not self.print_manager.arquivos_encontrados:
                show_warning(
                    "Aviso",
                    "Nenhum arquivo válido foi encontrado para impressão.",
                    parent=self,
                )
                return

            self.imprimir_btn.setEnabled(False)
            self.imprimir_btn.setText("🖨️ Imprimindo...")

            if self.progress_bar is not None:
                self.progress_bar.setValue(0)
                self.progress_bar.setVisible(True)

            self.print_worker = PrintWorker(
                diretorio, self.print_manager.arquivos_encontrados
            )
            self.print_worker.progress_update.connect(self.atualizar_resultado)

            if self.progress_bar is not None:
                self.print_worker.progress_percent.connect(self.progress_bar.setValue)
            self.print_worker.processo_finalizado.connect(self.impressao_finalizada)
            self.print_worker.start()

        except (OSError, ValueError) as e:
            show_error("Erro", f"Erro ao iniciar impressão: {e}", parent=self)
            self.imprimir_btn.setEnabled(True)
            self.imprimir_btn.setText("🖨️ Imprimir")

    def atualizar_resultado(self, mensagem: str):
        """Adiciona mensagens de progresso à caixa de texto de resultado."""
        assert self.resultado_text is not None
        self.resultado_text.append(mensagem)
        self.resultado_text.verticalScrollBar().setValue(
            self.resultado_text.verticalScrollBar().maximum()
        )

    def impressao_finalizada(self):
        """Chamado quando a thread de impressão termina."""
        show_info(
            "Processo Concluído", "A impressão em lote foi finalizada.", parent=self
        )
        self.imprimir_btn.setEnabled(True)
        self.imprimir_btn.setText("🖨️ Imprimir")
        self.print_worker = None
        if self.progress_bar is not None:
            self.progress_bar.setValue(100)
            # Ocultar progress bar após 2s, verificando se ainda existe

            def hide_progress():
                if isValid(self.progress_bar):
                    self.progress_bar.setVisible(False)

            QTimer.singleShot(2000, hide_progress)


class FormManager(BaseSingletonFormManager):
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    FORM_CLASS = FormImpressao


def main(parent=None):
    """Ponto de entrada para criar e exibir o formulário de impressão."""
    FormManager.show_form(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        main()
    except (ImportError, NameError) as e:
        show_error(
            "Erro de Dependência",
            f"Não foi possível iniciar o aplicativo: {e}.\n"
            "Execute este formulário a partir do aplicativo principal.",
        )
        sys.exit(1)

    sys.exit(app.exec())
