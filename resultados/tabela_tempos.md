# Resultados da bateria

Máquina: 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz (4 núcleos físicos, 8 lógicos, 23,7 GB de RAM) · Windows-11-10.0.26200-SP0 · Python 3.13.15 · Pillow 12.3.0

Entrada: 3334 imagens · impressão digital de todas as execuções: `ed067b987c6c422c`

Fração paralelizável estimada: f = 0,99944 (T_processamento / T_total da sequencial, média de 5 execuções)

## Tempos e speedup

| Configuração | Tempo total (s) | Speedup | Eficiência | Teto de Amdahl | Karp–Flatt |
|---|---|---|---|---|---|
| Sequencial | 252,57 ± 25,49 (n=5) | 1,00 | 100% | — | — |
| Processos, p = 2 | 155,93 ± 10,61 (n=5) | 1,62 | 81,0% | 2,00 | 0,2347 |
| Processos, p = 4 | 102,10 ± 10,68 (n=5) | 2,47 | 61,8% | 3,99 | 0,2056 |
| Processos, p = 8 | 76,07 ± 2,89 (n=5) | 3,32 | 41,5% | 7,97 | 0,2014 |
| Threads, p = 8 | 189,94 ± 1,23 (n=3) | 1,33 | 16,6% | 7,97 | 0,7166 |
| Trava grossa, p = 8 | 239,75 ± 4,28 (n=3) | 1,05 | 13,2% | 7,97 | 0,9420 |

## Onde está a diferença para o teto

| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |
|---|---|---|---|---|
| Processos, p = 2 | 22,3 | 0,42 | 0,15 | 99,9% |
| Processos, p = 4 | 27,0 | 0,50 | 0,36 | 99,7% |
| Processos, p = 8 | 45,5 | 0,64 | 0,52 | 99,4% |
| Threads, p = 8 | 14,2 | 0,03 | 0,68 | 99,8% |
| Trava grossa, p = 8 | 1666565,0 | 0,68 | 0,82 | 99,7% |
