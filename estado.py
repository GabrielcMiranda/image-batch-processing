from __future__ import annotations

import time

import numpy as np

N_BINS = 768
IMAGENS, PIXELS, ESPERA_NS, DENTRO_NS = 0, 1, 2, 3
N_CONTADORES = 4

_trava = None
_hist = None
_cont = None


def criar_memoria(ctx):
    hist_raw = ctx.RawArray("q", N_BINS)
    cont_raw = ctx.RawArray("q", N_CONTADORES)
    return hist_raw, cont_raw


def iniciar(trava, hist_raw, cont_raw) -> None:
    global _trava, _hist, _cont
    _trava = trava
    _hist = np.frombuffer(hist_raw, dtype=np.int64)
    _cont = np.frombuffer(cont_raw, dtype=np.int64)


def somar_sem_protecao(hist_local, n_pixels: int) -> None:
    _hist[:] += hist_local
    _cont[IMAGENS] += 1
    _cont[PIXELS] += n_pixels


def mesclar(hist_local, n_pixels: int) -> None:
    t0 = time.perf_counter_ns()
    with _trava:
        t1 = time.perf_counter_ns()
        somar_sem_protecao(hist_local, n_pixels)
        _cont[ESPERA_NS] += t1 - t0
        _cont[DENTRO_NS] += time.perf_counter_ns() - t1


def trava_do_estado():
    return _trava


def registrar_tempos_trava(espera_ns: int, dentro_ns: int) -> None:
    _cont[ESPERA_NS] += espera_ns
    _cont[DENTRO_NS] += dentro_ns


def ler(hist_raw, cont_raw) -> tuple[np.ndarray, dict]:
    hist = np.frombuffer(hist_raw, dtype=np.int64).copy()
    cont = np.frombuffer(cont_raw, dtype=np.int64).copy()
    return hist, {
        "imagens": int(cont[IMAGENS]),
        "pixels": int(cont[PIXELS]),
        "espera_trava_s": int(cont[ESPERA_NS]) / 1e9,
        "dentro_trava_s": int(cont[DENTRO_NS]) / 1e9,
    }
