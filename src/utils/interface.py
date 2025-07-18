"""
Módulo de Interface para o Aplicativo de Dobras.

Este módulo contém funções que interagem diretamente com a interface gráfica
(widgets PySide6). Ele é responsável por:
- Orquestrar os cálculos do módulo `calculos`.
- Atualizar os labels, comboboxes e outros widgets com os novos valores.
- Gerenciar a aparência (estilos, tooltips) dos widgets.
- Lidar com ações diretas na interface, como limpeza de campos.
"""

import traceback
from functools import partial
import pyperclip
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtCore import QTimer
from src.models.models import Espessura, Material, Canal, Deducao
from src.utils.banco_dados import session, obter_configuracoes
from src.utils import calculos
from src.config import globals as g

# --- CLASSES DE MANIPULAÇÃO DA INTERFACE ---


class CopyManager:
    """Gerencia operações de cópia de valores dos widgets."""

    def __init__(self):
        self.configuracoes = {
            'dedução': {'label': lambda *_: g.DED_LBL},
            'fator_k': {'label': lambda *_: g.K_LBL},
            'offset': {'label': lambda *_: g.OFFSET_LBL},
            'medida_dobra': {'label': lambda n, w: getattr(g, f'medidadobra{n}_label_{w}', None)},
            'metade_dobra': {'label': lambda n, w: getattr(g, f'metadedobra{n}_label_{w}', None)},
            'blank': {'label': lambda _, w: getattr(g, f'medida_blank_label_{w}', None)},
            'metade_blank': {'label': lambda _, w: getattr(g, f'metade_blank_label_{w}', None)}
        }

    def copiar(self, tipo, numero=None, w=None):
        """Copia o valor do label para a área de transferência."""
        label_func = self.configuracoes.get(tipo, {}).get('label')
        if not label_func:
            return
        label = label_func(numero, w)
        if not label or not hasattr(label, 'text'):
            return

        calcular_valores()
        texto_original = label.text().replace(" Copiado!", "")
        if not texto_original.strip():
            return

        pyperclip.copy(texto_original)
        label.setText(f'{texto_original} Copiado!')
        label.setStyleSheet("QLabel { color: green; }")

        QTimer.singleShot(2000, partial(
            self._restaurar_label, label, texto_original))

    def _restaurar_label(self, label, texto):
        """Restaura o texto e estilo original do label."""
        if label and hasattr(label, 'text') and "Copiado!" in label.text():
            label.setText(texto)
            label.setStyleSheet("")


copiar = CopyManager().copiar


class ListManager:
    """Gerencia operações de listagem de dados do banco na interface."""

    def __init__(self):
        self.configuracoes = None

    def listar(self, tipo):
        """
        Lista os itens do banco de dados na interface gráfica, de acordo com o tipo informado.
        """
        self.configuracoes = obter_configuracoes()
        if not self.configuracoes or tipo not in self.configuracoes:
            return

        config = self.configuracoes[tipo]
        lista_widget = config.get('lista')
        if not lista_widget:
            return

        lista_widget.clear()
        itens = session.query(config['modelo']).order_by(config['ordem']).all()

        for item in itens:
            if tipo == 'dedução' and not all([item.material, item.espessura, item.canal]):
                continue
            valores = config['valores'](item)
            valores_str = [str(v) if v is not None else '' for v in valores]
            item_widget = QTreeWidgetItem(valores_str)
            lista_widget.addTopLevelItem(item_widget)


listar = ListManager().listar


class LimparBusca:
    """Classe para limpar campos de busca dos formulários."""

    def limpar_busca(self, tipo):
        """
        Limpa os campos de busca e atualiza a lista correspondente.
        """
        try:
            configuracoes = obter_configuracoes()
            if tipo not in configuracoes:
                return

            config = configuracoes[tipo]
            if tipo == 'dedução':
                self._limpar_busca_deducao(config)
            else:
                self._limpar_busca_generica(config)
            listar(tipo)
        except (AttributeError, RuntimeError, ValueError, KeyError) as e:
            print(f"Erro ao limpar busca para {tipo}: {e}")

    def _limpar_busca_deducao(self, config):
        entries = config.get('entries', {})
        combos = [entries.get('material_combo'), entries.get(
            'espessura_combo'), entries.get('canal_combo')]
        for combo in combos:
            if combo and hasattr(combo, 'setCurrentIndex'):
                combo.setCurrentIndex(-1)

    def _limpar_busca_generica(self, config):
        busca_widget = config.get('busca')
        if busca_widget and hasattr(busca_widget, 'clear'):
            busca_widget.clear()


