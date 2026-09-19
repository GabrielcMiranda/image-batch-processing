from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from comum import (ENTRADA_PADRAO, N_BINS, Progresso, agora_iso, gravar_json, gravar_resultados,
                   imprimir_resumo, info_ambiente, listar_imagens, preparar_saida)
from pipeline import processar_imagem


def ler_argumentos() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Processamento de imagens em lote - versão sequencial")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO, help="pasta com as imagens .jpg")
    ap.add_argument("--saida", type=Path, default=Path("saida_seq"), help="pasta onde gravar os resultados")
    ap.add_argument("--limite", type=int, default=None, help="usar só as N primeiras imagens (ordem alfabética)")
    ap.add_argument("--progresso", type=int, default=250, help="imprimir andamento a cada N imagens (0 = nunca)")
    return ap.parse_args()


def main() -> None:
    args = ler_argumentos()
    inicio = agora_iso()
    t0 = time.perf_counter()

    imagens = listar_imagens(args.entrada, args.limite)
    preparar_saida(args.saida)
    t1 = time.perf_counter()

    histograma = np.zeros(N_BINS, dtype=np.int64)
    n_imagens = 0
    n_pixels = 0
    manifesto: dict[str, str] = {}
    progresso = Progresso(len(imagens), args.progresso)
    for caminho in imagens:
        nome, sha256, hist, pixels = processar_imagem(caminho, args.saida)
        histograma += np.asarray(hist, dtype=np.int64)
        n_imagens += 1
        n_pixels += pixels
        manifesto[nome] = sha256
        progresso.avancar()
    t2 = time.perf_counter()

    estatisticas = gravar_resultados(args.saida, manifesto, histograma, n_imagens, n_pixels)
    t3 = time.perf_counter()

    execucao = {
        "versao": "seq", "modo": None, "trava": None, "workers": 1, "chunksize": None,
        "entrada": str(args.entrada), "saida": str(args.saida), "limite": args.limite,
        "imagens": n_imagens, "pixels": n_pixels,
        "t_total_s": t3 - t0, "t_preparo_s": t1 - t0, "t_processamento_s": t2 - t1, "t_final_s": t3 - t2,
        "espera_trava_s": 0.0, "dentro_trava_s": 0.0,
        "inicio_primeira_tarefa_s": None, "cauda_s": None, "ocupacao": None, "fluxos_usados": 1,
        "media_rgb": estatisticas["media_rgb"], "desvio_rgb": estatisticas["desvio_rgb"],
        "impressao_digital": estatisticas["impressao_digital"],
        "inicio": inicio, "ambiente": info_ambiente(),
    }
    gravar_json(Path(args.saida) / "execucao.json", execucao)
    imprimir_resumo(execucao)


if __name__ == "__main__":
    main()
