"""
Funções auxiliares para o aplicativo de cálculo de dobras.
"""

from math import pi
import re
from src.config import globals as g
from src.models.models import Canal
from src.utils.banco_dados import session


def verificar_widget_inicializado(widget, metodo='get', default_value=''):
    """
    Verifica se um widget está inicializado antes de chamar seus métodos.

    Args:
        widget: O widget a ser verificado
        metodo: O método a ser chamado ('get', 'text', 'currentText')
        default_value: Valor padrão caso o widget não esteja inicializado

    Returns:
        O resultado do método ou o valor padrão
    """
    if widget is None:
        return default_value

    result = default_value

    try:
        # Corrigido R1714: Usar 'in' em vez de múltiplas comparações
        if metodo in ('get', 'text'):
            # PySide6 QLineEdit usa text()
            if hasattr(widget, 'text'):
                result = widget.text()
            elif hasattr(widget, 'currentText'):
                result = widget.currentText()
        elif metodo == 'currentText':
            if hasattr(widget, 'currentText'):
                temp_result = widget.currentText()
                result = temp_result if temp_result else default_value
        elif metodo == 'cget':
            # Para PySide6 QLabel, usa text()
            if hasattr(widget, 'text'):
                result = widget.text()
    except (AttributeError, TypeError):
        result = default_value

    return result


def _obter_valores_calculo_k():
    """Obtém valores necessários para cálculo do fator K."""
    espessura_text = verificar_widget_inicializado(
        g.ESP_COMB, 'currentText', '0') or '0'
    raio_interno_str = verificar_widget_inicializado(
        g.RI_ENTRY, 'text', '0') or '0'
    deducao_espec_str = verificar_widget_inicializado(
        g.DED_ESPEC_ENTRY, 'text', '0') or '0'
    deducao_label_text = verificar_widget_inicializado(
        g.DED_LBL, 'text', '0') or '0'

    return espessura_text, raio_interno_str, deducao_espec_str, deducao_label_text


def _converter_valores_k(espessura_text, raio_interno_str, deducao_espec_str, deducao_label_text):
    """Converte strings para valores numéricos para cálculo K."""
    espessura = float(espessura_text.replace(
        ',', '.')) if espessura_text and espessura_text.strip() != '' else 0
    raio_interno = float(raio_interno_str.replace(
        ',', '.')) if raio_interno_str and raio_interno_str.strip() != '' else 0
    deducao_espec = float(deducao_espec_str.replace(
        ',', '.')) if deducao_espec_str.strip() else 0
    deducao_valor = float(
        deducao_label_text.replace(' Copiado!', '').replace(',', '.')
    ) if deducao_label_text else 0

    return espessura, raio_interno, deducao_espec, deducao_valor


def _determinar_deducao_usada(deducao_espec, deducao_valor):
    """Determina qual dedução usar e se é específica."""
    deducao_usada = deducao_espec if deducao_espec > 0 else deducao_valor
    usa_deducao_especifica = deducao_espec > 0
    return deducao_usada, usa_deducao_especifica


def _calcular_fator_k(espessura, deducao_usada, raio_interno):
    """Calcula fator K usando fórmula personalizada."""
    fator_k = (4 * (espessura - (deducao_usada / 2) + raio_interno) -
               (pi * raio_interno)) / (pi * espessura)
    # Limita o fator K a valores razoáveis
    return max(0.0, min(fator_k, 0.5))


def _atualizar_labels_k_offset(fator_k, offset, usa_deducao_especifica):
    """Atualiza labels do fator K e offset."""
    if g.K_LBL and hasattr(g.K_LBL, 'setText'):
        g.K_LBL.setText(f"{fator_k:.2f}")
        if hasattr(g.K_LBL, 'setStyleSheet'):
            if usa_deducao_especifica:
                g.K_LBL.setStyleSheet("color: blue")
            else:
                g.K_LBL.setStyleSheet("")

    if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
        g.OFFSET_LBL.setText(f"{offset:.2f}")
        if hasattr(g.OFFSET_LBL, 'setStyleSheet'):
            if usa_deducao_especifica:
                g.OFFSET_LBL.setStyleSheet("color: blue")
            else:
                g.OFFSET_LBL.setStyleSheet("")


