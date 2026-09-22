# 6. O que limitou o ganho

Como a fração paralelizável é muito próxima de 1 (f = 0,99944), o teto de Amdahl fica perto de p, e a diferença
para o speedup medido vem de sobrecarga e de hardware, e não de uma parte serial fixa do programa. A métrica de
Karp–Flatt mostra isso de outro ângulo: e(p) = 0,2347, 0,2056 e 0,2014 para p = 2, 4 e 8 — praticamente
constante, e até levemente decrescente com p, em vez de crescente. Isso indica que a sobrecarga não piora
proporcionalmente quando mais processos são acrescentados; ela é sobretudo um custo fixo (criar os processos,
abrir o pool), diluído por um número maior de fluxos.

| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |
|---|---|---|---|---|
| Processos, p = 2 | 22,3 | 0,42 | 0,15 | 99,9% |
| Processos, p = 4 | 27,0 | 0,50 | 0,36 | 99,7% |
| Processos, p = 8 | 45,5 | 0,64 | 0,52 | 99,4% |
| Threads, p = 8 | 14,2 | 0,03 | 0,68 | 99,8% |
| Trava grossa, p = 8 | 1.666.565,0 | 0,68 | 0,82 | 99,7% |

- **Comunicação e criação dos processos:** com 8 processos, a primeira tarefa só começa 0,64 s depois do início
  do processamento, tempo gasto criando os processos (no Windows, cada um é um novo interpretador que importa
  Pillow e NumPy do zero, por causa do `spawn`). Pelo canal entre processos passam apenas o caminho de cada
  imagem e, na volta, o nome e o SHA-256: um volume de dados pequeno perto do tempo de processamento de cada
  imagem.
- **Divisão desigual do trabalho:** no fim do lote, os processos terminam em momentos diferentes; a cauda foi
  de 0,52 s com 8 processos. O `chunksize` de 4 e o balanceamento dinâmico do `imap_unordered` mantêm essa
  cauda pequena frente ao tempo total (76 s), mas ela ainda pesa mais, proporcionalmente, à medida que o tempo
  total cai com mais processos.
- **Espera na seção crítica:** com a trava fina, apenas 45,5 ms de espera acumulada ao longo de uma execução de
  76 s (cerca de 0,06% do tempo), desprezível. Com a trava em volta do processamento inteiro (trava grossa), a
  espera acumulada sobe para 1.666,6 s — os processos passam a maior parte do tempo enfileirados esperando a
  trava, em vez de trabalhar em paralelo — e o speedup despenca para 1,05x, quase o mesmo da versão sequencial.
- **Hardware:** a máquina tem 4 núcleos físicos e 8 lógicos (Hyper-Threading). Até p = 4 o ganho é quase linear
  (speedup 2,47x com eficiência de 61,8%), mas de p = 4 para p = 8 o ganho desacelera (speedup sobe só para
  3,32x, eficiência cai para 41,5%), porque os 4 fluxos extras passam a dividir as mesmas unidades de execução
  dos núcleos físicos já ocupados, em vez de ganhar capacidade de processamento nova. O Turbo Boost também
  favorece a execução sequencial: com um só núcleo ativo, a CPU roda numa frequência mais alta do que quando
  todos os núcleos estão ocupados, o que reduz um pouco a vantagem relativa da paralela.

**Conclusão.** A versão paralela alcançou 3,32x de speedup com 8 processos, 41,7% do teto de Amdahl para essa
fração paralelizável, e o principal limitador não foi a sincronização (a espera pela trava é desprezível na
configuração correta), e sim o Hyper-Threading acima dos 4 núcleos físicos, combinado com o custo fixo de criar
os processos no Windows. Os experimentos de controle confirmam a escolha de projeto: threads entregam só 1,33x,
porque o filtro de mediana segura o GIL, e uma trava mal dimensionada (em volta do processamento inteiro)
reduz o ganho a 1,05x, mostrando que tanto a escolha de processos quanto a granularidade fina da trava são
necessárias para o speedup observado.