limpar_busca = LimparBusca().limpar_busca


class WidgetUpdater:
    """Gerencia a atualização de comboboxes e seus dados dependentes."""

    def __init__(self):
        self.acoes = {
            'material': self._atualizar_material,
            'espessura': self._atualizar_espessura,
            'canal': self._atualizar_canal
        }

    def atualizar(self, tipo):
        """
        Atualiza os widgets da interface conforme o tipo especificado.
        """
        if tipo not in self.acoes:
            return
        valores_preservar = self._preservar_valores(tipo)
        self.acoes[tipo]()
        self._restaurar_valores(valores_preservar)
        calcular_valores()

    def _preservar_valores(self, tipo):
        valores = {}
        if tipo == 'material':
            valores['ESP_COMB'] = calculos.obter_valor_widget(
                g.ESP_COMB, 'currentText')
            valores['CANAL_COMB'] = calculos.obter_valor_widget(
                g.CANAL_COMB, 'currentText')
        elif tipo == 'espessura':
            valores['CANAL_COMB'] = calculos.obter_valor_widget(
                g.CANAL_COMB, 'currentText')
        return valores

    def _restaurar_valores(self, valores):
        for widget_name, valor in valores.items():
            if valor:
                widget = getattr(g, widget_name, None)
                if widget and hasattr(widget, 'setCurrentText'):
                    widget.setCurrentText(valor)

    def _atualizar_material(self):
        materiais = [m.nome for m in session.query(
            Material).order_by(Material.nome)]
        for combo_global in [g.MAT_COMB, g.DED_MATER_COMB]:
            if combo_global and hasattr(combo_global, 'clear'):
                combo_global.clear()
                combo_global.addItems(materiais)
                combo_global.setCurrentIndex(-1)

    def _atualizar_espessura(self):
        if hasattr(g, 'ESP_COMB') and g.ESP_COMB and hasattr(g.ESP_COMB, 'clear'):
            g.ESP_COMB.clear()
            material_nome = calculos.obter_valor_widget(
                g.MAT_COMB, 'currentText')
            if material_nome:
                material_obj = session.query(Material).filter_by(
                    nome=material_nome).first()
                if material_obj:
                    espessuras = session.query(Espessura).join(Deducao).filter(
                        Deducao.material_id == material_obj.id
                    ).order_by(Espessura.valor).distinct()
                    g.ESP_COMB.addItems([str(e.valor) for e in espessuras])

        if hasattr(g, 'DED_ESPES_COMB') and g.DED_ESPES_COMB and hasattr(g.DED_ESPES_COMB, 'clear'):
            espessuras_form = session.query(
                Espessura.valor).distinct().order_by(Espessura.valor).all()
            g.DED_ESPES_COMB.clear()
            g.DED_ESPES_COMB.addItems([str(val[0])
                                      for val in espessuras_form if val[0]])
            g.DED_ESPES_COMB.setCurrentIndex(-1)

    def _atualizar_canal(self):
        if hasattr(g, 'CANAL_COMB') and g.CANAL_COMB and hasattr(g.CANAL_COMB, 'clear'):
            g.CANAL_COMB.clear()
            material_nome = calculos.obter_valor_widget(
                g.MAT_COMB, 'currentText')
            espessura_valor = calculos.obter_valor_widget(
                g.ESP_COMB, 'currentText')
            if material_nome and espessura_valor:
                espessura_obj = session.query(Espessura).filter_by(
                    valor=float(espessura_valor)).first()
                material_obj = session.query(Material).filter_by(
                    nome=material_nome).first()
                if espessura_obj and material_obj:
                    canais = session.query(Canal).join(Deducao).filter(
                        Deducao.espessura_id == espessura_obj.id,
                        Deducao.material_id == material_obj.id
                    ).order_by(Canal.valor).distinct()
                    g.CANAL_COMB.addItems([str(c.valor) for c in canais])

        if hasattr(g, 'DED_CANAL_COMB') and g.DED_CANAL_COMB and hasattr(g.DED_CANAL_COMB, 'clear'):
            canais_form = session.query(
                Canal.valor).distinct().order_by(Canal.valor).all()
            g.DED_CANAL_COMB.clear()
            g.DED_CANAL_COMB.addItems([str(val[0])
                                      for val in canais_form if val[0]])
            g.DED_CANAL_COMB.setCurrentIndex(-1)


atualizar_widgets = WidgetUpdater().atualizar


# --- FUNÇÕES DE LIMPEZA (MOVIDAS DE limpeza.py) ---

