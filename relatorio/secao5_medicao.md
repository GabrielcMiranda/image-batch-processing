# 5. Medição e speedup

<!-- Pessoa 4. Troque tudo que está entre [[ ]] pelos números de resultados/tabela_tempos.md. -->

**Protocolo.** Todas as medições foram feitas na máquina da seção 4, com a mesma entrada ([[N]] imagens) e o
mesmo código (tag `v0.9`). A máquina ficou na tomada, em modo de alto desempenho e sem outros programas
abertos. O programa `bench.py` executou uma rodada de aquecimento, descartada, e depois [[5]] rodadas, cada
uma com a versão sequencial seguida das paralelas com p = [[2, 4, 8, ...]] processos. Cada execução rodou como
um processo separado, com a pasta de saída limpa antes, fora da medição. Todas as [[n]] execuções produziram a
mesma impressão digital.

**Tempos, speedup e eficiência.**

[[colar a primeira tabela da tabela_tempos.md]]

**Teto de Amdahl.** A versão sequencial mede separadamente o preparo, o processamento e a etapa final. A fração
paralelizável estimada é f = T_processamento / T_total = [[f]] (média de [[5]] execuções). Com [[p]]
processos, o teto de Amdahl é [[S_max]] e o speedup medido foi [[S]]: [[S / S_max x 100]]% do teto.

[[inserir resultados/speedup.png, largura ~14 cm, legenda: "Speedup medido x teto de Amdahl x ideal"]]
