from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def carregar(pasta: Path) -> tuple[dict[str, str], dict]:
    arq_manifesto = pasta / "manifesto.txt"
    arq_estatisticas = pasta / "estatisticas.json"
    if not arq_manifesto.exists() or not arq_estatisticas.exists():
        raise SystemExit(f"ERRO: '{pasta}' não tem manifesto.txt e estatisticas.json. Rode seq.py ou par.py antes.")
    manifesto = {}
    for linha in arq_manifesto.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            nome, sha256 = linha.split()
            manifesto[nome] = sha256
    estatisticas = json.loads(arq_estatisticas.read_text(encoding="utf-8"))
    return manifesto, estatisticas


def main() -> None:
    ap = argparse.ArgumentParser(description="Compara os resultados de duas execuções")
    ap.add_argument("pasta_a", type=Path)
    ap.add_argument("pasta_b", type=Path)
    args = ap.parse_args()

    man_a, est_a = carregar(args.pasta_a)
    man_b, est_b = carregar(args.pasta_b)
    so_em_a = sorted(man_a.keys() - man_b.keys())
    so_em_b = sorted(man_b.keys() - man_a.keys())
    diferentes = sorted(n for n in man_a.keys() & man_b.keys() if man_a[n] != man_b[n])
    hist_igual = est_a["histograma"] == est_b["histograma"]
    contadores_iguais = (est_a["imagens"], est_a["pixels"]) == (est_b["imagens"], est_b["pixels"])
    impressao_igual = est_a["impressao_digital"] == est_b["impressao_digital"]

    print(f"Comparando '{args.pasta_a}' com '{args.pasta_b}'")
    print(f"  imagens: {len(man_a)} x {len(man_b)} | só em A: {len(so_em_a)} | só em B: {len(so_em_b)}"
          f" | saídas diferentes: {len(diferentes)}")
    print(f"  histograma global idêntico: {'sim' if hist_igual else 'NÃO'}")
    print(f"  contadores (imagens, pixels) idênticos: {'sim' if contadores_iguais else 'NÃO'}")
    print(f"  impressão digital: {est_a['impressao_digital'][:16]} x {est_b['impressao_digital'][:16]}")
    for rotulo, lista in (("só em A", so_em_a), ("só em B", so_em_b), ("diferentes", diferentes)):
        if lista:
            print(f"  exemplos ({rotulo}): {', '.join(lista[:5])}")
    exec_a, exec_b = args.pasta_a / "execucao.json", args.pasta_b / "execucao.json"
    if exec_a.exists() and exec_b.exists():
        t_a = json.loads(exec_a.read_text(encoding="utf-8"))["t_total_s"]
        t_b = json.loads(exec_b.read_text(encoding="utf-8"))["t_total_s"]
        print(f"  tempo total: {t_a:.2f} s x {t_b:.2f} s | razão A/B (speedup desta execução): {t_a / t_b:.2f}")

    ok = not so_em_a and not so_em_b and not diferentes and hist_igual and contadores_iguais and impressao_igual
    print("RESULTADO: IDÊNTICO" if ok else "RESULTADO: DIVERGENTE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
