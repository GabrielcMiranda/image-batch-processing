# Pessoa 1: problema, dados e versão sequencial

**Projeto:** Processamento de imagens em lote · Sistemas Distribuídos e Paralelos · Projeto de Solução Distribuída, Etapa 1

**Seus arquivos:** `comum.py`, `pipeline.py`, `baixar_dados.py`, `calibrar.py`, `seq.py`, `verificar.py`

**Sua prioridade:** subir `comum.py` e `pipeline.py` no marco M1 (sábado, 15:30). A Pessoa 2 não consegue
testar a versão paralela sem eles.

## Como usar este documento

**Para você (Pessoa 1):** este arquivo tem tudo o que você precisa: o contexto do trabalho (seção 1), as
regras e contratos do grupo (seção 2), a sua parte (seções 3 a 10) e o código de referência de cada arquivo
seu, já testado no Python 3.12, 3.13 e 3.14. Leia as seções 1 a 4 antes de abrir a IA e depois trabalhe na
ordem da seção 4. Os outros três integrantes têm documentos com as mesmas seções 1 e 2, então todo mundo parte
das mesmas regras.

**Para a IA:** abra uma conversa nova, anexe (ou cole) este arquivo inteiro e envie a mensagem abaixo.

> Você vai me ajudar a implementar a minha parte de um projeto em grupo. O documento anexo é a especificação e
> deve ser seguido à risca:
> 1. Sou a Pessoa 1. Implemente apenas os meus arquivos: `comum.py`, `pipeline.py`, `baixar_dados.py`, `calibrar.py`, `seq.py` e `verificar.py`. Não crie nem edite nenhum outro arquivo.
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

Você cuida do que acontece com cada imagem (a unidade de trabalho), da versão sequencial, da prova de que a
paralela produz o mesmo resultado, dos dados de entrada e da calibração do volume. A versão paralela da Pessoa 2
importa as suas funções, então elas são a base do projeto inteiro.

| | |
|---|---|
| Seus arquivos | `comum.py`, `pipeline.py`, `baixar_dados.py`, `calibrar.py`, `seq.py`, `verificar.py` |
| Relatório | Seção 1, "Problema e dados" (≈ ¾ de página) |
| Apresentação | Parte 1, "O problema e por que ele se divide" (0:00–2:00), e disparar a sequencial aos ~0:20 |
| Critério que você defende | Definição do problema (avaliada dentro da apresentação) |
| Você depende de | Ninguém: você é o primeiro da fila |
| Dependem de você | P2 precisa de `comum.py` e `pipeline.py` (M1); todos precisam de `seq.py` e `verificar.py` (M2); P3 e P4 precisam do N calibrado (M3) |

## 4. Etapas de implementação

1. [ ] Preparar o PC (seção 2.1, passos 1 a 4) e começar o download do COCO pelo navegador (passo 5).
2. [ ] Criar `comum.py` (5.1) e `pipeline.py` (5.2), rodar o teste 6.1, fazer `git push` e avisar o grupo.
   **Marco M1.**
3. [ ] Criar `baixar_dados.py` (5.3), rodar e conferir as 5.000 imagens (teste 6.2), fazer `git push`.
4. [ ] Criar `seq.py` (5.4), rodar o teste 6.3, fazer `git push`.
5. [ ] Criar `verificar.py` (5.5), rodar o teste 6.4, fazer `git push`. Quando o `par.py` da Pessoa 2 chegar,
   rodar o teste de fumaça (seção 2.6, passo 2). **Marco M2.**
6. [ ] Criar `calibrar.py` (5.6), rodar **na máquina da demo** e anunciar o N no grupo: a P3 coloca no
   `demo.ps1` e a P4 usa no `bench.py`. Confirmar com uma sequencial completa (teste 6.5). **Marco M3.**
7. [ ] Escolher 4 pares antes/depois para o slide (seção 8).
8. [ ] Escrever a seção 1 do relatório (seção 7) e entregar à Pessoa 4 até domingo, 14:00.
9. [ ] Fazer os slides da parte 1 e entregar à Pessoa 3 até domingo, 14:00.
10. [ ] Estudar o banco de perguntas (seção 9) e participar do ensino cruzado e dos dois ensaios.

## 5. Como implementar