def _limpar_labels_k_erro():
    """Limpa labels em caso de erro."""
    if g.K_LBL and hasattr(g.K_LBL, 'setText'):
        g.K_LBL.setText('N/A')
        if hasattr(g.K_LBL, 'setStyleSheet'):
            g.K_LBL.setStyleSheet("color: red")

    if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
        g.OFFSET_LBL.setText('N/A')
        if hasattr(g.OFFSET_LBL, 'setStyleSheet'):
            g.OFFSET_LBL.setStyleSheet("color: red")


def calcular_k_offset():
    """
    Calcula o fator K com base nos valores de espessura, dedução e raio
    interno.

    - Fator K personalizado: K = (4 × (espessura - (dedução / 2) +
      raio_interno) - (π × raio_interno)) / (π × espessura)
    - Fator K padrão baseado na razão raio/espessura (usando tabela de
      referência)
    - Offset = Fator K × Espessura
    """
    try:
        # Obtém valores dos widgets
        espessura_text, raio_interno_str, deducao_espec_str, deducao_label_text = \
            _obter_valores_calculo_k()

        # Converte valores para float
        espessura, raio_interno, deducao_espec, deducao_valor = _converter_valores_k(
            espessura_text, raio_interno_str, deducao_espec_str, deducao_label_text)

        # Valida valores necessários
        if raio_interno <= 0 or espessura <= 0:
            if g.K_LBL and hasattr(g.K_LBL, 'setText'):
                g.K_LBL.setText('')
            if g.OFFSET_LBL and hasattr(g.OFFSET_LBL, 'setText'):
                g.OFFSET_LBL.setText('')
            return

        # Determina dedução usada
        deducao_usada, usa_deducao_especifica = _determinar_deducao_usada(
            deducao_espec, deducao_valor)

        # Calcula razão raio/espessura
        razao_re = raio_interno / espessura

        # Calcula fator K
        if deducao_usada > 0:
            fator_k = _calcular_fator_k(
                espessura, deducao_usada, raio_interno)
        else:
            fator_k = obter_fator_k_da_tabela(razao_re)

        offset = fator_k * espessura

        # Atualiza labels
        _atualizar_labels_k_offset(fator_k, offset, usa_deducao_especifica)

    except ValueError as e:
        print(f"Erro ao converter valores para o cálculo do fator K: {e}")
        _limpar_labels_k_erro()
    except (AttributeError, TypeError) as e:
        print(f"Erro de atributo ou tipo no cálculo do fator K: {e}")


def obter_fator_k_da_tabela(razao_re):
    """
    Obtém o fator K da tabela de referência baseado na razão raio/espessura.
    Usa interpolação linear para valores intermediários.
    """
    # Limita a razão aos valores da tabela
    razao_re = max(0.1, min(razao_re, 10.0))

    # Se o valor está exatamente na tabela, retorna diretamente
    if razao_re in g.RAIO_K:
        return g.RAIO_K[razao_re]

    # Encontra os valores adjacentes para interpolação
    razoes_ordenadas = sorted(g.RAIO_K.keys())
    for i in range(len(razoes_ordenadas) - 1):
        r1 = razoes_ordenadas[i]
        r2 = razoes_ordenadas[i + 1]
        if r1 <= razao_re <= r2:
            k1 = g.RAIO_K[r1]
            k2 = g.RAIO_K[r2]
            fator_k = k1 + (k2 - k1) * (razao_re - r1) / (r2 - r1)
            return fator_k

    # Se não encontrou na interpolação, usa o valor mais próximo
    if razao_re < razoes_ordenadas[0]:
        return g.RAIO_K[razoes_ordenadas[0]]

    return g.RAIO_K[razoes_ordenadas[-1]]


def _extrair_valor_canal(canal_valor):
    """Extrai valor numérico do canal."""
    numeros = re.findall(r'\d+\.?\d*', canal_valor)
    return float(numeros[0]) if numeros else None


def _atualizar_label_aba_externa(aba_minima_valor, erro=False):
    """Atualiza label da aba mínima externa."""
    if not g.ABA_EXT_LBL or not hasattr(g.ABA_EXT_LBL, 'setText'):
        return

    if erro:
        g.ABA_EXT_LBL.setText("N/A")
        if hasattr(g.ABA_EXT_LBL, 'setStyleSheet'):
            g.ABA_EXT_LBL.setStyleSheet("color: red")
    else:
        g.ABA_EXT_LBL.setText(f"{aba_minima_valor:.0f}")
        if hasattr(g.ABA_EXT_LBL, 'setStyleSheet'):
            g.ABA_EXT_LBL.setStyleSheet("")


