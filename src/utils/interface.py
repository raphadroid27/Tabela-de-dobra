"""
Este módulo contém funções auxiliares para o aplicativo de cálculo de dobras.

As funções incluem a atualização de widgets, manipulação de valores de dobras,
restauração de valores, e outras operações relacionadas ao funcionamento do
aplicativo de cálculo de dobras.
"""

import re
import traceback
import pyperclip
from PySide6.QtWidgets import QWidget, QGridLayout, QTreeWidgetItem
from PySide6.QtCore import QTimer
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.banco_dados import session, obter_configuracoes
from src.utils.calculos import (calcular_dobra,
                                calcular_k_offset,
                                aba_minima_externa,
                                z_minimo_externo,
                                razao_ri_espessura)
from src.config import globals as g


class CopyManager:
    """Gerencia operações de cópia de valores dos widgets."""

    def __init__(self):
        self.configuracoes = {
            'dedução': {
                'label': g.DED_LBL,
                'funcao_calculo': lambda: (atualizar_widgets('dedução'), calcular_k_offset())
            },
            'fator_k': {
                'label': g.K_LBL,
                'funcao_calculo': lambda: (atualizar_widgets('dedução'), calcular_k_offset())
            },
            'offset': {
                'label': g.OFFSET_LBL,
                'funcao_calculo': lambda: (atualizar_widgets('dedução'), calcular_k_offset())
            },
            'medida_dobra': {
                'label': lambda numero, w: getattr(g, f'medidadobra{numero}_label_{w}', None),
                'funcao_calculo': calcular_dobra
            },
            'metade_dobra': {
                'label': lambda numero, w: getattr(g, f'metadedobra{numero}_label_{w}', None),
                'funcao_calculo': calcular_dobra
            },
            'blank': {
                'label': lambda numero, w: getattr(g, f'medida_blank_label_{w}', None),
                'funcao_calculo': calcular_dobra
            },
            'metade_blank': {
                'label': lambda numero, w: getattr(g, f'metade_blank_label_{w}', None),
                'funcao_calculo': calcular_dobra
            }
        }

    def obter_label(self, tipo, numero=None, w=None):
        """Obtém o label correspondente ao tipo especificado."""
        config = self.configuracoes.get(tipo)
        if not config:
            return None

        label_func = config['label']
        if callable(label_func):
            return label_func(numero, w) if numero is not None else label_func(w)
        return label_func

    def validar_label(self, label, tipo, numero=None, w=None):
        """Valida se o label é válido para operações."""
        if label is None:
            print(
                f"Erro: Label não encontrado para o tipo '{tipo}' com numero={numero} e w={w}.")
            return False

        if not hasattr(label, 'text') and not hasattr(label, 'setText'):
            print(
                f"Erro: O objeto para o tipo '{tipo}' não é um widget válido do PySide6.")
            return False

        return True

    def obter_texto_atual(self, label):
        """Obtém o texto atual do label de forma segura."""
        try:
            texto_atual = label.text() if hasattr(label, 'text') else str(label.text)
            return str(texto_atual)
        except AttributeError:
            return ""

    def executar_calculo(self, tipo, w=None):
        """Executa o cálculo correspondente ao tipo."""
        config = self.configuracoes.get(tipo)
        if not config:
            return

        funcao_calculo = config['funcao_calculo']
        if w is not None:
            funcao_calculo(w)
        else:
            funcao_calculo()

    def atualizar_label_copiado(self, label, texto_atualizado):
        """Atualiza o label com indicação de copiado."""
        if not hasattr(label, 'setText'):
            return

        label.setText(f'{texto_atualizado} Copiado!')
        if hasattr(label, 'setStyleSheet'):
            label.setStyleSheet("color: green;")

    def agendar_remocao_copiado(self, label, texto_original):
        """Agenda a remoção da indicação 'Copiado!' após 2 segundos."""
        def remover_copiado():
            try:
                if hasattr(label, 'setText'):
                    label.setText(texto_original)
                if hasattr(label, 'setStyleSheet'):
                    label.setStyleSheet("color: black;")
            except AttributeError:
                pass

        try:
            timer = QTimer()
            timer.timeout.connect(remover_copiado)
            timer.setSingleShot(True)
            timer.start(2000)  # 2 segundos
        except ImportError:
            print(
                "QTimer não disponível, texto 'Copiado!' não será removido automaticamente")