Crie cada arquivo na raiz do projeto (`C:\projetos\lote-imagens\`) com **exatamente** o código de referência.
Ele foi testado no Python 3.12, 3.13 e 3.14 com as bibliotecas do `requirements.txt`. Depois de cada arquivo,
rode o teste correspondente da seção 6 antes de seguir.

### 5.1 `comum.py`: funções compartilhadas por seq.py e par.py

**Para que serve.** As duas versões precisam gravar os resultados exatamente no mesmo formato, senão a
verificação não funciona. Por isso tudo o que é comum às duas fica aqui: listar as imagens, criar as pastas,
gravar manifesto e estatísticas, calcular a impressão digital, descrever a máquina e imprimir o resumo.

**O que não pode mudar:** nomes e parâmetros das funções (a Pessoa 2 importa várias delas); o formato do
manifesto (`nome sha256`, ordem alfabética, quebra de linha no fim); a fórmula da impressão digital; os campos
do `estatisticas.json`; o `encoding="utf-8"` em toda leitura e gravação.

```python
"""Constantes e funções usadas tanto pela versão sequencial (seq.py) quanto pela paralela (par.py).

Dono: Pessoa 1. Outros arquivos dependem destes nomes e formatos: não mude sem avisar o grupo.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime
from pathlib import Path

ENTRADA_PADRAO = Path("dados") / "val2017"
EXTENSOES_ACEITAS = (".jpg", ".jpeg")
N_BINS = 768  # histograma RGB: 256 níveis x 3 canais (R, G, B)


def listar_imagens(entrada: Path, limite: int | None) -> list[Path]:
    """Lista as imagens da pasta em ordem alfabética do nome (ordem fixa = mesma entrada sempre)."""
    entrada = Path(entrada)
    if not entrada.is_dir():
        raise SystemExit(f"ERRO: a pasta de entrada '{entrada}' não existe. Baixe os dados com: python baixar_dados.py")
    imagens = sorted(
        (p for p in entrada.iterdir() if p.is_file() and p.suffix.lower() in EXTENSOES_ACEITAS),
        key=lambda p: p.name,
    )
    if limite is not None:
        if limite <= 0:
            raise SystemExit("ERRO: --limite precisa ser maior que zero.")
        imagens = imagens[:limite]
    if not imagens:
        raise SystemExit(f"ERRO: nenhuma imagem .jpg encontrada em '{entrada}'.")
    return imagens


def preparar_saida(saida: Path) -> None:
    """Cria as pastas de saída. Não apaga nada: quem limpa é o bench.py/demo.ps1, fora da medição."""
    (Path(saida) / "imagens").mkdir(parents=True, exist_ok=True)
    (Path(saida) / "miniaturas").mkdir(parents=True, exist_ok=True)


def estatisticas_do_histograma(histograma) -> dict:
    """Média e desvio-padrão de cada canal, calculados a partir do histograma global (contas com inteiros)."""
    medias, desvios = [], []
    for canal in range(3):
        h = [int(x) for x in histograma[canal * 256:(canal + 1) * 256]]
        n = sum(h)
        soma = sum(v * h[v] for v in range(256))
        soma_quadrados = sum(v * v * h[v] for v in range(256))
        medias.append(round(soma / n, 4))
        variancia = (n * soma_quadrados - soma * soma) / (n * n)  # numerador exato (inteiro)
        desvios.append(round(variancia ** 0.5, 4))
    return {"media_rgb": medias, "desvio_rgb": desvios}


def impressao_digital(manifesto: dict[str, str], histograma, imagens: int, pixels: int) -> str:
    """SHA-256 que resume o resultado do lote inteiro. Mesma impressão digital = mesmo resultado."""
    linhas = "\n".join(f"{nome} {sha}" for nome, sha in sorted(manifesto.items()))
    texto = linhas + "|" + ",".join(str(int(v)) for v in histograma) + f"|{int(imagens)}|{int(pixels)}"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def gravar_json(caminho: Path, dados: dict) -> None:
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def gravar_resultados(saida: Path, manifesto: dict[str, str], histograma, imagens: int, pixels: int) -> dict:
    """Grava manifesto.txt e estatisticas.json e devolve as estatísticas (com a impressão digital)."""
    saida = Path(saida)
    linhas = [f"{nome} {sha}" for nome, sha in sorted(manifesto.items())]
    (saida / "manifesto.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    estatisticas = {
        "imagens": int(imagens),
        "pixels": int(pixels),
        **estatisticas_do_histograma(histograma),
        "impressao_digital": impressao_digital(manifesto, histograma, imagens, pixels),
        "histograma": [int(v) for v in histograma],
    }
    gravar_json(saida / "estatisticas.json", estatisticas)
    return estatisticas


def agora_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def nome_cpu() -> str:
    """Nome comercial do processador (ex.: '12th Gen Intel(R) Core(TM) i7-12700H')."""
    if sys.platform == "win32":
        try:
            import winreg

            caminho = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, caminho) as chave:
                return str(winreg.QueryValueEx(chave, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    elif sys.platform.startswith("linux"):
        try:
            for linha in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                if linha.startswith("model name"):
                    return linha.split(":", 1)[1].strip()
        except OSError:
            pass
    return platform.processor() or "desconhecido"


def info_ambiente() -> dict:
    """Máquina e versões: vai para o execucao.json e para o relatório."""
    import numpy
    import PIL
    import psutil

    return {
        "cpu": nome_cpu(),
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "pillow": PIL.__version__,
        "numpy": numpy.__version__,
        "maquina": platform.node(),
    }


class Progresso:
    """Imprime o andamento a cada `passo` imagens (passo 0 = não imprime nada)."""

    def __init__(self, total: int, passo: int):
        self.total = total
        self.passo = passo
        self.feitas = 0
        self.inicio = time.perf_counter()

    def avancar(self) -> None:
        self.feitas += 1
        if self.passo and (self.feitas % self.passo == 0 or self.feitas == self.total):
            decorrido = time.perf_counter() - self.inicio
            print(f"  {self.feitas:>6}/{self.total} imagens ({100 * self.feitas / self.total:5.1f}%)"
                  f"  {decorrido:8.1f} s", flush=True)


def imprimir_resumo(execucao: dict) -> None:
    """Resumo igual para seq.py e par.py (é o que aparece na tela durante a demonstração)."""
    e = execucao
    print("=" * 72)
    if e["versao"] == "seq":
        print("VERSAO SEQUENCIAL | 1 fluxo")
    else:
        print(f"VERSAO PARALELA | {e['workers']} {e['modo']} | trava {e['trava']} | chunksize {e['chunksize']}")
    print(f"Imagens: {e['imagens']} | pixels: {e['pixels']}")
    print(f"Tempo total: {e['t_total_s']:.2f} s  (preparo {e['t_preparo_s']:.2f} s | "
          f"processamento {e['t_processamento_s']:.2f} s | final {e['t_final_s']:.2f} s)")
    if e["versao"] == "par":
        print(f"Espera pela trava: {1000 * e['espera_trava_s']:.1f} ms | dentro da trava: "
              f"{1000 * e['dentro_trava_s']:.1f} ms | cauda: {e['cauda_s']:.2f} s | ocupação: {100 * e['ocupacao']:.1f}%")
    print(f"Média RGB: {e['media_rgb']} | desvio RGB: {e['desvio_rgb']}")
    print(f"Impressão digital: {e['impressao_digital'][:16]}")
    print("=" * 72, flush=True)
```

**Explicação dos trechos importantes**

- `listar_imagens` ordena pelo **nome** do arquivo. Assim, "a mesma entrada" é sempre a mesma lista na mesma
  ordem, em qualquer máquina, e `--limite N` sempre pega as mesmas N imagens.
- `preparar_saida` **não apaga nada**. Apagar milhares de arquivos leva segundos no Windows e entraria na medição
  como tempo serial. Quem limpa as pastas é o `bench.py` e o `demo.ps1`, antes de cronometrar.
- `estatisticas_do_histograma` calcula média e desvio de cada canal a partir do histograma, com contas inteiras
  (soma de `v × h[v]` e de `v² × h[v]`). Só a divisão final é decimal. Por isso a sequencial e a paralela dão
  exatamente os mesmos números.
- `impressao_digital` é o SHA-256 do manifesto ordenado + histograma + contadores. Se um único byte de uma única
  imagem mudar, a impressão digital muda.
- `nome_cpu` lê o nome comercial do processador no registro do Windows (`winreg`). `info_ambiente` usa o
  `psutil` para contar núcleos físicos e lógicos: o `os.cpu_count()` do Python só conta os lógicos.
- `Progresso` imprime com `flush=True` para a linha aparecer na hora durante a demonstração.
- `imprimir_resumo` é o texto que aparece na tela no fim de cada execução, igual para as duas versões.

### 5.2 `pipeline.py`: a unidade de trabalho

**Para que serve.** Define o que acontece com UMA imagem. É a mesma função nas duas versões: a sequencial chama
num laço, e a paralela chama dentro de cada processo.

| # | Etapa | Chamada do Pillow | Custo medido no protótipo |
|---|---|---|---|
| 1 | Decodificar o JPEG | `Image.open(...).convert("RGB")` | 1,9 ms |
| 2 | Padronizar em 512×512 (corte central + redimensionamento) | `ImageOps.fit(im, TAM_SAIDA, LANCZOS)` | 4,7 ms |
| 3 | Remover ruído | `im.filter(ImageFilter.MedianFilter(3))` | 39,2 ms |
| 4 | Normalizar o contraste (corta 1% em cada ponta) | `ImageOps.autocontrast(im, cutoff=1)` | 1,2 ms |
| 5 | Nitidez | `ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3)` | 8,6 ms |
| 6 | Histograma RGB (768 contagens) | `im.histogram()` | 0,7 ms |
| 7–9 | Salvar JPEG, miniatura e SHA-256 | `save`, `thumbnail`, `hashlib.sha256` | 2,9 ms |
| | **Total** | | **≈ 59 ms** |

A etapa 3 é cerca de 2/3 do tempo de cada imagem e, no Pillow, segura o GIL do Python. É por isso que threads
quase não aceleram este trabalho e processos sim: é a justificativa "pela natureza do trabalho" que a lauda pede.

**O que não pode mudar:** a ordem das etapas e todos os parâmetros. A única exceção é `TAM_SAIDA`, e só se a
calibração (5.6) pedir, antes do marco M3.

```python
"""A unidade de trabalho: processar UMA imagem.

Dono: Pessoa 1. Esta função NÃO toca em estado compartilhado e NÃO tem nada aleatório:
a mesma imagem de entrada gera sempre os mesmos bytes de saída.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

TAM_SAIDA = (512, 512)           # única constante que a calibração pode mudar (para (640, 640))
TAM_MINIATURA = (128, 128)
QUALIDADE_JPEG = 90
QUALIDADE_MINIATURA = 85


def processar_imagem(origem: Path, pasta_saida: Path) -> tuple[str, str, list[int], int]:
    """Processa uma imagem e devolve (nome_original, sha256_da_saida, histograma_768, n_pixels)."""
    origem = Path(origem)
    pasta_saida = Path(pasta_saida)
    with Image.open(origem) as im:
        im = im.convert("RGB")                                               # 1. decodifica
    im = ImageOps.fit(im, TAM_SAIDA, Image.Resampling.LANCZOS)                # 2. padroniza 512x512
    im = im.filter(ImageFilter.MedianFilter(3))                               # 3. remove ruído
    im = ImageOps.autocontrast(im, cutoff=1)                                  # 4. normaliza contraste
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=3))  # 5. nitidez
    histograma = im.histogram()                                               # 6. 768 contagens inteiras
    destino = pasta_saida / "imagens" / f"{origem.stem}.jpg"
    im.save(destino, "JPEG", quality=QUALIDADE_JPEG)                          # 7. salva a imagem
    n_pixels = im.width * im.height
    im.thumbnail(TAM_MINIATURA, Image.Resampling.LANCZOS)                     # 8. miniatura
    im.save(pasta_saida / "miniaturas" / f"{origem.stem}.jpg", "JPEG", quality=QUALIDADE_MINIATURA)
    sha256 = hashlib.sha256(destino.read_bytes()).hexdigest()                 # 9. assinatura da saída
    return origem.name, sha256, histograma, n_pixels
