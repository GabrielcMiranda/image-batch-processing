from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import threading
import time
from functools import partial
from multiprocessing.pool import ThreadPool
from pathlib import Path

import numpy as np

import estado
from comum import (ENTRADA_PADRAO, Progresso, agora_iso, gravar_json, gravar_resultados, imprimir_resumo,
                   info_ambiente, listar_imagens, preparar_saida)
from pipeline import processar_imagem


def identificar_fluxo() -> str:
    return f"{os.getpid()}-{threading.get_ident()}"


def tarefa_trava_fina(caminho: str, pasta_saida: str):
    inicio = time.perf_counter()
    nome, sha256, hist, pixels = processar_imagem(Path(caminho), Path(pasta_saida))
    estado.mesclar(np.asarray(hist, dtype=np.int64), pixels)
    return nome, sha256, identificar_fluxo(), inicio, time.perf_counter()


def tarefa_trava_grossa(caminho: str, pasta_saida: str):
    inicio = time.perf_counter()
    t0 = time.perf_counter_ns()
    with estado.trava_do_estado():
        t1 = time.perf_counter_ns()
        nome, sha256, hist, pixels = processar_imagem(Path(caminho), Path(pasta_saida))
        estado.somar_sem_protecao(np.asarray(hist, dtype=np.int64), pixels)
        estado.registrar_tempos_trava(t1 - t0, time.perf_counter_ns() - t1)
    return nome, sha256, identificar_fluxo(), inicio, time.perf_counter()


def ler_argumentos() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Processamento de imagens em lote - versão paralela")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO, help="pasta com as imagens .jpg")
    ap.add_argument("--saida", type=Path, default=Path("saida_par"), help="pasta onde gravar os resultados")
    ap.add_argument("--limite", type=int, default=None, help="usar só as N primeiras imagens (ordem alfabética)")
    ap.add_argument("-w", "--workers", type=int, default=os.cpu_count(), help="número de fluxos (padrão: núcleos lógicos)")
    ap.add_argument("--chunksize", type=int, default=4, help="imagens enviadas por vez a cada fluxo")
    ap.add_argument("--modo", choices=["processos", "threads"], default="processos")
    ap.add_argument("--trava", choices=["fina", "grossa"], default="fina")
    ap.add_argument("--progresso", type=int, default=250, help="imprimir andamento a cada N imagens (0 = nunca)")
    return ap.parse_args()


def main() -> None:
    args = ler_argumentos()
    if args.workers < 1 or args.chunksize < 1:
        raise SystemExit("ERRO: --workers e --chunksize precisam ser >= 1.")
    inicio = agora_iso()
    t0 = time.perf_counter()

    imagens = listar_imagens(args.entrada, args.limite)
    preparar_saida(args.saida)
    t1 = time.perf_counter()

    ctx = mp.get_context("spawn")
    hist_raw, cont_raw = estado.criar_memoria(ctx)
    if args.modo == "processos":
        trava = ctx.Lock()
        pool = ctx.Pool(args.workers, initializer=estado.iniciar, initargs=(trava, hist_raw, cont_raw))
    else:
        trava = threading.Lock()
        estado.iniciar(trava, hist_raw, cont_raw)
        pool = ThreadPool(args.workers)
    tarefa = tarefa_trava_fina if args.trava == "fina" else tarefa_trava_grossa

    manifesto: dict[str, str] = {}
    ocupado: dict[str, float] = {}
    ultimo_fim: dict[str, float] = {}
    primeiro_inicio = float("inf")
    progresso = Progresso(len(imagens), args.progresso)
    with pool:
        funcao = partial(tarefa, pasta_saida=str(args.saida))
        caminhos = [str(p) for p in imagens]
        for nome, sha256, fluxo, t_ini, t_fim in pool.imap_unordered(funcao, caminhos, chunksize=args.chunksize):
            manifesto[nome] = sha256
            ocupado[fluxo] = ocupado.get(fluxo, 0.0) + (t_fim - t_ini)
            ultimo_fim[fluxo] = max(ultimo_fim.get(fluxo, 0.0), t_fim)
            primeiro_inicio = min(primeiro_inicio, t_ini)
            progresso.avancar()
        pool.close()
        pool.join()
    t2 = time.perf_counter()

    histograma, contadores = estado.ler(hist_raw, cont_raw)
    estatisticas = gravar_resultados(args.saida, manifesto, histograma, contadores["imagens"], contadores["pixels"])
    t3 = time.perf_counter()

    fim_da_ultima = max(ultimo_fim.values())
    janela = fim_da_ultima - primeiro_inicio
    execucao = {
        "versao": "par", "modo": args.modo, "trava": args.trava, "workers": args.workers,
        "chunksize": args.chunksize,
        "entrada": str(args.entrada), "saida": str(args.saida), "limite": args.limite,
        "imagens": contadores["imagens"], "pixels": contadores["pixels"],
        "t_total_s": t3 - t0, "t_preparo_s": t1 - t0, "t_processamento_s": t2 - t1, "t_final_s": t3 - t2,
        "espera_trava_s": contadores["espera_trava_s"], "dentro_trava_s": contadores["dentro_trava_s"],
        "inicio_primeira_tarefa_s": primeiro_inicio - t1,
        "cauda_s": fim_da_ultima - min(ultimo_fim.values()),
        "ocupacao": sum(ocupado.values()) / (args.workers * janela),
        "fluxos_usados": len(ocupado),
        "media_rgb": estatisticas["media_rgb"], "desvio_rgb": estatisticas["desvio_rgb"],
        "impressao_digital": estatisticas["impressao_digital"],
        "inicio": inicio, "ambiente": info_ambiente(),
    }
    gravar_json(Path(args.saida) / "execucao.json", execucao)
    imprimir_resumo(execucao)


if __name__ == "__main__":
    main()
