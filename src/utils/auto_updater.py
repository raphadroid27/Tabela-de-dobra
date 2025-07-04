"""
Sistema de Auto-Update para o aplicativo Cálculo de Dobra.
Permite atualizar o executável sem interromper o trabalho dos usuários.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import QThread, pyqtSignal, QTimer
from .update_paths import obter_caminho_updates, obter_caminho_executavel, obter_diretorio_aplicativo


class UpdateChecker(QThread):
    """Thread para verificar atualizações sem bloquear a interface."""

    update_available = pyqtSignal(dict)  # Sinal com info da atualização
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, current_version, update_server_path):
        super().__init__()
        self.current_version = current_version
        self.update_server_path = update_server_path

    def run(self):
        """Verifica se há atualizações disponíveis."""
        try:
            version_file = os.path.join(
                self.update_server_path, 'version.json')

            if not os.path.exists(version_file):
                self.no_update.emit()
                return

            with open(version_file, 'r', encoding='utf-8') as f:
                version_info = json.load(f)

            server_version = version_info.get('version', '0.0.0')

            if self._is_newer_version(server_version, self.current_version):
                self.update_available.emit(version_info)
            else:
                self.no_update.emit()

        except (OSError, json.JSONDecodeError) as e:
            self.error_occurred.emit(f"Erro ao verificar atualizações: {e}")

    def _is_newer_version(self, server_version, current_version):
        """Compara versões no formato x.y.z"""
        try:
            server_parts = [int(x) for x in server_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]

            # Normalizar tamanhos
            max_len = max(len(server_parts), len(current_parts))
            server_parts.extend([0] * (max_len - len(server_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            return server_parts > current_parts
        except (ValueError, IndexError):
            return False


class AutoUpdater:
    """Classe principal para gerenciar atualizações automáticas."""

    def __init__(self, current_version="1.0.0"):
        self.current_version = current_version
        # Usar funções utilitárias para obter caminhos
        self.update_server_path = obter_caminho_updates()
        self.app_path = obter_caminho_executavel()
        self.app_dir = obter_diretorio_aplicativo()
        self.show_no_update_message = False  # Inicializar aqui

        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_for_updates)
        self.checker = None  # Inicializar como None

    def start_periodic_check(self, interval_minutes=30):
        """Inicia verificação periódica de atualizações."""
        self.check_timer.start(interval_minutes * 60 *
                               1000)  # Converter para ms
        # Verificar imediatamente na inicialização
        # Aguardar 5s após startup
        QTimer.singleShot(5000, self.check_for_updates)

    def check_for_updates(self, show_no_update_message=False):
        """Verifica atualizações em background."""
        self.show_no_update_message = show_no_update_message
        self.checker = UpdateChecker(
            self.current_version, self.update_server_path)
        self.checker.update_available.connect(self._on_update_available)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.error_occurred.connect(self._on_error)
        self.checker.start()

    def _on_update_available(self, version_info):
        """Chamado quando há atualização disponível."""
        version = version_info.get('version', 'Desconhecida')
        changelog = version_info.get('changelog', 'Sem detalhes disponíveis.')
        mandatory = version_info.get('mandatory', False)

        if mandatory:
            self._show_mandatory_update(version, changelog, version_info)
        else:
            self._show_optional_update(version, changelog, version_info)

    def _on_no_update(self):
        """Chamado quando não há atualizações."""
        if hasattr(self, 'show_no_update_message') and self.show_no_update_message:
            QMessageBox.information(
                None,
                "Verificação de Atualizações",
                f"Você está usando a versão mais recente ({self.current_version}).\nNenhuma atualização disponível."
            )
        else:
            print("Sistema atualizado - nenhuma atualização disponível.")

    def _on_error(self, error_msg):
        """Chamado quando há erro na verificação."""
        if hasattr(self, 'show_no_update_message') and self.show_no_update_message:
            QMessageBox.warning(
                None,
                "Erro na Verificação",
                f"Não foi possível verificar atualizações:\n{error_msg}\n\nVerifique sua conexão com o servidor de atualizações."
            )
        else:
            print(f"Erro na verificação de atualizações: {error_msg}")

    def _show_update_dialog(self, version, changelog, version_info, mandatory=False):
        """Mostra diálogo unificado para atualizações."""
        msg = QMessageBox()

        if mandatory:
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Atualização Obrigatória")
            msg.setText(f"Atualização obrigatória para versão {version}")
            msg.setInformativeText(
                "Esta atualização é obrigatória e será aplicada automaticamente.")
            msg.setStandardButtons(QMessageBox.Ok)
        else:
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Atualização Disponível")
            msg.setText(f"Nova versão {version} disponível!")
            msg.setInformativeText("Deseja atualizar agora?")
            msg.setStandardButtons(
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Later)
            msg.setDefaultButton(QMessageBox.Later)

        msg.setDetailedText(f"Changelog:\n{changelog}")
        result = msg.exec()

        if mandatory or result == QMessageBox.Yes:
            self._perform_update(version_info, mandatory)
        elif result == QMessageBox.Later:
            # Perguntar novamente em 1 hora
            QTimer.singleShot(3600000, self.check_for_updates)

    def _show_optional_update(self, version, changelog, version_info):
        """Mostra diálogo para atualização opcional."""
        self._show_update_dialog(
            version, changelog, version_info, mandatory=False)

    def _show_mandatory_update(self, version, changelog, version_info):
        """Mostra diálogo para atualização obrigatória."""
        self._show_update_dialog(
            version, changelog, version_info, mandatory=True)

    def _perform_update(self, version_info, mandatory=False):
        """Executa o processo de atualização."""
        try:
            # Criar diálogo de progresso
            progress = QProgressDialog(
                "Preparando atualização...", "Cancelar", 0, 100)
            progress.setWindowTitle("Atualizando Aplicativo")
            progress.setModal(True)
            progress.show()

            # Passo 1: Verificar arquivos (10%)
            progress.setValue(10)
            progress.setLabelText("Verificando arquivos de atualização...")

            new_exe_path = os.path.join(self.update_server_path, version_info.get(
                'filename', 'Cálculo de Dobra_new.exe'))

            if not os.path.exists(new_exe_path):
                raise FileNotFoundError(
                    f"Arquivo de atualização não encontrado: {new_exe_path}")

            # Passo 2: Criar backup (30%)
            progress.setValue(30)
            progress.setLabelText("Criando backup da versão atual...")

            backup_dir = os.path.join(os.path.dirname(self.app_path), 'backup')
            os.makedirs(backup_dir, exist_ok=True)

            backup_path = os.path.join(
                backup_dir, f"Cálculo de Dobra_backup_{int(time.time())}.exe")
            shutil.copy2(self.app_path, backup_path)

            # Passo 3: Preparar script de atualização (50%)
            progress.setValue(50)
            progress.setLabelText("Preparando script de atualização...")

            update_script = self._create_update_script(
                new_exe_path, self.app_path, backup_path)

            # Passo 4: Executar atualização (70%)
            progress.setValue(70)
            progress.setLabelText("Aplicando atualização...")

            if mandatory:
                # Para atualizações obrigatórias, executar imediatamente
                self._execute_update_script(update_script)
            else:
                # Para opcionais, dar opção de quando aplicar
                self._schedule_update(update_script)

            progress.setValue(100)
            progress.setLabelText("Atualização concluída!")

            time.sleep(1)
            progress.close()

            # Informar sucesso
            QMessageBox.information(
                None,
                "Atualização Concluída",
                "A atualização será aplicada na próxima inicialização do programa."
            )

        except (OSError, shutil.Error, FileNotFoundError) as e:
            progress.close()
            QMessageBox.critical(
                None,
                "Erro na Atualização",
                f"Erro durante a atualização: {e}"
            )

    def _create_update_script(self, source_path, target_path, backup_path):
        """Cria script batch para atualização."""
        script_content = f"""@echo off
