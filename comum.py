from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

ENTRADA_PADRAO = Path("dados") / "val2017"
EXTENSOES_ACEITAS = (".jpg", ".jpeg")
N_BINS = 768


def listar_imagens(entrada: Path, limite: int | None) -> list[Path]:
    entrada = Path(entrada)
    if not entrada.is_dir():
        raise SystemExit(f"ERRO: a pasta de entrada '{entrada}' não existe. Baixe os dados com: python baixar_dados.py")
    imagens = sorted(
        (p for p in entrada.iterdir() if p.is_file() and p.suffix.lower() in EXTENSOES_ACEITAS),
        key=lambda p: p.name,
    )
    if limite is not None:
        if limite <= 0:
            raise SystemExit("ERRO: --limite precisa ser maior que zero.")
        imagens = imagens[:limite]
    if not imagens:
        raise SystemExit(f"ERRO: nenhuma imagem .jpg encontrada em '{entrada}'.")
    return imagens


def preparar_saida(saida: Path) -> None:
    (Path(saida) / "imagens").mkdir(parents=True, exist_ok=True)
    (Path(saida) / "miniaturas").mkdir(parents=True, exist_ok=True)


def estatisticas_do_histograma(histograma) -> dict:
    medias, desvios = [], []
    for canal in range(3):
        h = [int(x) for x in histograma[canal * 256:(canal + 1) * 256]]
        n = sum(h)
        soma = sum(v * h[v] for v in range(256))
        soma_quadrados = sum(v * v * h[v] for v in range(256))
        medias.append(round(soma / n, 4))
        variancia = (n * soma_quadrados - soma * soma) / (n * n)
        desvios.append(round(variancia ** 0.5, 4))
    return {"media_rgb": medias, "desvio_rgb": desvios}


def impressao_digital(manifesto: dict[str, str], histograma, imagens: int, pixels: int) -> str:
    linhas = "\n".join(f"{nome} {sha}" for nome, sha in sorted(manifesto.items()))
    texto = linhas + "|" + ",".join(str(int(v)) for v in histograma) + f"|{int(imagens)}|{int(pixels)}"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gravar_json(caminho: Path, dados: dict) -> None:
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def gravar_resultados(saida: Path, manifesto: dict[str, str], histograma, imagens: int, pixels: int) -> dict:
    saida = Path(saida)
    linhas = [f"{nome} {sha}" for nome, sha in sorted(manifesto.items())]
    (saida / "manifesto.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    estatisticas = {
        "imagens": int(imagens),
        "pixels": int(pixels),
        **estatisticas_do_histograma(histograma),
        "impressao_digital": impressao_digital(manifesto, histograma, imagens, pixels),
        "histograma": [int(v) for v in histograma],
    }
    gravar_json(saida / "estatisticas.json", estatisticas)
    return estatisticas


def agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def nome_cpu() -> str:
    if sys.platform == "win32":
        try:
            import winreg

            caminho = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, caminho) as chave:
                return str(winreg.QueryValueEx(chave, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    return platform.processor() or "desconhecido"


def info_ambiente() -> dict:
    import numpy
    import PIL
    import psutil

    return {
        "cpu": nome_cpu(),
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "pillow": PIL.__version__,
        "numpy": numpy.__version__,
        "maquina": platform.node(),
    }


class Progresso:

    def __init__(self, total: int, passo: int):
        self.total = total
        self.passo = passo
        self.feitas = 0
        self.inicio = time.perf_counter()

    def avancar(self) -> None:
        self.feitas += 1
        if self.passo and (self.feitas % self.passo == 0 or self.feitas == self.total):
            decorrido = time.perf_counter() - self.inicio
            print(f"  {self.feitas:>6}/{self.total} imagens ({100 * self.feitas / self.total:5.1f}%)"
                  f"  {decorrido:8.1f} s", flush=True)


def imprimir_resumo(execucao: dict) -> None:
    e = execucao
    print("=" * 72)
    if e["versao"] == "seq":
        print("VERSAO SEQUENCIAL | 1 fluxo")
    else:
        print(f"VERSAO PARALELA | {e['workers']} {e['modo']} | trava {e['trava']} | chunksize {e['chunksize']}")
    print(f"Imagens: {e['imagens']} | pixels: {e['pixels']}")
    print(f"Tempo total: {e['t_total_s']:.2f} s  (preparo {e['t_preparo_s']:.2f} s | "
          f"processamento {e['t_processamento_s']:.2f} s | final {e['t_final_s']:.2f} s)")
    if e["versao"] == "par":
        print(f"Espera pela trava: {1000 * e['espera_trava_s']:.1f} ms | dentro da trava: "
              f"{1000 * e['dentro_trava_s']:.1f} ms | cauda: {e['cauda_s']:.2f} s | ocupação: {100 * e['ocupacao']:.1f}%")
    print(f"Média RGB: {e['media_rgb']} | desvio RGB: {e['desvio_rgb']}")
    print(f"Impressão digital: {e['impressao_digital'][:16]}")
    print("=" * 72, flush=True)
