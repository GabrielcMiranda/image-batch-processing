# 6. O que limitou o ganho

<!-- Pessoa 4. Troque tudo que está entre [[ ]] pelos números de resultados/tabela_tempos.md. -->

Como a fração paralelizável é muito próxima de 1, o teto de Amdahl fica perto de p, e a diferença para o
speedup medido vem de sobrecarga e de hardware, e não de uma parte serial do programa. A métrica de Karp-Flatt
mostra isso: e(p) = [[valores]] para p = [[valores]], [[crescendo/constante]] com p.

[[colar a segunda tabela da tabela_tempos.md]]

- **Comunicação e criação dos processos:** a primeira tarefa só começa [[x]] s depois do início do
  processamento, tempo gasto criando os processos (no Windows, cada um é um novo interpretador que importa
  Pillow e NumPy). Pelo canal entre processos passam apenas o caminho de cada imagem e o SHA-256 de volta.
- **Divisão desigual do trabalho:** no fim do lote, os processos terminam em momentos diferentes; a cauda foi
  de [[y]] s. O `chunksize` de 4 e o `imap_unordered` mantêm essa cauda pequena.
- **Espera na seção crítica:** [[z]] ms no total, desprezível. A trava cobre só a soma do histograma. Com a
  trava em volta do processamento inteiro, a espera sobe para [[w]] s e o speedup cai para [[S_grossa]].
- **Hardware:** [[escolha o que se aplica: acima de [[físicos]] processos o ganho diminui porque os núcleos
  lógicos dividem um núcleo físico; o turbo favorece a execução sequencial; núcleos de eficiência]].

**Conclusão.** [[Uma frase: o speedup alcançado, a fração do teto, e o principal limitador.]]