class ListManager:
    """Gerencia operações de listagem de dados."""

    def __init__(self):
        self.configuracoes = None

    def inicializar_configuracoes(self):
        """Inicializa as configurações necessárias."""
        try:
            self.configuracoes = obter_configuracoes()
            return True
        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Erro ao obter configurações: {e}")
            return False

    def validar_configuracao(self, tipo):
        """Valida se a configuração existe para o tipo especificado."""
        if not self.configuracoes or tipo not in self.configuracoes:
            return False

        config = self.configuracoes[tipo]
        return config.get('lista') is not None

    def limpar_lista(self, tipo):
        """Limpa a lista da interface."""
        config = self.configuracoes[tipo]
        if config['lista']:
            config['lista'].clear()

    def obter_itens_ordenados(self, tipo):
        """Obtém itens do banco de dados ordenados."""
        config = self.configuracoes[tipo]
        itens = session.query(config['modelo']).order_by(config['ordem']).all()

        if tipo == 'material':
            return sorted(itens, key=lambda x: x.nome)
        return itens

    def processar_item_deducao(self, item):
        """Processa item específico de dedução."""
        if item.material is None or item.espessura is None or item.canal is None:
            return None
        return item

    def criar_item_widget(self, item, config):
        """Cria widget do item para a lista."""
        valores = config['valores'](item)
        valores_str = [str(v) if v is not None else '' for v in valores]
        return QTreeWidgetItem(valores_str)

    def adicionar_item_a_lista(self, item_widget, config):
        """Adiciona item widget à lista."""
        config['lista'].addTopLevelItem(item_widget)