```

**Explicação dos trechos importantes**

- O `with Image.open(...)` fecha o arquivo logo depois de decodificar. O `convert("RGB")` também trata as fotos
  do COCO que estão em tons de cinza.
- `ImageOps.fit` recorta o centro e redimensiona sem distorcer a foto. Todas as etapas pesadas trabalham sobre
  512×512, então cada tarefa custa quase o mesmo e a carga se equilibra bem entre os processos.
- O histograma é calculado **antes** de salvar o JPEG, porque a compressão altera levemente os pixels. Ele
  descreve a imagem processada em memória.
- `n_pixels` é calculado antes do `thumbnail`, que altera a imagem no lugar.
- O SHA-256 é do arquivo gravado. A mesma entrada gera sempre os mesmos bytes na mesma máquina, e é isso que
  permite provar que a paralela produz o mesmo que a sequencial.

### 5.3 `baixar_dados.py`: os dados de entrada

**Para que serve.** Baixa o COCO 2017 val (~1 GB) e extrai em `dados\val2017\`. Se o arquivo
`dados\val2017.zip` já existir (baixado pelo navegador), o script usa esse arquivo em vez de baixar de novo.

```python
"""Baixa e descompacta o COCO 2017 val (5.000 fotos reais, ~1 GB) em dados/val2017/.

Dono: Pessoa 1.   Uso:  python baixar_dados.py
Se o download pelo script falhar, baixe o zip pelo navegador, coloque em dados/val2017.zip
e rode o script de novo: ele usa o arquivo que já está lá.
"""
from __future__ import annotations

