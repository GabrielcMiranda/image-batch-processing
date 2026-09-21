from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dados") / "val2017"
    arquivos = sorted(pasta.glob("*.jpg"))
    total = sum(len(p.read_bytes()) for p in arquivos)
    print(f"Cache aquecido: {len(arquivos)} imagens, {total / 2**20:.0f} MB lidos de '{pasta}'")


if __name__ == "__main__":
    main()