def limpar_dobras():
    """Limpa os valores das dobras e a dedução específica."""
    if hasattr(g, 'VALORES_W'):
        for w in g.VALORES_W:
            for i in range(1, g.N):
                entry = getattr(g, f'aba{i}_entry_{w}', None)
                if entry and hasattr(entry, 'clear'):
                    entry.clear()

    ded_espec_entry = getattr(g, 'DED_ESPEC_ENTRY', None)
    if ded_espec_entry and hasattr(ded_espec_entry, 'clear'):
        ded_espec_entry.clear()

    calcular_valores()

    primeiro_entry = getattr(g, "aba1_entry_a", None)
    if primeiro_entry and hasattr(primeiro_entry, 'setFocus'):
        primeiro_entry.setFocus()


def limpar_tudo():
    """Limpa todos os campos e labels da interface principal."""
    # Limpar comboboxes do cabeçalho
    for combo_global in [g.ESP_COMB, g.CANAL_COMB]:
        if combo_global and hasattr(combo_global, 'setCurrentIndex'):
            combo_global.setCurrentIndex(-1)
            combo_global.clear()

    if hasattr(g, 'MAT_COMB') and g.MAT_COMB:
        g.MAT_COMB.setCurrentIndex(-1)

    # Limpar campos de entrada
    for entry_global in [g.RI_ENTRY, g.COMPR_ENTRY]:
        if entry_global and hasattr(entry_global, 'clear'):
            entry_global.clear()

    limpar_dobras()
    calcular_valores()


# --- FUNÇÕES DE ATUALIZAÇÃO DE LABELS ---

def _atualizar_label(label, valor, formato="{:.2f}", estilo_sucesso="", estilo_erro="color: red;"):
    """Função genérica para atualizar um QLineEdit ou QLabel."""
    if not label or not hasattr(label, 'setText'):
        return

    if valor is None:
        label.setText("")
        label.setStyleSheet(estilo_sucesso)
        return

    if isinstance(valor, str) and valor == 'N/A':
        label.setText("N/A")
        label.setStyleSheet(estilo_erro)
        return

    try:
        label.setText(formato.format(float(valor)))
        label.setStyleSheet(estilo_sucesso)
    except (ValueError, TypeError):
        label.setText("")
        label.setStyleSheet(estilo_sucesso)


def _verificar_aba_minima(entry_widget, valor_dobra_str):
    """Verifica se a aba inserida é maior que a mínima calculada."""
    if not entry_widget or not hasattr(entry_widget, 'setStyleSheet'):
        return
    if not valor_dobra_str.strip():
        entry_widget.setStyleSheet("")
        entry_widget.setToolTip("Insira o valor da dobra.")
        return

    aba_minima = calculos.CalculoAbaMinima().calcular()
    if aba_minima is None:
        return

    valor_dobra = calculos.converter_para_float(valor_dobra_str)
    if valor_dobra < aba_minima:
        entry_widget.setStyleSheet("color: white; background-color: red;")
        entry_widget.setToolTip(
            f"Aba ({valor_dobra}) menor que a mínima ({aba_minima:.0f}).")
    else:
        entry_widget.setStyleSheet("")
        entry_widget.setToolTip("Insira o valor da dobra.")

# --- ORQUESTRADOR DE CÁLCULOS E ATUALIZAÇÕES ---


def _atualizar_deducao_ui():
    """Busca e atualiza os widgets de dedução e observação."""
    resultado = calculos.CalculoDeducaoDB().buscar()
    if resultado:
        _atualizar_label(g.DED_LBL, resultado.get('valor'), formato="{:.2f}")
        if g.OBS_LBL:
            g.OBS_LBL.setText(resultado.get('obs', ''))
    else:
        _atualizar_label(g.DED_LBL, None)
        if g.OBS_LBL:
            g.OBS_LBL.setText('')


def _atualizar_k_offset_ui():
    """Calcula e atualiza os widgets de Fator K e Offset."""
    resultado = calculos.CalculoFatorK().calcular()
    if resultado:
        estilo = "color: blue;" if resultado['especifico'] else ""
        _atualizar_label(g.K_LBL, resultado['fator_k'], estilo_sucesso=estilo)
        _atualizar_label(
            g.OFFSET_LBL, resultado['offset'], estilo_sucesso=estilo)
    else:
        _atualizar_label(g.K_LBL, None)
        _atualizar_label(g.OFFSET_LBL, None)