import argparse
import time
import urllib.request
import zipfile
from pathlib import Path

URL_PADRAO = "http://images.cocodataset.org/zips/val2017.zip"
IMAGENS_ESPERADAS = 5000


def contar_jpgs(pasta: Path) -> int:
    return sum(1 for _ in pasta.glob("*.jpg")) if pasta.is_dir() else 0


def baixar(url: str, destino_zip: Path) -> None:
    parcial = destino_zip.with_name(destino_zip.name + ".parcial")
    t0 = time.perf_counter()
    with urllib.request.urlopen(url, timeout=60) as resposta, open(parcial, "wb") as arquivo:
        total = int(resposta.headers.get("Content-Length") or 0)
        baixado = 0
        proximo_aviso = 0.05
        while True:
            bloco = resposta.read(1024 * 1024)
            if not bloco:
                break
            arquivo.write(bloco)
            baixado += len(bloco)
            if total and baixado / total >= proximo_aviso:
                print(f"  {100 * baixado / total:5.1f}%  ({baixado / 2**20:.0f} de {total / 2**20:.0f} MB, "
                      f"{time.perf_counter() - t0:.0f} s)", flush=True)
                proximo_aviso += 0.05
    if total and baixado != total:
        raise SystemExit("ERRO: download incompleto. Rode o script de novo.")
    parcial.replace(destino_zip)


def extrair(arquivo_zip: Path, pasta_dados: Path) -> None:
    with zipfile.ZipFile(arquivo_zip) as z:
        membros = [m for m in z.namelist() if m.startswith("val2017/") and m.lower().endswith(".jpg")]
        for i, membro in enumerate(membros, 1):
            z.extract(membro, pasta_dados)  # a extração confere o CRC de cada arquivo
            if i % 500 == 0 or i == len(membros):
                print(f"  extraídas {i}/{len(membros)}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Baixa o COCO 2017 val em dados/val2017/")
    ap.add_argument("--dados", type=Path, default=Path("dados"), help="pasta onde ficam os dados")
    ap.add_argument("--url", default=URL_PADRAO)
    ap.add_argument("--manter-zip", action="store_true", help="não apagar o .zip depois de extrair")
    args = ap.parse_args()

    pasta_imagens = args.dados / "val2017"
    arquivo_zip = args.dados / "val2017.zip"
    ja_tem = contar_jpgs(pasta_imagens)
    if ja_tem >= IMAGENS_ESPERADAS:
        print(f"OK: '{pasta_imagens}' já tem {ja_tem} imagens. Nada a fazer.")
        return
    args.dados.mkdir(parents=True, exist_ok=True)
    if arquivo_zip.exists():
        print(f"Usando o arquivo já baixado: {arquivo_zip}")
    else:
        print(f"Baixando {args.url} (~1 GB) ...", flush=True)
        baixar(args.url, arquivo_zip)
    print("Extraindo ...", flush=True)
    extrair(arquivo_zip, args.dados)
    total = contar_jpgs(pasta_imagens)
    print(f"OK: {total} imagens em '{pasta_imagens}'")
    if total != IMAGENS_ESPERADAS:
        print(f"AVISO: eram esperadas {IMAGENS_ESPERADAS} imagens. O zip foi mantido para conferência.")
    elif not args.manter_zip:
        arquivo_zip.unlink()
        print("Zip apagado para liberar espaço (use --manter-zip para guardar).")


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- O download vai para `val2017.zip.parcial` e só é renomeado no fim. Se cair no meio, é só rodar de novo.
- A extração confere o CRC de cada arquivo, então um zip corrompido dá erro em vez de gerar imagens quebradas.
- O zip só é apagado se as 5.000 imagens estiverem lá. Use `--manter-zip` se quiser guardá-lo.
- Se o download pelo script falhar (rede da faculdade, proxy), baixe pelo navegador, salve como
  `dados\val2017.zip` e rode o script de novo.

### 5.4 `seq.py`: a versão sequencial

**Para que serve.** Processa as imagens uma por uma, num único fluxo. É a referência de tempo (T_seq) e de
resultado para a versão paralela.

**Por que medir três fases.** O programa mede separadamente o preparo (listar imagens e criar pastas), o
processamento (o laço, que é a parte que a paralela divide) e o final (gravar manifesto e estatísticas). A
Pessoa 4 usa isso para calcular a fração paralelizável da lei de Amdahl: f = T_processamento / T_total.

