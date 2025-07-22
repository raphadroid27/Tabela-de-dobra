"""
Launcher da Aplicação de Cálculo de Dobra.

Responsável por:
1. Verificar a existência de novas versões da aplicação a partir de uma pasta local.
2. Forçar o encerramento seguro de todas as instâncias em execução.
3. Aplicar a atualização de forma atômica para evitar corrupção de arquivos.
4. Iniciar a aplicação principal.

Este módulo foi projetado para ser executado como um executável independente.
"""

import sys
import os
import json
import subprocess
import zipfile
import time
import shutil
from datetime import datetime, timedelta
from typing import Tuple, Optional, Type

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from semantic_version import Version

# --- Configuração de Caminhos de Forma Robusta ---


def get_base_dir() -> str:
    """Retorna o diretório base da aplicação, seja em modo script ou executável."""
    # Se estiver rodando como um executável (criado pelo PyInstaller, por exemplo)
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Se estiver rodando como um script python normal
    return os.path.dirname(os.path.abspath(__file__))


# --- Constantes e Caminhos Globais ---
BASE_DIR = get_base_dir()
APP_EXECUTABLE = "app.exe"
APP_PATH = os.path.join(BASE_DIR, APP_EXECUTABLE)
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "tabela_de_dobra.db")
# Pasta de onde as atualizações serão lidas
UPDATES_DIR = os.path.join(BASE_DIR, 'updates')
# Caminho completo para o arquivo de versão
VERSION_FILE_PATH = os.path.join(UPDATES_DIR, 'versao.json')

# Adiciona o diretório 'src' ao path para encontrar os modelos
# Isso é necessário para que o launcher encontre os módulos da aplicação principal
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '.')))

# Importa o modelo e a versão APÓS a configuração do path
try:
    from src.models.models import SystemControl as SystemControlModel
    from src.app import APP_VERSION as LOCAL_APP_VERSION
except ImportError as e:
    print(
        f"[LAUNCHER] ERRO CRÍTICO: Não foi possível importar módulos da aplicação: {e}")
    print("[LAUNCHER] Verifique se o launcher está no diretório correto.")
    # Permite que o usuário veja o erro antes de fechar
    time.sleep(10)
    sys.exit(1)


# --- Funções do Launcher ---

def print_message(message: str) -> None:
    """Imprime uma mensagem formatada para o log do launcher."""
    print(f"[LAUNCHER] {datetime.now():%Y-%m-%d %H:%M:%S} - {message}")


def get_db_session() -> Tuple[Optional[Session], Optional[Type[SystemControlModel]]]:
    """
    Cria e retorna uma sessão do SQLAlchemy para interagir com o banco de dados.

    Returns:
        Uma tupla contendo a instância da sessão e a classe do modelo,
        ou (None, None) em caso de falha.
    """
    if not os.path.exists(DB_PATH):
        print_message(f"ERRO: Banco de dados não encontrado em: {DB_PATH}")
        return None, None
    try:
        engine = create_engine(f'sqlite:///{DB_PATH}')
        session_factory = sessionmaker(bind=engine)
        session = session_factory()
        return session, SystemControlModel
    except SQLAlchemyError as e:
        print_message(
            f"ERRO: Não foi possível conectar ao banco de dados: {e}")
        return None, None


