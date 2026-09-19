from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

TAM_SAIDA = (512, 512)
TAM_MINIATURA = (128, 128)
QUALIDADE_JPEG = 90
QUALIDADE_MINIATURA = 85


def processar_imagem(origem: Path, pasta_saida: Path) -> tuple[str, str, list[int], int]:
    origem = Path(origem)
    pasta_saida = Path(pasta_saida)
    with Image.open(origem) as im:
        im = im.convert("RGB")
    im = ImageOps.fit(im, TAM_SAIDA, Image.Resampling.LANCZOS)
    im = im.filter(ImageFilter.MedianFilter(3))
    im = ImageOps.autocontrast(im, cutoff=1)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))
    histograma = im.histogram()
    destino = pasta_saida / "imagens" / f"{origem.stem}.jpg"
    im.save(destino, "JPEG", quality=QUALIDADE_JPEG)
    n_pixels = im.width * im.height
    im.thumbnail(TAM_MINIATURA, Image.Resampling.LANCZOS)
    im.save(pasta_saida / "miniaturas" / f"{origem.stem}.jpg", "JPEG", quality=QUALIDADE_MINIATURA)
    sha256 = hashlib.sha256(destino.read_bytes()).hexdigest()
    return origem.name, sha256, histograma, n_pixels
