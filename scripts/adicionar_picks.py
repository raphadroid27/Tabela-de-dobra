#!/usr/bin/env python3
"""
Script para adicionar picks (marcações) automaticamente em arquivos DXF
As marcações são adicionadas nas intersecções entre linhas de dobra e contorno
O arco tem início e fim nos pontos de intersecção com a linha de contorno
Para dobras colineares, adiciona picks APENAS nas extremidades (não no meio)
Picks nas extremidades de uma mesma linha de dobra
CONVERGEM para o centro (espelhados)
Detecta também filetes/chanfros próximos às dobras
Remove arcos degenerados (vestígios com abertura < 1°)
Processa todos os arquivos DXF de uma pasta e salva em "dxf com pick"
"""

import glob
import math
import os
import sys
import traceback

import ezdxf
from ezdxf.math import Vec2

#  pylint: disable=R0913,R0914,R0917,R1702


def calcular_interseccao_linhas(p1_start, p1_end, p2_start, p2_end):
    """
    Calcula a intersecção entre duas linhas
    """
    x1, y1 = p1_start.x, p1_start.y
    x2, y2 = p1_end.x, p1_end.y
    x3, y3 = p2_start.x, p2_start.y
    x4, y4 = p2_end.x, p2_end.y

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-10:
        return None, None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return Vec2(x, y), t

    return None, None


def encontrar_ponto_mais_proximo_linha(ponto_ref, linha_start, linha_end):
    """
    Encontra o ponto mais próximo na linha a um ponto de referência
    Retorna o ponto projetado
    """
    dx = linha_end.x - linha_start.x
    dy = linha_end.y - linha_start.y

    length_sq = dx * dx + dy * dy
    if length_sq < 1e-10:
        return linha_start

    projection_param = (
        (ponto_ref.x - linha_start.x) * dx + (ponto_ref.y - linha_start.y) * dy
    ) / length_sq
    projection_param = max(0, min(1, projection_param))  # Clamp to [0,1]

    ponto = Vec2(
        linha_start.x + projection_param * dx, linha_start.y + projection_param * dy
    )

    return ponto


def linhas_sao_colineares_simples(
    linha1_start, linha1_end, linha2_start, linha2_end, tol=0.01
):
    """
    Verifica se duas linhas são colineares usando critério do AutoCAD
    """
    l1_horizontal = abs(linha1_start.y - linha1_end.y) < tol
    l1_vertical = abs(linha1_start.x - linha1_end.x) < tol

    l2_horizontal = abs(linha2_start.y - linha2_end.y) < tol
    l2_vertical = abs(linha2_start.x - linha2_end.x) < tol

    if l1_horizontal and l2_horizontal:
        return abs(linha1_start.y - linha2_start.y) < tol

    if l1_vertical and l2_vertical:
        return abs(linha1_start.x - linha2_start.x) < tol

    return False


def agrupar_dobras_colineares(linhas_dobra, tol=0.01):
    """
    Agrupa linhas de dobra colineares
    """
    n = len(linhas_dobra)
    grupos = {}
    visitados = set()
    grupo_id = 0

    for i in range(n):
        if i in visitados:
            continue

        visitados.add(i)
        grupo_atual = [i]
        linha1_s, linha1_e, _, _ = linhas_dobra[i]

        for j in range(i + 1, n):
            if j in visitados:
                continue

            linha2_s, linha2_e, _, _ = linhas_dobra[j]

            if linhas_sao_colineares_simples(
                linha1_s, linha1_e, linha2_s, linha2_e, tol
            ):
                visitados.add(j)
                grupo_atual.append(j)

        grupos[grupo_id] = grupo_atual

        grupo_id += 1

    return grupos


def encontrar_extremidades_grupo(linhas_dobra, indices_grupo):
    """
    Para um grupo de linhas colineares, encontra as coordenadas extremas
    """
    if not indices_grupo:
        return None, None, None

    idx0 = indices_grupo[0]
    s0, e0, _, _ = linhas_dobra[idx0]

    is_horizontal = abs(s0.y - e0.y) < 0.01

    if is_horizontal:
        coords = []
        for idx in indices_grupo:
            s, e, _, _ = linhas_dobra[idx]
            coords.extend([s.x, e.x])
        return min(coords), max(coords), True

    coords = []
    for idx in indices_grupo:
        s, e, _, _ = linhas_dobra[idx]
        coords.extend([s.y, e.y])
    return min(coords), max(coords), False


