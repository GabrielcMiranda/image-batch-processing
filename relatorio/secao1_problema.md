# 1. Problema e dados

Antes de treinar um modelo de visão computacional, as fotos de um dataset precisam ser padronizadas, e o
dataset inteiro precisa de estatísticas para normalizar a entrada da rede: a média e o desvio-padrão de cada
canal de cor. Este trabalho implementa esse pré-processamento em lote e o paraleliza.

**Entrada.** Conjunto de validação do COCO 2017: 5.000 fotografias reais em JPEG, cerca de 800 MB já
descompactados. Usamos as 3.334 primeiras em ordem alfabética do nome, número calibrado pelo programa
`calibrar.py` para a versão sequencial levar cerca de 4 minutos na máquina da demonstração. A ordem alfabética
é fixa, então `--limite 3334` seleciona sempre exatamente as mesmas imagens, em qualquer execução e em qualquer
máquina.

**Unidade de trabalho: uma imagem.** A função `processar_imagem()`, em `pipeline.py`, é chamada pelas duas
versões do programa e executa nove etapas para cada foto: decodifica o JPEG, recorta e redimensiona para
512x512 pixels com o filtro LANCZOS, remove ruído com um filtro de mediana 3x3, normaliza o contraste cortando
1% em cada extremo, aplica nitidez (unsharp mask), calcula o histograma RGB com 768 contagens inteiras, grava a
imagem resultante em JPEG com qualidade 90, gera uma miniatura de 128x128 e calcula o SHA-256 do arquivo
gerado. O filtro de mediana responde por cerca de dois terços do tempo de cada imagem, e é ele que sustenta a
escolha de processos em vez de threads, discutida na seção 2.

**Por que o problema se divide.** Nenhuma imagem depende de outra e as tarefas não trocam dados entre si, o que
caracteriza um paralelismo de dados puro. O único resultado combinado é o histograma global do lote: uma soma
de inteiros, operação associativa e comutativa, que pode ser feita em qualquer ordem sem alterar o resultado.
Média e desvio-padrão de cada canal são calculados uma única vez, ao final, a partir desse histograma. Manter
apenas inteiros no estado compartilhado é uma decisão de projeto: a soma de números de ponto flutuante depende
da ordem das parcelas, e em paralelo a ordem de chegada muda a cada execução, o que faria a versão paralela
divergir da sequencial no último dígito.

**Volume.** 3.334 imagens, ou 873.988.096 pixels processados e cerca de 320 MB gravados por execução, entre
imagens e miniaturas. A versão sequencial leva 252,57 ± 25,49 s (5 execuções) na máquina da demonstração, o que
equivale a 75,8 ms por imagem. Desse total, as fases de preparo e de gravação final somam menos de 0,2% do
tempo, o que dá uma fração paralelizável f = 0,99944, usada no teto de Amdahl da seção 5.

**Verificação.** As versões sequencial e paralela chamam a mesma `processar_imagem()`, então produzem os mesmos
bytes por construção. Cada execução grava um `manifesto.txt` com o nome e o SHA-256 de cada imagem gerada, em
ordem alfabética, e um `estatisticas.json` com o histograma global, os contadores e uma impressão digital do
lote, que é o SHA-256 do manifesto somado ao histograma e aos contadores. O programa `verificar.py` compara
duas execuções campo a campo e termina com código 0 quando são idênticas e 1 quando divergem; ele foi testado
também no caso de falha, com uma imagem a menos, e acusou corretamente a divergência. Nas 27 execuções da
bateria de medições, incluindo as versões com 2, 4 e 8 processos, com threads e com trava grossa, a impressão
digital foi sempre a mesma: `ed067b987c6c422c`.