```python
"""Versão SEQUENCIAL: processa as imagens uma por uma, em um único fluxo.

Dono: Pessoa 1.   Uso:  python seq.py --entrada dados/val2017 --saida saida_seq --limite 5000
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from comum import (ENTRADA_PADRAO, N_BINS, Progresso, agora_iso, gravar_json, gravar_resultados,
                   imprimir_resumo, info_ambiente, listar_imagens, preparar_saida)
from pipeline import processar_imagem


def ler_argumentos() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Processamento de imagens em lote - versão sequencial")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO, help="pasta com as imagens .jpg")
    ap.add_argument("--saida", type=Path, default=Path("saida_seq"), help="pasta onde gravar os resultados")
    ap.add_argument("--limite", type=int, default=None, help="usar só as N primeiras imagens (ordem alfabética)")
    ap.add_argument("--progresso", type=int, default=250, help="imprimir andamento a cada N imagens (0 = nunca)")
    return ap.parse_args()


def main() -> None:
    args = ler_argumentos()
    inicio = agora_iso()
    t0 = time.perf_counter()

    # 1) PREPARO (serial): lista as imagens e cria as pastas
    imagens = listar_imagens(args.entrada, args.limite)
    preparar_saida(args.saida)
    t1 = time.perf_counter()

    # 2) PROCESSAMENTO: a parte que a versão paralela divide entre os fluxos
    histograma = np.zeros(N_BINS, dtype=np.int64)
    n_imagens = 0
    n_pixels = 0
    manifesto: dict[str, str] = {}
    progresso = Progresso(len(imagens), args.progresso)
    for caminho in imagens:
        nome, sha256, hist, pixels = processar_imagem(caminho, args.saida)
        histograma += np.asarray(hist, dtype=np.int64)   # 1 fluxo só: não precisa de trava
        n_imagens += 1
        n_pixels += pixels
        manifesto[nome] = sha256
        progresso.avancar()
    t2 = time.perf_counter()

    # 3) FINAL (serial): estatísticas, manifesto e impressão digital
    estatisticas = gravar_resultados(args.saida, manifesto, histograma, n_imagens, n_pixels)
    t3 = time.perf_counter()

    execucao = {
        "versao": "seq", "modo": None, "trava": None, "workers": 1, "chunksize": None,
        "entrada": str(args.entrada), "saida": str(args.saida), "limite": args.limite,
        "imagens": n_imagens, "pixels": n_pixels,
        "t_total_s": t3 - t0, "t_preparo_s": t1 - t0, "t_processamento_s": t2 - t1, "t_final_s": t3 - t2,
        "espera_trava_s": 0.0, "dentro_trava_s": 0.0,
        "inicio_primeira_tarefa_s": None, "cauda_s": None, "ocupacao": None, "fluxos_usados": 1,
        "media_rgb": estatisticas["media_rgb"], "desvio_rgb": estatisticas["desvio_rgb"],
        "impressao_digital": estatisticas["impressao_digital"],
        "inicio": inicio, "ambiente": info_ambiente(),
    }
    gravar_json(Path(args.saida) / "execucao.json", execucao)
    imprimir_resumo(execucao)


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- Com um único fluxo, somar o histograma num array local não precisa de trava. A versão paralela faz a mesma
  soma, só que no estado compartilhado e protegida.
- Os campos que só existem na paralela (`cauda_s`, `ocupacao` etc.) vão como `None`, que vira `null` no JSON.
  Assim o `execucao.json` tem sempre os mesmos campos (contrato da seção 2.4).
- O `execucao.json` é gravado depois da medição: o `info_ambiente()` não entra no tempo.

**Saída esperada** (exemplo real do protótipo, com `--limite 100 --progresso 50`; os tempos mudam na sua
máquina):

```text
      50/100 imagens ( 50.0%)       3.6 s
     100/100 imagens (100.0%)       7.1 s