def calcular_coeficientes_circulo_linha(centro, raio, linha_start, linha_end):
    """
    Calcula os coeficientes da equação quadrática para intersecção círculo-linha
    """
    dx = linha_end.x - linha_start.x
    dy = linha_end.y - linha_start.y

    fx = linha_start.x - centro.x
    fy = linha_start.y - centro.y

    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - raio * raio

    return a, b, c, dx, dy


def resolver_equacao_quadratica(a, b, c):
    """
    Resolve equação quadrática ax² + bx + c = 0
    Retorna lista de raízes t
    """
    discriminant = b * b - 4 * a * c

    if discriminant < -1e-10:
        return []

    discriminant = max(discriminant, 0)
    sqrt_disc = math.sqrt(discriminant)

    t1 = (-b - sqrt_disc) / (2 * a)
    t2 = (-b + sqrt_disc) / (2 * a)

    return [t1, t2]


def calcular_ponto_interseccao(linha_start, linha_end, t, centro):
    """
    Calcula ponto na linha para parâmetro t e seu ângulo em relação ao centro
    """
    dx = linha_end.x - linha_start.x
    dy = linha_end.y - linha_start.y

    # Aumentar tolerância para linhas inclinadas
    if -0.1 <= t <= 1.1:
        t_clamped = max(0, min(1, t))
        x = linha_start.x + t_clamped * dx
        y = linha_start.y + t_clamped * dy
        ponto = Vec2(x, y)

        angulo = math.atan2(y - centro.y, x - centro.x)
        angulo_graus = math.degrees(angulo)

        return (ponto, t_clamped, angulo_graus)

    return None


def calcular_pontos_interseccao_arco_linha(centro, raio, linha_start, linha_end):
    """
    Calcula os pontos de intersecção entre um círculo e uma linha
    """
    dx = linha_end.x - linha_start.x
    dy = linha_end.y - linha_start.y

    linha_len = math.sqrt(dx * dx + dy * dy)
    if linha_len < 1e-10:
        return []

    a, b, c, dx, dy = calcular_coeficientes_circulo_linha(
        centro, raio, linha_start, linha_end
    )

    raizes_t = resolver_equacao_quadratica(a, b, c)

    pontos = []
    for t in raizes_t:
        ponto_info = calcular_ponto_interseccao(linha_start, linha_end, t, centro)
        if ponto_info:
            pontos.append(ponto_info)

    return pontos


def normalizar_angulo(angulo):
    """Normaliza ângulo para [0, 360)"""
    while angulo < 0:
        angulo += 360
    while angulo >= 360:
        angulo -= 360
    return angulo


def angulo_entre(ang, start, end):
    """Verifica se ângulo está entre start e end"""
    ang = normalizar_angulo(ang)
    start = normalizar_angulo(start)
    end = normalizar_angulo(end)

    if start <= end:
        return start <= ang <= end

    return ang >= start or ang <= end


def criar_pick_e_preparar_trim(
    centro, raio, direcao_interna, linha_start, linha_end, layer
):
    """
    Calcula os dados do pick e prepara informações para o trim
    """
    interseccoes = calcular_pontos_interseccao_arco_linha(
        centro, raio, linha_start, linha_end
    )

    if len(interseccoes) < 2:
        return False, None, None

    interseccoes.sort(key=lambda x: x[1])

    ponto1, _, angulo1 = interseccoes[0]
    ponto2, _, angulo2 = interseccoes[1]

    ponto_medio_arco = centro + direcao_interna * raio
    angulo_medio = math.atan2(
        ponto_medio_arco.y - centro.y, ponto_medio_arco.x - centro.x
    )
    angulo_medio_graus = normalizar_angulo(math.degrees(angulo_medio))

    angulo1 = normalizar_angulo(angulo1)
    angulo2 = normalizar_angulo(angulo2)

    if angulo_entre(angulo_medio_graus, angulo1, angulo2):
        start_angle = angulo1
        end_angle = angulo2
    else:
        start_angle = angulo2
        end_angle = angulo1

    # VALIDAÇÃO: Verificar se o arco tem abertura mínima
    angle_diff = abs(end_angle - start_angle)
    if angle_diff > 180:
        angle_diff = 360 - angle_diff

    # Rejeitar arcos com abertura menor que 1 grau (vestígios)
    if angle_diff < 1.0:
        return False, None, None

    dados_arco = {
        "centro": centro,
        "raio": raio,
        "start_angle": start_angle,
        "end_angle": end_angle,
        "layer": layer,
    }

    dados_trim = {
        "linha_start": linha_start,
        "linha_end": linha_end,
        "ponto1": ponto1,
        "ponto2": ponto2,
        "t1": interseccoes[0][1],
        "t2": interseccoes[1][1],
        "layer": layer,
    }

    return True, dados_arco, dados_trim


