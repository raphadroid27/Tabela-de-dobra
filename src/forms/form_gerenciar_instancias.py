"""
Formulário para gerenciamento de instâncias do sistema.

Este módulo implementa uma interface gráfica para administradores
visualizarem e gerenciarem instâncias ativas do sistema, incluindo
a funcionalidade de shutdown remoto de todas as instâncias.
"""

import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.components.barra_titulo import BarraTitulo
from src.utils import session_manager
from src.utils.estilo import aplicar_estilo_botao, obter_tema_atual
from src.utils.janelas import Janela
from src.utils.usuarios import tem_permissao
from src.utils.utilitarios import ICON_PATH, aplicar_medida_borda_espaco

# Constantes para configuração da interface
JANELA_LARGURA = 360
JANELA_ALTURA = 360
COLUNA_ID_LARGURA = 80
COLUNA_HOSTNAME_LARGURA = 110
COLUNA_ATIVIDADE_LARGURA = 150
TITULO_FORMULARIO = "Gerenciar Instâncias do Sistema"
TIMER_ATUALIZACAO_MS = 60000  # 60 segundos


class FormGerenciarInstancias(QDialog):
    """Janela para gerenciar instâncias ativas do sistema."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Atributos da instância para os widgets
        self.tree_sessoes = None
        self.label_total_instancias = None
        self.label_ultima_atualizacao = None
        self.timer_atualizacao = QTimer(self)

        self._inicializar_ui()
        self._inicializar_dados()

    def _inicializar_ui(self):
        """Configura a interface gráfica da janela."""
        self.setWindowTitle(TITULO_FORMULARIO)
        self.setFixedSize(JANELA_LARGURA, JANELA_ALTURA)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        # self.setModal(True)

        # pylint: disable=R0801
        if ICON_PATH:
            self.setWindowIcon(QIcon(ICON_PATH))

        Janela.aplicar_no_topo(self)
        Janela.posicionar_janela(self, None)

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)

        barra_titulo = BarraTitulo(self, tema=obter_tema_atual())
        barra_titulo.titulo.setText(TITULO_FORMULARIO)
        vlayout.addWidget(barra_titulo)

        conteudo = self._criar_widget_conteudo()
        vlayout.addWidget(conteudo)

    def _criar_widget_conteudo(self):
        """Cria o widget de conteúdo principal com todos os frames."""
        conteudo = QWidget()
        main_layout = QGridLayout(conteudo)
        aplicar_medida_borda_espaco(main_layout, 10)

        frame_info = self._criar_frame_informacoes()
        main_layout.addWidget(frame_info, 0, 0, 1, 3)

        frame_sessoes = self._criar_frame_sessoes()
        main_layout.addWidget(frame_sessoes, 1, 0, 1, 3)

        self._criar_botoes_acao(main_layout)

        return conteudo

    def _criar_frame_informacoes(self):
        """Cria o frame de informações do sistema."""
        frame_info = QGroupBox("ℹ️ Informações do Sistema")
        info_layout = QGridLayout(frame_info)

        info_layout.addWidget(QLabel("Total de Instâncias Ativas:"), 0, 0)
        self.label_total_instancias = QLabel("0")
        self.label_total_instancias.setStyleSheet("font-weight: bold; color: #0078d4;")
        info_layout.addWidget(self.label_total_instancias, 0, 1)

        info_layout.addWidget(QLabel("Última Atualização:"), 1, 0)
        self.label_ultima_atualizacao = QLabel("Carregando...")
        info_layout.addWidget(self.label_ultima_atualizacao, 1, 1)

        return frame_info

    def _criar_frame_sessoes(self):
        """Cria o frame de sessões ativas."""
        frame_sessoes = QGroupBox("🖥️ Instâncias Ativas")
        sessoes_layout = QVBoxLayout(frame_sessoes)

        self.tree_sessoes = QTreeWidget()
        self.tree_sessoes.setHeaderLabels(["ID Sessão", "Hostname", "Última Atividade"])
        self.tree_sessoes.setColumnWidth(0, COLUNA_ID_LARGURA)
        self.tree_sessoes.setColumnWidth(1, COLUNA_HOSTNAME_LARGURA)
        self.tree_sessoes.setColumnWidth(2, COLUNA_ATIVIDADE_LARGURA)
        sessoes_layout.addWidget(self.tree_sessoes)

        return frame_sessoes

    def _criar_botoes_acao(self, layout):
        """Cria e posiciona os botões de ação no layout fornecido."""
        atualizar_btn = QPushButton("🔄 Atualizar")
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._carregar_sessoes)
        layout.addWidget(atualizar_btn, 2, 0)

        shutdown_btn = QPushButton("⚠️ Shutdown Geral")
        aplicar_estilo_botao(shutdown_btn, "vermelho")
        shutdown_btn.clicked.connect(self._executar_shutdown_geral)
        layout.addWidget(shutdown_btn, 2, 1)

        relatorio_btn = QPushButton("📊 Relatório")
        aplicar_estilo_botao(relatorio_btn, "verde")
        relatorio_btn.clicked.connect(self._gerar_relatorio)
        layout.addWidget(relatorio_btn, 2, 2)

    def _inicializar_dados(self):
        """Carrega os dados iniciais e configura o timer de atualização."""
        self._carregar_sessoes()
        self.timer_atualizacao.timeout.connect(self._carregar_sessoes)
        self.timer_atualizacao.start(TIMER_ATUALIZACAO_MS)

    def _carregar_sessoes(self):
        """Carrega e exibe as sessões ativas na árvore."""
        if not self.tree_sessoes:
            return
        try:
            self.tree_sessoes.clear()
            sessoes = session_manager.obter_sessoes_ativas()

            self.label_total_instancias.setText(str(len(sessoes)))
            agora = datetime.now().strftime("%H:%M:%S")
            self.label_ultima_atualizacao.setText(agora)

            for sessao in sessoes:
                item = QTreeWidgetItem(
                    [
                        sessao.get("session_id", "N/A"),
                        sessao.get("hostname", "N/A"),
                        sessao.get("last_updated", "N/A"),
                    ]
                )
                self.tree_sessoes.addTopLevelItem(item)
        except (AttributeError, TypeError, ValueError) as e:
            QMessageBox.warning(self, "Erro", f"Erro ao carregar sessões: {e}")

    def _executar_shutdown_geral(self):
        """Executa o shutdown de todas as instâncias após confirmação."""
        msg = (
            "⚠️ ATENÇÃO! "
            "Esta ação irá fechar TODAS as instâncias do sistema. "
            "Deseja continuar?"
        )
        resposta = QMessageBox.question(
            self,
            "Confirmar Shutdown",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                session_manager.definir_comando_sistema("SHUTDOWN")
                info_msg = (
                    "✅ Comando de shutdown enviado para todas as instâncias. "
                    "As instâncias serão fechadas nos próximos segundos."
                )
                QMessageBox.information(self, "Comando Enviado", info_msg)
                self._carregar_sessoes()
            except (RuntimeError, ConnectionError, ValueError) as e:
                QMessageBox.critical(self, "Erro", f"Erro ao enviar comando: {e}")

    def _gerar_relatorio(self):
        """Gera um relatório textual das instâncias ativas."""
        try:
            sessoes = session_manager.obter_sessoes_ativas()
            if not sessoes:
                QMessageBox.information(
                    self, "Relatório", "📊 Nenhuma instância ativa encontrada."
                )
                return

            relatorio = f"📊 RELATÓRIO DE INSTÂNCIAS ATIVAS\n{'=' * 50}\n\n"
            relatorio += f"Total de Instâncias: {len(sessoes)}\n\n"
            for i, sessao in enumerate(sessoes, 1):
                relatorio += f"{i}. ID: {sessao.get('session_id', 'N/A')}\n"
                relatorio += f"   Host: {sessao.get('hostname', 'N/A')}\n"
                relatorio += f"   Atividade: {sessao.get('last_updated', 'N/A')}\n\n"
            QMessageBox.information(self, "Relatório de Instâncias", relatorio)
        except (AttributeError, TypeError, ValueError) as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def closeEvent(self, event):  # pylint: disable=invalid-name
        """Garante que o timer pare quando a janela for fechada."""
        self.timer_atualizacao.stop()
        event.accept()


class FormManager:
    """Gerencia a instância do formulário para garantir que seja um singleton."""

    _instance = None

    @classmethod
    def show_form(cls, parent=None):
        """Cria e exibe o formulário, garantindo uma única instância visível."""
        if cls._instance is None or not cls._instance.isVisible():
            cls._instance = FormGerenciarInstancias(parent)
            cls._instance.show()
        else:
            cls._instance.activateWindow()
            cls._instance.raise_()


def main(parent=None):
    """
    Função principal para abrir o formulário de gerenciamento de instâncias.
    Apenas administradores podem acessar esta funcionalidade.
    """
    if not tem_permissao("usuario", "admin"):
        return

    try:
        FormManager.show_form(parent)
    except (RuntimeError, ValueError, ConnectionError) as e:
        QMessageBox.critical(
            parent, "Erro", f"Erro ao abrir gerenciamento de instâncias: {e}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # para rodar o mockup é necessário desativar a função tem_permissao
    main()
    sys.exit(app.exec())
