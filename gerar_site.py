
from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera os PNG sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
CANAIS = [("Vermelho (R)", "#e34948"), ("Verde (G)", "#008300"), ("Azul (B)", "#2a78d6")]
IMAGENS_NA_GALERIA = 12


def virgula(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def grafico_histograma(estatisticas: dict, destino: Path) -> None:
    """Histograma global em 3 painéis (um por canal), em % dos pixels."""
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"]})
    histograma = estatisticas["histograma"]
    fig, eixos = plt.subplots(1, 3, figsize=(9, 3.0), dpi=200, sharey=True)
    fig.patch.set_facecolor(SUPERFICIE)
    niveis = list(range(256))
    for i, (ax, (nome, cor)) in enumerate(zip(eixos, CANAIS)):
        contagens = histograma[i * 256:(i + 1) * 256]
        total = sum(contagens)
        percentuais = [100 * c / total for c in contagens]
        ax.set_facecolor(SUPERFICIE)
        ax.fill_between(niveis, percentuais, color=cor, alpha=0.10, linewidth=0)
        ax.plot(niveis, percentuais, color=cor, linewidth=1.5)
        ax.set_title(nome, loc="left", color=TINTA, fontsize=10)
        ax.set_xlim(0, 255)
        ax.set_xticks([0, 64, 128, 192, 255])
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(EIXO)
        ax.tick_params(colors=EIXO, labelcolor=TINTA_SECUNDARIA, labelsize=8)
        ax.grid(True, color=GRADE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel("Nível (0 a 255)", color=TINTA_SECUNDARIA, fontsize=9)
    eixos[0].set_ylabel("% dos pixels", color=TINTA_SECUNDARIA, fontsize=9)
    eixos[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    fig.tight_layout()
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def miniatura(origem: Path, destino: Path) -> None:
    with Image.open(origem) as im:
        im = im.convert("RGB")
    im.thumbnail((256, 256), Image.Resampling.LANCZOS)
    im.save(destino, "JPEG", quality=85)


def tabela(linhas: list[tuple[str, str]]) -> str:
    corpo = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in linhas)
    return f"<table>{corpo}</table>"


def secao_desempenho(resultados: Path, site: Path) -> str:
    arquivo_resumo = resultados / "resumo.json"
    if not arquivo_resumo.exists():
        return "<p class='nota'>A bateria de medições ainda não foi analisada (resultados/resumo.json não existe).</p>"
    resumo = json.loads(arquivo_resumo.read_text(encoding="utf-8"))
    s = resumo["sequencial"]
    linhas = [f"<tr><td>Sequencial</td><td>{virgula(s['media'])} ± {virgula(s['desvio'])}</td>"
              f"<td>1,00</td><td>100%</td><td>—</td></tr>"]
    for c in resumo["configuracoes"]:
        t = c["tempo"]
        linhas.append(f"<tr><td>{html.escape(c['nome'])}</td><td>{virgula(t['media'])} ± {virgula(t['desvio'])}</td>"
                      f"<td>{virgula(c['speedup'])}</td><td>{virgula(100 * c['eficiencia'], 1)}%</td>"
                      f"<td>{virgula(c['amdahl'])}</td></tr>")
    figuras = ""
    for nome in ("speedup.png", "tempos.png"):
        if (resultados / nome).exists():
            shutil.copy2(resultados / nome, site / nome)
            figuras += f"<img class='grafico' src='{nome}' alt='{nome}'>"
    return (f"<p>Fração paralelizável estimada: f = {virgula(resumo['f'], 5)} · {s['n']} execuções por configuração.</p>"
            "<table class='dados'><tr><th>Configuração</th><th>Tempo total (s)</th><th>Speedup</th>"
            f"<th>Eficiência</th><th>Teto de Amdahl</th></tr>{''.join(linhas)}</table>{figuras}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera a página de resultados")
    ap.add_argument("--execucao", type=Path, default=Path("saida_par"), help="pasta de uma execução (seq ou par)")
    ap.add_argument("--entrada", type=Path, default=Path("dados") / "val2017", help="pasta das imagens originais")
    ap.add_argument("--resultados", type=Path, default=Path("resultados"))
    ap.add_argument("--site", type=Path, default=Path("site"))
    args = ap.parse_args()

    execucao = json.loads((args.execucao / "execucao.json").read_text(encoding="utf-8"))
    estatisticas = json.loads((args.execucao / "estatisticas.json").read_text(encoding="utf-8"))
    shutil.rmtree(args.site, ignore_errors=True)
    (args.site / "galeria").mkdir(parents=True)

    grafico_histograma(estatisticas, args.site / "histograma.png")
    nomes = [linha.split()[0] for linha in
             (args.execucao / "manifesto.txt").read_text(encoding="utf-8").splitlines() if linha.strip()]
    cartoes = []
    for nome in nomes[:IMAGENS_NA_GALERIA]:
        base = Path(nome).stem
        miniatura(args.entrada / nome, args.site / "galeria" / f"{base}_antes.jpg")
        miniatura(args.execucao / "imagens" / f"{base}.jpg", args.site / "galeria" / f"{base}_depois.jpg")
        cartoes.append(f"<figure><img src='galeria/{base}_antes.jpg' alt='original {base}'>"
                       f"<img src='galeria/{base}_depois.jpg' alt='processada {base}'>"
                       f"<figcaption>{html.escape(nome)}: original | processada</figcaption></figure>")

    e = execucao
    amb = e["ambiente"]
    fluxos = "1 fluxo (sequencial)" if e["versao"] == "seq" else f"{e['workers']} {e['modo']} (trava {e['trava']})"
    resumo_execucao = tabela([
        ("Versão", fluxos),
        ("Imagens processadas", str(e["imagens"])),
        ("Pixels processados", f"{e['pixels']:,}".replace(",", ".")),
        ("Tempo total", f"{virgula(e['t_total_s'])} s"),
        ("Espera pela trava", f"{virgula(1000 * e['espera_trava_s'], 1)} ms"),
        ("Média RGB do lote", " / ".join(virgula(v) for v in estatisticas["media_rgb"])),
        ("Desvio RGB do lote", " / ".join(virgula(v) for v in estatisticas["desvio_rgb"])),
        ("Impressão digital", estatisticas["impressao_digital"][:16]),
        ("Máquina", f"{amb['cpu']} · {amb['nucleos_fisicos']} núcleos físicos / {amb['nucleos_logicos']} lógicos"),
        ("Início da execução", e["inicio"]),
    ])
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lote de imagens: resultados</title>
<style>
  body {{ margin: 0; background: #f9f9f7; color: {TINTA}; font-family: system-ui, "Segoe UI", sans-serif; }}
  main {{ max-width: 1040px; margin: 0 auto; padding: 24px 16px 48px; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
  h2 {{ font-size: 1.15rem; margin: 32px 0 12px; }}
  .sub, .nota {{ color: {TINTA_SECUNDARIA}; }}
  table {{ border-collapse: collapse; background: {SUPERFICIE}; margin-bottom: 12px; }}
  th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid {GRADE}; }}
  th {{ color: {TINTA_SECUNDARIA}; font-weight: 600; }}
  td {{ font-variant-numeric: tabular-nums; }}
  img.grafico {{ width: 100%; max-width: 820px; display: block; margin: 12px 0; }}
  .galeria {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }}
  figure {{ margin: 0; background: {SUPERFICIE}; padding: 8px; border: 1px solid {GRADE}; border-radius: 8px; }}
  figure img {{ width: calc(50% - 4px); height: auto; vertical-align: top; }}
  figcaption {{ color: {TINTA_SECUNDARIA}; font-size: 0.85rem; margin-top: 4px; }}
</style>
</head>
<body>
<main>
  <h1>Processamento de imagens em lote</h1>
  <p class="sub">Resultados servidos na porta 8000 · página gerada em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
  <h2>Última execução</h2>
  {resumo_execucao}
  <h2>Desempenho (bateria de medições)</h2>
  {secao_desempenho(args.resultados, args.site)}
  <h2>Histograma global do lote</h2>
  <img class="grafico" src="histograma.png" alt="Histograma global por canal">
  <h2>Antes e depois ({len(cartoes)} primeiras imagens)</h2>
  <div class="galeria">{''.join(cartoes)}</div>
</main>
</body>
</html>
"""
    (args.site / "index.html").write_text(pagina, encoding="utf-8")
    print(f"Site gerado em '{args.site / 'index.html'}'.")
    print("Para servir na porta 8000: python -m http.server 8000 --directory site --bind 0.0.0.0")


if __name__ == "__main__":
    main()