def coletar_linhas_dobra(msp):
    """
    Coleta todas as linhas de dobra do modelspace
    """
    linhas_dobra = []
    for entity in msp.query("LINE"):
        try:
            layer = entity.get_dxf_attrib("layer", "0").upper()
            if "DOBRA" in layer:
                start = Vec2(entity.dxf.start.x, entity.dxf.start.y)
                end = Vec2(entity.dxf.end.x, entity.dxf.end.y)
                linhas_dobra.append((start, end, layer, entity))
        except (AttributeError, KeyError):
            continue
    return linhas_dobra


def coletar_linhas_contorno(msp):
    """
    Coleta todas as linhas de contorno do modelspace
    """
    linhas_contorno = []
    for entity in msp.query("LINE"):
        try:
            layer = entity.get_dxf_attrib("layer", "0").upper()
            color = entity.get_dxf_attrib("color", 256)
            if layer == "0" or layer == "CORTE_S_COMP" or color == 7:
                start = Vec2(entity.dxf.start.x, entity.dxf.start.y)
                end = Vec2(entity.dxf.end.x, entity.dxf.end.y)
                linhas_contorno.append((start, end, layer, entity))
        except (AttributeError, KeyError):
            continue
    return linhas_contorno


def coletar_interseccoes_grupo(
    indices_grupo, linhas_dobra, linhas_contorno, is_horizontal
):
    """
    Coleta todas as intersecções entre dobras do grupo e linhas de contorno
    """
    interseccoes_grupo = []

    for idx_dobra in indices_grupo:
        dobra_start, dobra_end, _, _ = linhas_dobra[idx_dobra]

        for (
            contorno_start,
            contorno_end,
            contorno_layer,
            contorno_entity,
        ) in linhas_contorno:
            ponto, _ = calcular_interseccao_linhas(
                dobra_start, dobra_end, contorno_start, contorno_end
            )

            # Se não encontrou interseção direta, verificar proximidade (filetes)
            if not ponto:
                # Verificar se alguma extremidade do contorno está próxima da dobra
                ponto_proj_start = encontrar_ponto_mais_proximo_linha(
                    contorno_start, dobra_start, dobra_end
                )
                ponto_proj_end = encontrar_ponto_mais_proximo_linha(
                    contorno_end, dobra_start, dobra_end
                )

                dist_start = (contorno_start - ponto_proj_start).magnitude
                dist_end = (contorno_end - ponto_proj_end).magnitude

                # Se alguma extremidade está a menos de 3mm da dobra,
                # considerar como intersecção
                if dist_start < 3.0:
                    ponto = ponto_proj_start
                elif dist_end < 3.0:
                    ponto = ponto_proj_end

            if ponto:
                coord = ponto.x if is_horizontal else ponto.y
                interseccoes_grupo.append(
                    (
                        ponto,
                        contorno_start,
                        contorno_end,
                        contorno_layer,
                        contorno_entity,
                        coord,
                    )
                )

    return interseccoes_grupo


def filtrar_interseccoes_extremas(
    interseccoes_grupo, coord_min, coord_max, tol_extremidade=0.5
):
    """
    Filtra apenas as intersecções que estão nas extremidades do grupo
    """
    interseccoes_extremas = []

    for item in interseccoes_grupo:
        _, _, _, _, _, coord = item

        if (
            abs(coord - coord_min) <= tol_extremidade
            or abs(coord - coord_max) <= tol_extremidade
        ):
            interseccoes_extremas.append(item)

    return interseccoes_extremas


