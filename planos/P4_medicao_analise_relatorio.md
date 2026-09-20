# Pessoa 4: medição, análise e relatório

**Projeto:** Processamento de imagens em lote · Sistemas Distribuídos e Paralelos · Projeto de Solução Distribuída, Etapa 1

**Seus arquivos:** `bench.py`, `analise.py`, os resultados em `resultados\` e a montagem do relatório em
`relatorio\`

**Sua prioridade:** ter o `bench.py` pronto antes do marco M3 (sábado, 19:00), porque a bateria oficial precisa
de cerca de 1h15 na máquina da demo parada, e rodar no sábado à noite.

## Como usar este documento

**Para você (Pessoa 4):** este arquivo tem tudo o que você precisa: o contexto do trabalho (seção 1), as
regras e contratos do grupo (seção 2), a sua parte (seções 3 a 10) e o código de referência de cada arquivo
seu, já testado no Python 3.12, 3.13 e 3.14. Leia as seções 1 a 4 antes de abrir a IA e depois trabalhe na
ordem da seção 4. Os outros três integrantes têm documentos com as mesmas seções 1 e 2, então todo mundo parte
das mesmas regras.

**Para a IA:** abra uma conversa nova, anexe (ou cole) este arquivo inteiro e envie a mensagem abaixo.

> Você vai me ajudar a implementar a minha parte de um projeto em grupo. O documento anexo é a especificação e
> deve ser seguido à risca:
> 1. Sou a Pessoa 4. Implemente apenas os meus arquivos: `bench.py` e `analise.py` (e os arquivos gerados em `resultados/` e `relatorio/`). Não crie nem edite nenhum outro arquivo.
> 2. Quando o documento trouxer o código de referência de um arquivo, use esse código exatamente como está. Você
>    pode explicá-lo, mas não refatore, não "melhore", não troque bibliotecas e não mude nomes, parâmetros,
>    mensagens, formatos de arquivo ou valores de processamento.
> 3. Não adicione dependências, opções de linha de comando, classes, logs, testes automatizados ou tratamento de
>    erros que não estejam no documento.
> 4. O ambiente é Windows 10/11, PowerShell e Python 3.12 a 3.14 (instalação padrão, com GIL). Todo comando que
>    você me passar deve ser de PowerShell, rodado na pasta do projeto com o ambiente virtual ativado.
> 5. Siga a ordem da seção 4 (Etapas de implementação). A cada arquivo, me passe o teste correspondente da
>    seção 6 e diga o que devo ver na tela.
> 6. Se algo não estiver definido no documento, se um teste der resultado diferente do esperado ou se aparecer
>    um erro que a seção 10 não explica, pare e me pergunte. Não invente uma solução por conta própria.
>
> Comece pela etapa 1 da seção 4.

## 1. Contexto do projeto (igual nos 4 documentos)

### 1.1 O que o professor pede

Trabalho: "Projeto de Solução Distribuída – Etapa 1", da disciplina Sistemas Distribuídos e Paralelos (070080),
com o Prof. Fábio Rocha de Araújo. Vale 3,0 pontos do 1º bimestre e a equipe tem 4 pessoas. A entrega e a
apresentação são na aula de **segunda, 21/09 (CC6NA)**; a CC6MA apresenta na terça, 22/09.

A lauda pede uma aplicação com processamento paralelo para um problema real, com o ganho de desempenho medido
e explicado. Ela fala em recursos na nuvem, mas o professor liberou rodar no PC local. **Por isso, todo o
projeto roda no Windows, no PC de um de nós, chamado aqui de "máquina da demo".**

**Entregas**

1. Código-fonte em repositório, com link no ambiente virtual, contendo a versão sequencial e a versão paralela
   do mesmo programa.
2. Relatório técnico em PDF, com até 6 páginas: o problema, a estratégia de paralelização, a seção crítica e a
   primitiva que a protege, os recursos usados, os tempos medidos, o speedup e o que limitou o ganho.
3. Apresentação de 10 minutos com demonstração ao vivo, seguida de arguição individual de 3 minutos por
   integrante.

O link do repositório e o PDF precisam estar no ambiente virtual **antes do início** do encontro.

**O que a aplicação precisa ter**

- Um trabalho que se divide em partes independentes.
- Volume de entrada suficiente para a versão sequencial levar minutos, e não segundos.
- Um resultado verificável, para provar que a versão paralela produz o mesmo que a sequencial.
- Estado compartilhado escrito por mais de um fluxo, protegido por lock, semáforo ou monitor.
- Execução numa máquina preparada pela equipe, com regras de acesso: porta administrativa restrita à origem da
  equipe e só a porta do serviço aberta.
- Em CPython, trabalho limitado por processador exige processos, e não threads. A escolha precisa estar
  justificada no relatório pela natureza do trabalho.

### 1.2 Como a nota é composta

| Critério | Peso |
|---|---|
| Apresentação e demonstração ao vivo, com arguição individual | 1,5 |
| Correção da sincronização, sem condições de corrida | 0,5 |
| Provisionamento e controle de acesso | 0,5 |
| Medição de desempenho e análise do ganho | 0,5 |
| **Total** | **3,0** |

**O que tira nota:** demonstração gravada ou em capturas de tela; speedup calculado sem o tempo sequencial
medido na mesma máquina e com a mesma entrada; recursos mostrados por print, sem o console aberto; tempo
estourado em mais de 2 minutos; integrante que não responde sobre a parte que não apresentou. Porta
administrativa aberta para qualquer origem **zera** o critério de acesso. Uma trava em volta do laço inteiro
deixa o programa correto, mas não paralelo, e a nota de medição reflete isso.

**Arguição:** cada integrante responde a uma pergunta sobre uma parte que **não** foi ele quem apresentou. A nota
da apresentação é da equipe; a arguição pode reduzir a nota individual. Por isso todos estudam o banco de
perguntas inteiro (seção 9.2), e não só a própria parte.

### 1.3 A solução escolhida

**Problema real:** pré-processamento em lote de um dataset de fotos para visão computacional. Antes de treinar
um modelo, as fotos precisam ser padronizadas, e o dataset inteiro precisa de estatísticas (média e
desvio-padrão de cada canal de cor), que são os valores usados para normalizar a entrada da rede.

- **Entrada:** COCO 2017 val, com 5.000 fotos reais (~1 GB), na pasta `dados\val2017\`.
- **Unidade de trabalho:** 1 imagem, processada pela função `processar_imagem()`: decodificar, padronizar em
  512×512, remover ruído (filtro de mediana), ajustar o contraste, aplicar nitidez, calcular o histograma,
  salvar o JPEG, gerar a miniatura e calcular o SHA-256 da saída. Nenhuma imagem depende de outra.
- **Estado compartilhado:** o histograma RGB do lote inteiro (768 inteiros) e 4 contadores, numa memória
  compartilhada pelos processos. Cada processo soma nela o histograma da imagem que acabou de processar.
- **Primitiva:** `multiprocessing.Lock`. A **seção crítica** é só a soma no estado global (microssegundos). O
  processamento da imagem (dezenas de milissegundos) fica fora da trava.
- **Paralelização:** `multiprocessing.Pool` com `p` processos, método de início `spawn` (o padrão do Windows),
  com distribuição dinâmica por `imap_unordered` e `chunksize=4`.
- **Verificação:** as duas versões chamam a mesma função, cada imagem gerada tem o seu SHA-256 e o lote inteiro
  tem uma "impressão digital". O `verificar.py` compara duas execuções e responde IDÊNTICO ou DIVERGENTE.
- **Medição:** o `bench.py` roda a sequencial e a paralela várias vezes na máquina da demo; o `analise.py`
  calcula speedup, eficiência, teto de Amdahl e Karp–Flatt e gera os gráficos.
- **Serviço e acesso:** uma página de resultados servida na porta 8000. As regras do Firewall do Windows deixam
  a porta 8000 aberta e a porta administrativa (SSH, 22) liberada só para o IP da equipe.

**Já validado num protótipo** (máquina de 2 núcleos). Os processos deram entre 1,7× e 2,0× de speedup (quanto
maior o lote, mais perto de 2) e as threads ~1,2×, porque o filtro de mediana segura o GIL do Python. A trava
em volta do trabalho inteiro deu ~1,0×, às vezes mais lenta que a sequencial. A sequencial e a paralela
produziram a mesma impressão digital em todas as execuções, e sem a trava o teste de estresse perdeu
atualizações em todas as rodadas. Todo o código deste documento foi testado com Python 3.12, 3.13 e 3.14.

### 1.4 Como as peças se encaixam

```text
                     dados\val2017\*.jpg   (5.000 fotos, ordem alfabética; --limite N usa as N primeiras)
                              |
          +-------------------+--------------------------------------+
          |                                                          |
      seq.py (P1)                                               par.py (P2)
   1 fluxo: para cada imagem                          Pool de p processos (spawn)
   processar_imagem()  (P1)                           cada processo, para cada imagem:
   soma o histograma num array local                    processar_imagem()        (fora da trava)
          |                                             estado.mesclar()          (DENTRO da trava)
          |                                                          |
      saida_seq\                                                 saida_par\
   imagens\ miniaturas\ manifesto.txt estatisticas.json execucao.json   (mesmo formato nas duas)
          |                                                          |
          +------------------> verificar.py (P1) <-------------------+
                               RESULTADO: IDÊNTICO

   bench.py (P4): roda seq.py e par.py várias vezes --> resultados\bateria.csv
   analise.py (P4): bateria.csv --> tabela_tempos.md, resumo.json, speedup.png, tempos.png
   gerar_site.py (P3): saida_par + resultados --> site\index.html --> porta 8000 (python -m http.server)
   demo.ps1 (P3): os comandos da apresentação, na ordem