class WidgetUpdater:
    """Gerencia atualizações de widgets."""

    def __init__(self):
        self.acoes = {
            'material': self._atualizar_material,
            'espessura': self._atualizar_espessura,
            'canal': self._atualizar_canal,
            'dedução': self._atualizar_deducao
        }

    def atualizar(self, tipo):
        """Atualiza widgets baseado no tipo."""
        if tipo not in self.acoes:
            return

        # Preservar valores antes da atualização
        valores_preservar = self._preservar_valores(tipo)

        # Executar atualização
        self.acoes[tipo]()

        # Restaurar valores preservados
        self._restaurar_valores(valores_preservar)

    def _preservar_valores(self, tipo):
        """Preserva valores que podem ser perdidos na atualização."""
        valores_preservar = {}

        if tipo == 'material' and hasattr(g, 'ESP_COMB') and g.ESP_COMB:
            valores_preservar['ESP_COMB'] = g.ESP_COMB.currentText()
            valores_preservar['CANAL_COMB'] = (getattr(g, 'CANAL_COMB', None)
                                               and g.CANAL_COMB.currentText())
        elif tipo == 'espessura' and hasattr(g, 'CANAL_COMB') and g.CANAL_COMB:
            valores_preservar['CANAL_COMB'] = g.CANAL_COMB.currentText()

        return valores_preservar

    def _restaurar_valores(self, valores_preservar):
        """Restaura valores preservados."""
        for widget_name, valor in valores_preservar.items():
            if valor:
                widget = getattr(g, widget_name, None)
                if widget and hasattr(widget, 'setCurrentText'):
                    try:
                        widget.setCurrentText(valor)
                    except (AttributeError, RuntimeError) as e:
                        print(f"Não foi possível restaurar {widget_name}: {e}")

    def _atualizar_material(self):
        """Atualiza os valores do combobox de materiais."""
        try:
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

            # Atualizar combobox de dedução se não em recarregamento
            self._atualizar_combo_deducao_material(atualizar_combobox_material)

            calcular_valores()

        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Erro ao atualizar materiais: {e}")
            traceback.print_exc()

    def _atualizar_combo_deducao_material(self, atualizar_func):
        """Atualiza combobox de dedução de material."""
        if (hasattr(g, 'DED_MATER_COMB') and g.DED_MATER_COMB and
                (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):

            g.UPDATING_DEDUCAO_COMBOS = True
            try:
                valor_atual = g.DED_MATER_COMB.currentText()
                atualizar_func(g.DED_MATER_COMB)

                if valor_atual and valor_atual.strip():
                    index = g.DED_MATER_COMB.findText(valor_atual)
                    g.DED_MATER_COMB.setCurrentIndex(
                        index if index >= 0 else -1)
            finally:
                g.UPDATING_DEDUCAO_COMBOS = False

    def _atualizar_espessura(self):
        """Atualiza os valores do combobox de espessuras."""
        if not g.MAT_COMB or not hasattr(g.MAT_COMB, 'currentText'):
            return

        material_nome = g.MAT_COMB.currentText()

        # Limpar espessuras sempre
        if g.ESP_COMB and hasattr(g.ESP_COMB, 'clear'):
            g.ESP_COMB.clear()

        if not material_nome or material_nome.strip() == "":
            return

        self._processar_espessuras_material(material_nome)
        calcular_valores()

    def _processar_espessuras_material(self, material_nome):
        """Processa espessuras do material selecionado."""
        material_obj = session.query(Material).filter_by(
            nome=material_nome).first()

        if material_obj and g.ESP_COMB:
            espessuras = session.query(Espessura).join(Deducao).filter(
                Deducao.material_id == material_obj.id
            ).order_by(Espessura.valor).distinct()

            espessuras_valores = [str(e.valor) for e in espessuras]
            g.ESP_COMB.addItems(espessuras_valores)

            self._atualizar_combo_deducao_espessura()

    def _atualizar_combo_deducao_espessura(self):
        """Atualiza combobox de dedução de espessura."""
        if (hasattr(g, 'DED_ESPES_COMB') and g.DED_ESPES_COMB and
            hasattr(g.DED_ESPES_COMB, 'clear') and
                (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):

            g.UPDATING_DEDUCAO_COMBOS = True
            try:
                valor_atual = g.DED_ESPES_COMB.currentText()

                valores_espessura = session.query(
                    Espessura.valor).distinct().all()
                valores_limpos = [
                    float(valor[0]) for valor in valores_espessura if valor[0] is not None]

                g.DED_ESPES_COMB.clear()
                g.DED_ESPES_COMB.addItems([str(valor)
                                          for valor in sorted(valores_limpos)])

                if valor_atual and valor_atual.strip():
                    index = g.DED_ESPES_COMB.findText(valor_atual)
                    g.DED_ESPES_COMB.setCurrentIndex(
                        index if index >= 0 else -1)
                else:
                    g.DED_ESPES_COMB.setCurrentIndex(-1)
            finally:
                g.UPDATING_DEDUCAO_COMBOS = False

    def _atualizar_canal(self):
        """Atualiza os valores do combobox de canais."""
        if (not g.ESP_COMB or not hasattr(g.ESP_COMB, 'currentText') or
                not g.MAT_COMB or not hasattr(g.MAT_COMB, 'currentText')):
            return

        espessura_valor = g.ESP_COMB.currentText()
        material_nome = g.MAT_COMB.currentText()

        # Limpar canais sempre
        if g.CANAL_COMB and hasattr(g.CANAL_COMB, 'clear'):
            g.CANAL_COMB.clear()

        if (not espessura_valor or not material_nome or
                espessura_valor.strip() == "" or material_nome.strip() == ""):
            return

        self._processar_canais_material_espessura(
            espessura_valor, material_nome)
        calcular_valores()

    def _processar_canais_material_espessura(self, espessura_valor, material_nome):
        """Processa canais do material e espessura selecionados."""
        try:
            espessura_obj = session.query(Espessura).filter_by(
                valor=float(espessura_valor)).first()
            material_obj = session.query(Material).filter_by(
                nome=material_nome).first()

            if espessura_obj and material_obj and g.CANAL_COMB:
                canais = session.query(Canal).join(Deducao).filter(
                    Deducao.espessura_id == espessura_obj.id,
                    Deducao.material_id == material_obj.id
                ).order_by(Canal.valor)

                canais_valores = sorted(
                    [str(c.valor) for c in canais],
                    key=lambda x: float(re.findall(r'\d+\.?\d*', x)[0])
                    if re.findall(r'\d+\.?\d*', x) else 0
                )

                g.CANAL_COMB.addItems(canais_valores)
                self._atualizar_combo_deducao_canal()

        except ValueError as e:
            print(f"Erro ao converter valor da espessura: {e}")
        except (AttributeError, RuntimeError) as e:
            print(f"Erro ao atualizar canais: {e}")

    def _atualizar_combo_deducao_canal(self):
        """Atualiza combobox de dedução de canal."""
        if (hasattr(g, 'DED_CANAL_COMB') and g.DED_CANAL_COMB and
            hasattr(g.DED_CANAL_COMB, 'clear') and
                (not hasattr(g, 'INTERFACE_RELOADING') or not g.INTERFACE_RELOADING)):

            g.UPDATING_DEDUCAO_COMBOS = True
            try:
                valor_atual = g.DED_CANAL_COMB.currentText()

                valores_canal = session.query(Canal.valor).distinct().all()
                valores_canal_limpos = [
                    str(valor[0]) for valor in valores_canal if valor[0] is not None]

                g.DED_CANAL_COMB.clear()
                g.DED_CANAL_COMB.addItems(sorted(valores_canal_limpos))

                if valor_atual and valor_atual.strip():
                    index = g.DED_CANAL_COMB.findText(valor_atual)
                    g.DED_CANAL_COMB.setCurrentIndex(
                        index if index >= 0 else -1)
                else:
                    g.DED_CANAL_COMB.setCurrentIndex(-1)
            finally:
                g.UPDATING_DEDUCAO_COMBOS = False

    def _atualizar_deducao(self):
        """Atualiza os valores de dedução com base nos widgets selecionados."""
        if not self._widgets_selecionados():
            self._limpar_deducao()
            return

        espessura_valor = g.ESP_COMB.currentText()
        material_nome = g.MAT_COMB.currentText()
        canal_valor = g.CANAL_COMB.currentText()

        if not self._selecoes_validas(espessura_valor, material_nome, canal_valor):
            self._limpar_deducao()
            return

        self._atualiza_labels_deducao(
            espessura_valor, material_nome, canal_valor)
        calcular_valores()

    def _widgets_selecionados(self):
        """Verifica se todos os widgets necessários estão selecionados."""
        widgets = [g.ESP_COMB, g.MAT_COMB, g.CANAL_COMB]
        metodos = ['currentText'] * 3

        for widget, metodo in zip(widgets, metodos):
            if not widget or not hasattr(widget, metodo):
                return False

        if (g.ESP_COMB.currentIndex() == -1 or
            g.MAT_COMB.currentIndex() == -1 or
                g.CANAL_COMB.currentIndex() == -1):
            return False

        return True

    def _selecoes_validas(self, espessura, material, canal):
        """Valida se as seleções são válidas."""
        if not all([espessura, material, canal]):
            return False

        if any(x.strip() == "" for x in (espessura, material, canal)):
            return False

        return True

    def _limpar_deducao(self):
        """Limpa labels de dedução."""
        if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
            g.DED_LBL.setText('')
            g.DED_LBL.setStyleSheet("")

        if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
            g.OBS_LBL.setText('')

    def _atualiza_labels_deducao(self, espessura_valor, material_nome, canal_valor):
        """Atualiza labels de dedução."""
        try:
            espessura_obj = session.query(Espessura).filter_by(
                valor=float(espessura_valor)).first()
            material_obj = session.query(Material).filter_by(
                nome=material_nome).first()
            canal_obj = session.query(Canal).filter_by(
                valor=canal_valor).first()

            if espessura_obj and material_obj and canal_obj:
                deducao_obj = session.query(Deducao).filter(
                    Deducao.espessura_id == espessura_obj.id,
                    Deducao.material_id == material_obj.id,
                    Deducao.canal_id == canal_obj.id
                ).first()

                if deducao_obj:
                    self._set_deducao_label(str(deducao_obj.valor), "")
                    self._set_obs_label(
                        deducao_obj.observacao or 'Observações não encontradas')
                else:
                    self._set_deducao_label('N/A', "color: red")
                    self._set_obs_label('Observações não encontradas')
            else:
                self._limpar_deducao()

        except ValueError as e:
            print(f"Erro ao converter valor da espessura: {e}")
        except (AttributeError, RuntimeError) as e:
            print(f"Erro ao atualizar dedução: {e}")

    def _set_deducao_label(self, texto, estilo):
        """Define texto e estilo do label de dedução."""
        if g.DED_LBL and hasattr(g.DED_LBL, 'setText'):
            g.DED_LBL.setText(texto)
            g.DED_LBL.setStyleSheet(estilo)

    def _set_obs_label(self, texto):
        """Define texto do label de observação."""
        if g.OBS_LBL and hasattr(g.OBS_LBL, 'setText'):
            g.OBS_LBL.setText(texto)


class ParameterValidator:
    """Classe para validar parâmetros da função atualizar_toneladas_m - Corrige R0916."""

    @staticmethod
    def validar_widgets_iniciais():
        """Valida se todos os widgets necessários estão disponíveis."""
        widgets_requeridos = [
            (g.COMPR_ENTRY, 'text'),
            (g.ESP_COMB, 'currentText'),
            (g.MAT_COMB, 'currentText'),
            (g.CANAL_COMB, 'currentText')
        ]

        return all(
            widget and hasattr(widget, metodo)
            for widget, metodo in widgets_requeridos
        )

    @staticmethod
    def validar_selecoes_combos():
        """Verifica se todas as seleções dos comboboxes são válidas."""
        return all([
            g.ESP_COMB.currentIndex() != -1,
            g.MAT_COMB.currentIndex() != -1,
            g.CANAL_COMB.currentIndex() != -1
        ])

    @staticmethod
    def obter_valores_calculo():
        """Obtém os valores necessários para o cálculo."""
        return {
            'comprimento': g.COMPR_ENTRY.text(),
            'espessura_valor': g.ESP_COMB.currentText(),
            'material_nome': g.MAT_COMB.currentText(),
            'canal_valor': g.CANAL_COMB.currentText()
        }

    @staticmethod
    def validar_valores_obtidos(valores):
        """Valida se os valores obtidos são válidos para cálculo - Corrige R0916."""
        # Separar validações em variáveis para reduzir expressões booleanas
        valores_existem = all(valores.values())
        valores_nao_vazios = all(
            valor.strip() != ""
            for valor in valores.values()
            if isinstance(valor, str)
        )

        return valores_existem and valores_nao_vazios


# Funções principais refatoradas usando as classes

def copiar(tipo, numero=None, w=None):
    """
    Copia o valor do label correspondente ao tipo e número
    especificados para a área de transferência.
    """
    copy_manager = CopyManager()

    # Obter e validar label
    label = copy_manager.obter_label(tipo, numero, w)
    if not copy_manager.validar_label(label, tipo, numero, w):
        return

    # Obter texto atual
    texto_atual = copy_manager.obter_texto_atual(label)
    if not texto_atual:
        return

    # Processar texto (remover "Copiado!" se existir)
    texto_original = _processar_texto_copiado(texto_atual)

    # Executar cálculo
    copy_manager.executar_calculo(tipo, w)

    # Obter texto atualizado após cálculo
    texto_atualizado = _obter_texto_atualizado(label, texto_original)

    # Copiar para área de transferência
    pyperclip.copy(texto_atualizado)
    print(f'Valor copiado {texto_atualizado}')

    # Atualizar interface
    copy_manager.atualizar_label_copiado(label, texto_atualizado)
    copy_manager.agendar_remocao_copiado(label, texto_atualizado)


def _processar_texto_copiado(texto_atual):
    """Remove 'Copiado!' do texto se já estiver presente."""
    return texto_atual.replace(" Copiado!", "") if " Copiado!" in texto_atual else texto_atual


def _obter_texto_atualizado(label, texto_original):
    """Obtém o texto atualizado após o cálculo."""
    try:
        texto_atualizado = label.text() if hasattr(label, 'text') else str(label.text)
        texto_atualizado = str(texto_atualizado)
        return (texto_atualizado.replace(" Copiado!", "")
                if (" Copiado!" in texto_atualizado)
                else texto_atualizado)
    except AttributeError:
        return texto_original


def listar(tipo):
    """
    Lista os itens do banco de dados na interface gráfica.
    """
    list_manager = ListManager()

    # Inicializar configurações
    if not list_manager.inicializar_configuracoes():
        return

    # Validar configuração
    if not list_manager.validar_configuracao(tipo):
        return

    # Limpar lista atual
    list_manager.limpar_lista(tipo)

    # Processar itens
    _processar_itens_lista(list_manager, tipo)


def _processar_itens_lista(list_manager, tipo):
    """Processa e adiciona itens à lista."""
    try:
        config = list_manager.configuracoes[tipo]
        itens = list_manager.obter_itens_ordenados(tipo)

        for item in itens:
            item_processado = _processar_item_individual(
                list_manager, item, tipo)
            if item_processado:
                item_widget = list_manager.criar_item_widget(
                    item_processado, config)
                list_manager.adicionar_item_a_lista(item_widget, config)

    except (AttributeError, RuntimeError, ValueError) as e:
        print(f"Erro ao processar itens da lista {tipo}: {e}")


def _processar_item_individual(list_manager, item, tipo):
    """Processa um item individual baseado no tipo."""
    if tipo == 'dedução':
        return list_manager.processar_item_deducao(item)
    return item


def atualizar_widgets(tipo):
    """
    Atualiza os valores de comboboxes com base no tipo especificado.
    """
    try:
        updater = WidgetUpdater()
        updater.atualizar(tipo)
    except (AttributeError, KeyError, RuntimeError) as e:
        print(f"Erro em atualizar_widgets({tipo}): {e}")


def limpar_busca(tipo):
    """
    Limpa os campos de busca e atualiza a lista correspondente.
    """
    try:
        configuracoes = obter_configuracoes()

        if tipo == 'dedução':
            _limpar_busca_deducao(configuracoes[tipo])
        else:
            _limpar_busca_generica(configuracoes[tipo])

        listar(tipo)

    except (AttributeError, RuntimeError, ValueError) as e:
        print(f"Erro ao limpar busca para {tipo}: {e}")


def _limpar_busca_deducao(config):
    """Limpa campos específicos de busca de dedução."""
    entries = config.get('entries', {})

    combos = [
        ('material_combo', entries.get('material_combo')),
        ('espessura_combo', entries.get('espessura_combo')),
        ('canal_combo', entries.get('canal_combo'))
    ]

    for nome, combo in combos:
        if combo and hasattr(combo, 'setCurrentIndex'):
            combo.setCurrentIndex(-1)
            print(f"Limpando combobox {nome}")


def _limpar_busca_generica(config):
    """Limpa campos genéricos de busca."""
    busca_widget = config.get('busca')
    if busca_widget and hasattr(busca_widget, 'clear'):
        busca_widget.clear()


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
    CORRIGIDO R0916: Reduzido número de expressões booleanas usando classe ParameterValidator.
    """
    validator = ParameterValidator()

    # Validação inicial dos widgets
    if not validator.validar_widgets_iniciais():
        return

    # Validação das seleções
    if not validator.validar_selecoes_combos():
        _limpar_forca_label()
        return

    # Obter e validar valores
    valores = validator.obter_valores_calculo()
    if not validator.validar_valores_obtidos(valores):
        _limpar_forca_label()
        return

    # Executar cálculo
    _calcular_forca_toneladas(**valores)


def _limpar_forca_label():
    """Limpa o label de força."""
    if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
        g.FORCA_LBL.setText('')


def _calcular_forca_toneladas(comprimento, espessura_valor, material_nome, canal_valor):
    """Calcula força em toneladas."""
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
                _set_forca_label(f'{toneladas_m:.0f}', "")
            else:
                _set_forca_label('N/A', "color: red")

            _verificar_comprimento_canal(comprimento, canal_obj)

    except ValueError as e:
        print(f"Erro ao converter valores numéricos: {e}")
    except (AttributeError, RuntimeError) as e:
        print(f"Erro ao atualizar toneladas/m: {e}")


def _set_forca_label(texto, estilo):
    """Define texto e estilo do label de força."""
    if g.FORCA_LBL and hasattr(g.FORCA_LBL, 'setText'):
        g.FORCA_LBL.setText(texto)
        g.FORCA_LBL.setStyleSheet(estilo)


def _verificar_comprimento_canal(comprimento, canal_obj):
    """Verifica se comprimento é adequado para o canal."""
    if not g.COMPR_ENTRY or not hasattr(g.COMPR_ENTRY, 'setStyleSheet'):
        return

    comprimento_total = getattr(
        canal_obj, 'comprimento_total', None) if canal_obj else None
    comprimento_float = float(comprimento) if comprimento else None

    if canal_obj and comprimento_float and comprimento_total:
        if comprimento_float < comprimento_total:
            g.COMPR_ENTRY.setStyleSheet("")
        elif comprimento_float >= comprimento_total:
            g.COMPR_ENTRY.setStyleSheet("color: red")


def focus_next_entry(current_index, w):
    """Move o foco para o próximo campo de entrada na aba atual."""
    next_index = current_index + 1
    if next_index < g.N:
        next_entry = getattr(g, f'aba{next_index}_entry_{w}', None)
        if next_entry:
            next_entry.setFocus()


def focus_previous_entry(current_index, w):
    """Move o foco para o campo de entrada anterior na aba atual."""
    previous_index = current_index - 1
    if previous_index > 0:
        previous_entry = getattr(g, f'aba{previous_index}_entry_{w}', None)
        if previous_entry:
            previous_entry.setFocus()


def todas_funcoes():
    """Executa todas as funções necessárias para atualizar os valores e labels do aplicativo."""
    try:
        for tipo in ['material', 'espessura', 'canal', 'dedução']:
            try:
                atualizar_widgets(tipo)
            except (AttributeError, RuntimeError, ValueError) as e:
                print(f"Erro ao atualizar widgets {tipo}: {e}")

        _executar_calculos_gerais()

    except (AttributeError, RuntimeError) as e:
        print(f"Erro geral em todas_funcoes: {e}")
        traceback.print_exc()


def _executar_calculos_gerais():
    """Executa todos os cálculos gerais."""
    calculos = [
        ('calcular_k_offset', calcular_k_offset),
        ('aba_minima_externa', aba_minima_externa),
        ('z_minimo_externo', z_minimo_externo),
        ('razao_ri_espessura', razao_ri_espessura)
    ]

    for nome, funcao in calculos:
        try:
            funcao()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao executar {nome}: {e}")

    # Calcular dobras para cada valor W
    try:
        for w in g.VALORES_W:
            calcular_dobra(w)
    except (AttributeError, ValueError, ZeroDivisionError) as e:
        print(f"Erro ao calcular dobras: {e}")


def calcular_valores():
    """Executa apenas os cálculos necessários sem atualizar os comboboxes."""
    try:
        _executar_calculos_gerais()

        try:
            atualizar_toneladas_m()
        except (AttributeError, ValueError, ZeroDivisionError) as e:
            print(f"Erro ao atualizar toneladas/m: {e}")

    except (AttributeError, RuntimeError) as e:
        print(f"Erro geral em calcular_valores: {e}")


def configurar_main_frame(parent):
    """Configura o frame principal com colunas e linhas padrão."""
    main_frame = QWidget(parent)
    layout = QGridLayout(main_frame)
    main_frame.setLayout(layout)

    # Configurar o layout principal do parent para usar o main_frame
    if not parent.layout():
        parent_layout = QGridLayout(parent)
        parent.setLayout(parent_layout)

    parent.layout().addWidget(main_frame)
    return main_frame