def _atualizar_parametros_principais_ui():
    """Calcula e atualiza Aba Mínima, Z Mínimo e Razão RI/E."""
    _atualizar_label(
        g.ABA_EXT_LBL, calculos.CalculoAbaMinima().calcular(), formato="{:.0f}")
    _atualizar_label(
        g.Z_EXT_LBL, calculos.CalculoZMinimo().calcular(), formato="{:.0f}")
    _atualizar_label(
        g.RAZAO_RIE_LBL, calculos.CalculoRazaoRIE().calcular(), formato="{:.1f}")


def _atualizar_forca_ui():
    """Calcula e atualiza o widget de Força."""
    resultado = calculos.CalculoForca().calcular()
    if resultado:
        _atualizar_label(g.FORCA_LBL, resultado.get('forca'), formato="{:.0f}")
        if g.COMPR_ENTRY and hasattr(g.COMPR_ENTRY, 'setStyleSheet'):
            canal_obj = resultado.get('canal_obj')
            comprimento = resultado.get('comprimento')
            comprimento_total = getattr(
                canal_obj, 'comprimento_total', None) if canal_obj else None
            if comprimento and comprimento_total and comprimento >= comprimento_total:
                g.COMPR_ENTRY.setStyleSheet("color: red;")
            else:
                g.COMPR_ENTRY.setStyleSheet("")
    else:
        _atualizar_label(g.FORCA_LBL, None)
        if g.COMPR_ENTRY:
            g.COMPR_ENTRY.setStyleSheet("")


def _atualizar_coluna_dobras_ui(w):
    """Calcula e atualiza uma coluna inteira de dobras."""
    resultado_coluna = calculos.CalculoDobra().calcular_coluna(w)
    blank_total = 0
    if resultado_coluna:
        blank_total = resultado_coluna.get('blank_total', 0)
        for i, res in enumerate(resultado_coluna.get('resultados', []), 1):
            _atualizar_label(
                getattr(g, f'medidadobra{i}_label_{w}', None), res.get('medida'))
            _atualizar_label(
                getattr(g, f'metadedobra{i}_label_{w}', None), res.get('metade'))
            entry_widget = getattr(g, f'aba{i}_entry_{w}', None)
            valor_str = calculos.obter_valor_widget(entry_widget, 'text')
            _verificar_aba_minima(entry_widget, valor_str)
    else:
        for i in range(1, g.N):
            _atualizar_label(
                getattr(g, f'medidadobra{i}_label_{w}', None), None)
            _atualizar_label(
                getattr(g, f'metadedobra{i}_label_{w}', None), None)

    _atualizar_label(getattr(
        g, f'medida_blank_label_{w}', None), blank_total if blank_total > 0 else None)
    _atualizar_label(getattr(
        g, f'metade_blank_label_{w}', None), blank_total / 2 if blank_total > 0 else None)


def calcular_valores():
    """
    Função principal que orquestra todos os cálculos e atualizações da UI.
    """
    try:
        _atualizar_deducao_ui()
        _atualizar_k_offset_ui()
        _atualizar_parametros_principais_ui()
        _atualizar_forca_ui()
        for w in g.VALORES_W:
            _atualizar_coluna_dobras_ui(w)
    except (AttributeError, RuntimeError, ValueError, KeyError, TypeError) as e:
        print(f"Erro inesperado em calcular_valores: {e}")
        traceback.print_exc()


def todas_funcoes():
    """Executa a atualização completa da interface, incluindo comboboxes."""
    for tipo in ['material', 'espessura', 'canal']:
        atualizar_widgets(tipo)


# --- FUNÇÕES ADICIONAIS DE UI ---

def focus_next_entry(current_index, w):
    """Move o foco para o próximo campo de entrada."""
    next_entry = getattr(g, f'aba{current_index + 1}_entry_{w}', None)
    if next_entry:
        next_entry.setFocus()


def focus_previous_entry(current_index, w):
    """Move o foco para o campo de entrada anterior."""
    prev_entry = getattr(g, f'aba{current_index - 1}_entry_{w}', None)
    if prev_entry:
        prev_entry.setFocus()


def canal_tooltip():
    """Atualiza o tooltip do combobox de canais."""
    if not g.CANAL_COMB:
        return
    canal_str = calculos.obter_valor_widget(g.CANAL_COMB, 'currentText')
    if not canal_str:
        g.CANAL_COMB.setToolTip("Selecione o canal de dobra.")
        return
    canal_obj = session.query(Canal).filter_by(valor=canal_str).first()
    if canal_obj:
        obs = getattr(canal_obj, 'observacao', "N/A")
        comp = getattr(canal_obj, 'comprimento_total', "N/A")
        g.CANAL_COMB.setToolTip(f'Obs: {obs}\nComprimento total: {comp}')
    else:
        g.CANAL_COMB.setToolTip("Canal não encontrado.")