def aba_minima_externa():
    """
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Aba mínima = (Largura do canal / 2) + Espessura + Margem de segurança
    """
    aba_minima_valor = 0

    try:
        canal_valor = verificar_widget_inicializado(
            g.CANAL_COMB, 'currentText', '')

        if canal_valor == "":
            if g.ABA_EXT_LBL and hasattr(g.ABA_EXT_LBL, 'setText'):
                g.ABA_EXT_LBL.setText("")
            return aba_minima_valor

        # Extrai valor numérico do canal
        canal_valor_num = _extrair_valor_canal(canal_valor)

        if canal_valor_num is None:
            _atualizar_label_aba_externa(0, erro=True)
            return aba_minima_valor

        espessura_text = verificar_widget_inicializado(
            g.ESP_COMB, 'currentText', '0')
        espessura = float(espessura_text.replace(',', '.'))

        aba_minima_valor = canal_valor_num / 2 + espessura + 2

        _atualizar_label_aba_externa(aba_minima_valor)

    except (ValueError, AttributeError) as e:
        print(f"Erro ao calcular aba mínima externa: {e}")
        _atualizar_label_aba_externa(0, erro=True)

    return aba_minima_valor


def _obter_dados_z_minimo():
    """Obtém dados necessários para cálculo Z mínimo."""
    material = verificar_widget_inicializado(g.MAT_COMB, 'currentText', '')
    espessura_text = verificar_widget_inicializado(
        g.ESP_COMB, 'currentText', '0')
    canal_valor = verificar_widget_inicializado(
        g.CANAL_COMB, 'currentText', '')
    deducao_label_text = verificar_widget_inicializado(
        g.DED_LBL, 'text', '0').replace(' Copiado!', '')

    return material, espessura_text, canal_valor, deducao_label_text


def _validar_dados_z_minimo(material, canal_valor, espessura):
    """Valida dados para cálculo Z mínimo."""
    return bool(material and canal_valor and espessura > 0)


def _atualizar_label_z_externo(valor, erro_tipo=None):
    """Atualiza label Z externo."""
    if not g.Z_EXT_LBL or not hasattr(g.Z_EXT_LBL, 'setText'):
        return

    if erro_tipo == "limpar":
        g.Z_EXT_LBL.setText("")
    elif erro_tipo == "na":
        g.Z_EXT_LBL.setText("N/A")
        if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
            g.Z_EXT_LBL.setStyleSheet("color: red")
    elif erro_tipo == "orange":
        g.Z_EXT_LBL.setText("N/A")
        if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
            g.Z_EXT_LBL.setStyleSheet("color: orange")
    else:
        g.Z_EXT_LBL.setText(f'{valor:.0f}')
        if hasattr(g.Z_EXT_LBL, 'setStyleSheet'):
            g.Z_EXT_LBL.setStyleSheet("")


def z_minimo_externo():
    """
    Calcula o valor mínimo externo Z com base na espessura, dedução e largura do canal.
    Z mínimo = Espessura + (Dedução / 2) + (Largura do canal / 2) + Margem
    """
    try:
        # Obtém dados
        material, espessura_text, canal_valor, deducao_label_text = _obter_dados_z_minimo()

        # Converte espessura
        espessura = float(espessura_text.replace(',', '.'))
        deducao_valor = float(deducao_label_text.replace(
            ',', '.')) if deducao_label_text else 0

        # Valida dados necessários
        if not _validar_dados_z_minimo(material, canal_valor, espessura):
            _atualizar_label_z_externo(0, "limpar")
            return

        # Busca canal no banco de dados
        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if canal_obj is None:
            _atualizar_label_z_externo(0, "na")
            return

        # Verifica largura do canal
        try:
            largura_canal = canal_obj.largura
            if largura_canal is None:
                _atualizar_label_z_externo(0, "na")
                return
        except (AttributeError, ValueError, TypeError):
            _atualizar_label_z_externo(0, "na")
            return

        # Calcula Z mínimo externo
        if deducao_valor > 0:
            valor_z_min_ext = espessura + \
                (deducao_valor / 2) + (largura_canal / 2) + 2
            _atualizar_label_z_externo(valor_z_min_ext)
        else:
            _atualizar_label_z_externo(0, "orange")

    except ValueError as e:
        print(
            f"Erro ao converter valores para o cálculo do Z mínimo externo: {e}")
        _atualizar_label_z_externo(0, "na")
    except (AttributeError, TypeError) as e:
        print(f"Erro de atributo ou tipo no cálculo do Z mínimo externo: {e}")