echo Iniciando atualizacao do Calculo de Dobra...
timeout /t 2 /nobreak > nul

REM Aguardar o processo principal fechar
:wait_loop
tasklist /FI "IMAGENAME eq Cálculo de Dobra.exe" 2>NUL | find /I /N "Cálculo de Dobra.exe">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto wait_loop
)

echo Aplicando atualizacao...
copy /Y "{source_path}" "{target_path}"

if %ERRORLEVEL% EQU 0 (
    echo Atualizacao aplicada com sucesso!
    REM Reiniciar aplicativo
    start "" "{target_path}"
) else (
    echo Erro na atualizacao! Restaurando backup...
    copy /Y "{backup_path}" "{target_path}"
    start "" "{target_path}"
)

REM Limpar script temporário
del "%~f0"
"""

        script_path = os.path.join(self.app_dir, 'update_temp.bat')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

    def _execute_update_script(self, script_path):
        """Executa o script de atualização e fecha o aplicativo."""
        subprocess.Popen([script_path], shell=True)
        # Fechar aplicativo atual
        QTimer.singleShot(1000, lambda: sys.exit(0))

    def _schedule_update(self, script_path):
        """Agenda atualização para o próximo fechamento."""
        # Salvar caminho do script para executar no fechamento
        with open(os.path.join(self.app_dir, 'pending_update.txt'), 'w', encoding='utf-8') as f:
            f.write(script_path)

    def check_pending_update(self):
        """Verifica se há atualização pendente no startup."""
        pending_file = os.path.join(self.app_dir, 'pending_update.txt')
        if os.path.exists(pending_file):
            try:
                with open(pending_file, 'r', encoding='utf-8') as f:
                    script_path = f.read().strip()

                if os.path.exists(script_path):
                    result = QMessageBox.question(
                        None,
                        "Atualização Pendente",
                        "Há uma atualização pendente. Aplicar agora?",
                        QMessageBox.Yes | QMessageBox.No
                    )

                    if result == QMessageBox.Yes:
                        self._execute_update_script(script_path)
                        return True

                os.remove(pending_file)
            except (OSError, IOError):
                pass  # Falha silenciosa na limpeza

        return False

    def check_for_updates_manual(self):
        """Verifica atualizações manualmente e fornece feedback direto ao usuário."""
        self.check_for_updates(show_no_update_message=True)


# Função para integrar no app principal
def setup_auto_updater(app_version="1.0.0"):
    """Configura o sistema de auto-update."""
    updater = AutoUpdater(app_version)

    # Verificar atualização pendente no startup
    if not updater.check_pending_update():
        # Iniciar verificação periódica
        updater.start_periodic_check(interval_minutes=30)

    return updater
