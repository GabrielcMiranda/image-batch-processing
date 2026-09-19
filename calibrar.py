from __future__ import annotations

import argparse
import math
import shutil
import time
from pathlib import Path

from comum import ENTRADA_PADRAO, listar_imagens, preparar_saida
from pipeline import TAM_SAIDA, processar_imagem

PASTA_TEMPORARIA = Path("saida_calibracao")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibra o volume de entrada para a demonstração")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO)
    ap.add_argument("--amostra", type=int, default=200, help="quantas imagens medir")
    ap.add_argument("--alvo-min", type=float, default=4.0, help="duração desejada da sequencial, em minutos")
    args = ap.parse_args()

    todas = listar_imagens(args.entrada, None)
    amostra = todas[:args.amostra]
    shutil.rmtree(PASTA_TEMPORARIA, ignore_errors=True)
    preparar_saida(PASTA_TEMPORARIA)
    for caminho in amostra[:20]:
        processar_imagem(caminho, PASTA_TEMPORARIA)
    t0 = time.perf_counter()
    for caminho in amostra:
        processar_imagem(caminho, PASTA_TEMPORARIA)
    por_imagem = (time.perf_counter() - t0) / len(amostra)
    shutil.rmtree(PASTA_TEMPORARIA, ignore_errors=True)

    alvo_s = args.alvo_min * 60
    com_todas_s = len(todas) * por_imagem
    print(f"TAM_SAIDA atual: {TAM_SAIDA}")
    print(f"Tempo médio por imagem: {1000 * por_imagem:.1f} ms (medido em {len(amostra)} imagens)")
    print(f"Com todas as {len(todas)} imagens, a sequencial levaria ~{com_todas_s / 60:.1f} min")
    if com_todas_s >= alvo_s:
        n = math.floor(alvo_s / por_imagem)
        print(f"RECOMENDAÇÃO: use --limite {n} (sequencial estimada em {n * por_imagem / 60:.1f} min)")
    elif com_todas_s >= 2.5 * 60:
        print(f"RECOMENDAÇÃO: use todas as imagens (--limite {len(todas)}); "
              f"a sequencial leva ~{com_todas_s / 60:.1f} min, o que atende ao requisito.")
    else:
        print("ATENÇÃO: nem com todas as imagens a sequencial chega a 2,5 min.")
        print("Troque TAM_SAIDA para (640, 640) em pipeline.py e rode calibrar.py de novo.")
        print("Se ainda não chegar, use (768, 768).")


if __name__ == "__main__":
    main()
