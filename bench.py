"""Bateria de medições: roda seq.py e par.py várias vezes na MESMA máquina e com a MESMA entrada.

Dono: Pessoa 4.
Uso (na máquina da demonstração, com o N calibrado pela Pessoa 1):
    python bench.py --limite N --com-threads --com-trava-grossa
Cada execução roda como um processo separado e grava uma linha em resultados/bateria.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

RAIZ = Path(__file__).resolve().parent
PASTA_SAIDA = RAIZ / "saida_bench"
CAMPOS = [
    "data_hora", "rodada", "aquecimento", "versao", "modo", "trava", "workers", "chunksize",
    "imagens", "pixels", "t_total_s", "t_preparo_s", "t_processamento_s", "t_final_s",
    "espera_trava_s", "dentro_trava_s", "inicio_primeira_tarefa_s", "cauda_s", "ocupacao", "fluxos_usados",
    "impressao_digital", "cpu", "nucleos_fisicos", "nucleos_logicos", "ram_gb", "sistema",
    "python", "pillow", "numpy", "maquina",
]


def workers_padrao() -> list[int]:
    """Potências de 2 até o nº de núcleos lógicos, mais os nº de núcleos físicos e lógicos."""
    fisicos = psutil.cpu_count(logical=False) or 1
    logicos = psutil.cpu_count(logical=True) or 1
    valores = {p for p in (2, 4, 8, 16, 32, 64) if p <= logicos} | {fisicos, logicos}
    return sorted(p for p in valores if p >= 2)


def montar_plano(args, workers: list[int]) -> list[dict]:
    """Lista ordenada das execuções: aquecimento, depois rodadas alternando seq e par."""
    p_max = max(workers)
    plano = [{"descricao": "aquecimento (sequencial, descartada)", "rodada": 0, "aquecimento": 1,
              "script": "seq.py", "extra": []}]
    for rodada in range(1, args.repeticoes + 1):
        plano.append({"descricao": "sequencial", "rodada": rodada, "aquecimento": 0, "script": "seq.py", "extra": []})
        for p in workers:
            plano.append({"descricao": f"paralela, {p} processos", "rodada": rodada, "aquecimento": 0,
                          "script": "par.py", "extra": ["--workers", str(p)]})
    for rodada in range(1, args.repeticoes_extras + 1):
        if args.com_threads:
            plano.append({"descricao": f"experimento: {p_max} threads", "rodada": rodada, "aquecimento": 0,
                          "script": "par.py", "extra": ["--workers", str(p_max), "--modo", "threads"]})
        if args.com_trava_grossa:
            plano.append({"descricao": f"experimento: trava grossa, {p_max} processos", "rodada": rodada,
                          "aquecimento": 0, "script": "par.py",
                          "extra": ["--workers", str(p_max), "--trava", "grossa"]})
    return plano


def executar(item: dict, entrada: Path, limite: int) -> dict:
    """Roda uma execução como processo separado e devolve o execucao.json que ela gravou."""
    shutil.rmtree(PASTA_SAIDA, ignore_errors=True)            # limpa FORA da medição
    comando = [sys.executable, str(RAIZ / item["script"]), "--entrada", str(entrada), "--limite", str(limite),
               "--saida", str(PASTA_SAIDA), "--progresso", "0", *item["extra"]]
    ambiente = dict(os.environ, PYTHONUTF8="1")
    subprocess.run(comando, check=True, cwd=RAIZ, env=ambiente)
    return json.loads((PASTA_SAIDA / "execucao.json").read_text(encoding="utf-8"))


def linha_csv(execucao: dict, item: dict) -> dict:
    amb = execucao["ambiente"]
    linha = {campo: execucao.get(campo) for campo in CAMPOS}
    linha.update({
        "data_hora": execucao["inicio"], "rodada": item["rodada"], "aquecimento": item["aquecimento"],
        "cpu": amb["cpu"], "nucleos_fisicos": amb["nucleos_fisicos"], "nucleos_logicos": amb["nucleos_logicos"],
        "ram_gb": amb["ram_gb"], "sistema": amb["sistema"], "python": amb["python"], "pillow": amb["pillow"],
        "numpy": amb["numpy"], "maquina": amb["maquina"],
    })
    return {k: ("" if v is None else v) for k, v in linha.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description="Bateria de medições (seq x par)")
    ap.add_argument("--entrada", type=Path, default=Path("dados") / "val2017")
    ap.add_argument("--limite", type=int, required=True, help="N calibrado pela Pessoa 1 (mesmo N da demo)")
    ap.add_argument("--repeticoes", type=int, default=5, help="rodadas de seq + paralelas")
    ap.add_argument("--workers", type=int, nargs="+", default=None, help="lista de nº de processos (padrão: automático)")
    ap.add_argument("--com-threads", action="store_true", help="inclui o experimento com threads")
    ap.add_argument("--com-trava-grossa", action="store_true", help="inclui o experimento com trava grossa")
    ap.add_argument("--repeticoes-extras", type=int, default=3, help="rodadas de cada experimento extra")
    ap.add_argument("--csv", type=Path, default=Path("resultados") / "bateria.csv")
    ap.add_argument("--continuar", action="store_true", help="acrescentar a um CSV que já existe")
    ap.add_argument("--pausa", type=float, default=2.0, help="segundos de pausa entre execuções")
    ap.add_argument("--somente-plano", action="store_true", help="só mostra o plano, sem rodar nada")
    args = ap.parse_args()

    entrada = args.entrada.resolve()
    workers = sorted(set(args.workers)) if args.workers else workers_padrao()
    plano = montar_plano(args, workers)
    print(f"Máquina: {psutil.cpu_count(logical=False)} núcleos físicos, {psutil.cpu_count(logical=True)} lógicos")
    print(f"Entrada: {entrada} | limite: {args.limite} | workers testados: {workers}")
    print(f"Plano: {len(plano)} execuções")
    for i, item in enumerate(plano, 1):
        print(f"  {i:>3}. rodada {item['rodada']}: {item['descricao']}")
    if args.somente_plano:
        return
    if args.csv.exists() and not args.continuar:
        raise SystemExit(f"ERRO: '{args.csv}' já existe. Apague o arquivo ou use --continuar.")
    args.csv.parent.mkdir(parents=True, exist_ok=True)

    inicio = time.perf_counter()
    impressao_referencia = None
    for i, item in enumerate(plano, 1):
        print(f"[{i}/{len(plano)}] {item['descricao']} (rodada {item['rodada']}) ...", flush=True)
        execucao = executar(item, entrada, args.limite)
        if impressao_referencia is None:
            impressao_referencia = execucao["impressao_digital"]
        elif execucao["impressao_digital"] != impressao_referencia:
            raise SystemExit("ERRO: impressão digital diferente das execuções anteriores. "
                             "Existe um erro de sincronização ou a entrada mudou. Pare e avise a Pessoa 2.")
        novo_arquivo = not args.csv.exists()
        with open(args.csv, "a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            if novo_arquivo:
                escritor.writeheader()
            escritor.writerow(linha_csv(execucao, item))
        decorrido = (time.perf_counter() - inicio) / 60
        print(f"      tempo total {execucao['t_total_s']:.2f} s | impressão {execucao['impressao_digital'][:16]}"
              f" | bateria em andamento há {decorrido:.1f} min", flush=True)
        if i == 1:
            t_seq = execucao["t_total_s"]
            print(f"      (a sequencial leva {t_seq:.0f} s nesta máquina; com esse valor, a bateria inteira "
                  f"leva por volta de {estimar_minutos(plano, t_seq, workers):.0f} min, numa estimativa grosseira)")
        time.sleep(args.pausa)
    shutil.rmtree(PASTA_SAIDA, ignore_errors=True)
    print(f"Bateria concluída: {len(plano)} execuções em {(time.perf_counter() - inicio) / 60:.1f} min.")
    print(f"Resultados em '{args.csv}'. Próximo passo: python analise.py")


def estimar_minutos(plano: list[dict], t_seq: float, workers: list[int]) -> float:
    """Estimativa grosseira: supõe ganho de 70% do número de núcleos físicos nas paralelas."""
    fisicos = psutil.cpu_count(logical=False) or 1
    total = 0.0
    for item in plano[1:]:
        extra = item["extra"]
        if item["script"] == "seq.py" or "grossa" in extra:
            total += t_seq
        elif "threads" in extra:
            total += t_seq / 1.2
        else:
            p = int(extra[extra.index("--workers") + 1])
            total += t_seq / max(1.0, 0.7 * min(p, fisicos))
    return total / 60


if __name__ == "__main__":
    main()