```

### 1.5 Quem faz o quê

| | Pessoa 1 | Pessoa 2 | Pessoa 3 | Pessoa 4 |
|---|---|---|---|---|
| Papel | Problema, dados e versão sequencial | Versão paralela e sincronização | Ambiente, acesso e demonstração | Medição, análise e relatório |
| Arquivos | `comum.py`, `pipeline.py`, `baixar_dados.py`, `calibrar.py`, `seq.py`, `verificar.py` | `estado.py`, `par.py`, `teste_corrida.py` | `README.md`, `requirements.txt`, `.gitignore`, `ficha_maquina.py`, `aquecer_cache.py`, `gerar_site.py`, `demo.ps1`, `infra\` | `bench.py`, `analise.py`, `resultados\`, `relatorio\` |
| Relatório | §1 Problema e dados | §2 Estratégia + §3 Seção crítica | §4 Recursos | §5 Medição + §6 Limites; monta o PDF |
| Apresenta | Parte 1 (2 min) e dispara a sequencial | Parte 2 (2 min) | Parte 3 (2 min) | Partes 4 e 5 (4 min) |
| Critério que defende | Definição do problema | Sincronização (0,5) | Provisionamento e acesso (0,5) | Medição (0,5) |

Nomes: P1 = __________ · P2 = __________ · P3 = __________ · P4 = __________

### 1.6 Cronograma e marcos

| Quando | Marco | O que precisa estar pronto |
|---|---|---|
| Sáb 14:00 | Largada (todos, 30 min) | Definir quem é P1–P4; P3 cria o repositório com `README.md`, `requirements.txt` e `.gitignore`; todos começam a seção 2.1 e o download do COCO. |
| Sáb 14:30 | **M0** | Todos com Git, Python, ambiente virtual e bibliotecas instalados e o repositório clonado. |
| Sáb 15:30 | **M1** | P1 subiu `comum.py`, `pipeline.py` e `baixar_dados.py`; P2 subiu `estado.py` e `teste_corrida.py`; P3 subiu `infra\firewall_windows.ps1`; P4 subiu `bench.py`. |
| Sáb 18:00 | **M2 (integração)** | `seq.py`, `verificar.py` (P1) e `par.py` (P2) no repositório; todos rodaram o teste de fumaça (seção 2.6) com IDÊNTICO; P4 rodou uma bateria pequena. |
| Sáb 19:00 | **M3 (congelamento)** | P1 calibrou o N na máquina da demo; P3 cria a tag `v0.9`. Depois disso ninguém muda `comum.py`, `pipeline.py`, `estado.py`, `seq.py` nem `par.py`. |
| Sáb 19:30–21:00 | Bateria oficial | P4 roda o `bench.py` na máquina da demo parada, na tomada. Enquanto isso, os outros escrevem as suas seções do relatório. |
| Dom 11:00 | **M4** | P4 com tabelas e gráficos; P3 com site, `demo.ps1` e firewall testados na máquina da demo; rascunhos das seções prontos. |
| Dom 14:00 | **M5** | Slides de todos com a P3; seções do relatório com a P4. |
| Dom 14:00–15:30 | Ensino cruzado | Cada um explica a sua parte em ~15 min para os outros três. É daqui que sai a nota individual da arguição. |
| Dom 16:00 | Ensaio 1 | Apresentação cronometrada com a demonstração real, na máquina da demo. |
| Dom 18:00 | **M6** | PDF final (até 6 páginas) pronto. |
| Dom 20:00 | Ensaio 2 | Ensaio + arguição simulada (cada um responde 3 perguntas sobre partes que não apresentou); P3 cria a tag `v1.0`. |
| Seg até 12:00 | Entrega | P4 põe o link do repositório e o PDF no ambiente virtual. |
| Seg, antes da aula | Checklist | P3 prepara a máquina da demo (seção 8 do documento da P3). |

### 1.7 Roteiro da apresentação (10 min, na ordem da lauda)

| Tempo | Quem | Parte | O que aparece na tela | Comando |
|---|---|---|---|---|
| antes de começar | P3 | Preparação | Terminais abertos na pasta do projeto, fonte grande | `.\demo.ps1 -Etapa preparar` |
| 0:00–2:00 | P1 | O problema e por que ele se divide | Fotos antes/depois; entrada, unidade de trabalho e volume | aos ~0:20, no terminal 1: `.\demo.ps1 -Etapa seq` (fica rodando ~4 min) |
| 2:00–4:00 | P2 | A seção crítica | Trecho do `estado.py` com a trava; teste de corrida; duas execuções com o mesmo resultado | terminal 2: `.\demo.ps1 -Etapa corrida` e `.\demo.ps1 -Etapa estavel` |
| 4:00–6:00 | P3 | Os recursos | Ficha da máquina; regras do firewall ao vivo (`wf.msc`); Gerenciador de Tarefas com a sequencial usando 1 núcleo | — |
| 6:00–9:00 | P4 | A execução | Tempo final da sequencial (terminal 1); paralela rodando com todos os núcleos (terminal 2); verificação | `.\demo.ps1 -Etapa par` e `.\demo.ps1 -Etapa verificar` |
| 9:00–10:00 | P4 | O ganho | Gráfico speedup medido × Amdahl × ideal; o que limitou | — |

A sequencial leva minutos e a fatia da execução tem 3. Por isso ela é disparada aos ~20 s e roda **ao vivo**
enquanto as partes 1 a 3 são apresentadas; o tempo dela já está na tela quando chega a parte 4. Se o professor
não aceitar, o plano B é rodar as duas versões com `--limite 1000` dentro da fatia de 3 minutos. Vídeo nunca é
plano B: demonstração gravada tira nota.

### 1.8 Glossário mínimo

- **Fluxo:** quem executa o trabalho em paralelo; aqui, um processo (ou uma thread, só no experimento).
- **GIL:** trava interna do CPython que deixa só uma thread executar código Python por vez em cada processo.
  Por isso, para trabalho de CPU, usamos processos, cada um com o seu próprio interpretador e GIL.
- **spawn:** método de início de processos do Windows. Cada processo filho é um `python.exe` novo que importa os
  módulos do zero e não herda variáveis do pai.
- **Estado compartilhado:** dado que vários fluxos escrevem; aqui, o histograma global e os contadores.
- **Condição de corrida:** erro que aparece quando dois fluxos fazem "ler, somar e escrever" no mesmo dado ao
  mesmo tempo e uma atualização apaga a outra.
- **Seção crítica:** trecho que só um fluxo pode executar por vez; aqui, a soma no estado global.
- **Trava (Lock):** primitiva de exclusão mútua que protege a seção crítica.
- **Speedup:** S(p) = T_sequencial / T_paralelo(p). **Eficiência:** E(p) = S(p) / p.
- **Lei de Amdahl:** teto do speedup, S_max(p) = 1 / ((1 − f) + f / p), onde f é a fração paralelizável.
- **Karp–Flatt:** e(p) = (1/S − 1/p) / (1 − 1/p), a fração serial "efetiva" medida. Se cresce com p, a perda
  vem de sobrecarga (criar processos, comunicação, espera).
- **Impressão digital:** SHA-256 que resume o resultado do lote inteiro. Duas execuções com a mesma impressão
  digital produziram exatamente os mesmos bytes e as mesmas estatísticas.

## 2. Ambiente, regras e contratos do grupo (igual nos 4 documentos)

### 2.1 Preparar o PC (Windows): passo a passo

Faça tudo no **PowerShell** (menu Iniciar → "Terminal" ou "Windows PowerShell"). O terminal do VS Code também
é PowerShell. Onde aparecer `<...>`, troque pelo valor indicado.

**Passo 1: Git.** Rode `git --version`. Se o comando não existir, instale e depois feche e abra o PowerShell:

```powershell
winget install --id Git.Git -e --source winget
git config --global user.name "<Seu Nome>"
git config --global user.email "<seu e-mail do GitHub>"
```

**Passo 2: Python 3.12, 3.13 ou 3.14 (64 bits).** Rode `py -3.13 --version` (ou `py -3.12` / `py -3.14`). Se
aparecer "Python 3.13.x", pule para o passo 3. Se não tiver nenhuma dessas versões, instale o gerenciador de
instalação do Python e depois o 3.13, e em seguida feche e abra o PowerShell:

```powershell
winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity
py install 3.13
py -3.13 --version
```

Sem o `winget`, baixe o "Python install manager" em python.org/downloads. **Não use a variante
"free-threaded" (3.13t ou 3.14t):** ela remove o GIL e invalida a comparação entre threads e processos.

**Passo 3: pasta e repositório.** Use uma pasta **fora do OneDrive**: a sincronização de milhares de arquivos
atrapalha as medições. O link do repositório é enviado pela Pessoa 3 na largada.

```powershell
mkdir C:\projetos -Force
cd C:\projetos
git clone <LINK_DO_REPOSITORIO> lote-imagens
cd lote-imagens
```

**Passo 4: ambiente virtual e bibliotecas.** Troque `3.13` pela versão que você tem.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import PIL, numpy, matplotlib, psutil; print('ambiente ok')"
```

Se a ativação falhar com "a execução de scripts foi desabilitada neste sistema", rode uma vez o comando abaixo e
ative de novo:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
```

**Toda vez que abrir um PowerShell novo:** `cd C:\projetos\lote-imagens` e `.\.venv\Scripts\Activate.ps1`. O
prompt passa a começar com `(.venv)`. Sem isso, `python` pode abrir outra instalação, ou a Microsoft Store.

**Passo 5: dados (COCO 2017 val, ~1 GB).** Para adiantar, baixe pelo navegador o arquivo
`http://images.cocodataset.org/zips/val2017.zip`, crie a pasta `dados` dentro do projeto e salve o arquivo nela
como `val2017.zip`. Quando a Pessoa 1 subir o `baixar_dados.py` (marco M1), rode `git pull` e
`python baixar_dados.py`: o script usa o zip que já estiver lá (ou baixa sozinho) e extrai. No fim, deve
existir `dados\val2017\` com 5.000 arquivos `.jpg`.

### 2.2 Repositório e Git

- A Pessoa 3 cria o repositório `lote-imagens` no GitHub e adiciona os outros três como colaboradores. Ele pode
  ser público ou privado com o professor adicionado, porque o link vai para o ambiente virtual.
- Todos trabalham direto na branch `main`, **cada um só nos próprios arquivos** (tabela 2.3). Assim não há
  conflito.
- Antes de começar e antes de subir: `git pull --rebase`. Para subir: `git add <seus arquivos>`,
  `git commit -m "P1: adiciona pipeline.py"`, `git push`. Não use `git add .` sem conferir o `git status`.
- Nunca suba `dados\`, `saida_*`, `site\` nem `.venv\` (o `.gitignore` já impede).
- Marcos: a Pessoa 3 cria a tag `v0.9` no congelamento (M3) e `v1.0` na versão final, com
  `git tag v0.9` e `git push --tags`.

### 2.3 Estrutura de pastas e donos

```text
lote-imagens\
├── README.md               P3   como instalar e rodar
├── requirements.txt        P3   versões fixas das bibliotecas
├── .gitignore              P3
├── comum.py                P1   constantes e funções usadas por seq.py e par.py
├── pipeline.py             P1   processar_imagem(): a unidade de trabalho
├── baixar_dados.py         P1   baixa e extrai o COCO 2017 val
├── calibrar.py             P1   recomenda o --limite para a sequencial levar ~4 min
├── seq.py                  P1   versão sequencial
├── verificar.py            P1   compara duas execuções
├── estado.py               P2   estado compartilhado + SEÇÃO CRÍTICA
├── par.py                  P2   versão paralela
├── teste_corrida.py        P2   mostra a condição de corrida sem a trava
├── ficha_maquina.py        P3   ficha técnica da máquina
├── aquecer_cache.py        P3   lê as imagens antes da demonstração
├── gerar_site.py           P3   página de resultados (porta 8000)
├── demo.ps1                P3   comandos da apresentação
├── infra\                  P3   firewall_windows.ps1, regras_de_acesso.md, ficha_maquina.md
├── bench.py                P4   bateria de medições
├── analise.py              P4   tabelas, speedup, Amdahl, Karp–Flatt, gráficos
├── resultados\             P4   bateria.csv, tabela_tempos.md, resumo.json, speedup.png, tempos.png
├── relatorio\              P4   seções de cada um e o PDF final
├── dados\                  --   dataset (não vai para o Git)
└── saida_seq\, saida_par\, saida_bench\, site\ ...   gerados (não vão para o Git)
```

### 2.4 Contratos entre as partes (não mudar sem avisar o grupo)

**`pipeline.py` (P1).** `processar_imagem(origem: Path, pasta_saida: Path) -> tuple[str, str, list[int], int]`
recebe o caminho de uma imagem e a pasta da execução. Grava `pasta_saida\imagens\<nome>.jpg` (512×512, JPEG
qualidade 90) e `pasta_saida\miniaturas\<nome>.jpg` (128×128, qualidade 85) e devolve
`(nome_original, sha256_do_jpeg_gerado, histograma_com_768_inteiros, numero_de_pixels)`. Não toca em estado
compartilhado e não tem nada aleatório. Constantes: `TAM_SAIDA = (512, 512)`, `TAM_MINIATURA = (128, 128)`,
`QUALIDADE_JPEG = 90` e `QUALIDADE_MINIATURA = 85`.

**`comum.py` (P1)**

| Nome | O que faz |
|---|---|
| `ENTRADA_PADRAO` | `Path("dados") / "val2017"` |
| `N_BINS` | `768` (histograma RGB: 256 níveis × 3 canais) |
| `listar_imagens(entrada, limite) -> list[Path]` | `.jpg`/`.jpeg` da pasta em ordem alfabética do nome; `limite` pega as N primeiras; erro claro se a pasta não existir ou estiver vazia |
| `preparar_saida(saida)` | cria `saida\imagens` e `saida\miniaturas`; não apaga nada |
| `gravar_resultados(saida, manifesto, histograma, imagens, pixels) -> dict` | grava `manifesto.txt` e `estatisticas.json`; devolve as estatísticas, inclusive `impressao_digital` |
| `gravar_json(caminho, dados)` | grava um JSON em UTF-8 |
| `agora_iso() -> str` | data e hora atuais, ex.: `2026-09-19T15:30:00` |
| `info_ambiente() -> dict` | `cpu`, `nucleos_fisicos`, `nucleos_logicos`, `ram_gb`, `sistema`, `python`, `pillow`, `numpy`, `maquina` |
| `Progresso(total, passo)` e `.avancar()` | imprime o andamento a cada `passo` imagens (0 = nunca) |
| `imprimir_resumo(execucao)` | imprime o resumo final (mesmo formato para seq e par) |
| `estatisticas_do_histograma`, `impressao_digital`, `nome_cpu` | auxiliares usadas pelas funções acima |

**`estado.py` (P2).** Constantes `N_BINS = 768` e as posições dos contadores `IMAGENS, PIXELS, ESPERA_NS,
DENTRO_NS = 0, 1, 2, 3`. Funções: `criar_memoria(ctx)`, `iniciar(trava, hist_raw, cont_raw)`,
`somar_sem_protecao(hist_local, n_pixels)`, `mesclar(hist_local, n_pixels)` (a seção crítica),
`trava_do_estado()`, `registrar_tempos_trava(espera_ns, dentro_ns)` e `ler(hist_raw, cont_raw) -> (hist, dict)`.

**Pasta de saída de uma execução** (igual para `seq.py` e `par.py`):

```text
<saida>\
  imagens\<nome>.jpg      imagem processada (512x512)
  miniaturas\<nome>.jpg   miniatura (128x128)
  manifesto.txt           uma linha por imagem: "<nome_original> <sha256>", em ordem alfabética
  estatisticas.json       imagens, pixels, media_rgb, desvio_rgb, impressao_digital, histograma (768)
  execucao.json           tempos, parâmetros e ambiente desta execução
