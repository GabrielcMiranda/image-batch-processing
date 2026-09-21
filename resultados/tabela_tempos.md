# Resultados da bateria

Máquina: AMD Ryzen 5 5600X 6-Core Processor (6 núcleos físicos, 12 lógicos, 23,9 GB de RAM) · Windows-10-10.0.19045-SP0 · Python 3.14.6 · Pillow 12.3.0

Entrada: 5000 imagens · impressão digital de todas as execuções: `4b458bb014e97826`

Fração paralelizável estimada: f = 0,99932 (T_processamento / T_total da sequencial, média de 5 execuções)

## Tempos e speedup

| Configuração | Tempo total (s) | Speedup | Eficiência | Teto de Amdahl | Karp–Flatt |
|---|---|---|---|---|---|
| Sequencial | 257,83 ± 0,47 (n=5) | 1,00 | 100% | — | — |
| Processos, p = 2 | 133,52 ± 0,86 (n=5) | 1,93 | 96,6% | 2,00 | 0,0357 |
| Processos, p = 4 | 74,16 ± 0,33 (n=5) | 3,48 | 86,9% | 3,99 | 0,0502 |
| Processos, p = 6 | 54,02 ± 0,19 (n=5) | 4,77 | 79,5% | 5,98 | 0,0514 |
| Processos, p = 8 | 46,93 ± 0,58 (n=5) | 5,49 | 68,7% | 7,96 | 0,0652 |
| Processos, p = 12 | 37,32 ± 0,20 (n=5) | 6,91 | 57,6% | 11,91 | 0,0670 |
| Threads, p = 12 | 182,68 ± 0,14 (n=3) | 1,41 | 11,8% | 11,91 | 0,6820 |
| Trava grossa, p = 12 | 264,80 ± 0,90 (n=3) | 0,97 | 8,1% | 11,91 | 1,0295 |

## Onde está a diferença para o teto

| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |
|---|---|---|---|---|
| Processos, p = 2 | 13,5 | 0,19 | 0,09 | 99,9% |
| Processos, p = 4 | 17,6 | 0,21 | 0,21 | 99,8% |
| Processos, p = 6 | 18,6 | 0,22 | 0,21 | 99,7% |
| Processos, p = 8 | 20,9 | 0,25 | 0,26 | 99,6% |
| Processos, p = 12 | 28,2 | 0,34 | 0,29 | 99,5% |
| Threads, p = 12 | 75,0 | 0,02 | 0,75 | 99,9% |
| Trava grossa, p = 12 | 2899084,3 | 0,33 | 0,90 | 99,8% |
