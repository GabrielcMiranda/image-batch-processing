# 2. Estratégia de paralelização

O programa usa paralelismo de dados no padrão mestre-trabalhadores: o processo principal cria um
`multiprocessing.Pool` com p processos e distribui as 3.334 imagens da entrada entre eles pelo método
`imap_unordered`, com `chunksize=4`. Cada processo executa a mesma função `processar_imagem()` da versão
sequencial, e o único ponto de contato entre eles é a soma do histograma no estado global, descrita na seção 3.

**Por que `imap_unordered` e `chunksize=4`.** Como as imagens não têm relação entre si, a ordem em que os
resultados chegam não importa: `imap_unordered` entrega cada resultado assim que fica pronto, então um processo
que termina cedo recebe mais trabalho, sem esperar pelos outros. Essa é a distribuição dinâmica que equilibra a
carga entre os fluxos. O `chunksize=4` agrupa 4 imagens por envio, reduzindo o número de idas e vindas pelo
canal entre processos; pelo canal passam apenas o caminho de cada imagem e, na volta, o nome, o SHA-256 e um
identificador do fluxo. A biblioteca usada é `multiprocessing.Pool`, e não `ProcessPoolExecutor`, porque o
`Pool` tem um equivalente para threads com a mesma interface (`ThreadPool`), o que permite comparar processos e
threads trocando uma única opção do `par.py` (`--modo processos|threads`).

**Como a trava chega aos processos filhos.** No Windows, o método de início é `spawn`: cada processo filho é um
`python.exe` novo que importa os módulos do zero e não herda variáveis do processo pai. A trava e a memória
compartilhada (o estado global de `estado.py`) são passadas pelo `initializer` do `Pool`, que roda uma vez em
cada processo filho antes de ele receber a primeira tarefa. Passar a trava como argumento de uma tarefa, em vez
do `initializer`, dá `RuntimeError: Lock objects should only be shared between processes through inheritance`,
porque o `Lock` não pode ser serializado entre processos independentes.

**Processos, e não threads: por que, com números.** Em CPython, o GIL permite que apenas uma thread execute
código Python por vez dentro de um mesmo processo. O Pillow libera o GIL durante boa parte das suas operações
em C (decodificar, redimensionar, aplicar nitidez), mas o filtro de mediana 3x3 — cerca de dois terços do tempo
de cada imagem — mantém o GIL preso enquanto ordena os 9 valores de vizinhança de cada pixel e cada canal. Como
esse filtro é a etapa dominante do pipeline, o trabalho é limitado por CPU e não escala com threads dentro de
um único processo.

A bateria de medições confirma isso na prática. Com 8 fluxos na mesma máquina (4 núcleos físicos, 8 lógicos):

| Configuração | Tempo total | Speedup |
|---|---|---|
| Sequencial (referência) | 252,57 ± 25,49 s | 1,00x |
| Processos, p = 8 | 76,07 ± 2,89 s | **3,32x** |
| Threads, p = 8 | 189,94 ± 1,23 s | 1,33x |

Processos deram 3,32x de speedup; threads, apenas 1,33x, porque as threads continuam disputando o mesmo
interpretador e o mesmo GIL para a etapa que mais pesa no tempo total. Cada processo, em vez disso, tem o seu
próprio interpretador e o seu próprio GIL, e por isso o ganho de processos se aproxima do número de núcleos
físicos disponíveis, enquanto o de threads fica limitado à fração do tempo que o Pillow consegue liberar o GIL.
Essa é a justificativa, pela natureza do trabalho, para escolher processos.

**Granularidade da trava.** A trava protege apenas a soma do histograma no estado global (seção 3), não o
processamento da imagem inteira. O experimento com a trava em volta de todo o processamento (`--trava grossa`)
mostra o efeito de errar essa granularidade: com 8 processos, o tempo total sobe para 239,75 ± 4,28 s, um
speedup de apenas 1,05x, quase igual à versão sequencial, porque os processos passam a maior parte do tempo
esperando a trava em vez de trabalhar em paralelo.