def force_shutdown_all_instances(
    session: Session, system_control_model: Type[SystemControlModel]
) -> bool:
    """
    Envia comando de desligamento e aguarda o fechamento de todas as sessões ativas.

    Args:
        session: A sessão do banco de dados ativa.
        system_control_model: A classe do modelo SystemControl.

    Returns:
        True se todas as instâncias foram fechadas, False caso contrário.
    """
    print_message(
        "Enviando comando de desligamento para todas as instâncias...")
    try:
        # 1. Envia o comando de desligamento para a tabela de controle
        cmd_entry = session.query(system_control_model).filter_by(
            key='UPDATE_CMD').first()
        if cmd_entry:
            cmd_entry.value = 'SHUTDOWN'
            cmd_entry.last_updated = datetime.utcnow()
            session.commit()

        # 2. Aguarda o fechamento das instâncias (timeout de 2 minutos)
        print_message("Aguardando o fechamento das aplicações abertas...")
        start_time = time.time()
        while (time.time() - start_time) < 120:
            # Limpa sessões "mortas" (sem heartbeat há mais de 30 segundos)
            timeout_threshold = datetime.utcnow() - timedelta(seconds=30)
            session.query(system_control_model).filter(
                system_control_model.type == 'SESSION',
                system_control_model.last_updated < timeout_threshold
            ).delete(synchronize_session=False)
            session.commit()

            active_sessions = session.query(
                system_control_model).filter_by(type='SESSION').count()
            print_message(f"Sessões ativas restantes: {active_sessions}")

            if active_sessions == 0:
                print_message(
                    "Todas as instâncias foram fechadas com sucesso.")
                return True
            time.sleep(5)  # Aguarda 5 segundos antes de verificar novamente

        print_message(
            "ERRO: Timeout! Algumas instâncias não fecharam a tempo.")
        return False
    except SQLAlchemyError as e:
        print_message(f"ERRO ao forçar o desligamento: {e}")
        session.rollback()
        return False
    finally:
        # 3. Limpa o comando de desligamento para evitar que futuras instâncias fechem sozinhas
        try:
            cmd_entry = session.query(system_control_model).filter_by(
                key='UPDATE_CMD').first()
            if cmd_entry:
                cmd_entry.value = 'NONE'
                session.commit()
        except SQLAlchemyError as e:
            print_message(f"ERRO ao limpar o comando de desligamento: {e}")
            session.rollback()


def check_for_updates() -> Tuple[bool, Optional[str]]:
    """
    Verifica se há uma nova versão da aplicação disponível na pasta 'updates'.

    Returns:
        Uma tupla (bool, str) indicando se há atualização e o caminho completo
        para o arquivo de download.
    """
    print_message(f"Versão local do app: {LOCAL_APP_VERSION}")
    print_message(f"Verificando atualizações em: {VERSION_FILE_PATH}")

    if not os.path.exists(VERSION_FILE_PATH):
        print_message(
            "Arquivo 'versao.json' não encontrado na pasta 'updates'. Pulando verificação.")
        return False, None

    try:
        with open(VERSION_FILE_PATH, 'r', encoding='utf-8') as f:
            server_info = json.load(f)

        server_version_str = server_info["versao"]
        # Agora esperamos apenas o nome do arquivo
        download_filename = server_info["url_download"]

        print_message(f"Versão disponível no servidor: {server_version_str}")

        # Compara as versões usando o padrão de versionamento semântico
        if Version(server_version_str) > Version(LOCAL_APP_VERSION):
            print_message("Nova versão encontrada!")

            # *** LÓGICA MODIFICADA ***
            # Monta o caminho completo para o arquivo de atualização,
            # considerando que ele está na pasta 'updates'.
            full_download_path = os.path.join(UPDATES_DIR, download_filename)
            print_message(
                f"Caminho do arquivo de atualização: {full_download_path}")

            return True, full_download_path

        print_message("Sua aplicação já está atualizada.")
        return False, None
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
        print_message(f"ERRO ao verificar atualizações: {e}")
        return False, None


