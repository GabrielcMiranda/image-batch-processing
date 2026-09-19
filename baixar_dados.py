from __future__ import annotations

import argparse
import time
import urllib.request
import zipfile
from pathlib import Path

URL_PADRAO = "http://images.cocodataset.org/zips/val2017.zip"
IMAGENS_ESPERADAS = 5000


def contar_jpgs(pasta: Path) -> int:
    return sum(1 for _ in pasta.glob("*.jpg")) if pasta.is_dir() else 0


def baixar(url: str, destino_zip: Path) -> None:
    parcial = destino_zip.with_name(destino_zip.name + ".parcial")
    t0 = time.perf_counter()
    with urllib.request.urlopen(url, timeout=60) as resposta, open(parcial, "wb") as arquivo:
        total = int(resposta.headers.get("Content-Length") or 0)
        baixado = 0
        proximo_aviso = 0.05
        while True:
            bloco = resposta.read(1024 * 1024)
            if not bloco:
                break
            arquivo.write(bloco)
            baixado += len(bloco)
            if total and baixado / total >= proximo_aviso:
                print(f"  {100 * baixado / total:5.1f}%  ({baixado / 2**20:.0f} de {total / 2**20:.0f} MB, "
                      f"{time.perf_counter() - t0:.0f} s)", flush=True)
                proximo_aviso += 0.05
    if total and baixado != total:
        raise SystemExit("ERRO: download incompleto. Rode o script de novo.")
    parcial.replace(destino_zip)


def extrair(arquivo_zip: Path, pasta_dados: Path) -> None:
    with zipfile.ZipFile(arquivo_zip) as z:
        membros = [m for m in z.namelist() if m.startswith("val2017/") and m.lower().endswith(".jpg")]
        for i, membro in enumerate(membros, 1):
            z.extract(membro, pasta_dados)
            if i % 500 == 0 or i == len(membros):
                print(f"  extraídas {i}/{len(membros)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Baixa o COCO 2017 val em dados/val2017/")
    ap.add_argument("--dados", type=Path, default=Path("dados"), help="pasta onde ficam os dados")
    ap.add_argument("--url", default=URL_PADRAO)
    ap.add_argument("--manter-zip", action="store_true", help="não apagar o .zip depois de extrair")
    args = ap.parse_args()

    pasta_imagens = args.dados / "val2017"
    arquivo_zip = args.dados / "val2017.zip"
    ja_tem = contar_jpgs(pasta_imagens)
    if ja_tem >= IMAGENS_ESPERADAS:
        print(f"OK: '{pasta_imagens}' já tem {ja_tem} imagens. Nada a fazer.")
        return
    args.dados.mkdir(parents=True, exist_ok=True)
    if arquivo_zip.exists():
        print(f"Usando o arquivo já baixado: {arquivo_zip}")
    else:
        print(f"Baixando {args.url} (~1 GB) ...", flush=True)
        baixar(args.url, arquivo_zip)
    print("Extraindo ...", flush=True)
    extrair(arquivo_zip, args.dados)
    total = contar_jpgs(pasta_imagens)
    print(f"OK: {total} imagens em '{pasta_imagens}'")
    if total != IMAGENS_ESPERADAS:
        print(f"AVISO: eram esperadas {IMAGENS_ESPERADAS} imagens. O zip foi mantido para conferência.")
    elif not args.manter_zip:
        arquivo_zip.unlink()
        print("Zip apagado para liberar espaço (use --manter-zip para guardar).")


if __name__ == "__main__":
    main()
