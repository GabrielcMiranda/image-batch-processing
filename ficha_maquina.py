from __future__ import annotations

import shutil
from pathlib import Path

import psutil

from comum import agora_iso, info_ambiente


def main() -> None:
    amb = info_ambiente()
    frequencia = psutil.cpu_freq()
    disco = shutil.disk_usage(Path.cwd())
    linhas = [
        "# Ficha técnica da máquina da demonstração", "",
        f"Gerada em {agora_iso()} por ficha_maquina.py", "",
        "| Item | Valor |",
        "|---|---|",
        f"| Processador | {amb['cpu']} |",
        f"| Núcleos físicos | {amb['nucleos_fisicos']} |",
        f"| Núcleos lógicos (threads de hardware) | {amb['nucleos_logicos']} |",
        f"| Frequência máxima informada | {frequencia.max:.0f} MHz |" if frequencia and frequencia.max else
        "| Frequência máxima informada | nao disponivel |",
        f"| Memória RAM | {amb['ram_gb']} GB |",
        f"| Disco livre na pasta do projeto | {disco.free / 2**30:.0f} GB |",
        f"| Sistema operacional | {amb['sistema']} |",
        f"| Python | {amb['python']} |",
        f"| Pillow | {amb['pillow']} |",
        f"| NumPy | {amb['numpy']} |",
        f"| Nome da máquina | {amb['maquina']} |",
    ]
    Path("infra").mkdir(exist_ok=True)
    Path("infra", "ficha_maquina.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))
    print("\nGravado em infra/ficha_maquina.md")


if __name__ == "__main__":
    main()