```

**Campos do `execucao.json`** (lidos pelo `bench.py` e pelo `gerar_site.py`):

| Campo | Sequencial | Paralela |
|---|---|---|
| `versao` | `"seq"` | `"par"` |
| `modo`, `trava`, `chunksize` | `null` | `"processos"`/`"threads"`, `"fina"`/`"grossa"`, inteiro |
| `workers` | `1` | número de fluxos |
| `entrada`, `saida`, `limite` | argumentos usados | argumentos usados |
| `imagens`, `pixels` | totais processados | totais lidos do estado compartilhado |
| `t_total_s`, `t_preparo_s`, `t_processamento_s`, `t_final_s` | tempos por fase, em segundos | idem |
| `espera_trava_s`, `dentro_trava_s` | `0.0` | tempo total esperando a trava e com a trava na mão |
| `inicio_primeira_tarefa_s` | `null` | do início do processamento até a 1ª tarefa começar (custo de criar os processos) |
| `cauda_s` | `null` | diferença entre o primeiro e o último fluxo a terminar (divisão desigual no fim) |
| `ocupacao` | `null` | fração do tempo em que os fluxos estavam dentro de tarefas (0 a 1) |
| `fluxos_usados` | `1` | quantos fluxos processaram pelo menos uma imagem |
| `media_rgb`, `desvio_rgb`, `impressao_digital` | estatísticas do lote | idem |
| `inicio`, `ambiente` | data e hora; saída de `info_ambiente()` | idem |

**Colunas do `resultados\bateria.csv`** (gravado só pelo `bench.py`): `data_hora, rodada, aquecimento, versao,
modo, trava, workers, chunksize, imagens, pixels, t_total_s, t_preparo_s, t_processamento_s, t_final_s,
espera_trava_s, dentro_trava_s, inicio_primeira_tarefa_s, cauda_s, ocupacao, fluxos_usados, impressao_digital,
cpu, nucleos_fisicos, nucleos_logicos, ram_gb, sistema, python, pillow, numpy, maquina`.

### 2.5 Linha de comando de todos os scripts

| Script | Dono | Uso típico | Opções |
|---|---|---|---|
| `baixar_dados.py` | P1 | `python baixar_dados.py` | `--dados dados`, `--url <url>`, `--manter-zip` |
| `calibrar.py` | P1 | `python calibrar.py` | `--entrada`, `--amostra 200`, `--alvo-min 4.0` |
| `seq.py` | P1 | `python seq.py --limite N` | `--entrada dados/val2017`, `--saida saida_seq`, `--limite`, `--progresso 250` |
| `verificar.py` | P1 | `python verificar.py saida_seq saida_par` | termina com código 0 (idêntico) ou 1 (divergente) |
| `par.py` | P2 | `python par.py --limite N --workers P` | `--entrada`, `--saida saida_par`, `--limite`, `-w/--workers` (padrão: núcleos lógicos), `--chunksize 4`, `--modo processos\|threads`, `--trava fina\|grossa`, `--progresso 250` |
| `teste_corrida.py` | P2 | `python teste_corrida.py` | `-p 4` (processos), `-m 20000` (somas), `-r 3` (rodadas) |
| `ficha_maquina.py` | P3 | `python ficha_maquina.py` | grava `infra\ficha_maquina.md` |
| `aquecer_cache.py` | P3 | `python aquecer_cache.py dados\val2017` | — |
| `gerar_site.py` | P3 | `python gerar_site.py --execucao saida_par` | `--entrada`, `--resultados resultados`, `--site site` |
| servidor | P3 | `python -m http.server 8000 --directory site --bind 0.0.0.0` | — |
| `demo.ps1` | P3 | `.\demo.ps1 -Etapa seq` | etapas: `preparar`, `seq`, `corrida`, `estavel`, `par`, `verificar`, `site`, `servir` |
| `infra\firewall_windows.ps1` | P3 | `.\infra\firewall_windows.ps1 -IpEquipe <ip>` (como administrador) | `-Remover` |
| `bench.py` | P4 | `python bench.py --limite N --com-threads --com-trava-grossa` | `--entrada`, `--repeticoes 5`, `--workers 2 4 8`, `--repeticoes-extras 3`, `--csv`, `--continuar`, `--pausa 2`, `--somente-plano` |
| `analise.py` | P4 | `python analise.py` | `--csv resultados\bateria.csv`, `--saida resultados` |

### 2.6 Como rodar o projeto do zero (roteiro completo)

Com o ambiente pronto (seção 2.1) e o ambiente virtual ativado, na pasta do projeto:

```powershell
python baixar_dados.py                          # 1. dados: dados\val2017 com 5.000 imagens
python seq.py --limite 100                      # 2. teste de fumaça: sequencial
python par.py --limite 100                      #    paralela
python verificar.py saida_seq saida_par         #    deve terminar com "RESULTADO: IDÊNTICO"
python teste_corrida.py                         # 3. corrida: SEM trava perde, COM trava bate
python calibrar.py                              # 4. na máquina da demo: recomenda o N
python bench.py --limite N --com-threads --com-trava-grossa   # 5. bateria oficial (~1h15)
python analise.py                               # 6. tabelas e gráficos em resultados\
python par.py --limite N                        # 7. uma execução completa para o site
python gerar_site.py --execucao saida_par       #    gera site\index.html
python -m http.server 8000 --directory site --bind 0.0.0.0    # 8. serviço (Ctrl+C para parar)
```

Na apresentação, os mesmos comandos são rodados pelo `demo.ps1` (seção 1.7).

### 2.7 Regras de código (valem para todos os arquivos)

1. Python 3.12 ou mais novo. Comentários e mensagens em português.
2. Todo script executável termina com `if __name__ == "__main__": main()`. Funções entregues ao `Pool` ficam no
   nível do módulo: nada de `lambda` ou função definida dentro de outra função.
3. Caminhos sempre com `pathlib.Path`; nunca montar caminho juntando texto com barras.
4. Todo arquivo de texto é lido e gravado com `encoding="utf-8"`; CSV com `newline=""`.
5. Mensagens na tela usam só letras, números, pontuação e acentos do português. Nada de emoji, setas "→", "✓" ou
   caracteres de desenho de caixa: o console do Windows pode quebrar com eles quando a saída é redirecionada.
6. Bibliotecas permitidas: biblioteca padrão, Pillow, NumPy, psutil e matplotlib (esta só em `analise.py` e
   `gerar_site.py`), nas versões do `requirements.txt`.
7. Nada de aleatoriedade no processamento; a ordem das imagens é sempre a alfabética do nome.
8. Nada de tratamento silencioso de erro: se uma imagem falhar, o programa para e mostra o erro.
9. Não mudar os parâmetros do processamento (filtros, tamanhos, qualidade JPEG). A única mudança permitida é
   `TAM_SAIDA` em `pipeline.py`, e só se a calibração pedir, antes do marco M3.

## 3. Sua parte: visão geral

Você cuida da medição e da análise do ganho, que valem 0,5 da nota, e da montagem do relatório. A lauda é
específica: tempo sequencial e paralelo **na mesma máquina, com a mesma entrada, medidos mais de uma vez**;
speedup comparado ao **teto de Amdahl** para a fração paralelizável estimada; e uma explicação para a diferença
(comunicação entre processos, divisão desigual do trabalho ou espera na seção crítica).

| | |
|---|---|
| Seus arquivos | `bench.py`, `analise.py`; gera `resultados\bateria.csv`, `tabela_tempos.md`, `resumo.json`, `speedup.png` e `tempos.png` |
| Relatório | Seção 5, "Medição e speedup" (≈ 1,5 página), seção 6, "O que limitou o ganho" (≈ ¾ de página), e a montagem do PDF inteiro |
| Apresentação | Parte 4, "A execução" (6:00–9:00), e parte 5, "O ganho" (9:00–10:00) |
| Critério que você defende | Medição de desempenho e análise do ganho (0,5) |
| Você depende de | P1 e P2: `seq.py` e `par.py` (M2); P1: o N calibrado (M3); P3: a máquina da demo preparada (M3) |
| Dependem de você | P3: o melhor número de processos para o `demo.ps1`; todos: tabelas e gráficos para o relatório e os slides |

## 4. Etapas de implementação

1. [ ] Preparar o PC (seção 2.1, passos 1 a 4) e começar o download do COCO (passo 5).
2. [ ] Ler a seção 5.1 (conceitos de medição). É isso que o professor vai perguntar.
3. [ ] Criar `bench.py` (5.2), rodar o teste 6.1 (`--somente-plano`), fazer `git push`. **Marco M1.**
4. [ ] Criar `analise.py` (5.3), rodar o teste 6.2 com o CSV de exemplo, fazer `git push`.
5. [ ] Depois do M2: rodar uma bateria pequena no seu PC (5.4, teste 6.3). **Marco M2.**
6. [ ] Depois do M3, na máquina da demo preparada: rodar a **bateria oficial** (5.5).
7. [ ] Rodar o `analise.py`, interpretar os números (5.6), fazer `git push` da pasta `resultados\` e mandar ao
   grupo o melhor número de processos (a P3 coloca em `$P` no `demo.ps1`) e os números que cada um usa na sua
   seção. **Marco M4.**
8. [ ] Escrever as seções 5 e 6, receber as seções 1 a 4 até domingo, 14:00, e montar o PDF (seção 7).
   **Marco M6** (domingo, 18:00).
9. [ ] Fazer os slides das partes 4 e 5 e entregar à Pessoa 3 até domingo, 14:00.
10. [ ] Segunda, até 12:00: pôr o link do repositório e o PDF no ambiente virtual.
11. [ ] Estudar o banco de perguntas (seção 9) e participar do ensino cruzado e dos dois ensaios.

## 5. Como implementar

Crie cada arquivo na raiz do projeto (`C:\projetos\lote-imagens\`) com **exatamente** o código de referência.
Ele foi testado no Python 3.12, 3.13 e 3.14.

### 5.1 Conceitos de medição (leia antes de codar)

**Speedup e eficiência.** S(p) = T_seq / T_par(p), com T_seq e T_par médios, medidos na mesma máquina e com a
mesma entrada. E(p) = S(p) / p: 100% seria o ideal. Na prática fica abaixo disso.

**Fração paralelizável (f) e lei de Amdahl.** O `seq.py` mede três fases: preparo, processamento e final. Só o
processamento é dividido entre os processos, então f = T_processamento / T_total da sequencial. O teto de
Amdahl é S_max(p) = 1 / ((1 − f) + f / p). Neste projeto f fica muito perto de 1 (0,999 no protótipo), porque
o preparo e o final levam milissegundos: o teto fica praticamente igual a p. Por isso quase toda a diferença
entre o medido e o teto é **sobrecarga e hardware**, e não parte serial do programa.

**Karp–Flatt.** e(p) = (1/S − 1/p) / (1 − 1/p) é a fração serial "efetiva" calculada a partir do speedup
medido. Se e(p) fica constante quando p cresce, existe uma parte serial fixa. Se e(p) **cresce** com p, a perda
vem de sobrecarga que aumenta com o número de processos (criar processos, comunicação, disputa por memória ou
disco). É o argumento quantitativo mais forte para a seção 6.

**De onde vem a diferença para o teto** (colunas da segunda tabela do `analise.py`):

- **Criação dos processos e comunicação** (coluna "início da 1ª tarefa"): no Windows, cada processo é um
  `python.exe` novo que importa Pillow e NumPy antes de começar. Resultados e tarefas passam por um canal entre
  processos.
- **Divisão desigual do trabalho** (coluna "cauda"): no fim do lote, alguns processos ficam sem tarefa enquanto
  os últimos terminam.
- **Espera na seção crítica** (coluna "espera pela trava"): na trava fina, milissegundos; na trava grossa,
  quase o tempo todo.
- **Hardware**, que não aparece numa coluna, mas explica o resto: *turbo* (um núcleo sozinho roda em clock mais
  alto do que todos juntos, o que favorece a sequencial); *Hyper-Threading* (acima do número de núcleos
  físicos, dois fluxos dividem um núcleo); núcleos de desempenho e de eficiência em processadores Intel mais
  novos; e disco, já que cada execução grava centenas de MB.

**Gustafson.** Se o problema cresce junto com o número de processos, os custos fixos pesam menos e a eficiência
se mantém. Num lote maior, o speedup sobe um pouco.

**Protocolo** (é o que o `bench.py` faz): mesma máquina, mesma entrada, uma execução de aquecimento descartada
(cache de disco), 5 repetições alternando sequencial e paralelas, média ± desvio-padrão, pasta de saída limpa
antes de cada execução (fora da medição) e a impressão digital conferida em todas as execuções.

### 5.2 `bench.py`: a bateria de medições

**Para que serve.** Roda o `seq.py` e o `par.py` várias vezes, cada execução num processo separado, e grava uma
linha por execução em `resultados\bateria.csv` (colunas da seção 2.4). Confere que todas as execuções têm a
mesma impressão digital: se uma for diferente, para tudo, porque isso indicaria erro de sincronização.

```python
"""Bateria de medições: roda seq.py e par.py várias vezes na MESMA máquina e com a MESMA entrada.

Dono: Pessoa 4.
Uso (na máquina da demonstração, com o N calibrado pela Pessoa 1):
    python bench.py --limite N --com-threads --com-trava-grossa
Cada execução roda como um processo separado e grava uma linha em resultados/bateria.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

RAIZ = Path(__file__).resolve().parent
PASTA_SAIDA = RAIZ / "saida_bench"
CAMPOS = [
    "data_hora", "rodada", "aquecimento", "versao", "modo", "trava", "workers", "chunksize",
    "imagens", "pixels", "t_total_s", "t_preparo_s", "t_processamento_s", "t_final_s",
    "espera_trava_s", "dentro_trava_s", "inicio_primeira_tarefa_s", "cauda_s", "ocupacao", "fluxos_usados",
    "impressao_digital", "cpu", "nucleos_fisicos", "nucleos_logicos", "ram_gb", "sistema",
    "python", "pillow", "numpy", "maquina",
]


def workers_padrao() -> list[int]:
    """Potências de 2 até o nº de núcleos lógicos, mais os nº de núcleos físicos e lógicos."""
    fisicos = psutil.cpu_count(logical=False) or 1
    logicos = psutil.cpu_count(logical=True) or 1
    valores = {p for p in (2, 4, 8, 16, 32, 64) if p <= logicos} | {fisicos, logicos}
    return sorted(p for p in valores if p >= 2)


def montar_plano(args, workers: list[int]) -> list[dict]:
    """Lista ordenada das execuções: aquecimento, depois rodadas alternando seq e par."""
    p_max = max(workers)
    plano = [{"descricao": "aquecimento (sequencial, descartada)", "rodada": 0, "aquecimento": 1,
              "script": "seq.py", "extra": []}]
    for rodada in range(1, args.repeticoes + 1):
        plano.append({"descricao": "sequencial", "rodada": rodada, "aquecimento": 0, "script": "seq.py", "extra": []})
        for p in workers:
            plano.append({"descricao": f"paralela, {p} processos", "rodada": rodada, "aquecimento": 0,
                          "script": "par.py", "extra": ["--workers", str(p)]})
    for rodada in range(1, args.repeticoes_extras + 1):
        if args.com_threads:
            plano.append({"descricao": f"experimento: {p_max} threads", "rodada": rodada, "aquecimento": 0,
                          "script": "par.py", "extra": ["--workers", str(p_max), "--modo", "threads"]})
        if args.com_trava_grossa:
            plano.append({"descricao": f"experimento: trava grossa, {p_max} processos", "rodada": rodada,
                          "aquecimento": 0, "script": "par.py",
                          "extra": ["--workers", str(p_max), "--trava", "grossa"]})
    return plano


def executar(item: dict, entrada: Path, limite: int) -> dict:
    """Roda uma execução como processo separado e devolve o execucao.json que ela gravou."""
    shutil.rmtree(PASTA_SAIDA, ignore_errors=True)            # limpa FORA da medição
    comando = [sys.executable, str(RAIZ / item["script"]), "--entrada", str(entrada), "--limite", str(limite),
               "--saida", str(PASTA_SAIDA), "--progresso", "0", *item["extra"]]
    ambiente = dict(os.environ, PYTHONUTF8="1")
    subprocess.run(comando, check=True, cwd=RAIZ, env=ambiente)
    return json.loads((PASTA_SAIDA / "execucao.json").read_text(encoding="utf-8"))


def linha_csv(execucao: dict, item: dict) -> dict:
    amb = execucao["ambiente"]
    linha = {campo: execucao.get(campo) for campo in CAMPOS}
    linha.update({
        "data_hora": execucao["inicio"], "rodada": item["rodada"], "aquecimento": item["aquecimento"],
        "cpu": amb["cpu"], "nucleos_fisicos": amb["nucleos_fisicos"], "nucleos_logicos": amb["nucleos_logicos"],
        "ram_gb": amb["ram_gb"], "sistema": amb["sistema"], "python": amb["python"], "pillow": amb["pillow"],
        "numpy": amb["numpy"], "maquina": amb["maquina"],
    })
    return {k: ("" if v is None else v) for k, v in linha.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description="Bateria de medições (seq x par)")
    ap.add_argument("--entrada", type=Path, default=Path("dados") / "val2017")
    ap.add_argument("--limite", type=int, required=True, help="N calibrado pela Pessoa 1 (mesmo N da demo)")
    ap.add_argument("--repeticoes", type=int, default=5, help="rodadas de seq + paralelas")
    ap.add_argument("--workers", type=int, nargs="+", default=None, help="lista de nº de processos (padrão: automático)")
    ap.add_argument("--com-threads", action="store_true", help="inclui o experimento com threads")
    ap.add_argument("--com-trava-grossa", action="store_true", help="inclui o experimento com trava grossa")
    ap.add_argument("--repeticoes-extras", type=int, default=3, help="rodadas de cada experimento extra")
    ap.add_argument("--csv", type=Path, default=Path("resultados") / "bateria.csv")
    ap.add_argument("--continuar", action="store_true", help="acrescentar a um CSV que já existe")
    ap.add_argument("--pausa", type=float, default=2.0, help="segundos de pausa entre execuções")
    ap.add_argument("--somente-plano", action="store_true", help="só mostra o plano, sem rodar nada")
    args = ap.parse_args()

    entrada = args.entrada.resolve()
    workers = sorted(set(args.workers)) if args.workers else workers_padrao()
    plano = montar_plano(args, workers)
    print(f"Máquina: {psutil.cpu_count(logical=False)} núcleos físicos, {psutil.cpu_count(logical=True)} lógicos")
    print(f"Entrada: {entrada} | limite: {args.limite} | workers testados: {workers}")
    print(f"Plano: {len(plano)} execuções")
    for i, item in enumerate(plano, 1):
        print(f"  {i:>3}. rodada {item['rodada']}: {item['descricao']}")
    if args.somente_plano:
        return
    if args.csv.exists() and not args.continuar:
        raise SystemExit(f"ERRO: '{args.csv}' já existe. Apague o arquivo ou use --continuar.")
    args.csv.parent.mkdir(parents=True, exist_ok=True)

    inicio = time.perf_counter()
    impressao_referencia = None
    for i, item in enumerate(plano, 1):
        print(f"[{i}/{len(plano)}] {item['descricao']} (rodada {item['rodada']}) ...", flush=True)
        execucao = executar(item, entrada, args.limite)
        if impressao_referencia is None:
            impressao_referencia = execucao["impressao_digital"]
        elif execucao["impressao_digital"] != impressao_referencia:
            raise SystemExit("ERRO: impressão digital diferente das execuções anteriores. "
                             "Existe um erro de sincronização ou a entrada mudou. Pare e avise a Pessoa 2.")
        novo_arquivo = not args.csv.exists()
        with open(args.csv, "a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            if novo_arquivo:
                escritor.writeheader()
            escritor.writerow(linha_csv(execucao, item))
        decorrido = (time.perf_counter() - inicio) / 60
        print(f"      tempo total {execucao['t_total_s']:.2f} s | impressão {execucao['impressao_digital'][:16]}"
              f" | bateria em andamento há {decorrido:.1f} min", flush=True)
        if i == 1:
            t_seq = execucao["t_total_s"]
            print(f"      (a sequencial leva {t_seq:.0f} s nesta máquina; com esse valor, a bateria inteira "
                  f"leva por volta de {estimar_minutos(plano, t_seq, workers):.0f} min, numa estimativa grosseira)")
        time.sleep(args.pausa)
    shutil.rmtree(PASTA_SAIDA, ignore_errors=True)
    print(f"Bateria concluída: {len(plano)} execuções em {(time.perf_counter() - inicio) / 60:.1f} min.")
    print(f"Resultados em '{args.csv}'. Próximo passo: python analise.py")


def estimar_minutos(plano: list[dict], t_seq: float, workers: list[int]) -> float:
    """Estimativa grosseira: supõe ganho de 70% do número de núcleos físicos nas paralelas."""
    fisicos = psutil.cpu_count(logical=False) or 1
    total = 0.0
    for item in plano[1:]:
        extra = item["extra"]
        if item["script"] == "seq.py" or "grossa" in extra:
            total += t_seq
        elif "threads" in extra:
            total += t_seq / 1.2
        else:
            p = int(extra[extra.index("--workers") + 1])
            total += t_seq / max(1.0, 0.7 * min(p, fisicos))
    return total / 60


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- `workers_padrao()` testa potências de 2 até o número de núcleos lógicos, mais o número de núcleos físicos e o
  de lógicos. Numa máquina com 8 físicos e 16 lógicos, testa p = 2, 4, 8 e 16.
- `montar_plano()` define a ordem: aquecimento (marcado com `aquecimento = 1` no CSV e descartado na análise);
  depois, em cada rodada, a sequencial seguida das paralelas; e por fim os experimentos (threads e trava
  grossa com o maior p), com 3 rodadas cada.
- `executar()` apaga a pasta `saida_bench` **antes** de rodar, fora da medição, e roda o script com o mesmo
  Python do ambiente virtual (`sys.executable`). A saída das execuções não é capturada, então nenhum caractere
  especial quebra o console do Windows.
- O CSV é aberto em modo de acréscimo a cada linha: se a bateria for interrompida, o que já rodou fica salvo.
  O `bench.py` se recusa a sobrescrever um CSV existente, a não ser com `--continuar`.
- Depois da primeira execução, ele imprime uma estimativa grosseira da duração da bateria inteira.

**Saída esperada do `--somente-plano`** (exemplo real do protótipo, com 2 núcleos e
`--limite 60 --repeticoes 3 --com-threads --com-trava-grossa --repeticoes-extras 2`):

```text
Máquina: 2 núcleos físicos, 2 lógicos
Entrada: /home/claude/lote-imagens/dados/val2017 | limite: 60 | workers testados: [2]
Plano: 11 execuções
    1. rodada 0: aquecimento (sequencial, descartada)
    2. rodada 1: sequencial
    3. rodada 1: paralela, 2 processos
    4. rodada 2: sequencial
    5. rodada 2: paralela, 2 processos
    6. rodada 3: sequencial
    7. rodada 3: paralela, 2 processos
    8. rodada 1: experimento: 2 threads
    9. rodada 1: experimento: trava grossa, 2 processos
   10. rodada 2: experimento: 2 threads
   11. rodada 2: experimento: trava grossa, 2 processos
```

**Andamento de uma bateria** (mesmo exemplo; entre as linhas abaixo aparece o resumo de cada execução):

```text
[1/11] aquecimento (sequencial, descartada) (rodada 0) ...
      tempo total 4.29 s | impressão 3ee171606c532d89 | bateria em andamento há 0.1 min
      (a sequencial leva 4 s nesta máquina; com esse valor, a bateria inteira leva por volta de 1 min, numa estimativa grosseira)
[2/11] sequencial (rodada 1) ...
      tempo total 4.28 s | impressão 3ee171606c532d89 | bateria em andamento há 0.2 min
[3/11] paralela, 2 processos (rodada 1) ...
      tempo total 2.50 s | impressão 3ee171606c532d89 | bateria em andamento há 0.2 min
[4/11] sequencial (rodada 2) ...
      tempo total 4.36 s | impressão 3ee171606c532d89 | bateria em andamento há 0.3 min
[5/11] paralela, 2 processos (rodada 2) ...
      tempo total 2.44 s | impressão 3ee171606c532d89 | bateria em andamento há 0.4 min
[6/11] sequencial (rodada 3) ...
      tempo total 4.27 s | impressão 3ee171606c532d89 | bateria em andamento há 0.5 min
[7/11] paralela, 2 processos (rodada 3) ...
      tempo total 2.48 s | impressão 3ee171606c532d89 | bateria em andamento há 0.5 min
[8/11] experimento: 2 threads (rodada 1) ...
      tempo total 3.65 s | impressão 3ee171606c532d89 | bateria em andamento há 0.6 min
[9/11] experimento: trava grossa, 2 processos (rodada 1) ...
      tempo total 4.51 s | impressão 3ee171606c532d89 | bateria em andamento há 0.7 min
[10/11] experimento: 2 threads (rodada 2) ...
      tempo total 3.65 s | impressão 3ee171606c532d89 | bateria em andamento há 0.8 min
[11/11] experimento: trava grossa, 2 processos (rodada 2) ...
      tempo total 4.50 s | impressão 3ee171606c532d89 | bateria em andamento há 0.9 min
Bateria concluída: 11 execuções em 0.9 min.
Resultados em 'resultados/bateria.csv'. Próximo passo: python analise.py
```

### 5.3 `analise.py`: tabelas, speedup, Amdahl, Karp–Flatt e gráficos

**Para que serve.** Lê o `bateria.csv`, descarta o aquecimento, confere que todas as linhas são da mesma máquina
e da mesma entrada e calcula, para cada configuração: média ± desvio do tempo total, speedup, eficiência, teto
de Amdahl, Karp–Flatt e as médias de espera pela trava, início da 1ª tarefa, cauda e ocupação. Grava:

- `resultados\tabela_tempos.md`: as duas tabelas, prontas para colar no relatório;
- `resultados\resumo.json`: os mesmos números, lidos pelo site da Pessoa 3;
- `resultados\speedup.png`: speedup medido × teto de Amdahl × ideal, em função de p;
- `resultados\tempos.png`: tempo médio de cada configuração, com o desvio-padrão.

```python
"""Análise da bateria: tempos, speedup, eficiência, teto de Amdahl, Karp-Flatt e gráficos.