def _obter_valores_dobras(w):
    """Obtém os valores das dobras dos widgets de entrada para uma coluna específica."""
    return [
        getattr(g, f'aba{i}_entry_{w}').text() or ''
        if getattr(g, f'aba{i}_entry_{w}', None) is not None else ''
        for i in range(1, g.N)
    ]


def _obter_valor_deducao():
    """Obtém o valor da dedução dos widgets correspondentes."""
    deducao_valor = str(verificar_widget_inicializado(
        g.DED_LBL, 'text', '')).replace(' Copiado!', '')
    deducao_espec_str = verificar_widget_inicializado(
        g.DED_ESPEC_ENTRY, 'text', '') or ''
    deducao_espec = deducao_espec_str.replace(',', '.')

    if deducao_espec != "":
        return deducao_espec
    return deducao_valor


def _calcular_medida_dobra(dobra, deducao_valor, i, valores_dobras):
    """
    Calcula a medida da dobra baseada na posição e valor de dedução,
    considerando blocos contínuos de abas preenchidas.
    """
    deducao_valor = float(deducao_valor)
    preenchidos = [bool(v.strip()) for v in valores_dobras]
    blocos = []
    bloco_atual = []
    for idx, preenchido in enumerate(preenchidos):
        if preenchido:
            bloco_atual.append(idx)
        else:
            if bloco_atual:
                blocos.append(bloco_atual)
                bloco_atual = []
    if bloco_atual:
        blocos.append(bloco_atual)
    pos = i - 1
    bloco_encontrado = None
    for bloco in blocos:
        if pos in bloco:
            bloco_encontrado = bloco
            break
    if bloco_encontrado is None:
        return None
    pos_bloco = bloco_encontrado.index(pos)
    valor = float(dobra)
    if len(bloco_encontrado) == 1:
        resultado = valor - deducao_valor / 2
    else:
        if pos_bloco in (0, len(bloco_encontrado) - 1):
            resultado = valor - deducao_valor / 2
        else:
            resultado = valor - deducao_valor
    return resultado


def _atualizar_widgets_dobra(i, w, medidadobra, metade_dobra):
    """Atualiza os widgets com os valores calculados de dobra."""
    def atualizar_widget_seguro(widget, valor):
        """Atualiza um widget de forma segura"""
        if widget is not None and hasattr(widget, 'setText'):
            widget.setText(f"{valor:.2f}")
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet("")

    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)

    atualizar_widget_seguro(widget_medida, medidadobra)
    atualizar_widget_seguro(widget_metade, metade_dobra)


def _limpar_widgets_dobra(i, w):
    """Limpa os widgets de dobra quando o valor está vazio."""
    def limpar_widget_seguro(widget):
        """Limpa um widget de forma segura"""
        if widget is not None and hasattr(widget, 'setText'):
            widget.setText("")

    widget_medida = getattr(g, f'medidadobra{i}_label_{w}', None)
    widget_metade = getattr(g, f'metadedobra{i}_label_{w}', None)

    limpar_widget_seguro(widget_medida)
    limpar_widget_seguro(widget_metade)


def _calcular_e_atualizar_blank(w):
    """Calcula e atualiza os valores de blank para uma coluna."""
    blank = sum(
        float(getattr(g, f'medidadobra{row}_label_{w}').text().replace(
            ' Copiado!', ''))
        for row in range(1, g.N)
        if getattr(g, f'medidadobra{row}_label_{w}', None) is not None
        and hasattr(getattr(g, f'medidadobra{row}_label_{w}'), 'text')
        and getattr(g, f'medidadobra{row}_label_{w}').text()
    )

    metade_blank = blank / 2

    # Atualizar os widgets com os valores calculados
    label = getattr(g, f'medida_blank_label_{w}', None)
    if label and hasattr(label, 'setText'):
        if blank:
            label.setText(f"{blank:.2f}")
            if hasattr(label, 'setStyleSheet'):
                label.setStyleSheet("")
        else:
            label.setText("")

    label = getattr(g, f'metade_blank_label_{w}', None)
    if label and hasattr(label, 'setText'):
        if metade_blank:
            label.setText(f"{metade_blank:.2f}")
            if hasattr(label, 'setStyleSheet'):
                label.setStyleSheet("")
        else:
            label.setText("")


