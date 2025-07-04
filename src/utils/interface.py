"""
Este módulo contém funções auxiliares para o aplicativo de cálculo de dobras.

As funções incluem a atualização de widgets, manipulação de valores de dobras,
restauração de valores, e outras operações relacionadas ao funcionamento do
aplicativo de cálculo de dobras.
"""
import re
import traceback
import pyperclip
from PySide6.QtWidgets import QWidget, QGridLayout, QTreeWidgetItem  # type: ignore
from PySide6.QtCore import QTimer
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.banco_dados import session, obter_configuracoes
from src.utils.calculos import (calcular_dobra,
                                calcular_k_offset,
                                aba_minima_externa,
                                z_minimo_externo,
                                razao_ri_espessura
                                )
from src.config import globals as g


def _atualizar_material():
    """
    Atualiza os valores do combobox de materiais.
    Exibe todos os materiais da tabela Material, ordenados por nome.
    Inicia vazia para permitir seleção manual.
    """
    try:
        # Função auxiliar para atualizar combobox de materiais
        def atualizar_combobox_material(combo):
            if combo and hasattr(combo, 'clear'):
                materiais = [m.nome for m in session.query(
                    Material).order_by(Material.nome)]
                combo.clear()
                combo.addItems(materiais)
                combo.setCurrentIndex(-1)

        # Atualizar combobox principal
        if hasattr(g, 'MAT_COMB') and g.MAT_COMB:
            atualizar_combobox_material(g.MAT_COMB)

        # Atualizar combobox de dedução apenas se não estiver em recarregamento da interface
        if (hasattr(g, 'DED_MATER_COMB') and g.DED_MATER_COMB and
                (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):
            # Sinaliza atualização automática dos comboboxes de dedução
            g.UPDATING_DEDUCAO_COMBOS = True
            try:
                # Capturar valor atual antes de limpar
                valor_atual = g.DED_MATER_COMB.currentText()

                atualizar_combobox_material(g.DED_MATER_COMB)

                # Tentar restaurar o valor anterior se ainda existir na lista
                if valor_atual and valor_atual.strip():
                    index = g.DED_MATER_COMB.findText(valor_atual)
                    g.DED_MATER_COMB.setCurrentIndex(
                        index if index >= 0 else -1)
            finally:
                g.UPDATING_DEDUCAO_COMBOS = False

        # Chamar calcular_valores após atualizar material
        calcular_valores()

    except (AttributeError, RuntimeError, ValueError) as e:
        print(f"Erro ao atualizar materiais: {e}")
        traceback.print_exc()


def _atualizar_espessura():
    """
    Atualiza os valores do combobox de espessuras.
    Exibe apenas as espessuras relacionadas ao material selecionado através da tabela Deducao.
    Só carrega quando um material válido for selecionado.
    """
    if not g.MAT_COMB or not hasattr(g.MAT_COMB, 'currentText'):
        return

    material_nome = g.MAT_COMB.currentText()

    # Limpar espessuras sempre
    if g.ESP_COMB and hasattr(g.ESP_COMB, 'clear'):
        g.ESP_COMB.clear()

    if not material_nome or material_nome.strip() == "":
        return

    material_obj = session.query(Material).filter_by(
        nome=material_nome).first()
    if material_obj and g.ESP_COMB:
        # Buscar espessuras relacionadas ao material através da tabela Deducao
        espessuras = session.query(Espessura).join(Deducao).filter(
            Deducao.material_id == material_obj.id
        ).order_by(Espessura.valor).distinct()

        espessuras_valores = [str(e.valor) for e in espessuras]
        g.ESP_COMB.addItems(espessuras_valores)

    # Verifica se o combobox de dedução de espessura existe e atualiza seus valores
    # Apenas se não estiver em recarregamento da interface
    if (hasattr(g, 'DED_ESPES_COMB') and g.DED_ESPES_COMB and hasattr(g.DED_ESPES_COMB, 'clear') and
            (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):
        # Definir flag para indicar que estamos atualizando os comboboxes de dedução automaticamente
        g.UPDATING_DEDUCAO_COMBOS = True
        try:
            # Capturar valor atual antes de limpar
            valor_atual = g.DED_ESPES_COMB.currentText()

            valores_espessura = session.query(Espessura.valor).distinct().all()
            valores_limpos = [
                float(valor[0]) for valor in valores_espessura if valor[0] is not None]
            g.DED_ESPES_COMB.clear()
            g.DED_ESPES_COMB.addItems([str(valor)
                                      for valor in sorted(valores_limpos)])

            # Tentar restaurar o valor anterior se ainda existir na lista
            if valor_atual and valor_atual.strip():
                index = g.DED_ESPES_COMB.findText(valor_atual)
                g.DED_ESPES_COMB.setCurrentIndex(index if index >= 0 else -1)
            else:
                g.DED_ESPES_COMB.setCurrentIndex(-1)
        finally:
            g.UPDATING_DEDUCAO_COMBOS = False

    # Chamar calcular_valores após atualizar espessura para garantir que
    # os cálculos sejam atualizados
    calcular_valores()


def _atualizar_canal():
    """
    Atualiza os valores do combobox de canais.
    Exibe apenas os canais relacionados ao material e espessura
    selecionados através da tabela Deducao.
    Só carrega quando material e espessura válidos forem selecionados.
    """
    if (not g.ESP_COMB or not hasattr(g.ESP_COMB, 'currentText') or
            not g.MAT_COMB or not hasattr(g.MAT_COMB, 'currentText')):
        return

    espessura_valor = g.ESP_COMB.currentText()
    material_nome = g.MAT_COMB.currentText()

    # Limpar canais sempre
    if g.CANAL_COMB and hasattr(g.CANAL_COMB, 'clear'):
        g.CANAL_COMB.clear()

    # Só continuar se ambos material e espessura estiverem selecionados
    if (not espessura_valor or
        not material_nome or
            espessura_valor.strip() == "" or material_nome.strip() == ""):
        return

    try:
        espessura_obj = session.query(Espessura).filter_by(
            valor=float(espessura_valor)).first()
        material_obj = session.query(Material).filter_by(
            nome=material_nome).first()

        if espessura_obj and material_obj and g.CANAL_COMB:
            # Buscar canais relacionados ao material e espessura através da tabela Deducao
            canais = session.query(Canal).join(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id
            ).order_by(Canal.valor)

            canais_valores = sorted(
                [str(c.valor) for c in canais],
                key=lambda x: float(re.findall(
                    r'\d+\.?\d*', x)[0]) if re.findall(r'\d+\.?\d*', x) else 0
            )

            g.CANAL_COMB.addItems(canais_valores)

        # Verifica se o combobox de dedução de canal existe e atualiza seus valores
        # Apenas se não estiver em recarregamento da interface
        if (hasattr(g, 'DED_CANAL_COMB') and g.DED_CANAL_COMB and hasattr(g.DED_CANAL_COMB,
                                                                          'clear') and
                (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):
            # Sinaliza atualização automática dos comboboxes de dedução
            g.UPDATING_DEDUCAO_COMBOS = True
            try:
                # Capturar valor atual antes de limpar
                valor_atual = g.DED_CANAL_COMB.currentText()

                valores_canal = session.query(Canal.valor).distinct().all()
                valores_canal_limpos = [
                    str(valor[0]) for valor in valores_canal if valor[0] is not None]
                g.DED_CANAL_COMB.clear()
                g.DED_CANAL_COMB.addItems(sorted(valores_canal_limpos))

                # Tentar restaurar o valor anterior se ainda existir na lista
                if valor_atual and valor_atual.strip():
                    index = g.DED_CANAL_COMB.findText(valor_atual)
                    g.DED_CANAL_COMB.setCurrentIndex(
                        index if index >= 0 else -1)
                else:
                    g.DED_CANAL_COMB.setCurrentIndex(-1)
            finally:
                g.UPDATING_DEDUCAO_COMBOS = False

        # Chamar calcular_valores após atualizar canal para garantir que
        # os cálculos sejam atualizados
        calcular_valores()

    except ValueError as e:
        print(f"Erro ao converter valor da espessura: {e}")
    except (AttributeError, RuntimeError) as e:
        print(f"Erro ao atualizar canais: {e}")


def _atualizar_deducao():
    """
    Atualiza os valores de dedução com base nos widgets selecionados.
    Só calcula quando todas as seleções forem válidas (não vazias).
    """
    # Verificar se todos os widgets necessários estão disponíveis
    widgets_requeridos = [
        (g.ESP_COMB, 'currentText'),
        (g.MAT_COMB, 'currentText'),
        (g.CANAL_COMB, 'currentText')
    ]

    for widget, metodo in widgets_requeridos:
        if not widget or not hasattr(widget, metodo):
            return

    # Verificar se alguma combobox não tem seleção (currentIndex == -1)
    if (g.ESP_COMB.currentIndex() == -1 or
        g.MAT_COMB.currentIndex() == -1 or
            g.CANAL_COMB.currentIndex() == -1):

        # Limpar valores de dedução se alguma seleção estiver vazia
        if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
            g.DED_LBL.setText('')
        if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
            g.OBS_LBL.setText('')
        return

    espessura_valor = g.ESP_COMB.currentText()
    material_nome = g.MAT_COMB.currentText()
    canal_valor = g.CANAL_COMB.currentText()

    # Verificar se todas as seleções são válidas (não vazias)
    if (not espessura_valor or not material_nome or not canal_valor or
            espessura_valor.strip() == ("" or material_nome.strip() == ""
                                        or canal_valor.strip() == "")):

        # Limpar valores de dedução se alguma seleção estiver vazia
        if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
            g.DED_LBL.setText('')
        if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
            g.OBS_LBL.setText('')
        return

    try:
        espessura_obj = session.query(Espessura).filter_by(
            valor=float(espessura_valor)).first()
        material_obj = session.query(Material).filter_by(
            nome=material_nome).first()
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if espessura_obj and material_obj and canal_obj:
            deducao_obj = session.query(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id,
                Deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj:
                if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
                    g.DED_LBL.setText(str(deducao_obj.valor))
                    g.DED_LBL.setStyleSheet("")
                observacao = deducao_obj.observacao or 'Observações não encontradas'
                if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
                    g.OBS_LBL.setText(observacao)
            else:
                if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
                    g.DED_LBL.setText('N/A')
                    g.DED_LBL.setStyleSheet("color: red")
                if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
                    g.OBS_LBL.setText('Observações não encontradas')
        else:
            if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
                g.DED_LBL.setText('')
            if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
                g.OBS_LBL.setText('')

        # Chamar calcular_valores após atualizar a dedução para garantir que
        # os cálculos das dobras usem a dedução correta
        calcular_valores()

    except ValueError as e:
        print(f"Erro ao converter valor da espessura: {e}")
    except (AttributeError, RuntimeError) as e:
        print(f"Erro ao atualizar dedução: {e}")


def atualizar_widgets(tipo):
    """
    Atualiza os valores de comboboxes com base no tipo especificado.
    Preserva o estado dos widgets do cabeçalho principal que podem ser afetados pela atualização.

    Args:
        tipo (str): O tipo de combobox a ser atualizado.
    """
    try:
        # Mapeamento de tipos para funções
        acoes = {
            'material': _atualizar_material,
            'espessura': _atualizar_espessura,
            'canal': _atualizar_canal,
            'dedução': _atualizar_deducao
        }

        # Executa a ação correspondente ao tipo
        if tipo in acoes:
            # Capturar valores atuais dos comboboxes do cabeçalho principal antes da atualização
            valores_preservar = {}

            # Preservar seleções do cabeçalho principal que podem ser perdidas pela atualização
            if tipo == 'material' and hasattr(g, 'ESP_COMB') and g.ESP_COMB:
                valores_preservar['ESP_COMB'] = g.ESP_COMB.currentText()
                valores_preservar['CANAL_COMB'] = getattr(
                    g, 'CANAL_COMB', None) and g.CANAL_COMB.currentText()
            elif tipo == 'espessura' and hasattr(g, 'CANAL_COMB') and g.CANAL_COMB:
                valores_preservar['CANAL_COMB'] = g.CANAL_COMB.currentText()

            # Executar a atualização
            acoes[tipo]()

            # Tentar restaurar valores preservados do cabeçalho principal quando possível
            for widget_name, valor in valores_preservar.items():
                if valor:  # Só restaurar se havia um valor
                    widget = getattr(g, widget_name, None)
                    if widget and hasattr(widget, 'setCurrentText'):
                        try:
                            widget.setCurrentText(valor)
                        except (AttributeError, RuntimeError) as e:
                            print(
                                f"Não foi possível restaurar {widget_name}: {e}")

    except (AttributeError, KeyError, RuntimeError) as e:
        print(f"Erro em atualizar_widgets({tipo}): {e}")


def canal_tooltip():
    """
    Atualiza o tooltip do combobox de canais com as
    observações e comprimento total do canal selecionado.
    """
    if not g.CANAL_COMB:
        return

    if g.CANAL_COMB.currentText() == "":
        g.CANAL_COMB.setToolTip("Selecione o canal de dobra.")
    else:
        canal_obj = session.query(Canal).filter_by(
            valor=g.CANAL_COMB.currentText()).first()
        if canal_obj:
            canal_obs = getattr(canal_obj, 'observacao', None) or "N/A."
            canal_comprimento_total = getattr(
                canal_obj, 'comprimento_total', None) or "N/A."

            tooltip_text = f'Obs: {canal_obs}\nComprimento total: {canal_comprimento_total}'
            g.CANAL_COMB.setToolTip(tooltip_text)
        else:
            g.CANAL_COMB.setToolTip("Canal não encontrado.")


def atualizar_toneladas_m():
    """
    Atualiza o valor de toneladas por metro com base no comprimento e na dedução selecionada.
    Só calcula quando todas as seleções forem válidas (não vazias).
    """
    # Verificar se todos os widgets necessários estão disponíveis
    widgets_requeridos = [
        (g.COMPR_ENTRY, 'text'),
        (g.ESP_COMB, 'currentText'),
        (g.MAT_COMB, 'currentText'),
        (g.CANAL_COMB, 'currentText')
    ]

    for widget, metodo in widgets_requeridos:
        if not widget or not hasattr(widget, metodo):
            return

    # Verificar se alguma combobox não tem seleção (currentIndex == -1)
    if (g.ESP_COMB.currentIndex() == -1 or
        g.MAT_COMB.currentIndex() == -1 or
            g.CANAL_COMB.currentIndex() == -1):

        # Limpar valor de força se alguma seleção estiver vazia
        if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
            g.FORCA_LBL.setText('')
        return

    comprimento = g.COMPR_ENTRY.text()
    espessura_valor = g.ESP_COMB.currentText()
    material_nome = g.MAT_COMB.currentText()
    canal_valor = g.CANAL_COMB.currentText()

    # Verificar se todas as seleções são válidas (não vazias)
    if (not espessura_valor or not material_nome or not canal_valor or
            espessura_valor.strip() == ("" or material_nome.strip() == ""
                                        or canal_valor.strip() == "")):

        # Limpar valor de força se alguma seleção estiver vazia
        if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
            g.FORCA_LBL.setText('')
        return

    try:
        espessura_obj = session.query(Espessura).filter_by(
            valor=float(espessura_valor)).first()
        material_obj = session.query(Material).filter_by(
            nome=material_nome).first()
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if espessura_obj and material_obj and canal_obj:
            deducao_obj = session.query(Deducao).filter(
                Deducao.espessura_id == espessura_obj.id,
                Deducao.material_id == material_obj.id,
                Deducao.canal_id == canal_obj.id
            ).first()

            if deducao_obj and deducao_obj.forca is not None:
                toneladas_m = ((deducao_obj.forca * float(comprimento)) / 1000
                               if comprimento else deducao_obj.forca)
                if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
                    g.FORCA_LBL.setText(f'{toneladas_m:.0f}')
                    g.FORCA_LBL.setStyleSheet("")
            else:
                if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
                    g.FORCA_LBL.setText('N/A')
                    g.FORCA_LBL.setStyleSheet("color: red")

        # Verificar se o comprimento é menor que o comprimento total do canal
        if g.CANAL_COMB and hasattr(g.CANAL_COMB, 'currentText') and canal_valor.strip():
            canal_obj = session.query(Canal).filter_by(
                valor=canal_valor).first()
            comprimento_total = getattr(
                canal_obj, 'comprimento_total', None) if canal_obj else None
            comprimento_float = float(comprimento) if comprimento else None

            if canal_obj and comprimento_float and comprimento_total:
                if comprimento_float < comprimento_total:
                    if g.COMPR_ENTRY and hasattr(g.COMPR_ENTRY, 'setStyleSheet'):
                        g.COMPR_ENTRY.setStyleSheet("")
                elif comprimento_float >= comprimento_total:
                    if g.COMPR_ENTRY and hasattr(g.COMPR_ENTRY, 'setStyleSheet'):
                        g.COMPR_ENTRY.setStyleSheet("color: red")

    except ValueError as e:
        print(f"Erro ao converter valores numéricos: {e}")
    except (AttributeError, RuntimeError) as e:
        print(f"Erro ao atualizar toneladas/m: {e}")


def copiar(tipo, numero=None, w=None):
    """
    Copia o valor do label correspondente ao tipo e 
    número especificados para a área de transferência.
    """
    configuracoes = {
        'dedução': {
            'label': g.DED_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'),
                                       calcular_k_offset())
        },
        'fator_k': {
            'label': g.K_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'),
                                       calcular_k_offset())
        },
        'offset': {
            'label': g.OFFSET_LBL,
            'funcao_calculo': lambda: (atualizar_widgets('dedução'),
                                       calcular_k_offset())
        },
        'medida_dobra': {
            'label': lambda numero: getattr(g, f'medidadobra{numero}_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'metade_dobra': {
            'label': lambda numero: getattr(g, f'metadedobra{numero}_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'blank': {
            'label': getattr(g, f'medida_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        },
        'metade_blank': {
            'label': getattr(g, f'metade_blank_label_{w}', None),
            'funcao_calculo': lambda: calcular_dobra(w)
        }
    }

    config = configuracoes[tipo]

    label = config['label'](numero) if callable(
        config['label']) else config['label']
    if label is None:
        print(
            f"Erro: Label não encontrado para o tipo '{tipo}' com numero={numero} e w={w}.")
        return

    # Verificar se o label é um widget válido do PySide6
    if not hasattr(label, 'text') and not hasattr(label, 'setText'):
        print(
            f"Erro: O objeto para o tipo '{tipo}' não é um widget válido do PySide6.")
        return

    # Verificar se o texto está vazio
    try:
        # Para widgets PySide6, usar text() para obter o texto
        texto_atual = label.text() if hasattr(label, 'text') else str(label.text)
        # Converter para string para garantir compatibilidade
        texto_atual = str(texto_atual)
        if texto_atual == "":
            return
    except AttributeError:
        print(
            f"Erro: Não foi possível acessar o texto do widget para o tipo '{tipo}'.")
        return

    # Remover " Copiado!" se já estiver presente para evitar repetição
    if " Copiado!" in texto_atual:
        texto_original = texto_atual.replace(" Copiado!", "")
    else:
        texto_original = texto_atual

    config['funcao_calculo']()

    # Obter o texto atualizado após o cálculo
    try:
        texto_atualizado = label.text() if hasattr(label, 'text') else str(label.text)
        # Converter para string e remover " Copiado!" se já estiver presente
        texto_atualizado = str(texto_atualizado)
        if " Copiado!" in texto_atualizado:
            texto_atualizado = texto_atualizado.replace(" Copiado!", "")
    except AttributeError:
        texto_atualizado = texto_original

    pyperclip.copy(texto_atualizado)
    print(f'Valor copiado {texto_atualizado}')

    # Para widgets PySide6, usar setText() e setStyleSheet() para alterar cor
    if hasattr(label, 'setText'):
        label.setText(f'{texto_atualizado} Copiado!')
        if hasattr(label, 'setStyleSheet'):
            label.setStyleSheet("color: green;")

    # Agendar a remoção do "Copiado!" após 2 segundos usando QTimer
    def remover_copiado():
        try:
            if hasattr(label, 'setText'):
                label.setText(texto_atualizado)
                if hasattr(label, 'setStyleSheet'):
                    label.setStyleSheet("color: black;")
        except AttributeError:
            pass

    # Usar QTimer em vez de after() do Tkinter
    try:
        timer = QTimer()
        timer.timeout.connect(remover_copiado)
        timer.setSingleShot(True)
        timer.start(2000)  # 2 segundos
    except ImportError:
        # Fallback se QTimer não estiver disponível
        print("QTimer não disponível, texto 'Copiado!' não será removido automaticamente")


def limpar_busca(tipo):
    """
    Limpa os campos de busca e atualiza a lista correspondente.
    """
    configuracoes = obter_configuracoes()
    if tipo == 'dedução':
        # Limpar apenas a seleção, mantendo os itens disponíveis
        if configuracoes[tipo]['entries']['material_combo']:
            configuracoes[tipo]['entries']['material_combo'].setCurrentIndex(
                -1)
        if configuracoes[tipo]['entries']['espessura_combo']:
            configuracoes[tipo]['entries']['espessura_combo'].setCurrentIndex(
                -1)
        if configuracoes[tipo]['entries']['canal_combo']:
            configuracoes[tipo]['entries']['canal_combo'].setCurrentIndex(-1)
    else:
        configuracoes[tipo]['busca'].clear()

    listar(tipo)


def focus_next_entry(current_index, w):
    """
    Move o foco para o próximo campo de entrada na aba atual.
    """
    next_index = current_index + 1
    if next_index < g.N:
        next_entry = getattr(g, f'aba{next_index}_entry_{w}', None)
        if next_entry:
            next_entry.setFocus()


def focus_previous_entry(current_index, w):
    """
    Move o foco para o campo de entrada anterior na aba atual.
    """
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(g, f'aba{previous_index}_entry_{w}', None)
        if previous_entry:
            previous_entry.setFocus()


def listar(tipo):
    """
    Lista os itens do banco de dados na interface gráfica.
    """
    try:
        configuracoes = obter_configuracoes()
        config = configuracoes[tipo]

        if config['lista'] is None:
            return

        config['lista'].clear()

        itens = session.query(config['modelo']).order_by(config['ordem']).all()

        if tipo == 'material':
            itens = sorted(itens, key=lambda x: x.nome)

        for item in itens:
            if tipo == 'dedução':
                if item.material is None or item.espessura is None or item.canal is None:
                    continue

            valores = config['valores'](item)
            # Garantir que todos os valores sejam strings
            valores_str = [str(v) if v is not None else '' for v in valores]
            item_widget = QTreeWidgetItem(valores_str)
            config['lista'].addTopLevelItem(item_widget)

    except (AttributeError, RuntimeError, ValueError) as e:
        print(f"Erro ao listar {tipo}: {e}")


def todas_funcoes():
    """
    Executa todas as funções necessárias para atualizar os valores e labels do aplicativo.
    """
    try:
        for tipo in ['material', 'espessura', 'canal', 'dedução']:
            try:
                atualizar_widgets(tipo)
            except (AttributeError, RuntimeError, ValueError) as e:
                print(f"Erro ao atualizar widgets {tipo}: {e}")

        try:
            calcular_k_offset()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular k_offset: {e}")

        try:
            aba_minima_externa()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular aba mínima externa: {e}")

        try:
            z_minimo_externo()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular z mínimo externo: {e}")

        try:
            for w in g.VALORES_W:
                calcular_dobra(w)
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular dobras: {e}")

        try:
            razao_ri_espessura()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular razão ri/espessura: {e}")

    except (AttributeError, RuntimeError) as e:
        print(f"Erro geral em todas_funcoes: {e}")
        traceback.print_exc()


def calcular_valores():
    """
    Executa apenas os cálculos necessários sem atualizar os comboboxes.
    Usada quando apenas valores de entrada mudam, não seleções de combobox.
    """
    try:
        try:
            calcular_k_offset()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular k_offset: {e}")

        try:
            aba_minima_externa()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular aba mínima externa: {e}")

        try:
            z_minimo_externo()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular z mínimo externo: {e}")

        try:
            for w in g.VALORES_W:
                calcular_dobra(w)
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular dobras: {e}")

        try:
            razao_ri_espessura()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao calcular razão ri/espessura: {e}")

        try:
            atualizar_toneladas_m()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao atualizar toneladas/m: {e}")

    except (AttributeError, RuntimeError) as e:
        print(f"Erro geral em calcular_valores: {e}")


def configurar_main_frame(parent, rows=4):
    """
    Configura o frame principal com colunas e linhas padrão.
    """
    main_frame = QWidget(parent)
    layout = QGridLayout(main_frame)
    main_frame.setLayout(layout)

    # Configurar o layout principal do parent para usar o main_frame
    if not parent.layout():
        parent_layout = QGridLayout(parent)
        parent.setLayout(parent_layout)

    parent.layout().addWidget(main_frame)

    return main_frame