def agrupar_picks_por_extremidade(
    interseccoes_extremas, coord_min, coord_max, tol_extremidade=0.5
):
    """
    Agrupa os picks por extremidade (mínimo ou máximo)
    """
    picks_no_minimo = []
    picks_no_maximo = []

    for ponto, cs, ce, cl, cent, coord in interseccoes_extremas:
        if abs(coord - coord_min) <= tol_extremidade:
            picks_no_minimo.append((ponto, cs, ce, cl, cent))
        if abs(coord - coord_max) <= tol_extremidade:
            picks_no_maximo.append((ponto, cs, ce, cl, cent))

    return picks_no_minimo, picks_no_maximo


def calcular_centro_dobra(
    coord_min, coord_max, is_horizontal, linhas_dobra, indices_grupo
):
    """
    Calcula o ponto central da linha de dobra
    """
    if is_horizontal:
        centro_dobra = Vec2(
            (coord_min + coord_max) / 2, linhas_dobra[indices_grupo[0]][0].y
        )
    else:
        centro_dobra = Vec2(
            linhas_dobra[indices_grupo[0]][0].x, (coord_min + coord_max) / 2
        )

    return centro_dobra


def criar_picks_para_extremidade(picks_na_extremidade, centro_dobra, raio):
    """
    Cria picks para uma extremidade específica
    """
    picks_info = []

    for (
        ponto,
        contorno_start,
        contorno_end,
        contorno_layer,
        contorno_entity,
    ) in picks_na_extremidade:
        direcao_interna = (centro_dobra - ponto).normalize()

        sucesso, dados_arco, dados_trim = criar_pick_e_preparar_trim(
            ponto,
            raio,
            direcao_interna,
            contorno_start,
            contorno_end,
            contorno_layer,
        )

        if sucesso:
            picks_info.append((contorno_entity, dados_arco, dados_trim))

    return picks_info


def processar_grupo_dobras(indices_grupo, linhas_dobra, linhas_contorno, raio):
    """
    Processa um grupo de dobras colineares e adiciona picks
    """
    picks_por_linha = {}

    # Encontrar extremidades do grupo
    coord_min, coord_max, is_horizontal = encontrar_extremidades_grupo(
        linhas_dobra, indices_grupo
    )

    if coord_min is None:
        return picks_por_linha

    # Coletar TODAS as intersecções do grupo
    interseccoes_grupo = coletar_interseccoes_grupo(
        indices_grupo, linhas_dobra, linhas_contorno, is_horizontal
    )

    # Filtrar APENAS extremidades
    tol_extremidade = 0.5
    interseccoes_extremas = filtrar_interseccoes_extremas(
        interseccoes_grupo, coord_min, coord_max, tol_extremidade
    )

    # Agrupar picks por extremidade (min ou max)
    picks_no_minimo, picks_no_maximo = agrupar_picks_por_extremidade(
        interseccoes_extremas, coord_min, coord_max, tol_extremidade
    )

    # Calcular ponto central da linha de dobra
    centro_dobra = calcular_centro_dobra(
        coord_min, coord_max, is_horizontal, linhas_dobra, indices_grupo
    )

    # Criar picks apontando para o centro da dobra
    # Picks no mínimo apontam para o máximo (centro)
    picks_minimo = criar_picks_para_extremidade(picks_no_minimo, centro_dobra, raio)

    # Picks no máximo apontam para o mínimo (centro)
    picks_maximo = criar_picks_para_extremidade(picks_no_maximo, centro_dobra, raio)

    # Consolidar todos os picks
    for contorno_entity, dados_arco, dados_trim in picks_minimo + picks_maximo:
        handle = contorno_entity.dxf.handle

        if handle not in picks_por_linha:
            picks_por_linha[handle] = {
                "entity": contorno_entity,
                "picks": [],
            }

        picks_por_linha[handle]["picks"].append((dados_arco, dados_trim))

    return picks_por_linha