========================================================================
VERSAO SEQUENCIAL | 1 fluxo
Imagens: 100 | pixels: 26214400
Tempo total: 7.06 s  (preparo 0.00 s | processamento 7.05 s | final 0.00 s)
Média RGB: [126.3267, 123.4042, 127.0195] | desvio RGB: [83.9809, 78.151, 80.7383]
Impressão digital: a4a8b7e96f80fd7e
========================================================================
```

### 5.5 `verificar.py`: a prova de que a paralela produz o mesmo

**Para que serve.** Compara duas pastas de execução: o manifesto (nome e SHA-256 de cada imagem), o histograma
global, os contadores e a impressão digital. Imprime `RESULTADO: IDÊNTICO` e termina com código 0, ou
`RESULTADO: DIVERGENTE` com exemplos das diferenças e código 1. Se as duas pastas tiverem `execucao.json`, mostra
também os dois tempos totais e a razão entre eles (o speedup daquela execução), que a Pessoa 4 usa ao vivo na
demonstração.

```python
"""Compara duas execuções: mesmas saídas (SHA-256 de cada imagem) e mesmas estatísticas.

Dono: Pessoa 1.   Uso:  python verificar.py saida_seq saida_par
Sai com código 0 se forem idênticas e 1 se forem diferentes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def carregar(pasta: Path) -> tuple[dict[str, str], dict]:
    arq_manifesto = pasta / "manifesto.txt"
    arq_estatisticas = pasta / "estatisticas.json"
    if not arq_manifesto.exists() or not arq_estatisticas.exists():
        raise SystemExit(f"ERRO: '{pasta}' não tem manifesto.txt e estatisticas.json. Rode seq.py ou par.py antes.")
    manifesto = {}
    for linha in arq_manifesto.read_text(encoding="utf-8").splitlines():
        if linha.strip():
            nome, sha256 = linha.split()
            manifesto[nome] = sha256
    estatisticas = json.loads(arq_estatisticas.read_text(encoding="utf-8"))
    return manifesto, estatisticas


def main() -> None:
    ap = argparse.ArgumentParser(description="Compara os resultados de duas execuções")
    ap.add_argument("pasta_a", type=Path)
    ap.add_argument("pasta_b", type=Path)
    args = ap.parse_args()

    man_a, est_a = carregar(args.pasta_a)
    man_b, est_b = carregar(args.pasta_b)
    so_em_a = sorted(man_a.keys() - man_b.keys())
    so_em_b = sorted(man_b.keys() - man_a.keys())
    diferentes = sorted(n for n in man_a.keys() & man_b.keys() if man_a[n] != man_b[n])
    hist_igual = est_a["histograma"] == est_b["histograma"]
    contadores_iguais = (est_a["imagens"], est_a["pixels"]) == (est_b["imagens"], est_b["pixels"])
    impressao_igual = est_a["impressao_digital"] == est_b["impressao_digital"]

    print(f"Comparando '{args.pasta_a}' com '{args.pasta_b}'")
    print(f"  imagens: {len(man_a)} x {len(man_b)} | só em A: {len(so_em_a)} | só em B: {len(so_em_b)}"
          f" | saídas diferentes: {len(diferentes)}")
    print(f"  histograma global idêntico: {'sim' if hist_igual else 'NÃO'}")
    print(f"  contadores (imagens, pixels) idênticos: {'sim' if contadores_iguais else 'NÃO'}")
    print(f"  impressão digital: {est_a['impressao_digital'][:16]} x {est_b['impressao_digital'][:16]}")
    for rotulo, lista in (("só em A", so_em_a), ("só em B", so_em_b), ("diferentes", diferentes)):
        if lista:
            print(f"  exemplos ({rotulo}): {', '.join(lista[:5])}")
    exec_a, exec_b = args.pasta_a / "execucao.json", args.pasta_b / "execucao.json"
    if exec_a.exists() and exec_b.exists():
        t_a = json.loads(exec_a.read_text(encoding="utf-8"))["t_total_s"]
        t_b = json.loads(exec_b.read_text(encoding="utf-8"))["t_total_s"]
        print(f"  tempo total: {t_a:.2f} s x {t_b:.2f} s | razão A/B (speedup desta execução): {t_a / t_b:.2f}")

    ok = not so_em_a and not so_em_b and not diferentes and hist_igual and contadores_iguais and impressao_igual
    print("RESULTADO: IDÊNTICO" if ok else "RESULTADO: DIVERGENTE")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

**Saída esperada, pastas iguais** (exemplo real):

```text
Comparando 'saida_seq' com 'saida_par'
  imagens: 100 x 100 | só em A: 0 | só em B: 0 | saídas diferentes: 0
  histograma global idêntico: sim
  contadores (imagens, pixels) idênticos: sim
  impressão digital: a4a8b7e96f80fd7e x a4a8b7e96f80fd7e
  tempo total: 7.06 s x 3.86 s | razão A/B (speedup desta execução): 1.83
RESULTADO: IDÊNTICO
```

**Saída esperada, pastas diferentes** (exemplo real: `saida_99` foi gerada com `--limite 99`):

```text
Comparando 'saida_seq' com 'saida_99'
  imagens: 100 x 99 | só em A: 1 | só em B: 0 | saídas diferentes: 0
  histograma global idêntico: NÃO
  contadores (imagens, pixels) idênticos: NÃO
  impressão digital: a4a8b7e96f80fd7e x b2176d56386a3b2b
  exemplos (só em A): 000000090057.jpg
  tempo total: 7.06 s x 6.96 s | razão A/B (speedup desta execução): 1.01
RESULTADO: DIVERGENTE
```

### 5.6 `calibrar.py`: quanto de entrada usar

**Para que serve.** A lauda exige que a sequencial leve minutos, e a demonstração exige que ela termine antes
do minuto 6 da apresentação, porque é disparada aos ~20 s. O alvo é **4 minutos**. O script mede o tempo médio
por imagem na máquina da demo e recomenda o `--limite` (N = 240 s ÷ tempo por imagem).

```python
"""Mede o tempo por imagem NESTA máquina e recomenda o --limite para a sequencial levar ~4 minutos.