def apply_update(zip_filepath: str) -> bool:
    """
    Aplica a atualização a partir de um arquivo .zip de forma atômica.
    CUIDADO: Pode falhar por falta de permissão de escrita.
    Execute o launcher como administrador se necessário.

    Args:
        zip_filepath: O caminho completo para o arquivo zip da atualização.

    Returns:
        True se a atualização foi bem-sucedida, False caso contrário.
    """
    app_dir = BASE_DIR
    temp_extract_dir = os.path.join(app_dir, "_temp_update")
    backup_dir = os.path.join(app_dir, "_backup")

    if not os.path.exists(zip_filepath):
        print_message(
            f"ERRO: Arquivo de atualização não encontrado em {zip_filepath}")
        return False

    try:
        # Limpa diretórios antigos se existirem de uma tentativa anterior
        if os.path.isdir(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)

        print_message(
            f"Extraindo arquivos para pasta temporária: {temp_extract_dir}")
        os.makedirs(temp_extract_dir, exist_ok=True)
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)

        print_message("Criando backup dos arquivos antigos...")
        os.makedirs(backup_dir, exist_ok=True)
        # Itera sobre os novos arquivos para saber o que substituir
        for item_name in os.listdir(temp_extract_dir):
            old_item_path = os.path.join(app_dir, item_name)
            if os.path.exists(old_item_path):
                shutil.move(old_item_path, os.path.join(backup_dir, item_name))

        print_message(
            "Movendo novos arquivos para o diretório da aplicação...")
        for item_name in os.listdir(temp_extract_dir):
            shutil.move(os.path.join(temp_extract_dir, item_name),
                        os.path.join(app_dir, item_name))

        print_message("Atualização aplicada com sucesso!")
        return True

    except (IOError, OSError, zipfile.BadZipFile) as e:
        print_message(f"ERRO ao aplicar a atualização: {e}")
        print_message(
            "Permissão negada? Tente executar o launcher como Administrador.")
        # Tenta restaurar o backup em caso de falha
        _rollback_update(backup_dir, app_dir)
        return False
    finally:
        print_message("Limpando arquivos temporários...")
        if os.path.isdir(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)


def _rollback_update(backup_dir: str, app_dir: str) -> None:
    """Restaura os arquivos a partir do backup em caso de falha na atualização."""
    print_message("...Iniciando rollback da atualização...")
    if not os.path.isdir(backup_dir):
        print_message(
            "Diretório de backup não encontrado. Rollback impossível.")
        return
    try:
        # Move os arquivos de volta do backup para o diretório principal
        for item in os.listdir(backup_dir):
            shutil.move(os.path.join(backup_dir, item),
                        os.path.join(app_dir, item))
        print_message("Rollback concluído. A versão anterior foi restaurada.")
    except OSError as e:
        print_message(
            f"ERRO CRÍTICO DURANTE O ROLLBACK: {e}. A instalação pode estar corrompida.")


def start_application() -> None:
    """Inicia a aplicação principal (app.exe)."""
    if not os.path.exists(APP_PATH):
        print_message(
            f"ERRO: Executável da aplicação não encontrado em: {APP_PATH}")
        return
    print_message(f"Iniciando a aplicação: {APP_PATH}")
    try:
        # Inicia o app como um processo separado
        subprocess.Popen([APP_PATH])
    except (OSError, ValueError) as e:
        print_message(f"ERRO ao iniciar a aplicação: {e}")


def main() -> int:
    """Fluxo principal do Launcher."""
    print_message("=" * 50)
    print_message("Launcher iniciado.")
    print_message(
        "AVISO: A atualização pode exigir permissões de Administrador.")

    update_available, download_path = check_for_updates()

    if update_available and download_path:
        print_message("Atualização encontrada. Preparando para instalar...")
        db_session, model = get_db_session()
        if not db_session:
            print_message(
                "Não foi possível conectar ao DB. A atualização foi cancelada.")
        else:
            if force_shutdown_all_instances(db_session, model):
                if apply_update(download_path):
                    print_message(
                        "Processo de atualização finalizado com sucesso.")
                else:
                    print_message(
                        "Falha ao aplicar a atualização. A versão anterior foi mantida.")
            else:
                print_message(
                    "Não foi possível fechar todas as instâncias do app. "
                    "A atualização foi cancelada."
                )
            db_session.close()

    start_application()
    print_message("Launcher finalizado.")
    print_message("=" * 50)
    time.sleep(3)  # Pequena pausa para o usuário poder ler a saída final
    return 0


if __name__ == "__main__":
    sys.exit(main())