Dono: Pessoa 4.   Uso:  python analise.py
Lê resultados/bateria.csv e grava em resultados/: tabela_tempos.md, resumo.json, speedup.png e tempos.png.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera os PNG sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

# Cores dos gráficos (paleta validada para daltonismo) e tinta do texto
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_FRACA = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"
LARANJA = "#eb6834"

CAMPOS_NUMERICOS = ["t_total_s", "t_preparo_s", "t_processamento_s", "t_final_s", "espera_trava_s",
                    "dentro_trava_s", "inicio_primeira_tarefa_s", "cauda_s", "ocupacao"]


def virgula(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def carregar(caminho: Path) -> list[dict]:
    if not caminho.exists():
        raise SystemExit(f"ERRO: '{caminho}' não existe. Rode o bench.py antes.")
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:  # aceita arquivo com ou sem BOM
        linhas = list(csv.DictReader(arquivo))
    medidas = [linha for linha in linhas if linha["aquecimento"] != "1"]
    if not medidas:
        raise SystemExit("ERRO: o CSV não tem execuções medidas (só aquecimento).")
    combinacoes = {(linha["maquina"], linha["imagens"]) for linha in medidas}
    if len(combinacoes) != 1:
        raise SystemExit(f"ERRO: o CSV mistura máquinas ou entradas diferentes: {sorted(combinacoes)}")
    if len({linha["impressao_digital"] for linha in linhas}) != 1:
        raise SystemExit("ERRO: há impressões digitais diferentes no CSV (resultado não é estável).")
    for linha in medidas:
        for campo in CAMPOS_NUMERICOS:
            linha[campo] = float(linha[campo]) if linha[campo] != "" else None
        linha["workers"] = int(linha["workers"])
    return medidas


def resumir(valores: list[float]) -> dict:
    return {
        "media": statistics.fmean(valores),
        "desvio": statistics.stdev(valores) if len(valores) > 1 else 0.0,
        "n": len(valores), "min": min(valores), "max": max(valores),
    }


def media_do_campo(linhas: list[dict], campo: str) -> float | None:
    valores = [linha[campo] for linha in linhas if linha[campo] is not None]
    return statistics.fmean(valores) if valores else None


def nome_da_configuracao(modo: str, trava: str, p: int) -> str:
    if trava == "grossa":
        return f"Trava grossa, p = {p}"
    return f"{'Processos' if modo == 'processos' else 'Threads'}, p = {p}"


def analisar(medidas: list[dict]) -> dict:
    seq = [linha for linha in medidas if linha["versao"] == "seq"]
    if not seq:
        raise SystemExit("ERRO: o CSV não tem execuções sequenciais.")
    t_seq = resumir([linha["t_total_s"] for linha in seq])
    f = statistics.fmean(linha["t_processamento_s"] / linha["t_total_s"] for linha in seq)

    grupos: dict[tuple, list[dict]] = {}
    for linha in medidas:
        if linha["versao"] == "par":
            grupos.setdefault((linha["modo"], linha["trava"], linha["workers"]), []).append(linha)
    ordem_tipo = {("processos", "fina"): 0, ("threads", "fina"): 1, ("processos", "grossa"): 2}
    configuracoes = []
    for (modo, trava, p), linhas in sorted(grupos.items(), key=lambda kv: (ordem_tipo.get(kv[0][:2], 9), kv[0][2])):
        tempo = resumir([linha["t_total_s"] for linha in linhas])
        speedup = t_seq["media"] / tempo["media"]
        configuracoes.append({
            "nome": nome_da_configuracao(modo, trava, p), "modo": modo, "trava": trava, "workers": p,
            "tempo": tempo, "speedup": speedup, "eficiencia": speedup / p,
            "amdahl": 1 / ((1 - f) + f / p),
            "karp_flatt": (1 / speedup - 1 / p) / (1 - 1 / p) if p > 1 else None,
            "espera_trava_s": media_do_campo(linhas, "espera_trava_s"),
            "inicio_primeira_tarefa_s": media_do_campo(linhas, "inicio_primeira_tarefa_s"),
            "cauda_s": media_do_campo(linhas, "cauda_s"),
            "ocupacao": media_do_campo(linhas, "ocupacao"),
        })
    ref = seq[0]
    return {
        "maquina": {chave: ref[chave] for chave in ("cpu", "nucleos_fisicos", "nucleos_logicos", "ram_gb",
                                                   "sistema", "python", "pillow", "numpy", "maquina")},
        "imagens": int(ref["imagens"]), "impressao_digital": ref["impressao_digital"],
        "f": f, "sequencial": t_seq, "configuracoes": configuracoes,
    }


def escrever_tabela(res: dict, destino: Path) -> str:
    m = res["maquina"]
    s = res["sequencial"]
    linhas = [
        "# Resultados da bateria", "",
        f"Máquina: {m['cpu']} ({m['nucleos_fisicos']} núcleos físicos, {m['nucleos_logicos']} lógicos, "
        f"{virgula(float(m['ram_gb']), 1)} GB de RAM) · {m['sistema']} · Python {m['python']} · Pillow {m['pillow']}", "",
        f"Entrada: {res['imagens']} imagens · impressão digital de todas as execuções: `{res['impressao_digital'][:16]}`", "",
        f"Fração paralelizável estimada: f = {virgula(res['f'], 5)} (T_processamento / T_total da sequencial, "
        f"média de {s['n']} execuções)", "",
        "## Tempos e speedup", "",
        "| Configuração | Tempo total (s) | Speedup | Eficiência | Teto de Amdahl | Karp–Flatt |",
        "|---|---|---|---|---|---|",
        f"| Sequencial | {virgula(s['media'])} ± {virgula(s['desvio'])} (n={s['n']}) | 1,00 | 100% | — | — |",
    ]
    for c in res["configuracoes"]:
        t = c["tempo"]
        kf = virgula(c["karp_flatt"], 4) if c["karp_flatt"] is not None else "—"
        linhas.append(f"| {c['nome']} | {virgula(t['media'])} ± {virgula(t['desvio'])} (n={t['n']}) | "
                      f"{virgula(c['speedup'])} | {virgula(100 * c['eficiencia'], 1)}% | {virgula(c['amdahl'])} | {kf} |")
    linhas += [
        "", "## Onde está a diferença para o teto", "",
        "| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |",
        "|---|---|---|---|---|",
    ]
    for c in res["configuracoes"]:
        linhas.append(f"| {c['nome']} | {virgula(1000 * c['espera_trava_s'], 1)} | "
                      f"{virgula(c['inicio_primeira_tarefa_s'])} | {virgula(c['cauda_s'])} | "
                      f"{virgula(100 * c['ocupacao'], 1)}% |")
    texto = "\n".join(linhas) + "\n"
    destino.write_text(texto, encoding="utf-8")
    return texto


def preparar_estilo() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
    })


