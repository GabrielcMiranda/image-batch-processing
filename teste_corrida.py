from __future__ import annotations

import argparse
import multiprocessing as mp
import time

import numpy as np

import estado


def trabalhador(trava, barreira, hist_raw, cont_raw, somas: int, usar_trava: bool) -> None:
    estado.iniciar(trava, hist_raw, cont_raw)
    local = np.ones(estado.N_BINS, dtype=np.int64)
    barreira.wait()
    for _ in range(somas):
        if usar_trava:
            estado.mesclar(local, 1)
        else:
            estado.somar_sem_protecao(local, 1)


def rodada(ctx, processos: int, somas: int, usar_trava: bool) -> dict:
    trava = ctx.Lock()
    barreira = ctx.Barrier(processos)
    hist_raw, cont_raw = estado.criar_memoria(ctx)
    filhos = [ctx.Process(target=trabalhador, args=(trava, barreira, hist_raw, cont_raw, somas, usar_trava))
              for _ in range(processos)]
    t0 = time.perf_counter()
    for filho in filhos:
        filho.start()
    for filho in filhos:
        filho.join()
    hist, contadores = estado.ler(hist_raw, cont_raw)
    esperado = processos * somas
    return {
        "esperado": esperado,
        "contador": contadores["imagens"],
        "soma": int(hist.sum()),
        "posicoes_erradas": int((hist != esperado).sum()),
        "segundos": time.perf_counter() - t0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Demonstra a condição de corrida no estado global")
    ap.add_argument("-p", "--processos", type=int, default=4)
    ap.add_argument("-m", "--somas", type=int, default=20000, help="somas feitas por cada processo")
    ap.add_argument("-r", "--rodadas", type=int, default=3)
    args = ap.parse_args()
    ctx = mp.get_context("spawn")

    print(f"{args.processos} processos x {args.somas} somas cada | esperado: contador = "
          f"{args.processos * args.somas} e soma do histograma = {args.processos * args.somas * estado.N_BINS}")
    for usar_trava in (False, True):
        for i in range(1, args.rodadas + 1):
            r = rodada(ctx, args.processos, args.somas, usar_trava)
            ok = r["contador"] == r["esperado"] and r["posicoes_erradas"] == 0
            print(f"{'COM trava' if usar_trava else 'SEM trava'} | rodada {i}: contador {r['contador']:>8}/{r['esperado']}"
                  f" | posições erradas {r['posicoes_erradas']:>3}/{estado.N_BINS}"
                  f" | {'OK' if ok else 'PERDEU ATUALIZAÇÕES'} ({r['segundos']:.1f} s)", flush=True)
    print("Conclusão: sem a trava o resultado muda a cada rodada; com a trava é sempre o esperado.")


if __name__ == "__main__":
    main()