def aplicar_trims(picks_por_linha, msp):
    """
    Aplica trims nas linhas baseado nos picks
    """
    picks_adicionados = 0
    trims_aplicados = 0

    for info in picks_por_linha.values():
        entity = info["entity"]
        picks = info["picks"]

        for dados_arco, dados_trim in picks:
            msp.add_arc(
                center=(dados_arco["centro"].x, dados_arco["centro"].y),
                radius=dados_arco["raio"],
                start_angle=dados_arco["start_angle"],
                end_angle=dados_arco["end_angle"],
                dxfattribs={"layer": dados_arco["layer"]},
            )
            picks_adicionados += 1

        if len(picks) > 0:
            try:
                linha_start = Vec2(entity.dxf.start.x, entity.dxf.start.y)
                linha_end = Vec2(entity.dxf.end.x, entity.dxf.end.y)
                layer = entity.dxf.layer
                color = entity.dxf.color

                pontos_corte = []
                for _, dados_trim in picks:
                    pontos_corte.append((dados_trim["t1"], dados_trim["ponto1"]))
                    pontos_corte.append((dados_trim["t2"], dados_trim["ponto2"]))

                pontos_corte.sort(key=lambda x: x[0])

                if len(pontos_corte) > 0:
                    ponto_atual = linha_start

                    for i in range(0, len(pontos_corte), 2):
                        if i + 1 < len(pontos_corte):
                            _, p1 = pontos_corte[i]
                            _, p2 = pontos_corte[i + 1]

                            if (ponto_atual - p1).magnitude > 1e-3:
                                msp.add_line(
                                    (ponto_atual.x, ponto_atual.y),
                                    (p1.x, p1.y),
                                    dxfattribs={"layer": layer, "color": color},
                                )

                            ponto_atual = p2

                    if (ponto_atual - linha_end).magnitude > 1e-3:
                        msp.add_line(
                            (ponto_atual.x, ponto_atual.y),
                            (linha_end.x, linha_end.y),
                            dxfattribs={"layer": layer, "color": color},
                        )

                    msp.delete_entity(entity)
                    trims_aplicados += 1

            except (ValueError, TypeError):
                pass

    return picks_adicionados, trims_aplicados


def processar_dxf(arquivo_entrada, pasta_saida, tamanho_pick=0.8):
    """
    Processa um arquivo DXF e adiciona picks com trim
    """
    try:
        print(f"\n{'='*60}")
        print(f"Processando: {os.path.basename(arquivo_entrada)}")
        print("=" * 60)

        doc = ezdxf.readfile(arquivo_entrada)
        msp = doc.modelspace()

        # Coletar dobras
        linhas_dobra = coletar_linhas_dobra(msp)
        print(f"Linhas de dobra: {len(linhas_dobra)}")

        # Agrupar dobras colineares
        grupos = agrupar_dobras_colineares(linhas_dobra)
        print(f"Grupos colineares de dobras: {len(grupos)}")

        # Coletar contorno
        linhas_contorno = coletar_linhas_contorno(msp)
        print(f"Linhas de contorno: {len(linhas_contorno)}")

        raio = tamanho_pick / 2

        # Para cada grupo, coletar intersecções e manter só as extremidades
        picks_por_linha = {}

        for _, indices_grupo in grupos.items():
            grupo_picks = processar_grupo_dobras(
                indices_grupo, linhas_dobra, linhas_contorno, raio
            )
            picks_por_linha.update(grupo_picks)

        picks_adicionados, trims_aplicados = aplicar_trims(picks_por_linha, msp)

        print(f"Picks adicionados: {picks_adicionados}")
        print(f"Trims aplicados: {trims_aplicados}")

        nome_arquivo = os.path.basename(arquivo_entrada)
        arquivo_saida = os.path.join(pasta_saida, nome_arquivo)
        doc.saveas(arquivo_saida)
        print(f"✓ Salvo: {arquivo_saida}")

        return True, picks_adicionados

    except (OSError, ValueError, TypeError) as e:
        print(f"✗ ERRO: {e}")
        traceback.print_exc()
        return False, 0


