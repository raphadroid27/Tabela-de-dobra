'''
Funções auxiliares para o aplicativo de cálculo de dobras.
'''
from math import pi
import re
from src.config import globals as g
from src.models.models import Canal
from src.utils.banco_dados import session

def calcular_k_offset():
    '''
    Calcula o fator K com base nos valores de espessura, dedução e raio interno.
    Atualiza o label correspondente com o valor calculado.
    '''
    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(g.ESP_COMB.get() or 0)
        raio_interno = float(g.RI_ENTRY.get().replace(',', '.') or 0)
        deducao_espec = float(g.DED_ESPEC_ENTRY.get().replace(',', '.') or 0)
        deducao_valor = float(g.DED_LBL.cget('text') or 0)

        # Usa a dedução específica, se fornecida
        if g.DED_ESPEC_ENTRY.get():
            deducao_valor = deducao_espec

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura or not deducao_valor:
            return

        # Calcula o fator K
        fator_k = (4 * (espessura - (deducao_valor / 2) + raio_interno) -
                     (pi * raio_interno)) / (pi * espessura)

        # Limita o fator K a 0.5
        fator_k = min(fator_k, 0.5)

        #Calcula o offset
        offset = fator_k * espessura

        # Atualiza o label com o valor calculado
        g.K_LBL.config(text=f"{fator_k:.2f}", fg="blue"
                       if deducao_valor == deducao_espec else "black")

        g.OFFSET_LBL.config(text=f"{offset:.2f}", fg="blue"
                            if deducao_valor == deducao_espec else "black")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do fator K.")

def aba_minima_externa():
    '''
    Calcula a aba mínima externa com base no valor do canal e na espessura.
    Atualiza o label correspondente com o valor calculado.
    '''
    aba_minima_valor = 0  # Valor padrão caso a condição não seja satisfeita

    try:
        if g.CANAL_COMB.get() != "":
            canal_valor = float(re.findall(r'\d+\.?\d*', g.CANAL_COMB.get())[0])
            espessura = float(g.ESP_COMB.get())

            aba_minima_valor = canal_valor / 2 + espessura + 2
            g.ABA_EXT_LBL.config(text=f"{aba_minima_valor:.0f}")
    except (ValueError, AttributeError) as e:
        print(f"Erro ao calcular aba mínima externa: {e}")
        g.ABA_EXT_LBL.config(text="N/A", fg="red")

    return aba_minima_valor

def z_minimo_externo():
    '''
    Calcula o valor mínimo externo com base na espessura, dedução e largura do canal.
    Atualiza o label correspondente com o valor calculado.
    '''
    try:
        # Obtém os valores diretamente e verifica se são válidos
        material = g.MAT_COMB.get()
        espessura = float(g.ESP_COMB.get())
        canal_valor = g.CANAL_COMB.get()
        deducao_valor = float(g.DED_LBL.cget('text'))

        canal_obj = session.query(Canal).filter_by(valor=canal_valor).first()

        if material != "" and espessura != "" and canal_valor != "":
            if not canal_obj.largura:
                g.Z_EXT_LBL.config(text="N/A", fg="red")
                return

            if canal_valor and deducao_valor:
                canal_valor = float(re.findall(r'\d+\.?\d*', canal_valor)[0])
                valor_z_min_ext = espessura + (deducao_valor / 2) + (canal_obj.largura / 2) + 2
                g.Z_EXT_LBL.config(text=f'{valor_z_min_ext:.0f}', fg="black")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo do Z mínimo externo.")

