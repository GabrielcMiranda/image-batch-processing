"""Análise da bateria: tempos, speedup, eficiência, teto de Amdahl, Karp-Flatt e gráficos.

Dono: Pessoa 4.   Uso:  python analise.py
Lê resultados/bateria.csv e grava em resultados/: tabela_tempos.md, resumo.json, speedup.png e tempos.png.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera os PNG sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# Cores dos gráficos (paleta validada para daltonismo) e tinta do texto
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"
LARANJA = "#eb6834"

CAMPOS_NUMERICOS = ["t_total_s", "t_preparo_s", "t_processamento_s", "t_final_s", "espera_trava_s",
                    "dentro_trava_s", "inicio_primeira_tarefa_s", "cauda_s", "ocupacao"]


def virgula(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def carregar(caminho: Path) -> list[dict]:
    if not caminho.exists():
        raise SystemExit(f"ERRO: '{caminho}' não existe. Rode o bench.py antes.")
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:  # aceita arquivo com ou sem BOM
        linhas = list(csv.DictReader(arquivo))
    medidas = [linha for linha in linhas if linha["aquecimento"] != "1"]
    if not medidas:
        raise SystemExit("ERRO: o CSV não tem execuções medidas (só aquecimento).")
    combinacoes = {(linha["maquina"], linha["imagens"]) for linha in medidas}
    if len(combinacoes) != 1:
        raise SystemExit(f"ERRO: o CSV mistura máquinas ou entradas diferentes: {sorted(combinacoes)}")
    if len({linha["impressao_digital"] for linha in linhas}) != 1:
        raise SystemExit("ERRO: há impressões digitais diferentes no CSV (resultado não é estável).")
    for linha in medidas:
        for campo in CAMPOS_NUMERICOS:
            linha[campo] = float(linha[campo]) if linha[campo] != "" else None
        linha["workers"] = int(linha["workers"])
    return medidas


def resumir(valores: list[float]) -> dict:
    return {
        "media": statistics.fmean(valores),
        "desvio": statistics.stdev(valores) if len(valores) > 1 else 0.0,
        "n": len(valores), "min": min(valores), "max": max(valores),
    }


def media_do_campo(linhas: list[dict], campo: str) -> float | None:
    valores = [linha[campo] for linha in linhas if linha[campo] is not None]
    return statistics.fmean(valores) if valores else None


def nome_da_configuracao(modo: str, trava: str, p: int) -> str:
    if trava == "grossa":
        return f"Trava grossa, p = {p}"
    return f"{'Processos' if modo == 'processos' else 'Threads'}, p = {p}"


def analisar(medidas: list[dict]) -> dict:
    seq = [linha for linha in medidas if linha["versao"] == "seq"]
    if not seq:
        raise SystemExit("ERRO: o CSV não tem execuções sequenciais.")
    t_seq = resumir([linha["t_total_s"] for linha in seq])
    f = statistics.fmean(linha["t_processamento_s"] / linha["t_total_s"] for linha in seq)

    grupos: dict[tuple, list[dict]] = {}
    for linha in medidas:
        if linha["versao"] == "par":
            grupos.setdefault((linha["modo"], linha["trava"], linha["workers"]), []).append(linha)
    ordem_tipo = {("processos", "fina"): 0, ("threads", "fina"): 1, ("processos", "grossa"): 2}
    configuracoes = []
    for (modo, trava, p), linhas in sorted(grupos.items(), key=lambda kv: (ordem_tipo.get(kv[0][:2], 9), kv[0][2])):
        tempo = resumir([linha["t_total_s"] for linha in linhas])
        speedup = t_seq["media"] / tempo["media"]
        configuracoes.append({
            "nome": nome_da_configuracao(modo, trava, p), "modo": modo, "trava": trava, "workers": p,
            "tempo": tempo, "speedup": speedup, "eficiencia": speedup / p,
            "amdahl": 1 / ((1 - f) + f / p),
            "karp_flatt": (1 / speedup - 1 / p) / (1 - 1 / p) if p > 1 else None,
            "espera_trava_s": media_do_campo(linhas, "espera_trava_s"),
            "inicio_primeira_tarefa_s": media_do_campo(linhas, "inicio_primeira_tarefa_s"),
            "cauda_s": media_do_campo(linhas, "cauda_s"),
            "ocupacao": media_do_campo(linhas, "ocupacao"),
        })
    ref = seq[0]
    return {
        "maquina": {chave: ref[chave] for chave in ("cpu", "nucleos_fisicos", "nucleos_logicos", "ram_gb",
                                                   "sistema", "python", "pillow", "numpy", "maquina")},
        "imagens": int(ref["imagens"]), "impressao_digital": ref["impressao_digital"],
        "f": f, "sequencial": t_seq, "configuracoes": configuracoes,
    }


def escrever_tabela(res: dict, destino: Path) -> str:
    m = res["maquina"]
    s = res["sequencial"]
    linhas = [
        "# Resultados da bateria", "",
        f"Máquina: {m['cpu']} ({m['nucleos_fisicos']} núcleos físicos, {m['nucleos_logicos']} lógicos, "
        f"{virgula(float(m['ram_gb']), 1)} GB de RAM) · {m['sistema']} · Python {m['python']} · Pillow {m['pillow']}", "",
        f"Entrada: {res['imagens']} imagens · impressão digital de todas as execuções: `{res['impressao_digital'][:16]}`", "",
        f"Fração paralelizável estimada: f = {virgula(res['f'], 5)} (T_processamento / T_total da sequencial, "
        f"média de {s['n']} execuções)", "",
        "## Tempos e speedup", "",
        "| Configuração | Tempo total (s) | Speedup | Eficiência | Teto de Amdahl | Karp–Flatt |",
        "|---|---|---|---|---|---|",
        f"| Sequencial | {virgula(s['media'])} ± {virgula(s['desvio'])} (n={s['n']}) | 1,00 | 100% | — | — |",
    ]
    for c in res["configuracoes"]:
        t = c["tempo"]
        kf = virgula(c["karp_flatt"], 4) if c["karp_flatt"] is not None else "—"
        linhas.append(f"| {c['nome']} | {virgula(t['media'])} ± {virgula(t['desvio'])} (n={t['n']}) | "
                      f"{virgula(c['speedup'])} | {virgula(100 * c['eficiencia'], 1)}% | {virgula(c['amdahl'])} | {kf} |")
    linhas += [
        "", "## Onde está a diferença para o teto", "",
        "| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |",
        "|---|---|---|---|---|",
    ]
    for c in res["configuracoes"]:
        linhas.append(f"| {c['nome']} | {virgula(1000 * c['espera_trava_s'], 1)} | "
                      f"{virgula(c['inicio_primeira_tarefa_s'])} | {virgula(c['cauda_s'])} | "
                      f"{virgula(100 * c['ocupacao'], 1)}% |")
    texto = "\n".join(linhas) + "\n"
    destino.write_text(texto, encoding="utf-8")
    return texto


def preparar_estilo() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
    })


def estilizar(fig, ax) -> None:
    fig.patch.set_facecolor(SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(EIXO)
        ax.spines[lado].set_linewidth(1)
    ax.tick_params(colors=EIXO, labelcolor=TINTA_SECUNDARIA, labelsize=9)
    ax.grid(True, color=GRADE, linewidth=0.8, linestyle="-")
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(TINTA_SECUNDARIA)
    ax.yaxis.label.set_color(TINTA_SECUNDARIA)
    formato = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    ax.xaxis.set_major_formatter(formato)
    ax.yaxis.set_major_formatter(formato)


def titulo(ax, principal: str, subtitulo: str) -> None:
    ax.set_title(principal, loc="left", color=TINTA, fontweight="bold", pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, color=TINTA_SECUNDARIA, fontsize=9, va="bottom")


def grafico_speedup(res: dict, destino: Path) -> None:
    processos = [c for c in res["configuracoes"] if c["modo"] == "processos" and c["trava"] == "fina"]
    if not processos:
        return
    f = res["f"]
    ps = [1] + [c["workers"] for c in processos]
    medido = [1.0] + [c["speedup"] for c in processos]
    xs = [1 + i * (ps[-1] - 1) / 200 for i in range(201)]
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=200)
    estilizar(fig, ax)
    ax.plot(xs, xs, color=TINTA_FRACA, linewidth=1.5, label="Ideal (S = p)")
    ax.plot(xs, [1 / ((1 - f) + f / x) for x in xs], color=LARANJA, linewidth=2,
            label=f"Teto de Amdahl (f = {virgula(f, 4)})")
    ax.plot(ps, medido, color=AZUL, linewidth=2, marker="o", markersize=8, markerfacecolor=AZUL,
            markeredgecolor=SUPERFICIE, markeredgewidth=2, label="Medido (processos)", zorder=3)
    ax.annotate(f"{virgula(medido[-1])}x", (ps[-1], medido[-1]), xytext=(8, -4), textcoords="offset points",
                color=TINTA_SECUNDARIA, fontsize=10)
    ax.set_xticks(ps)
    ax.set_xlim(0.5, ps[-1] + 1.5)
    ax.set_ylim(0, ps[-1] + 1)
    ax.set_xlabel("Número de processos (p)")
    ax.set_ylabel("Speedup (T_seq / T_par)")
    ax.legend(frameon=False, loc="upper left", labelcolor=TINTA_SECUNDARIA, fontsize=9)
    m = res["maquina"]
    titulo(ax, "Speedup medido x teto de Amdahl",
           f"{res['imagens']} imagens · {m['nucleos_fisicos']} núcleos físicos / {m['nucleos_logicos']} lógicos · "
           f"média de {res['sequencial']['n']} execuções")
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def grafico_tempos(res: dict, destino: Path) -> None:
    nomes = ["Sequencial"] + [c["nome"] for c in res["configuracoes"]]
    medias = [res["sequencial"]["media"]] + [c["tempo"]["media"] for c in res["configuracoes"]]
    desvios = [res["sequencial"]["desvio"]] + [c["tempo"]["desvio"] for c in res["configuracoes"]]
    posicoes = list(range(len(nomes)))[::-1]  # o primeiro item fica em cima
    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(nomes) + 1.3), dpi=200)
    estilizar(fig, ax)
    ax.grid(False, axis="y")
    ax.barh(posicoes, medias, height=0.5, color=AZUL, xerr=desvios,
            error_kw={"ecolor": TINTA_SECUNDARIA, "elinewidth": 1, "capsize": 3})
    folga = max(medias) * 0.015
    for y, media, desvio in zip(posicoes, medias, desvios):
        ax.text(media + desvio + folga, y, f"{virgula(media, 1)} s", va="center", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_yticks(posicoes)
    ax.set_yticklabels(nomes)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(m + d for m, d in zip(medias, desvios)) * 1.15)
    ax.set_xlabel("Tempo total (s), média ± desvio-padrão")
    titulo(ax, "Tempo total por configuração", f"{res['imagens']} imagens · mesma máquina e mesma entrada")
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Analisa a bateria de medições")
    ap.add_argument("--csv", type=Path, default=Path("resultados") / "bateria.csv")
    ap.add_argument("--saida", type=Path, default=Path("resultados"))
    args = ap.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)

    resultados = analisar(carregar(args.csv))
    print(escrever_tabela(resultados, args.saida / "tabela_tempos.md"))
    (args.saida / "resumo.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    preparar_estilo()
    grafico_speedup(resultados, args.saida / "speedup.png")
    grafico_tempos(resultados, args.saida / "tempos.png")
    print(f"Arquivos gravados em '{args.saida}': tabela_tempos.md, resumo.json, speedup.png, tempos.png")


if __name__ == "__main__":
    main()