def calcular_dobra(w):
    """
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    """
    # Obter valores das dobras diretamente dos widgets para a coluna específica
    valores_dobras = _obter_valores_dobras(w)

    # Obter valor da dedução
    deducao_valor = _obter_valor_deducao()

    if not deducao_valor:
        return

    # Iterar pelas linhas para calcular as medidas
    for i in range(1, g.N):
        indice_lista = i - 1  # Índice na lista valores_dobras (base 0)

        if indice_lista >= len(valores_dobras):
            continue

        dobra = valores_dobras[indice_lista].replace(',', '.')

        if dobra == "":
            _limpar_widgets_dobra(i, w)
        else:
            medidadobra = _calcular_medida_dobra(
                dobra, deducao_valor, i, valores_dobras)
            metade_dobra = medidadobra / 2

            _atualizar_widgets_dobra(i, w, medidadobra, metade_dobra)

            # Verificar aba mínima usando o valor atual
            valor_atual = valores_dobras[indice_lista] if indice_lista < len(
                valores_dobras) else ""
            verificar_aba_minima(valor_atual, i, w)

    # Calcular e atualizar blank para esta coluna (fora do loop)
    _calcular_e_atualizar_blank(w)


def verificar_aba_minima(dobra, i, w):
    """
    Verifica se a dobra é menor que a aba mínima e atualiza o widget correspondente.
    """
    # Verificar se a dobra é menor que a aba mínima
    aba_minima = aba_minima_externa()

    # Obter o widget dinamicamente
    entry_widget = getattr(g, f'aba{i}_entry_{w}', None)

    if entry_widget is None:
        return

    # Verificar se o campo está vazio
    if not dobra.strip():  # Se o campo estiver vazio ou contiver apenas espaços
        if hasattr(entry_widget, 'setStyleSheet'):
            entry_widget.setStyleSheet("")
        return

    # Corrigido R1705: Removido else desnecessário após return
    try:
        if float(dobra) < aba_minima:
            if hasattr(entry_widget, 'setStyleSheet'):
                entry_widget.setStyleSheet(
                    "color: white; background-color: red")
        else:
            if hasattr(entry_widget, 'setStyleSheet'):
                entry_widget.setStyleSheet("")
    except ValueError:
        # Tratar erros de conversão
        if hasattr(entry_widget, 'setStyleSheet'):
            entry_widget.setStyleSheet("")
        print(f"Erro: Valor inválido na aba {i}, coluna {w}.")


def razao_ri_espessura():
    """
    Calcula a razão entre o raio interno e a espessura, atualizando o label correspondente.
    razao = raio_interno / espessura
    """
    # Verifica se o widget existe
    if not g.RAZAO_RIE_LBL or not hasattr(g.RAZAO_RIE_LBL, 'setText'):
        return

    try:
        # Obtém os valores dos widgets e valida
        espessura_text = verificar_widget_inicializado(
            g.ESP_COMB, 'currentText', '0') or '0'
        espessura = float(espessura_text.replace(',', '.'))

        raio_interno_str = verificar_widget_inicializado(
            g.RI_ENTRY, 'text', '0') or '0'
        raio_interno = float(raio_interno_str.replace(',', '.'))

        # Valida se os valores necessários são maiores que zero
        if raio_interno <= 0 or espessura <= 0:
            g.RAZAO_RIE_LBL.setText('')
            return

        razao = raio_interno / espessura

        # Limita a razão a valores razoáveis (conforme tabela de referência)
        razao = min(razao, 10.0)

        # Atualiza o label com o valor calculado
        g.RAZAO_RIE_LBL.setText(f"{razao:.1f}")

        # Aplica cor baseada na faixa de valores
        if hasattr(g.RAZAO_RIE_LBL, 'setStyleSheet'):
            if razao < 0.5:
                g.RAZAO_RIE_LBL.setStyleSheet(
                    "color: red")  # Razão muito baixa
            elif razao > 5.0:
                g.RAZAO_RIE_LBL.setStyleSheet("color: orange")  # Razão alta
            else:
                g.RAZAO_RIE_LBL.setStyleSheet("")  # Faixa normal - cor padrão

    except ValueError as e:
        print(f"Erro ao converter valores para o cálculo da razão: {e}")
        g.RAZAO_RIE_LBL.setText('N/A')
        if hasattr(g.RAZAO_RIE_LBL, 'setStyleSheet'):
            g.RAZAO_RIE_LBL.setStyleSheet("color: red")
    except (AttributeError, TypeError) as e:
        print(
            f"Erro de atributo ou tipo no cálculo da razão ri/espessura: {e}")