def buscar_arquivos_dxf(pasta):
    """
    Busca todos os arquivos .dxf em uma pasta
    """
    if not os.path.exists(pasta):
        return []

    if os.path.isfile(pasta) and pasta.lower().endswith(".dxf"):
        return [pasta]

    padrao = os.path.join(pasta, "*.dxf")
    arquivos = glob.glob(padrao)

    return sorted(arquivos)


def processar_pasta(pasta_entrada, tamanho_pick=0.8):
    """
    Processa todos os arquivos DXF de uma pasta
    """
    print("\n" + "=" * 60)
    print("PROCESSAMENTO EM LOTE - PICKS AUTOMÁTICOS")
    print("=" * 60)
    print(f"Pasta de entrada: {pasta_entrada}")

    arquivos = buscar_arquivos_dxf(pasta_entrada)

    if not arquivos:
        print(f"\n✗ Nenhum arquivo DXF encontrado em: {pasta_entrada}")
        return

    print(f"Arquivos encontrados: {len(arquivos)}\n")

    pasta_saida = os.path.join(pasta_entrada, "dxf com pick")

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
        print(f"Pasta criada: {pasta_saida}\n")
    else:
        print(f"Pasta de saída: {pasta_saida}\n")

    total_arquivos = len(arquivos)
    sucesso = 0
    total_picks = 0
    arquivos_erro = []

    for i, arquivo in enumerate(arquivos, 1):
        print(f"\n[{i}/{total_arquivos}]")
        ok, picks = processar_dxf(arquivo, pasta_saida, tamanho_pick)
        if ok:
            sucesso += 1
            total_picks += picks
        else:
            arquivos_erro.append(os.path.basename(arquivo))

    print("=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"Arquivos processados com sucesso: {sucesso}/{total_arquivos}")
    print(f"Total de picks adicionados: {total_picks}")
    print(f"Pasta de saída: {pasta_saida}")

    if arquivos_erro:
        print(f"\n⚠ Arquivos com erro ({len(arquivos_erro)}):")
        for arq in arquivos_erro:
            print(f"  - {arq}")

    print("=" * 60)


if __name__ == "__main__":
    TAMANHO_PICK = 0.8
    PASTA_ENTRADA = None
    if len(sys.argv) < 2:
        print("=" * 60)
        print("ADICIONAR PICKS AUTOMÁTICOS - MODO INTERATIVO")
        print("=" * 60)
        print("\nEste script processa arquivos DXF adicionando picks automaticamente")
        print("nas intersecções entre linhas de dobra e contorno.\n")
        print(
            "Para dobras colineares (segmentadas), picks são adicionados APENAS nas extremidades.\n"
        )
        print("Picks nas extremidades CONVERGEM para o centro da linha de dobra.\n")
        print(
            "Detecta também filetes/chanfros próximos às dobras (até 3mm de distância).\n"
        )

        PASTA_ENTRADA = input("Digite o caminho da pasta com os arquivos DXF: ").strip()
        PASTA_ENTRADA = PASTA_ENTRADA.strip('"').strip("'")

        if not os.path.exists(PASTA_ENTRADA):
            print(f"\n✗ Erro: A pasta não existe: {PASTA_ENTRADA}")
            sys.exit(1)

        tamanho_input = input(
            "\nTamanho do pick (pressione Enter para usar 0.8): "
        ).strip()

        if tamanho_input:
            try:
                TAMANHO_PICK = float(tamanho_input)
            except ValueError:
                print("⚠ Valor inválido. Usando tamanho padrão: 0.8")
        else:
            TAMANHO_PICK = 0.8

        print()
    else:
        PASTA_ENTRADA = sys.argv[1]
        TAMANHO_PICK = 0.8

        if len(sys.argv) > 2:
            try:
                TAMANHO_PICK = float(sys.argv[2])
            except ValueError:
                print(
                    f"⚠ Aviso: '{sys.argv[2]}' não é um número válido. Usando tamanho padrão: 0.8"
                )

    try:
        processar_pasta(PASTA_ENTRADA, TAMANHO_PICK)
        print("\n✓ Processamento concluído!")
    except (OSError, ValueError, TypeError) as e:
        print(f"\n✗ Erro fatal: {e}")
        traceback.print_exc()
        sys.exit(1)