def calcular_dobra(w):
    '''
    Calcula as medidas de dobra e metade de dobra com base nos valores de entrada.
    '''
    # Criar uma lista de listas para armazenar os valores de linha i e coluna w
    g.DOBRAS_VALORES = [
        [
            getattr(g, f'aba{i}_entry_{col}').get() or ''  # Substitui valores vazios por '0'
            for col in range(1, w + 1)
        ]
        for i in range(1, g.N)
    ]

    deducao_valor = str(g.DED_LBL.cget('text')).replace(' Copiado!', '')
    deducao_espec = g.DED_ESPEC_ENTRY.get().replace(',', '.')

    # Exibir a matriz de valores para depuração
    print("Matriz de dobras (g.dobras_get):")
    for linha in g.DOBRAS_VALORES:
        print(linha)

    # Determinar o valor da dedução
    if deducao_espec != "":
        deducao_valor = deducao_espec

    if not deducao_valor:
        return

    # Função auxiliar para calcular medidas
    def calcular_medida(deducao_valor, i, w):
        dobra = g.DOBRAS_VALORES[i - 1][w - 1].replace(',', '.')

        if dobra == "":
            getattr(g, f'medidadobra{i}_label_{w}').config(text="")
            getattr(g, f'metadedobra{i}_label_{w}').config(text="")
        else:
            if i in (1, g.N - 1):
                medidadobra = float(dobra) - float(deducao_valor) / 2
            else:
                if g.DOBRAS_VALORES[i][w - 1] == "":
                    medidadobra = float(dobra) - float(deducao_valor) / 2
                else:
                    medidadobra = float(dobra) - float(deducao_valor)

            metade_dobra = medidadobra / 2

            # Atualizar os widgets com os valores calculados
            getattr(g, f'medidadobra{i}_label_{w}').config(text=f'{medidadobra:.2f}', fg="black")
            getattr(g, f'metadedobra{i}_label_{w}').config(text=f'{metade_dobra:.2f}', fg="black")

        blank = sum(
        float(getattr(g, f'medidadobra{row}_label_{w}').cget('text').replace(' Copiado!', ''))
        for row in range(1, g.N)
        if getattr(g, f'medidadobra{row}_label_{w}').cget('text')
    )

        metade_blank = blank / 2

        # Atualizar os widgets com os valores calculados
        label = getattr(g, f'medida_blank_label_{w}')
        if blank:
            label.config(text=f"{blank:.2f}", fg="black")
        else:
            label.config(text="")

        label = getattr(g, f'metade_blank_label_{w}')
        if metade_blank:
            label.config(text=f"{metade_blank:.2f}", fg="black")
        else:
            label.config(text="")

    # Iterar pelas linhas e colunas para calcular as medidas
    for i in range(1, g.N):
        for col in range(1, w + 1):
            calcular_medida(deducao_valor, i, col)
            verificar_aba_minima(g.DOBRAS_VALORES[i - 1][col - 1], i, col)

def verificar_aba_minima(dobra, i, w):
    '''
    Verifica se a dobra é menor que a aba mínima e atualiza o widget correspondente.
    '''
    # Verificar se a dobra é menor que a aba mínima
    aba_minima = aba_minima_externa()

    # Obter o widget dinamicamente
    entry_widget = getattr(g, f'aba{i}_entry_{w}')

    # Verificar se o campo está vazio
    if not dobra.strip():  # Se o campo estiver vazio ou contiver apenas espaços
        entry_widget.config(fg="black", bg="white")
        print(f"Valor vazio na aba {i}, coluna {w}.")
    else:
        try:
            # Converter o valor de 'dobra' para float e verificar se é menor que 'aba_minima'
            if float(dobra) < aba_minima:
                entry_widget.config(fg="white", bg="red")
            else:
                entry_widget.config(fg="black", bg="white")
        except ValueError:
            # Tratar erros de conversão
            entry_widget.config(fg="black", bg="white")
            print(f"Erro: Valor inválido na aba {i}, coluna {w}.")

def razao_ri_espessura():
    '''
    Calcula a razão entre o raio interno e a espessura, atualizando o label correspondente.
    '''
    if not g.RAZAO_RIE_LBL or not g.RAZAO_RIE_LBL.winfo_exists():
        return

    try:
        # Obtém os valores diretamente e verifica se são válidos
        espessura = float(g.ESP_COMB.get() or 0)
        raio_interno = float(g.RI_ENTRY.get().replace(',', '.') or 0)

        # Valida se os valores necessários são maiores que zero
        if not raio_interno or not espessura:
            return

        # Calcula a razão
        razao = raio_interno / espessura

        # Atualiza o label com o valor calculado
        g.RAZAO_RIE_LBL.config(text=f"{razao:.2f}")

    except ValueError:
        # Trata erros de conversão
        print("Erro: Valores inválidos fornecidos para o cálculo da razão.")
