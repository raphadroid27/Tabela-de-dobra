"""
Widget de gerenciamento de sessões/instâncias para a interface administrativa.
"""

import logging
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.utils.estilo import aplicar_estilo_botao, aplicar_estilo_table_widget
from src.utils.session_manager import (
    force_shutdown_all_instances,
    obter_sessoes_ativas,
)
from src.utils.utilitarios import (
    aplicar_medida_borda_espaco,
    ask_yes_no,
    show_error,
    show_info,
)
from src.utils.interface_manager import safe_process_events


class InstancesWidget(QWidget):
    """Widget para a aba de Gerenciamento de Instâncias."""

    def __init__(self, parent=None):
        """Inicializa o widget de gerenciamento de instâncias."""
        super().__init__(parent)
        self.table_sessoes = QTableWidget()
        self.label_total_instancias = QLabel("0")
        self.label_ultima_atualizacao = QLabel("N/A")
        self.status_label = QLabel()
        self.timer_atualizacao = QTimer(self)
        self._setup_ui()
        self._initialize_data()

    def _setup_ui(self):
        """Configura a interface do usuário para o widget."""
        main_layout = QVBoxLayout(self)
        aplicar_medida_borda_espaco(main_layout, 10, 10)

        frame_info = self._create_info_frame()
        main_layout.addWidget(frame_info)

        self.table_sessoes.setColumnCount(3)
        self.table_sessoes.setHorizontalHeaderLabels(
            ["ID Sessão", "Hostname", "Última Atividade"]
        )
        header = self.table_sessoes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_sessoes.setColumnWidth(0, 80)
        self.table_sessoes.setToolTip("Lista de instâncias ativas da aplicação")
        aplicar_estilo_table_widget(self.table_sessoes)
        self.table_sessoes.setSortingEnabled(True)
        self.table_sessoes.setAlternatingRowColors(True)
        self.table_sessoes.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table_sessoes.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table_sessoes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_sessoes.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table_sessoes)

        action_buttons = self._create_action_buttons()
        main_layout.addWidget(action_buttons)

        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #0078d4; margin-top: 5px;")
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado para o widget de instâncias."""
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self._load_sessions)

    def _create_info_frame(self):
        """Cria o frame de informações do sistema."""
        frame = QGroupBox("Informações do Sistema")
        layout = QGridLayout(frame)
        aplicar_medida_borda_espaco(layout)
        layout.addWidget(QLabel("Total de Instâncias Ativas:"), 0, 0)
        self.label_total_instancias.setStyleSheet("font-weight: bold; color: #0078d4;")
        layout.addWidget(self.label_total_instancias, 0, 1)
        layout.addWidget(QLabel("Última Atualização:"), 1, 0)
        layout.addWidget(self.label_ultima_atualizacao, 1, 1)
        return frame

    def _create_action_buttons(self):
        """Cria o container com os botões de ação."""
        container = QWidget()
        buttons_layout = QHBoxLayout(container)
        aplicar_medida_borda_espaco(buttons_layout, 0)
        buttons_layout.setSpacing(10)

        atualizar_btn = QPushButton("🔄 Atualizar")
        atualizar_btn.setToolTip("Atualizar lista de instâncias ativas (F5)")
        atualizar_btn.setShortcut(QKeySequence("F5"))
        aplicar_estilo_botao(atualizar_btn, "azul")
        atualizar_btn.clicked.connect(self._load_sessions)
        buttons_layout.addWidget(atualizar_btn)

        shutdown_btn = QPushButton("⚠️ Shutdown Geral")
        shutdown_btn.setToolTip("Encerrar todas as instâncias ativas (Ctrl+Shift+Q)")
        shutdown_btn.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        aplicar_estilo_botao(shutdown_btn, "vermelho")
        shutdown_btn.clicked.connect(self._start_global_shutdown)
        buttons_layout.addWidget(shutdown_btn)

        return container

    def _initialize_data(self):
        """Inicializa os dados e o timer de atualização."""
        self._load_sessions()
        self.timer_atualizacao.timeout.connect(self._load_sessions)
        self.timer_atualizacao.start(10000)

    def _load_sessions(self):
        """Carrega e exibe as sessões ativas."""
        try:
            self.table_sessoes.setRowCount(0)
            sessoes = obter_sessoes_ativas()
            self.label_total_instancias.setText(str(len(sessoes)))
            self.label_ultima_atualizacao.setText(datetime.now().strftime("%H:%M:%S"))
            for sessao in sessoes:
                row_position = self.table_sessoes.rowCount()
                self.table_sessoes.insertRow(row_position)
                self.table_sessoes.setItem(
                    row_position,
                    0,
                    QTableWidgetItem(sessao.get("session_id", "N/A")[:8]),
                )
                self.table_sessoes.setItem(
                    row_position, 1, QTableWidgetItem(sessao.get("hostname", "N/A"))
                )
                self.table_sessoes.setItem(
                    row_position, 2, QTableWidgetItem(sessao.get("last_updated", "N/A"))
                )
            self.table_sessoes.setCurrentCell(-1, -1)
        except (KeyError, AttributeError, TypeError) as e:
            logging.error("Erro ao carregar sessões: %s", e)
            self._set_status_message("Erro ao carregar sessões.")

    def _update_shutdown_status(self, active_sessions: int):
        """Atualiza a mensagem de status durante o shutdown."""
        self._set_status_message(f"Aguardando {active_sessions} instância(s) fechar...")

    def _start_global_shutdown(self):
        """Inicia o processo de encerramento de todas as instâncias."""
        msg = "Todas as instâncias da aplicação serão fechadas. Deseja continuar?"
        if not ask_yes_no("Confirmar Shutdown", msg, parent=self):
            return
        self._set_status_message("Enviando comando de encerramento...")
        safe_process_events()

        success = False
        try:
            success = force_shutdown_all_instances(self._update_shutdown_status)
        except (RuntimeError, ConnectionError, TimeoutError) as e:
            logging.error("Erro no shutdown: %s", e)
            show_error(
                "Erro no Encerramento",
                f"Não foi possível executar o encerramento: {e}",
                parent=self,
            )

        if success:
            show_info(
                "Sucesso",
                "Todas as instâncias foram encerradas com sucesso.",
                parent=self,
            )
            self._set_status_message("Encerramento concluído com sucesso.")
        else:
            show_error("Timeout", "As instâncias não fecharam a tempo.", parent=self)
            self._set_status_message("Falha no encerramento (timeout).")

        self._load_sessions()
        QTimer.singleShot(5000, lambda: self._set_status_message(""))

    def _set_status_message(self, message: str):
        """Define a mensagem de status e controla a visibilidade do label."""
        if message:
            self.status_label.setText(message)
            self.status_label.setVisible(True)
        else:
            self.status_label.setVisible(False)

    def stop_timer(self):
        """Para o timer de atualização."""
        self.timer_atualizacao.stop()