Dono: Pessoa 1.   Uso:  python calibrar.py      (rodar na máquina da demonstração)
"""
from __future__ import annotations

import argparse
import math
import shutil
import time
from pathlib import Path

from comum import ENTRADA_PADRAO, listar_imagens, preparar_saida
from pipeline import TAM_SAIDA, processar_imagem

PASTA_TEMPORARIA = Path("saida_calibracao")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibra o volume de entrada para a demonstração")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO)
    ap.add_argument("--amostra", type=int, default=200, help="quantas imagens medir")
    ap.add_argument("--alvo-min", type=float, default=4.0, help="duração desejada da sequencial, em minutos")
    args = ap.parse_args()

    todas = listar_imagens(args.entrada, None)
    amostra = todas[:args.amostra]
    shutil.rmtree(PASTA_TEMPORARIA, ignore_errors=True)
    preparar_saida(PASTA_TEMPORARIA)
    for caminho in amostra[:20]:                 # aquecimento: cache de disco e imports
        processar_imagem(caminho, PASTA_TEMPORARIA)
    t0 = time.perf_counter()
    for caminho in amostra:
        processar_imagem(caminho, PASTA_TEMPORARIA)
    por_imagem = (time.perf_counter() - t0) / len(amostra)
    shutil.rmtree(PASTA_TEMPORARIA, ignore_errors=True)

    alvo_s = args.alvo_min * 60
    com_todas_s = len(todas) * por_imagem
    print(f"TAM_SAIDA atual: {TAM_SAIDA}")
    print(f"Tempo médio por imagem: {1000 * por_imagem:.1f} ms (medido em {len(amostra)} imagens)")
    print(f"Com todas as {len(todas)} imagens, a sequencial levaria ~{com_todas_s / 60:.1f} min")
    if com_todas_s >= alvo_s:
        n = math.floor(alvo_s / por_imagem)
        print(f"RECOMENDAÇÃO: use --limite {n} (sequencial estimada em {n * por_imagem / 60:.1f} min)")
    elif com_todas_s >= 2.5 * 60:
        print(f"RECOMENDAÇÃO: use todas as imagens (--limite {len(todas)}); "
              f"a sequencial leva ~{com_todas_s / 60:.1f} min, o que atende ao requisito.")
    else:
        print("ATENÇÃO: nem com todas as imagens a sequencial chega a 2,5 min.")
        print("Troque TAM_SAIDA para (640, 640) em pipeline.py e rode calibrar.py de novo.")
        print("Se ainda não chegar, use (768, 768).")


if __name__ == "__main__":
    main()
```

**Como usar**

1. Rode **na máquina da demo**, na tomada, com os outros programas fechados: `python calibrar.py`.
2. Anuncie no grupo a linha "RECOMENDAÇÃO", por exemplo "N = 4800". A Pessoa 3 coloca esse valor em `$N` no
   `demo.ps1` e a Pessoa 4 usa `--limite 4800` no `bench.py`.
3. Confirme com uma sequencial completa: `python seq.py --limite 4800`. O "Tempo total" deve ficar entre 3,5 e
   4,5 minutos (210 a 270 s). Se ficar fora, rode o `calibrar.py` de novo e ajuste.
4. Se o script disser que nem com todas as imagens a sequencial chega a 2,5 minutos (máquina muito rápida),
   troque em `pipeline.py` a linha `TAM_SAIDA = (512, 512)` por `TAM_SAIDA = (640, 640)` e rode o
   `calibrar.py` de novo. Se ainda não chegar, use `(768, 768)`. Esta é a **única** mudança permitida no
   pipeline, e só antes do marco M3. Avise o grupo, porque ela muda os tempos de todo mundo.

**Saída esperada** (exemplo real do protótipo, que só tinha 600 imagens; por isso foi rodado com
`--alvo-min 0.5`, apenas para mostrar o formato):

```text
TAM_SAIDA atual: (512, 512)
Tempo médio por imagem: 69.5 ms (medido em 200 imagens)
Com todas as 600 imagens, a sequencial levaria ~0.7 min
RECOMENDAÇÃO: use --limite 431 (sequencial estimada em 0.5 min)
```

## 6. Testes de aceitação (definição de pronto)

Rode cada teste no PowerShell, na pasta do projeto, com o ambiente virtual ativado.

**6.1 `comum.py` e `pipeline.py`** (precisa de pelo menos uma imagem em `dados\val2017`). Rode duas vezes:

```powershell
python -c "from pathlib import Path; from comum import preparar_saida, listar_imagens; from pipeline import processar_imagem; preparar_saida(Path('saida_teste')); img = listar_imagens(Path('dados/val2017'), 1)[0]; nome, sha, h, px = processar_imagem(img, Path('saida_teste')); print(nome, sha[:16], len(h), sum(h), px)"
```

Esperado: `<nome da 1ª imagem> <16 caracteres hexadecimais> 768 786432 262144`, **idêntico nas duas vezes**
(786.432 = 3 canais × 262.144 pixels). No protótipo saiu `000000000245.jpg c62091874a81d609 768 786432 262144`.
Depois apague a pasta de teste: `Remove-Item -Recurse -Force saida_teste`.

**6.2 `baixar_dados.py`:** `python baixar_dados.py` termina com `OK: 5000 imagens em 'dados\val2017'`. Rodando
de novo, deve dizer `já tem 5000 imagens. Nada a fazer.`

**6.3 `seq.py`**

```powershell
python seq.py --limite 100 --progresso 50
Get-ChildItem saida_seq
Get-Content saida_seq\manifesto.txt -TotalCount 3
(Get-Content saida_seq\manifesto.txt).Count      # deve dar 100
```

Esperado: resumo igual ao da seção 5.4 (com os seus tempos); pastas `imagens` e `miniaturas` e os arquivos
`manifesto.txt`, `estatisticas.json` e `execucao.json`. Rode `python seq.py --limite 100` uma segunda vez: a
impressão digital precisa ser **a mesma**.

**6.4 `verificar.py`**

```powershell
Copy-Item -Recurse saida_seq saida_copia
python verificar.py saida_seq saida_copia        # IDÊNTICO
$LASTEXITCODE                                    # 0
python seq.py --limite 99 --saida saida_99 --progresso 0
python verificar.py saida_seq saida_99           # DIVERGENTE, só em A: 1
$LASTEXITCODE                                    # 1
Remove-Item -Recurse -Force saida_copia, saida_99
```

**6.5 Integração e calibração**

- [ ] (M2) Com o `par.py` da Pessoa 2: `python par.py --limite 100` e `python verificar.py saida_seq saida_par`
  terminam em `RESULTADO: IDÊNTICO`.
- [ ] (M3) `python calibrar.py` na máquina da demo; N anunciado; `python seq.py --limite N` leva de 3,5 a
  4,5 minutos.

## 7. Sua seção do relatório: "1. Problema e dados" (≈ ¾ de página)

Escreva em `relatorio\secao1_problema.md` e entregue à Pessoa 4 até domingo, 14:00. Troque tudo entre `[[ ]]`
pelos valores reais (o N é o da calibração; os tempos vêm da `resultados\tabela_tempos.md` da Pessoa 4).

> **1. Problema e dados**
>
> Antes de treinar um modelo de visão computacional, as fotos de um dataset precisam ser padronizadas, e o
> dataset inteiro precisa de estatísticas para normalizar a entrada da rede: a média e o desvio-padrão de cada
> canal de cor. Este trabalho implementa esse pré-processamento em lote e o paraleliza.
>
> **Entrada.** Conjunto de validação do COCO 2017: 5.000 fotografias reais em JPEG (cerca de 1 GB). Usamos as
> [[N]] primeiras em ordem alfabética do nome, número calibrado para a versão sequencial levar cerca de
> 4 minutos na máquina da demonstração.
>
> **Unidade de trabalho: uma imagem.** Para cada imagem, o programa decodifica o JPEG, recorta e redimensiona
> para 512×512 pixels (filtro LANCZOS), remove ruído com filtro de mediana 3×3, normaliza o contraste (corte de
> 1% em cada extremo), aplica nitidez (unsharp mask), calcula o histograma RGB (768 contagens inteiras), grava
> o resultado em JPEG (qualidade 90) e uma miniatura de 128×128 e calcula o SHA-256 do arquivo gerado. O filtro
> de mediana responde por cerca de 2/3 do tempo de cada imagem.
>
> **Por que o problema se divide.** Nenhuma imagem depende de outra, e as tarefas não trocam dados. O único
> resultado combinado é o histograma global do lote, uma soma de inteiros, operação associativa e comutativa que
> pode ser feita em qualquer ordem. Média e desvio de cada canal são calculados uma única vez, no final, a
> partir desse histograma.
>
> **Volume.** [[N]] imagens, ou [[N × 262.144]] pixels processados. A versão sequencial leva
> [[T_seq]] ± [[desvio]] s na máquina da demonstração, cerca de [[T_seq ÷ N × 1000]] ms por imagem.
>
> **Verificação.** As versões sequencial e paralela chamam a mesma função por imagem. Cada execução grava um
> manifesto com o SHA-256 de cada imagem gerada, o histograma global e uma impressão digital do lote (SHA-256
> de tudo). O programa `verificar.py` compara duas execuções; em todas as execuções da bateria de medições, a
> impressão digital foi a mesma: `[[16 primeiros caracteres]]`.

## 8. Sua parte da apresentação (0:00–2:00)

**Antes de começar:** a Pessoa 3 já rodou `.\demo.ps1 -Etapa preparar` e deixou dois terminais abertos na
pasta do projeto, com o ambiente virtual ativado e fonte grande.

**Slides (2):**

1. *O problema.* Título "Pré-processamento em lote de um dataset de fotos"; uma frase com o problema real; 4
   pares antes/depois; "Entrada: COCO 2017 val, 5.000 fotos, ~1 GB". Para os pares, use o site da Pessoa 3
   (`site\galeria\*_antes.jpg` e `*_depois.jpg`) ou abra uma imagem de `dados\val2017` e a de mesmo nome em
   `saida_seq\imagens`.
2. *Por que se divide.* "Unidade de trabalho: 1 imagem" com as 9 etapas em uma linha; o desenho "N imagens →
   p processos → cada imagem independente → só o histograma global é somado"; "Volume: [[N]] imagens,
   sequencial ≈ [[T_seq]] min".

**Roteiro falado (~2 min):**

- (0:00) "Nosso problema é o pré-processamento de um dataset de fotos para visão computacional. Antes de
  treinar um modelo, cada foto precisa ser padronizada e o dataset inteiro precisa de estatísticas de cor."
- (0:20) **Ação ao vivo**, no terminal 1: `.\demo.ps1 -Etapa seq`. Diga: "Vou disparar agora a versão
  sequencial com [[N]] imagens. Ela leva uns 4 minutos e vai rodar ao vivo enquanto apresentamos; o tempo dela
  vai estar na tela quando chegarmos à execução." Deixe o terminal visível num canto.
- (0:40) "A entrada é o COCO 2017, 5.000 fotos reais. A unidade de trabalho é uma imagem: decodificar,
  padronizar em 512 por 512, tirar ruído, ajustar contraste e nitidez, salvar e calcular o histograma."
- (1:10) "Por que se divide: nenhuma imagem depende de outra. O único dado em comum é o histograma global do
  lote, que é uma soma de inteiros e pode ser feita em qualquer ordem. Esse é o nosso estado compartilhado, e
  é dele que a [[Pessoa 2]] vai falar."
- (1:40) "Volume: [[N]] imagens, [[X]] bilhões de pixels, cerca de 4 minutos na versão sequencial."

## 9. Arguição

### 9.1 O que você precisa dominar na sua parte

- Por que a unidade é uma imagem, e não um bloco de pixels ou um lote de imagens (granularidade: custo de envio
  × equilíbrio de carga).
- Por que a mediana é a etapa mais cara (ordena 9 valores por pixel e por canal) e por que isso justifica usar
  processos (ela segura o GIL).
- Por que a ordem das imagens é a alfabética, e por que isso importa para o `--limite`.
- Como média e desvio saem do histograma: média = Σ v·h[v] / n; variância = (n·Σ v²·h[v] − (Σ v·h[v])²) / n².
- Por que só inteiros no estado global (pergunta 4 do banco).
- O que a impressão digital resume e por que duas execuções iguais têm a mesma impressão digital.
- Por que o alvo da sequencial é 4 minutos (minutos, e não segundos, pela lauda; e terminar antes do minuto 6
  da apresentação).

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
| `ERRO: a pasta de entrada 'dados\val2017' não existe` | Dados não baixados ou comando rodado fora da pasta do projeto | `cd C:\projetos\lote-imagens` e `python baixar_dados.py` |
| `ModuleNotFoundError: No module named 'PIL'` | Ambiente virtual não ativado | `.\.venv\Scripts\Activate.ps1` (o prompt começa com `(.venv)`) |
| `python` abre a Microsoft Store | Ambiente virtual não ativado | Ative o ambiente virtual; não instale nada pela Store |
| Download parado ou muito lento | Rede | Baixe pelo navegador, salve como `dados\val2017.zip` e rode o script de novo |
| `zipfile.BadZipFile` na extração | Zip incompleto | Apague `dados\val2017.zip` e baixe de novo |
| Impressão digital muda entre duas execuções da **sequencial** | Alguém mudou `pipeline.py` ou a pasta de entrada entre as execuções | Confira `git status` e `git diff`; a sequencial é determinística |
| `PIL.UnidentifiedImageError` | Arquivo corrompido em `dados\val2017` | Apague a pasta `dados\val2017` e rode `python baixar_dados.py` de novo |
| Sequencial muito mais lenta que o esperado | Notebook na bateria ou antivírus analisando os arquivos | Ligue na tomada, use o modo de energia "Melhor desempenho" e rode de novo |
