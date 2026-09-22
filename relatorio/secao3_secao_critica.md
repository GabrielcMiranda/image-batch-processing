# 3. Seção crítica e primitiva

**O estado compartilhado.** Todos os processos escrevem no mesmo histograma RGB global (768 inteiros de 64
bits) e em 4 contadores (imagens processadas, pixels processados, nanossegundos esperando a trava e
nanossegundos com a trava na mão). Essa memória é criada em `ctx.RawArray("q", ...)`, que é compartilhada entre
processos mas **não tem trava própria**: qualquer processo pode ler e escrever nela livremente, e é por isso
que a soma precisa de proteção explícita.

**A condição de corrida.** A operação `_hist[:] += hist_local` não é atômica: na prática, é ler o valor atual do
vetor, somar o histograma local e escrever o resultado de volta. Se dois processos fazem essa sequência ao
mesmo tempo, os dois leem o mesmo valor antigo, e o processo que escreve por último apaga a soma do outro. É a
atualização perdida, e ela existe porque o `+=` sobre memória compartilhada, sem trava, não garante exclusão
mútua entre os processos.

**A seção crítica e a primitiva.** A primitiva usada é um `multiprocessing.Lock`, criado uma vez no processo
principal e propagado aos processos filhos pelo `initializer` do `Pool`. A seção crítica está nas **linhas 37 a
42 de `estado.py`**, dentro da função `mesclar()`:

```python
def mesclar(hist_local, n_pixels: int) -> None:
    t0 = time.perf_counter_ns()
    with _trava:                                           # ===== INÍCIO DA SEÇÃO CRÍTICA =====
        t1 = time.perf_counter_ns()
        somar_sem_protecao(hist_local, n_pixels)
        _cont[ESPERA_NS] += t1 - t0
        _cont[DENTRO_NS] += time.perf_counter_ns() - t1
    #                                                      ===== FIM DA SEÇÃO CRÍTICA =====
```

Só as três linhas dentro do `with _trava:` formam a seção crítica: somar o histograma local no global e
atualizar os dois contadores. O processamento da imagem inteira — decodificar, filtrar, salvar, calcular o
SHA-256 — fica fora da trava e roda em paralelo sem qualquer sincronização, porque cada processo trabalha sobre
a sua própria cópia local da imagem até o momento de mesclar.

**Por que `Lock`, e não semáforo ou monitor.** O estado global é um único recurso, e o requisito é exclusão
mútua simples: só um processo por vez pode somar nele. Um `Lock` é exatamente um semáforo binário (contador
0/1). Um semáforo com contador maior que 1 permitiria que vários processos entrassem na seção crítica ao mesmo
tempo, o que reintroduziria a corrida. Um monitor — uma trava associada a uma variável de condição — seria
necessário se algum processo precisasse esperar por uma condição além da posse da trava (por exemplo, esperar o
estado atingir um certo valor antes de prosseguir), o que não acontece aqui: cada processo só quer entrar,
somar e sair.

**Por que não é possível haver deadlock.** Existe uma única trava no programa inteiro, sempre adquirida com
`with _trava:` (que garante a liberação mesmo se `somar_sem_protecao` lançar uma exceção) e nunca adquirida
dentro de outra trava. Sem múltiplas travas mantidas simultaneamente por diferentes processos, não existe espera
circular, condição necessária para deadlock.

**Prova experimental: `teste_corrida.py`.** Para expor a corrida de forma confiável — no programa real ela é
rara, porque a seção crítica dura microssegundos a cada dezenas de milissegundos de processamento — o teste usa
4 processos fazendo 20.000 somas cada um sobre o mesmo estado, sincronizados por uma `Barrier` para começarem
juntos e disputarem de verdade. O resultado esperado é sempre contador = 80.000 e cada posição do histograma =
80.000. Rodado nesta máquina:

```text
4 processos x 20000 somas cada | esperado: contador = 80000 e soma do histograma = 61440000
SEM trava | rodada 1: contador    48111/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.5 s)
SEM trava | rodada 2: contador    57253/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.5 s)
SEM trava | rodada 3: contador    55793/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.5 s)
COM trava | rodada 1: contador    80000/80000 | posições erradas   0/768 | OK (1.4 s)
COM trava | rodada 2: contador    80000/80000 | posições erradas   0/768 | OK (1.5 s)
COM trava | rodada 3: contador    80000/80000 | posições erradas   0/768 | OK (1.5 s)
```

Sem a trava, o contador final variou a cada rodada (48.111, 57.253, 55.793 de 80.000 esperado), e as 768
posições do histograma erraram em todas as rodadas: a atualização perdida acontece na prática, não é só uma
possibilidade teórica. Com a trava, as três rodadas bateram exatamente em 80.000, sem nenhuma posição errada. O
teste foi repetido em execuções independentes e o padrão se manteve: toda rodada sem trava perde atualizações e
toda rodada com trava acerta.

**Custo da sincronização.** Na bateria oficial (3.334 imagens reais, não o teste de estresse), a soma no estado
global custa muito pouco frente ao processamento: com 8 processos, a espera total pela trava foi de apenas
45,5 ms ao longo de uma execução de 76 s (cerca de 0,06% do tempo), e a ocupação dos fluxos ficou em 99,4%. Essa
é a evidência de que a granularidade fina da trava — proteger só a soma, não o processamento — é o que permite o
speedup de 3,32x discutido na seção 2: a sincronização em si não é o fator limitante do ganho.
