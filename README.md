# Processamento de imagens em lote: sequencial x paralelo

Projeto de Solução Distribuída, Etapa 1 · Sistemas Distribuídos e Paralelos (CESUPA).

O programa pré-processa em lote as 5.000 fotos do COCO 2017 val: cada foto é padronizada em 512×512,
passa por remoção de ruído, ajuste de contraste e nitidez, e ganha uma miniatura. O lote inteiro produz
as estatísticas globais do dataset (histograma RGB, média e desvio por canal), guardadas num estado
compartilhado protegido por uma trava. A versão sequencial (`seq.py`) e a paralela (`par.py`, com
processos do `multiprocessing`) usam a mesma função por imagem e produzem exatamente o mesmo resultado.

## Requisitos

- Windows 10 ou 11, 64 bits
- Python 3.12, 3.13 ou 3.14, 64 bits, instalação padrão (não use a variante "free-threaded" 3.13t/3.14t)
- Git e cerca de 3 GB livres em disco

## Instalação (PowerShell, na pasta do projeto)

```powershell
py -3.13 -m venv .venv                 # troque 3.13 pela versão instalada (3.12 ou 3.14)
.\.venv\Scripts\Activate.ps1           # se der erro de "execução de scripts", veja abaixo
python -m pip install --upgrade pip
pip install -r requirements.txt
python baixar_dados.py                 # ~1 GB: baixa e extrai em dados\val2017
```

Se a ativação falhar com "a execução de scripts foi desabilitada neste sistema", rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force` e ative de novo.

## Como rodar

```powershell
python seq.py --limite 300                           # versão sequencial (saída em saida_seq)
python par.py --limite 300                           # versão paralela (saída em saida_par)
python verificar.py saida_seq saida_par              # prova que as duas produziram o mesmo resultado
python teste_corrida.py                              # mostra a condição de corrida sem a trava
python calibrar.py                                   # recomenda o --limite para a sequencial levar ~4 min
python bench.py --limite N --com-threads --com-trava-grossa   # bateria de medições
python analise.py                                    # tabelas e gráficos em resultados\
python gerar_site.py --execucao saida_par            # página de resultados em site\
python -m http.server 8000 --directory site --bind 0.0.0.0   # serve a página na porta 8000
```

A demonstração usa `demo.ps1` (etapas `preparar`, `seq`, `corrida`, `estavel`, `par`, `verificar`,
`site`, `servir`) e as regras de acesso ficam em `infra\firewall_windows.ps1`.

## Estrutura

| Arquivo | O que faz | Dono |
|---|---|---|
| `comum.py` | constantes e funções compartilhadas por seq e par | Pessoa 1 |
| `pipeline.py` | `processar_imagem()`: a unidade de trabalho | Pessoa 1 |
| `baixar_dados.py` | baixa o COCO 2017 val | Pessoa 1 |
| `calibrar.py` | mede o tempo por imagem e recomenda o `--limite` | Pessoa 1 |
| `seq.py` | versão sequencial | Pessoa 1 |
| `verificar.py` | compara duas execuções | Pessoa 1 |
| `estado.py` | estado compartilhado e seção crítica | Pessoa 2 |
| `par.py` | versão paralela | Pessoa 2 |
| `teste_corrida.py` | demonstra a condição de corrida | Pessoa 2 |
| `ficha_maquina.py` | ficha técnica da máquina | Pessoa 3 |
| `aquecer_cache.py` | lê as imagens antes da demonstração | Pessoa 3 |
| `gerar_site.py` | página de resultados | Pessoa 3 |
| `demo.ps1` | comandos da apresentação | Pessoa 3 |
| `infra/` | regras de firewall e ficha da máquina | Pessoa 3 |
| `bench.py` | bateria de medições | Pessoa 4 |
| `analise.py` | speedup, eficiência, Amdahl, Karp-Flatt e gráficos | Pessoa 4 |
| `resultados/` | CSV, tabelas e gráficos oficiais | Pessoa 4 |
| `relatorio/` | seções e PDF do relatório | Pessoa 4 (consolida) |