def estilizar(fig, ax) -> None:
    fig.patch.set_facecolor(SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(EIXO)
        ax.spines[lado].set_linewidth(1)
    ax.tick_params(colors=EIXO, labelcolor=TINTA_SECUNDARIA, labelsize=9)
    ax.grid(True, color=GRADE, linewidth=0.8, linestyle="-")
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(TINTA_SECUNDARIA)
    ax.yaxis.label.set_color(TINTA_SECUNDARIA)
    formato = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    ax.xaxis.set_major_formatter(formato)
    ax.yaxis.set_major_formatter(formato)


def titulo(ax, principal: str, subtitulo: str) -> None:
    ax.set_title(principal, loc="left", color=TINTA, fontweight="bold", pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, color=TINTA_SECUNDARIA, fontsize=9, va="bottom")


def grafico_speedup(res: dict, destino: Path) -> None:
    processos = [c for c in res["configuracoes"] if c["modo"] == "processos" and c["trava"] == "fina"]
    if not processos:
        return
    f = res["f"]
    ps = [1] + [c["workers"] for c in processos]
    medido = [1.0] + [c["speedup"] for c in processos]
    xs = [1 + i * (ps[-1] - 1) / 200 for i in range(201)]
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=200)
    estilizar(fig, ax)
    ax.plot(xs, xs, color=TINTA_FRACA, linewidth=1.5, label="Ideal (S = p)")
    ax.plot(xs, [1 / ((1 - f) + f / x) for x in xs], color=LARANJA, linewidth=2,
            label=f"Teto de Amdahl (f = {virgula(f, 4)})")
    ax.plot(ps, medido, color=AZUL, linewidth=2, marker="o", markersize=8, markerfacecolor=AZUL,
            markeredgecolor=SUPERFICIE, markeredgewidth=2, label="Medido (processos)", zorder=3)
    ax.annotate(f"{virgula(medido[-1])}x", (ps[-1], medido[-1]), xytext=(8, -4), textcoords="offset points",
                color=TINTA_SECUNDARIA, fontsize=10)
    ax.set_xticks(ps)
    ax.set_xlim(0.5, ps[-1] + 1.5)
    ax.set_ylim(0, ps[-1] + 1)
    ax.set_xlabel("Número de processos (p)")
    ax.set_ylabel("Speedup (T_seq / T_par)")
    ax.legend(frameon=False, loc="upper left", labelcolor=TINTA_SECUNDARIA, fontsize=9)
    m = res["maquina"]
    titulo(ax, "Speedup medido x teto de Amdahl",
           f"{res['imagens']} imagens · {m['nucleos_fisicos']} núcleos físicos / {m['nucleos_logicos']} lógicos · "
           f"média de {res['sequencial']['n']} execuções")
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def grafico_tempos(res: dict, destino: Path) -> None:
    nomes = ["Sequencial"] + [c["nome"] for c in res["configuracoes"]]
    medias = [res["sequencial"]["media"]] + [c["tempo"]["media"] for c in res["configuracoes"]]
    desvios = [res["sequencial"]["desvio"]] + [c["tempo"]["desvio"] for c in res["configuracoes"]]
    posicoes = list(range(len(nomes)))[::-1]  # o primeiro item fica em cima
    fig, ax = plt.subplots(figsize=(7.5, 0.42 * len(nomes) + 1.3), dpi=200)
    estilizar(fig, ax)
    ax.grid(False, axis="y")
    ax.barh(posicoes, medias, height=0.5, color=AZUL, xerr=desvios,
            error_kw={"ecolor": TINTA_SECUNDARIA, "elinewidth": 1, "capsize": 3})
    folga = max(medias) * 0.015
    for y, media, desvio in zip(posicoes, medias, desvios):
        ax.text(media + desvio + folga, y, f"{virgula(media, 1)} s", va="center", color=TINTA_SECUNDARIA, fontsize=9)
    ax.set_yticks(posicoes)
    ax.set_yticklabels(nomes)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(m + d for m, d in zip(medias, desvios)) * 1.15)
    ax.set_xlabel("Tempo total (s), média ± desvio-padrão")
    titulo(ax, "Tempo total por configuração", f"{res['imagens']} imagens · mesma máquina e mesma entrada")
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Analisa a bateria de medições")
    ap.add_argument("--csv", type=Path, default=Path("resultados") / "bateria.csv")
    ap.add_argument("--saida", type=Path, default=Path("resultados"))
    args = ap.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)

    resultados = analisar(carregar(args.csv))
    print(escrever_tabela(resultados, args.saida / "tabela_tempos.md"))
    (args.saida / "resumo.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    preparar_estilo()
    grafico_speedup(resultados, args.saida / "speedup.png")
    grafico_tempos(resultados, args.saida / "tempos.png")
    print(f"Arquivos gravados em '{args.saida}': tabela_tempos.md, resumo.json, speedup.png, tempos.png")


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- `carregar()` recusa um CSV que misture máquinas ou números de imagens diferentes: o speedup só vale com
  sequencial e paralela na mesma máquina e com a mesma entrada. Também recusa impressões digitais diferentes.
- `analisar()` calcula f como a média de T_processamento / T_total das execuções sequenciais e aplica as
  fórmulas da seção 5.1 a cada configuração paralela.
- Os gráficos usam uma paleta testada para daltonismo (azul para o medido, laranja para Amdahl e cinza para o
  ideal), com os números em formato brasileiro (vírgula decimal). O `matplotlib.use("Agg")` gera os PNG sem
  abrir janela.

**Teste com o CSV de exemplo.** Antes de existir uma bateria de verdade, salve o conteúdo abaixo como
`exemplo_bateria.csv` na raiz do projeto (é a bateria real do protótipo, com 60 imagens e 2 núcleos):

```text
data_hora,rodada,aquecimento,versao,modo,trava,workers,chunksize,imagens,pixels,t_total_s,t_preparo_s,t_processamento_s,t_final_s,espera_trava_s,dentro_trava_s,inicio_primeira_tarefa_s,cauda_s,ocupacao,fluxos_usados,impressao_digital,cpu,nucleos_fisicos,nucleos_logicos,ram_gb,sistema,python,pillow,numpy,maquina
2026-09-19T11:12:44,0,1,seq,,,1,,60,15728640,4.293008887999804,0.004244122999807587,4.288015601000097,0.000749163999898883,0.0,0.0,,,,1,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:12:50,1,0,seq,,,1,,60,15728640,4.277965622000011,0.004486177999979191,4.272761242999877,0.0007182010001542949,0.0,0.0,,,,1,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:12:55,1,0,par,processos,fina,2,4,60,15728640,2.501536764000093,0.0045297870001377305,2.4961442499998157,0.0008627270001397846,0.000146265,0.001258753,0.17582893899998453,0.2175347889999557,0.9482227873899213,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:12:59,2,0,seq,,,1,,60,15728640,4.355141021999998,0.00447902900009467,4.3498952219999865,0.0007667709999168437,0.0,0.0,,,,1,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:04,2,0,par,processos,fina,2,4,60,15728640,2.441878481999993,0.004471443000056752,2.436515806999978,0.0008912319999581086,0.000146165,0.001174136,0.17324513599987768,0.14066593600000488,0.9649251542404048,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:08,3,0,seq,,,1,,60,15728640,4.266817605999677,0.004169803999957367,4.261925450000035,0.0007223519996841787,0.0,0.0,,,,1,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:13,3,0,par,processos,fina,2,4,60,15728640,2.4780423469997004,0.004605971999808389,2.4725108860002365,0.0009254889996554994,0.000138713,0.001107537,0.17785577499989813,0.22127513400027965,0.9469548967220232,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:17,1,0,par,threads,fina,2,4,60,15728640,3.6547458979998737,0.004574780999973882,3.6493234159997883,0.0008477010001115559,0.000107752,0.001406298,0.014039746999969793,0.26128574899985324,0.9638628367857269,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:22,1,0,par,processos,grossa,2,4,60,15728640,4.509549826999773,0.004458815999896615,4.504163085000073,0.0009279259998038469,4.027272991,4.306465662,0.16989350299991202,0.2651045409998005,0.9671260034370617,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:27,2,0,par,threads,fina,2,4,60,15728640,3.6535764870000094,0.004939560999901005,3.6478219770001488,0.0008149489999595971,0.000101524,0.001364905,0.0050670149998950365,0.2667442930001016,0.9632667958523217,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
2026-09-19T11:13:32,2,0,par,processos,grossa,2,4,60,15728640,4.49869113800014,0.005325308999999834,4.492371427999842,0.0009944010002982395,4.012750362,4.298368612,0.16840599299985115,0.26910803000009764,0.9663625903755819,2,3ee171606c532d892f1b1fd1a2797f84a3ef5793e7488fa15635fc927a3b625d,Intel(R) Xeon(R) Processor @ 2.80GHz,2,2,7.8,Linux-6.18.44-fc-v37-x86_64-with-glibc2.39,3.13.7,12.3.0,2.4.6,vm
```

E rode `python analise.py --csv exemplo_bateria.csv --saida teste_analise`. A saída esperada é:

```text
# Resultados da bateria

Máquina: Intel(R) Xeon(R) Processor @ 2.80GHz (2 núcleos físicos, 2 lógicos, 7,8 GB de RAM) · Linux-6.18.44-fc-v37-x86_64-with-glibc2.39 · Python 3.13.7 · Pillow 12.3.0

Entrada: 60 imagens · impressão digital de todas as execuções: `3ee171606c532d89`

Fração paralelizável estimada: f = 0,99881 (T_processamento / T_total da sequencial, média de 3 execuções)

## Tempos e speedup

| Configuração | Tempo total (s) | Speedup | Eficiência | Teto de Amdahl | Karp–Flatt |
|---|---|---|---|---|---|
| Sequencial | 4,30 ± 0,05 (n=3) | 1,00 | 100% | — | — |
| Processos, p = 2 | 2,47 ± 0,03 (n=3) | 1,74 | 86,9% | 2,00 | 0,1506 |
| Threads, p = 2 | 3,65 ± 0,00 (n=2) | 1,18 | 58,8% | 2,00 | 0,6996 |
| Trava grossa, p = 2 | 4,50 ± 0,01 (n=2) | 0,95 | 47,7% | 2,00 | 1,0950 |

## Onde está a diferença para o teto

| Configuração | Espera pela trava (ms) | Início da 1ª tarefa (s) | Cauda (s) | Ocupação |
|---|---|---|---|---|
| Processos, p = 2 | 0,1 | 0,18 | 0,19 | 95,3% |
| Threads, p = 2 | 0,1 | 0,01 | 0,26 | 96,4% |
| Trava grossa, p = 2 | 4020,0 | 0,17 | 0,27 | 96,7% |

Arquivos gravados em 'teste_analise': tabela_tempos.md, resumo.json, speedup.png, tempos.png
```

Abra `teste_analise\speedup.png` e `teste_analise\tempos.png` e confira que aparecem os dois gráficos. Depois
apague os arquivos de teste: `Remove-Item -Recurse -Force teste_analise, exemplo_bateria.csv`. Eles não vão
para o Git.

### 5.4 Bateria pequena no seu PC (depois do M2)

Serve para achar problemas antes da bateria oficial. Não use o arquivo oficial nem a pasta `resultados\`:

```powershell
python bench.py --limite 60 --repeticoes 2 --com-threads --com-trava-grossa --repeticoes-extras 1 --pausa 1 --csv teste_bench.csv
python analise.py --csv teste_bench.csv --saida teste_analise
Remove-Item -Recurse -Force teste_analise, teste_bench.csv
```

### 5.5 A bateria oficial (depois do M3, na máquina da demo)

**Antes de rodar**, com o dono da máquina e a Pessoa 3 (seção 5.2 do documento da P3):

- [ ] Código congelado (tag `v0.9`) e `git pull` feito na máquina da demo.
- [ ] N anunciado pela Pessoa 1 (calibração feita **nesta** máquina).
- [ ] Na tomada, modo de energia "Melhor desempenho", atualizações pausadas, "Não incomodar" ligado, navegador e
  sincronizações fechados.
- [ ] Configurações → Sistema → Energia e bateria (no Windows 10, "Energia e suspensão") → tela e suspensão na
  tomada: **Nunca**, para a máquina não dormir no meio da bateria.
- [ ] `python aquecer_cache.py dados\val2017`.

**Rodar:**

```powershell
python bench.py --limite <N> --com-threads --com-trava-grossa --somente-plano    # confira o plano
python bench.py --limite <N> --com-threads --com-trava-grossa                    # a bateria (~1h15)
python analise.py
```

A duração depende da máquina: numa de 8 núcleos físicos com a sequencial em ~4 minutos, fica na ordem de 1h15.
O próprio `bench.py` imprime uma estimativa depois da primeira execução. Durante a bateria, **ninguém usa a
máquina**. Se ela for interrompida, o CSV guarda o que já rodou: rode o mesmo comando com `--continuar` (uma
nova execução de aquecimento é feita e descartada).

**Depois:** `git add resultados` → `git commit -m "P4: bateria oficial"` → `git push`. Mande ao grupo o p de
menor tempo (para o `$P` do `demo.ps1`) e a tabela.

### 5.6 Como interpretar os resultados

Leia a `resultados\tabela_tempos.md` nesta ordem (os números abaixo são do exemplo da seção 5.3):

1. **Desvio-padrão pequeno em relação à média?** Ex.: 4,30 ± 0,05 s (~1%). Se passar de ~5%, a máquina não
   estava parada: descubra o motivo e rode de novo.
2. **Speedup e eficiência dos processos.** Ex.: 1,74× com 2 processos, eficiência de 86,9%. Espere eficiência
   caindo quando p cresce, principalmente acima do número de núcleos físicos.
3. **Teto de Amdahl.** Ex.: f = 0,99881, teto de 2,00 com 2 processos. Diga quanto do teto foi alcançado:
   1,74 / 2,00 = 87%.
4. **Karp–Flatt.** Ex.: 0,15 com p = 2. Com vários valores de p, diga se e(p) cresce (sobrecarga) ou fica
   constante (parte serial fixa).
5. **Segunda tabela (onde está a diferença).** Ex.: início da 1ª tarefa de 0,18 s e cauda de 0,19 s numa
   execução de 2,47 s: juntos, ~15% do tempo paralelo, o que explica boa parte da diferença para o ideal. Espera
   pela trava de 0,1 ms: a seção crítica não limitou o ganho.
6. **Experimentos.** Threads: 1,18× (o GIL). Trava grossa: 0,95×, com 4,0 s de espera pela trava numa execução
   de 4,5 s: correto, mas serial.
7. **Hardware.** Se o speedup para de crescer depois do número de núcleos físicos, é o Hyper-Threading. Se ficar
   bem abaixo do teto mesmo com p pequeno, cite o turbo.

## 6. Testes de aceitação (definição de pronto)

**6.1 `bench.py` sem rodar nada:** `python bench.py --limite 100 --somente-plano` lista o plano (aquecimento +
5 rodadas de sequencial e paralelas) e termina sem criar CSV.

**6.2 `analise.py`:** com o CSV de exemplo (5.3), a saída bate com a da seção 5.3 e são gerados os 4 arquivos
em `teste_analise\`.

**6.3 Bateria pequena (5.4):** termina com `Bateria concluída`, sem erro de impressão digital, e o `analise.py`
gera as tabelas.

**6.4 Bateria oficial:**

- [ ] `resultados\bateria.csv` com todas as execuções do plano e uma única impressão digital.
- [ ] `resultados\tabela_tempos.md`, `resumo.json`, `speedup.png` e `tempos.png` gerados e no Git.
- [ ] Desvio-padrão da sequencial abaixo de ~5% da média.

## 7. O relatório: sua parte e a montagem do PDF

### 7.1 Esqueleto completo (até 6 páginas)

| Seção | Quem | Páginas | Tem que conter (itens cobrados pela lauda em negrito) |
|---|---|---|---|
| Cabeçalho | P4 | — | Título, integrantes, disciplina, professor, data, **link do repositório** |
| 1. Problema e dados | P1 | 0,75 | **O problema**; dataset; unidade de trabalho; volume; verificação |
| 2. Estratégia de paralelização | P2 | 1 | **Estratégia**; **processos × threads justificado pela natureza do trabalho**, com números |
| 3. Seção crítica e primitiva | P2 | 1 | **A seção crítica no código (arquivo e linhas) e a primitiva**; teste de corrida; resultado estável |
| 4. Recursos provisionados | P3 | 0,75 | **Recursos**: máquina; **o que fica em cada porta e a origem de cada regra** |
| 5. Medição e speedup | P4 | 1,5 | **Tempos medidos** (mais de uma vez, mesma máquina e entrada); **speedup**; **teto de Amdahl** |
| 6. O que limitou o ganho | P4 | 0,75 | **O que limitou**: comunicação, divisão desigual, espera na seção crítica, hardware |
| **Total** | | **5,75** | |

### 7.2 Sua seção 5 (≈ 1,5 página)

Escreva em `relatorio\secao5_medicao.md`, trocando o que está entre `[[ ]]` pelos números da
`resultados\tabela_tempos.md`:

> **5. Medição e speedup**
>
> **Protocolo.** Todas as medições foram feitas na máquina da seção 4, com a mesma entrada ([[N]] imagens) e o
> mesmo código (tag `v0.9`). A máquina ficou na tomada, em modo de alto desempenho e sem outros programas
> abertos. O programa `bench.py` executou uma rodada de aquecimento, descartada, e depois [[5]] rodadas, cada
> uma com a versão sequencial seguida das paralelas com p = [[2, 4, 8, ...]] processos. Cada execução rodou como
> um processo separado, com a pasta de saída limpa antes, fora da medição. Todas as [[n]] execuções produziram a
> mesma impressão digital.
>
> **Tempos, speedup e eficiência.** [[colar a primeira tabela da tabela_tempos.md]]
>
> **Teto de Amdahl.** A versão sequencial mede separadamente o preparo, o processamento e a etapa final. A fração
> paralelizável estimada é f = T_processamento / T_total = [[f]] (média de [[5]] execuções). Com [[p]]
> processos, o teto de Amdahl é [[S_max]] e o speedup medido foi [[S]]: [[S / S_max × 100]]% do teto.
>
> [[inserir resultados/speedup.png, largura ~14 cm, legenda: "Speedup medido x teto de Amdahl x ideal"]]

### 7.3 Sua seção 6 (≈ ¾ de página)

> **6. O que limitou o ganho**
>
> Como a fração paralelizável é muito próxima de 1, o teto de Amdahl fica perto de p, e a diferença para o
> speedup medido vem de sobrecarga e de hardware, e não de uma parte serial do programa. A métrica de Karp–Flatt
> mostra isso: e(p) = [[valores]] para p = [[valores]], [[crescendo/constante]] com p.
>
> [[colar a segunda tabela da tabela_tempos.md]]
>
> - **Comunicação e criação dos processos:** a primeira tarefa só começa [[x]] s depois do início do
>   processamento, tempo gasto criando os processos (no Windows, cada um é um novo interpretador que importa
>   Pillow e NumPy). Pelo canal entre processos passam apenas o caminho de cada imagem e o SHA-256 de volta.
> - **Divisão desigual do trabalho:** no fim do lote, os processos terminam em momentos diferentes; a cauda foi
>   de [[y]] s. O `chunksize` de 4 e o `imap_unordered` mantêm essa cauda pequena.
> - **Espera na seção crítica:** [[z]] ms no total, desprezível. A trava cobre só a soma do histograma. Com a
>   trava em volta do processamento inteiro, a espera sobe para [[w]] s e o speedup cai para [[S_grossa]].
> - **Hardware:** [[escolha o que se aplica: acima de [[físicos]] processos o ganho diminui porque os núcleos
>   lógicos dividem um núcleo físico; o turbo favorece a execução sequencial; núcleos de eficiência]].
>
> **Conclusão.** [[Uma frase: o speedup alcançado, a fração do teto, e o principal limitador.]]

### 7.4 Montagem e entrega do PDF

1. Crie um documento compartilhado (Google Docs ou Word online) com o esqueleto da 7.1 e cole as seções que os
   outros entregarem até domingo, 14:00.
2. Formato: margens de 2 cm, fonte de 11 pt, espaçamento simples. Figuras: `speedup.png` (obrigatória) e
   `tempos.png` (se couber). Tabelas: as duas da `tabela_tempos.md`. Código: o trecho da `mesclar()` com os
   números de linha (P2).
3. Confira que tem **no máximo 6 páginas** e que todos os itens em negrito da 7.1 aparecem.
4. Exporte em PDF (Arquivo → Fazer download → PDF, ou Salvar como PDF), salve como
   `relatorio\relatorio_etapa1.pdf` e suba no Git.
5. **Segunda, até 12:00:** poste no ambiente virtual o PDF e o link do repositório. A lauda exige que os dois
   estejam lá antes do início do encontro.

## 8. Sua parte da apresentação (6:00–10:00)

**Slides (3):** "A execução" (o que observar: tempo da sequencial, tempo da paralela, núcleos, verificação); "O
ganho" (`speedup.png` + a linha "speedup [[S]] com [[p]] processos = [[x]]% do teto de Amdahl ([[S_max]])");
"O que limitou" (3 tópicos com números da segunda tabela).

**Roteiro falado:**

- (6:00) Aponte o terminal 1: "A sequencial que disparamos no começo terminou: [[T_seq]] segundos para [[N]]
  imagens, num núcleo."
- (6:20) **Ação ao vivo**, no terminal 2: `.\demo.ps1 -Etapa par`. Mostre o Gerenciador de Tarefas: "Agora a
  versão paralela, com [[p]] processos: todos os núcleos em 100%. O progresso vem do processo principal."
- (7:30) Quando terminar: "[[T_par]] segundos." **Ação ao vivo:** `.\demo.ps1 -Etapa verificar`. "Mesmas
  imagens, mesmo histograma, mesma impressão digital: IDÊNTICO. E a razão entre os tempos, o speedup desta
  execução ao vivo, é [[x]]."
- (8:30) "Esses números batem com a bateria de medições: [[5]] repetições de cada configuração."
- (9:00) Slide "O ganho": "Com [[p]] processos, o speedup médio foi [[S]]. A fração paralelizável medida é
  [[f]], então o teto de Amdahl é [[S_max]]: chegamos a [[x]]% dele."
- (9:30) Slide "O que limitou": "A espera na trava foi de [[z]] ms, desprezível. O que limitou foi a criação dos
  processos ([[x]] s), a cauda no fim do lote ([[y]] s) e o hardware: [[Hyper-Threading / turbo]]."

A paralela leva T_seq ÷ speedup: com a sequencial em ~4 minutos e speedup entre 4 e 6, algo entre 40 s e
1 minuto. Confira no ensaio. Se sobrar tempo depois dela, não enrole: vá para o "ganho".

## 9. Arguição

### 9.1 O que você precisa dominar na sua parte

- As fórmulas de speedup, eficiência, Amdahl e Karp–Flatt, e como cada número da tabela foi calculado.
- Por que f fica tão perto de 1 e o que isso significa para o teto.
- A diferença entre Amdahl (problema fixo) e Gustafson (problema cresce com p).
- Por que medir mais de uma vez, descartar o aquecimento e alternar seq e par.
- O que significa cada coluna da segunda tabela e qual delas explica o quê.
- Por que o speedup não passa do número de núcleos físicos (Hyper-Threading) e por que o turbo favorece a
  sequencial.
- Por que o speedup ao vivo pode diferir um pouco do da bateria (os testes da parte 2 rodaram ao mesmo tempo que
  a sequencial).

### 9.2 Banco de perguntas de todas as partes (igual nos 4 documentos)

Cada um responde sobre uma parte **que não apresentou**, então estude todas. As respostas são curtas de
propósito; troque os números do protótipo pelos da bateria oficial (`resultados\tabela_tempos.md`).

**Parte 1: o problema**

1. *Por que o problema se divide bem?* Cada imagem é processada sem depender de nenhuma outra, e as tarefas não
   trocam dados entre si. O único ponto em comum é a soma do histograma de cada imagem no histograma global, que
   é curta e protegida pela trava.
2. *Qual é a unidade de trabalho e por que esse tamanho?* Uma imagem, dezenas de milissegundos de CPU. É grande o
   bastante para o custo de enviar a tarefa a um processo (microssegundos) ser desprezível, e pequena o bastante
   para milhares de tarefas se equilibrarem entre os processos.
3. *Como vocês provam que a paralela produz o mesmo que a sequencial?* As duas chamam a mesma
   `processar_imagem()`. O `verificar.py` compara o SHA-256 de cada imagem gerada, o histograma global e os
   contadores. Se tudo bate, a impressão digital do lote também é igual.
4. *Por que o estado global só tem inteiros?* Porque a soma de floats depende da ordem:
   `(0.1 + 0.2) + 0.3` dá `0.6000000000000001`, mas `0.1 + (0.2 + 0.3)` dá `0.6`. Em paralelo a ordem de
   chegada muda a cada execução. Com inteiros, a soma é exata em qualquer ordem, e média e desvio são calculados
   uma única vez, no final.
5. *Qual etapa é a mais cara e por quê?* O filtro de mediana 3×3, cerca de 2/3 do tempo de cada imagem no
   protótipo: para cada pixel e cada canal ele ordena 9 valores.

**Parte 2: a seção crítica**

6. *Qual é a seção crítica e qual primitiva a protege?* As linhas dentro do `with _trava:` na função `mesclar()`
   do `estado.py`, que somam o histograma da imagem e os contadores no estado global. A primitiva é um
   `multiprocessing.Lock`.
7. *O que acontece sem a trava?* O `+=` é ler, somar e escrever. Dois processos leem o mesmo valor antigo e um
   sobrescreve o resultado do outro: é a atualização perdida. No `teste_corrida.py`, sem a trava o resultado sai
   errado e diferente a cada rodada; com a trava, sempre exato.
8. *Se tirarem a trava do programa, o resultado sai errado?* Quase nunca, porque a seção crítica dura
   microssegundos a cada dezenas de milissegundos. É isso que torna a corrida perigosa: rodar e dar certo não
   prova que ela não existe. Por isso a demonstração usa um teste de estresse.
9. *Por que não travar o laço inteiro?* Fica correto, mas serial: os processos passam o tempo esperando a trava.
   A bateria mede isso no experimento "trava grossa", que fica perto de 1× (às vezes pior que a sequencial).
10. *Por que Lock e não semáforo ou monitor?* Há um único recurso e ele exige exclusão mútua, que é o caso do
    Lock (equivale a um semáforo binário). Um semáforo com contador maior que 1 deixaria vários processos
    escreverem juntos. Um monitor (trava + variável de condição) serviria se alguém precisasse esperar uma
    condição, e isso não acontece aqui.
11. *`multiprocessing.Value` já tem lock. `v.value += 1` é seguro?* Não. O lock interno protege a leitura e a
    escrita separadamente, não o conjunto. No protótipo, 4 processos × 20.000 incrementos terminaram com 28 a 37
    mil em vez de 80.000. O certo é `with v.get_lock(): v.value += 1`. Por isso usamos memória sem trava própria
    (`RawArray`) e uma trava explícita.
12. *Pode dar deadlock?* Não. Há uma única trava, sempre usada com `with` (é liberada até se der erro) e nunca
    adquirida dentro de outra, então não existe espera circular.
13. *Como a trava chega aos processos filhos?* Pelo `initializer` do `Pool`, na criação de cada processo. No
    Windows os processos nascem com `spawn` e não herdam variáveis do pai; passar a trava como argumento de
    tarefa dá `RuntimeError: Lock objects should only be shared between processes through inheritance`.

**Parte 3: os recursos**

14. *Quais portas estão abertas e para quem?* A 8000 (o serviço: a página de resultados) para qualquer origem;
    a 22 (administração por SSH) só para o IP da equipe. Todo o resto é bloqueado por padrão.
15. *Por que a porta administrativa não pode ficar aberta para qualquer origem?* Porque fica exposta a tentativas
    de senha e a falhas do serviço de administração. O princípio é o menor privilégio: só quem administra
    alcança a porta de administração. A lauda zera o critério nesse caso.
16. *Quantos núcleos físicos e lógicos a máquina tem, e por que isso importa?* Com Hyper-Threading, dois fluxos
    dividem as unidades de execução de um núcleo físico. Acima do número de núcleos físicos, o ganho cresce bem
    menos que o número de processos.
17. *Por que a máquina precisa estar na tomada e em modo de desempenho?* Na bateria, o Windows reduz o clock do
    processador. Isso muda os tempos entre uma execução e outra e estraga a comparação.

**Parte 4: a execução**

18. *Por que a sequencial começou antes?* Ela leva ~4 minutos e a fatia da execução tem 3. Rodou ao vivo, na
    mesma máquina, com a mesma entrada, enquanto as partes 1 a 3 eram apresentadas.
19. *O que é `chunksize` e por que `imap_unordered`?* `chunksize=4` é quantas imagens vão em cada envio a um
    processo (menos idas e vindas pelo canal entre processos). `imap_unordered` entrega os resultados na ordem
    em que terminam, então quem fica livre pega mais trabalho: é o balanceamento dinâmico.
20. *Por que a primeira execução é mais lenta?* Por causa do cache de disco: na primeira, os arquivos vêm do
    disco; depois, da memória. Por isso a bateria descarta uma execução de aquecimento e a demo roda o
    `aquecer_cache.py` antes.
21. *Por que usar `spawn` também fora do Windows?* Para o comportamento ser o mesmo em qualquer máquina, que é o
    comportamento do Windows onde o projeto roda.

**Parte 5: o ganho**

22. *Como vocês estimaram a fração paralelizável e o teto?* f = T_processamento / T_total da sequencial (o
    programa mede as três fases). Teto de Amdahl: S_max(p) = 1 / ((1 − f) + f / p).
23. *Por que o medido ficou abaixo do teto?* Criação dos processos (coluna "início da 1ª tarefa"), cauda no fim
    do lote (coluna "cauda"), espera na trava (medida, quase zero) e hardware: turbo (um núcleo sozinho roda em
    clock mais alto do que todos juntos), Hyper-Threading, núcleos de desempenho e de eficiência, memória. A
    Karp–Flatt mostra se a perda cresce com p.
24. *Se dobrar o número de imagens, o speedup muda?* Sobe um pouco: os custos fixos, como criar os processos,
    pesam menos num lote maior. É a ideia da lei de Gustafson.
25. *E com threads? E com o Python sem GIL?* As threads ficaram em ~1,2×, contra quase o dobro com processos,
    porque a mediana segura o GIL. O Python sem GIL (PEP 779, suportado oficialmente desde o 3.14) poderia
    escalar com threads, mas não é a instalação padrão e depende de as bibliotecas em C serem compatíveis.

## 10. Problemas comuns e soluções

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ERRO: 'resultados\bateria.csv' já existe` | Já rodou uma bateria | Para recomeçar, apague o arquivo; para completar uma interrompida, use `--continuar` |
| `ERRO: impressão digital diferente das execuções anteriores` | Erro de sincronização ou alguém mudou o código ou os dados no meio | Pare, avise a Pessoa 2, confira `git status`; não use essa bateria |
| `ERRO: o CSV mistura máquinas ou entradas diferentes` | CSV com linhas de outra máquina ou de outro `--limite` | Use um CSV por máquina e por N; a bateria oficial é só da máquina da demo |
| Desvio-padrão alto (> ~5%) | Máquina em uso, na bateria ou com antivírus analisando os arquivos | Refaça a preparação da 5.5 e rode de novo |
| Paralela com p maior fica **mais lenta** | Acima do número de núcleos físicos, ou superaquecimento | É um resultado válido: explique com Hyper-Threading ou temperatura na seção 6 |
| `analise.py` não gera gráfico | matplotlib não instalado | `pip install -r requirements.txt` com o ambiente virtual ativado |
| A bateria vai demorar demais | Muitos valores de p | Use `--workers` com menos valores (ex.: `--workers 2 4 8`); mantenha as 5 repetições |
| Números estranhos depois de abrir o CSV no Excel | O Excel troca ponto por vírgula e reformata ao salvar | Nunca salve o `bateria.csv` pelo Excel; se precisar olhar, abra uma cópia |
