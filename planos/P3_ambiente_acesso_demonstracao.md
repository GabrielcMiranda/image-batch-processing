# Pessoa 3: ambiente, controle de acesso e demonstração

**Projeto:** Processamento de imagens em lote · Sistemas Distribuídos e Paralelos · Projeto de Solução Distribuída, Etapa 1

**Seus arquivos:** `README.md`, `requirements.txt`, `.gitignore`, `ficha_maquina.py`, `aquecer_cache.py`,
`gerar_site.py`, `demo.ps1`, `infra\firewall_windows.ps1`, `infra\regras_de_acesso.md`

**Sua prioridade:** criar o repositório com `README.md`, `requirements.txt` e `.gitignore` **na largada**
(sábado, 14:00) e mandar o link ao grupo. Ninguém consegue instalar o ambiente antes disso.

## Como usar este documento

**Para você (Pessoa 3):** este arquivo tem tudo o que você precisa: o contexto do trabalho (seção 1), as
regras e contratos do grupo (seção 2), a sua parte (seções 3 a 10) e o código de referência de cada arquivo
seu, já testado no Python 3.12, 3.13 e 3.14. Leia as seções 1 a 4 antes de abrir a IA e depois trabalhe na
ordem da seção 4. Os outros três integrantes têm documentos com as mesmas seções 1 e 2, então todo mundo parte
das mesmas regras.

**Para a IA:** abra uma conversa nova, anexe (ou cole) este arquivo inteiro e envie a mensagem abaixo.

> Você vai me ajudar a implementar a minha parte de um projeto em grupo. O documento anexo é a especificação e
> deve ser seguido à risca:
> 1. Sou a Pessoa 3. Implemente apenas os meus arquivos: `README.md`, `requirements.txt`, `.gitignore`, `ficha_maquina.py`, `aquecer_cache.py`, `gerar_site.py`, `demo.ps1`, `infra/firewall_windows.ps1` e `infra/regras_de_acesso.md`. Não crie nem edite nenhum outro arquivo.
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

Você cuida de onde e como o projeto roda: o repositório, a máquina da demonstração, as regras de acesso (o
equivalente local do "grupo de segurança" da lauda), o serviço na porta 8000, o roteiro de comandos da
apresentação, a montagem dos slides e os ensaios. O critério "Provisionamento e controle de acesso" (0,5) é
seu, e ele **zera** se a porta administrativa ficar aberta para qualquer origem.

| | |
|---|---|
| Seus arquivos | `README.md`, `requirements.txt`, `.gitignore`, `ficha_maquina.py`, `aquecer_cache.py`, `gerar_site.py`, `demo.ps1`, `infra\firewall_windows.ps1`, `infra\regras_de_acesso.md` |
| Também é seu | Criar o repositório e as tags; preparar a máquina da demo com o dono dela; montar os slides; cronometrar os ensaios; o checklist do dia |
| Relatório | Seção 4, "Recursos provisionados" (≈ ¾ de página) |
| Apresentação | Parte 3, "Os recursos" (4:00–6:00), e a preparação antes de começar |
| Critério que você defende | Provisionamento e controle de acesso (0,5) |
| Você depende de | P1: `comum.py` (M1) para a ficha; P1 e P2: `seq.py` e `par.py` (M2) para o site e o `demo.ps1`; P1: o N (M3); P4: o melhor número de processos (bateria) |
| Dependem de você | Todos: o repositório (largada); P4: a máquina da demo pronta para a bateria (M3) |

## 4. Etapas de implementação

1. [ ] **Na largada:** criar o repositório com `README.md`, `requirements.txt` e `.gitignore` (5.1), convidar o
   grupo e mandar o link. **Marco M0.**
2. [ ] Preparar o seu PC (seção 2.1).
3. [ ] Criar `infra\firewall_windows.ps1` e `infra\regras_de_acesso.md` (5.4) e fazer `git push`. **Marco M1.**
4. [ ] Com todos, escolher a máquina da demo e prepará-la (5.2) antes do marco M3.
5. [ ] Depois do M1: criar `ficha_maquina.py` (5.3), rodar na máquina da demo, fazer `git push` do arquivo e do
   `infra\ficha_maquina.md` gerado.
6. [ ] Criar `aquecer_cache.py` (5.5) e fazer `git push`.
7. [ ] Aplicar as regras de firewall na máquina da demo e testar o acesso de outra máquina (5.4 e teste 6.3).
8. [ ] Depois do M2: criar `gerar_site.py` (5.6), testar e servir na porta 8000.
9. [ ] Criar `demo.ps1` (5.7), testar todas as etapas na máquina da demo e ajustar `$N` (da P1) e `$P` (da P4).
   **Marco M4.**
10. [ ] Criar a tag `v0.9` no M3 e a `v1.0` no domingo à noite (seção 2.2).
11. [ ] Montar os slides com o material de todos e cronometrar os dois ensaios (5.8). **Marco M5.**
12. [ ] Escrever a seção 4 do relatório (seção 7) e entregar à Pessoa 4 até domingo, 14:00.
13. [ ] Na segunda, antes da aula, fazer o checklist da seção 5.9.

## 5. Como implementar

Crie cada arquivo com **exatamente** o conteúdo de referência. O código Python foi testado no Python 3.12, 3.13
e 3.14; os dois scripts PowerShell passaram pela verificação de sintaxe do PowerShell, e as etapas do
`demo.ps1` foram executadas uma a uma.

### 5.1 O repositório e os arquivos base (na largada)

1. No GitHub: **New repository** → nome `lote-imagens` → público (ou privado, adicionando depois o professor) →
   **Create repository**, sem README (o nosso vem a seguir).
2. **Settings → Collaborators → Add people:** adicione os outros três.
3. No seu PC (depois dos passos 1 e 2 da seção 2.1):

```powershell
mkdir C:\projetos -Force
cd C:\projetos
git clone <LINK_DO_REPOSITORIO> lote-imagens
cd lote-imagens
```

4. Crie os três arquivos abaixo na raiz, e depois:

```powershell
git add README.md requirements.txt .gitignore
git commit -m "P3: arquivos base do projeto"
git push
```

5. Mande o link no grupo: "Repositório pronto; sigam a seção 2.1 a partir do passo 3".

**`requirements.txt`** (versões fixas, com pacotes prontos para Windows 64 bits no Python 3.12, 3.13 e 3.14):

```text
pillow==12.3.0
numpy==2.4.6
matplotlib==3.11.2
psutil==7.2.2
```

**`.gitignore`:**

```text
# ambiente virtual e cache do Python
.venv/
__pycache__/

# dados e saídas (grandes e regeneráveis): NÃO vão para o repositório
dados/
saida_*/
site/
*.zip
*.parcial
```

**`README.md`:**

````markdown
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
````

### 5.2 A máquina da demo: escolher e preparar

**Escolha (com o grupo, até o M3).** Cada um abre o Gerenciador de Tarefas (Ctrl+Shift+Esc) → Desempenho → CPU
e anota "Núcleos" e "Processadores lógicos". A máquina da demo é a de **mais núcleos físicos**, com SSD, pelo
menos 8 GB de RAM e 5 GB livres. A medição oficial (P4) e a apresentação acontecem nela. O dono dela segue os
passos abaixo com você.

**Preparação (antes da bateria de sábado e de novo antes da aula):**

1. Projeto em `C:\projetos\lote-imagens` (fora do OneDrive), ambiente virtual criado, `pip install -r
   requirements.txt` feito e `python baixar_dados.py` com as 5.000 imagens.
2. Na tomada. Configurações → Sistema → Energia e bateria → Modo de energia → **Melhor desempenho** (no
   Windows 10: clique no ícone da bateria e arraste para "Melhor desempenho").
3. Configurações → Windows Update → **Pausar atualizações** por 1 semana.
4. Ative o "Não incomodar" e feche navegador, Discord, jogos e sincronizações (OneDrive, Google Drive).
5. Recomendado durante o fim de semana: Segurança do Windows → Proteção contra vírus e ameaças → Gerenciar
   configurações → Exclusões → Adicionar exclusão → Pasta → `C:\projetos\lote-imagens`. Cada execução grava
   milhares de arquivos, e a análise de cada um pelo antivírus deixa os tempos instáveis. Remova a exclusão
   depois da apresentação.
6. Uma **máquina reserva** com o repositório, o ambiente e os dados prontos. Se a máquina da demo falhar, a
   apresentação continua nela. Vídeo não é plano B.

### 5.3 `ficha_maquina.py`: a ficha técnica da máquina

**Para que serve.** A lauda pede que o relatório registre os recursos usados. Rodando local, o equivalente de
"tipo de instância" é a ficha da máquina: processador, núcleos físicos e lógicos, memória, sistema e versões. O
script usa o `info_ambiente()` do `comum.py` (Pessoa 1) e grava `infra\ficha_maquina.md`.

```python
"""Ficha técnica da máquina da demonstração (vai para o relatório e para a parte 3 da apresentação).

Dono: Pessoa 3.   Uso:  python ficha_maquina.py      (grava infra/ficha_maquina.md)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import psutil

from comum import agora_iso, info_ambiente


def main() -> None:
    amb = info_ambiente()
    frequencia = psutil.cpu_freq()
    disco = shutil.disk_usage(Path.cwd())
    linhas = [
        "# Ficha técnica da máquina da demonstração", "",
        f"Gerada em {agora_iso()} por ficha_maquina.py", "",
        "| Item | Valor |",
        "|---|---|",
        f"| Processador | {amb['cpu']} |",
        f"| Núcleos físicos | {amb['nucleos_fisicos']} |",
        f"| Núcleos lógicos (threads de hardware) | {amb['nucleos_logicos']} |",
        f"| Frequência máxima informada | {frequencia.max:.0f} MHz |" if frequencia and frequencia.max else
        "| Frequência máxima informada | não disponível |",
        f"| Memória RAM | {amb['ram_gb']} GB |",
        f"| Disco livre na pasta do projeto | {disco.free / 2**30:.0f} GB |",
        f"| Sistema operacional | {amb['sistema']} |",
        f"| Python | {amb['python']} |",
        f"| Pillow | {amb['pillow']} |",
        f"| NumPy | {amb['numpy']} |",
        f"| Nome da máquina | {amb['maquina']} |",
    ]
    Path("infra").mkdir(exist_ok=True)
    Path("infra", "ficha_maquina.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))
    print("\nGravado em infra/ficha_maquina.md")


if __name__ == "__main__":
    main()
```

**Saída esperada** (exemplo real do protótipo; na máquina da demo aparecem o processador e o Windows dela):

```text
# Ficha técnica da máquina da demonstração

Gerada em 2026-09-19T11:12:44 por ficha_maquina.py

| Item | Valor |
|---|---|
| Processador | Intel(R) Xeon(R) Processor @ 2.80GHz |
| Núcleos físicos | 2 |
| Núcleos lógicos (threads de hardware) | 2 |
| Frequência máxima informada | não disponível |
| Memória RAM | 7.8 GB |
| Disco livre na pasta do projeto | 28 GB |
| Sistema operacional | Linux-6.18.44-fc-v37-x86_64-with-glibc2.39 |
| Python | 3.13.7 |
| Pillow | 12.3.0 |
| NumPy | 2.4.6 |
| Nome da máquina | vm |

Gravado em infra/ficha_maquina.md
```

Rode na máquina da demo e suba o `infra\ficha_maquina.md` gerado: ele vai para o relatório.

### 5.4 Controle de acesso: o "grupo de segurança" local

**A ideia.** Na nuvem, o grupo de segurança diz quais portas aceitam conexões e de quais origens. Rodando local,
quem faz isso é o Firewall do Windows. A lauda pede três coisas, e as regras abaixo cumprem as três:

| Porta | O que fica nela | Origem permitida |
|---|---|---|
| 8000/TCP | **Serviço:** página de resultados (`python -m http.server 8000 --directory site`) | Qualquer origem |
| 22/TCP | **Administração:** SSH (OpenSSH Server do Windows) | **Só o IP da máquina de quem administra** |
| Todas as outras | — | Bloqueadas (ação padrão de entrada = Bloquear) |

**`infra\firewall_windows.ps1`:**

```powershell
<#
.SYNOPSIS
  Regras de firewall do projeto: o equivalente local do "grupo de seguranca". Dono: Pessoa 3.
  Rode num PowerShell ABERTO COMO ADMINISTRADOR, na pasta do projeto:
      .\infra\firewall_windows.ps1 -IpEquipe 192.168.0.23
  Para apagar as regras depois da apresentacao:
      .\infra\firewall_windows.ps1 -Remover
#>
#Requires -RunAsAdministrator
param(
    [string]$IpEquipe,
    [switch]$Remover
)
$ErrorActionPreference = "Stop"
$Grupo = "Lote Imagens"

# apaga as regras antigas do projeto (o script pode ser rodado de novo quando o IP mudar)
Get-NetFirewallRule -Group $Grupo -ErrorAction SilentlyContinue | Remove-NetFirewallRule
if ($Remover) {
    Write-Host "Regras do grupo '$Grupo' removidas."
    return
}
if (-not $IpEquipe) {
    throw "Informe o IP da maquina de quem administra. Exemplo: -IpEquipe 192.168.0.23"
}

# negar por padrao: toda conexao de entrada sem regra de permissao e bloqueada
Set-NetFirewallProfile -Profile Domain, Private, Public -Enabled True -DefaultInboundAction Block

# porta do servico: a pagina de resultados, aberta
New-NetFirewallRule -Group $Grupo -DisplayName "Lote - Servico: pagina de resultados (TCP 8000)" `
    -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any | Out-Null

# porta administrativa: SSH, so a partir do IP da equipe
New-NetFirewallRule -Group $Grupo -DisplayName "Lote - Administracao: SSH so da equipe (TCP 22)" `
    -Direction Inbound -Protocol TCP -LocalPort 22 -RemoteAddress $IpEquipe -Action Allow -Profile Any | Out-Null

# o OpenSSH Server do Windows cria a regra OpenSSH-Server-In-TCP sem restringir a origem: restringe
if (Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue) {
    Set-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -RemoteAddress $IpEquipe
    Write-Host "Regra OpenSSH-Server-In-TCP restrita a $IpEquipe."
}

# mostra o resultado: e isto que vai para o relatorio e para a apresentacao
Get-NetFirewallRule -Group $Grupo | ForEach-Object {
    [PSCustomObject]@{
        Regra  = $_.DisplayName
        Porta  = ($_ | Get-NetFirewallPortFilter).LocalPort
        Origem = ($_ | Get-NetFirewallAddressFilter).RemoteAddress
        Acao   = $_.Action
    }
} | Format-Table -AutoSize
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction | Format-Table -AutoSize
```

**O que o script faz, em ordem:** apaga as regras antigas do grupo "Lote Imagens" (pode ser rodado de novo
quando o IP mudar); garante firewall ligado e entrada bloqueada por padrão nos três perfis; cria a regra da
porta 8000 aberta; cria a regra da porta 22 só para o IP da equipe; se o OpenSSH Server estiver instalado,
restringe a regra que ele mesmo cria (`OpenSSH-Server-In-TCP`), que vem sem restrição de origem; e mostra a
tabela final. Com `-Remover`, só apaga as regras do grupo.

**Passo a passo na máquina da demo**

1. **Descubra os IPs.** Na máquina da demo e na máquina de quem vai administrar (um colega), rode `ipconfig` e
   anote o "Endereço IPv4" do adaptador Wi-Fi. As duas precisam estar na mesma rede.
2. **(Recomendado) Instale o servidor SSH**, para a porta administrativa ter um serviço de verdade. Num
   PowerShell **como administrador**:

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
```

3. **Aplique as regras.** No menu Iniciar, clique com o botão direito em "Terminal" ou "Windows PowerShell" →
   **Executar como administrador**, e rode:

```powershell
cd C:\projetos\lote-imagens
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\infra\firewall_windows.ps1 -IpEquipe <IP_DA_MAQUINA_DE_QUEM_ADMINISTRA>
```

4. **Teste de outra máquina** (a do colega autorizado), trocando pelo IP da máquina da demo:

```powershell
Test-NetConnection <IP_DA_MAQUINA_DA_DEMO> -Port 8000     # TcpTestSucceeded : True (com o site sendo servido)
Test-NetConnection <IP_DA_MAQUINA_DA_DEMO> -Port 22       # True da máquina autorizada
```

   De uma terceira máquina (não autorizada), `-Port 22` precisa dar `False` e `-Port 8000`, `True`. No navegador
   do celular, `http://<IP_DA_MAQUINA_DA_DEMO>:8000` abre o site.
5. **Mostre ao vivo:** tecla Windows + R → `wf.msc` → Regras de Entrada → no painel da direita, "Filtrar por
   Grupo" → "Lote Imagens". Abra cada regra e mostre as abas "Protocolos e Portas" e "Escopo" (endereço remoto).
6. **Preencha `infra\regras_de_acesso.md`** com os IPs e a data, e suba no Git.

**Cuidados**

- Quando o Windows perguntar se o Python pode aceitar conexões na rede, clique em **Cancelar**. "Permitir" cria
  uma regra para o programa inteiro, em qualquer porta, e deixa de valer "só a porta do serviço aberta".
- O Wi-Fi da faculdade pode bloquear a comunicação entre aparelhos. Se isso acontecer, use o roteador do
  celular de um colega como rede da demonstração e conecte as duas máquinas nele.
- Os IPs mudam quando se troca de rede. No dia, rode o script de novo com o IP novo, antes de começar.
- **Nunca** crie regra para a porta 22 sem `-RemoteAddress`: porta administrativa aberta para qualquer origem
  zera o critério.
- Depois da apresentação: `.\infra\firewall_windows.ps1 -Remover` e `Stop-Service sshd` (como administrador).

**`infra\regras_de_acesso.md`** (preencha os colchetes):

```markdown
# Regras de acesso da máquina da demonstração

Equivalente local do "grupo de segurança": regras do Firewall do Windows criadas por
`infra/firewall_windows.ps1` (grupo "Lote Imagens"). Preencha os campos entre colchetes.

| Porta | Protocolo | O que fica nela | Origem permitida | Regra |
|---|---|---|---|---|
| 8000 | TCP | Serviço: página de resultados (`python -m http.server 8000 --directory site`) | Qualquer origem (é o serviço) | Lote - Servico: pagina de resultados (TCP 8000) |
| 22 | TCP | Administração: SSH (OpenSSH Server do Windows) | Só [IP da máquina de quem administra] | Lote - Administracao: SSH so da equipe (TCP 22) |
| Todas as outras | — | — | Bloqueadas: ação padrão de entrada = Bloquear | Perfis Domínio, Particular e Público |

- IP da máquina da demonstração (servidor): [preencher com o `ipconfig`]
- IP autorizado na porta 22 (administração): [preencher]
- Data em que as regras foram criadas: [preencher]

Como mostrar ao vivo: `wf.msc` → Regras de Entrada → filtrar pelo grupo "Lote Imagens".
```

### 5.5 `aquecer_cache.py`: primeira execução sem surpresa

**Para que serve.** Na primeira leitura, as imagens vêm do disco; depois, da memória (cache do sistema). Se a
sequencial da demonstração for a primeira leitura do dia, ela fica mais lenta que a da bateria. O script lê
todas as imagens uma vez; o `demo.ps1` roda ele na etapa `preparar`.

```python
"""Lê todas as imagens uma vez para o sistema guardá-las no cache de disco (rodar antes da demonstração).

Dono: Pessoa 3.   Uso:  python aquecer_cache.py dados/val2017
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dados") / "val2017"
    arquivos = sorted(pasta.glob("*.jpg"))
    total = sum(len(p.read_bytes()) for p in arquivos)
    print(f"Cache aquecido: {len(arquivos)} imagens, {total / 2**20:.0f} MB lidos de '{pasta}'")


if __name__ == "__main__":
    main()
```

### 5.6 `gerar_site.py`: o serviço na porta 8000

**Para que serve.** É o "serviço" cuja porta fica aberta: uma página estática com o resumo da última execução,
a tabela e os gráficos da bateria (se já existirem), o histograma global do lote e uma galeria antes/depois.
Não depende de internet. Depois de gerada, é servida pelo servidor HTTP da biblioteca padrão do Python.

```python
"""Gera a página de resultados (site/index.html), servida na porta 8000: a "porta do serviço".

Dono: Pessoa 3.
Uso:     python gerar_site.py --execucao saida_par --entrada dados/val2017
Servir:  python -m http.server 8000 --directory site --bind 0.0.0.0
"""
from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera os PNG sem abrir janela
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
CANAIS = [("Vermelho (R)", "#e34948"), ("Verde (G)", "#008300"), ("Azul (B)", "#2a78d6")]
IMAGENS_NA_GALERIA = 12


def virgula(valor: float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def grafico_histograma(estatisticas: dict, destino: Path) -> None:
    """Histograma global em 3 painéis (um por canal), em % dos pixels."""
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"]})
    histograma = estatisticas["histograma"]
    fig, eixos = plt.subplots(1, 3, figsize=(9, 3.0), dpi=200, sharey=True)
    fig.patch.set_facecolor(SUPERFICIE)
    niveis = list(range(256))
    for i, (ax, (nome, cor)) in enumerate(zip(eixos, CANAIS)):
        contagens = histograma[i * 256:(i + 1) * 256]
        total = sum(contagens)
        percentuais = [100 * c / total for c in contagens]
        ax.set_facecolor(SUPERFICIE)
        ax.fill_between(niveis, percentuais, color=cor, alpha=0.10, linewidth=0)
        ax.plot(niveis, percentuais, color=cor, linewidth=1.5)
        ax.set_title(nome, loc="left", color=TINTA, fontsize=10)
        ax.set_xlim(0, 255)
        ax.set_xticks([0, 64, 128, 192, 255])
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(EIXO)
        ax.tick_params(colors=EIXO, labelcolor=TINTA_SECUNDARIA, labelsize=8)
        ax.grid(True, color=GRADE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.set_xlabel("Nível (0 a 255)", color=TINTA_SECUNDARIA, fontsize=9)
    eixos[0].set_ylabel("% dos pixels", color=TINTA_SECUNDARIA, fontsize=9)
    eixos[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    fig.tight_layout()
    fig.savefig(destino, facecolor=SUPERFICIE, bbox_inches="tight")
    plt.close(fig)


def miniatura(origem: Path, destino: Path) -> None:
    with Image.open(origem) as im:
        im = im.convert("RGB")
    im.thumbnail((256, 256), Image.Resampling.LANCZOS)
    im.save(destino, "JPEG", quality=85)


def tabela(linhas: list[tuple[str, str]]) -> str:
    corpo = "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in linhas)
    return f"<table>{corpo}</table>"


def secao_desempenho(resultados: Path, site: Path) -> str:
    arquivo_resumo = resultados / "resumo.json"
    if not arquivo_resumo.exists():
        return "<p class='nota'>A bateria de medições ainda não foi analisada (resultados/resumo.json não existe).</p>"
    resumo = json.loads(arquivo_resumo.read_text(encoding="utf-8"))
    s = resumo["sequencial"]
    linhas = [f"<tr><td>Sequencial</td><td>{virgula(s['media'])} ± {virgula(s['desvio'])}</td>"
              f"<td>1,00</td><td>100%</td><td>—</td></tr>"]
    for c in resumo["configuracoes"]:
        t = c["tempo"]
        linhas.append(f"<tr><td>{html.escape(c['nome'])}</td><td>{virgula(t['media'])} ± {virgula(t['desvio'])}</td>"
                      f"<td>{virgula(c['speedup'])}</td><td>{virgula(100 * c['eficiencia'], 1)}%</td>"
                      f"<td>{virgula(c['amdahl'])}</td></tr>")
    figuras = ""
    for nome in ("speedup.png", "tempos.png"):
        if (resultados / nome).exists():
            shutil.copy2(resultados / nome, site / nome)
            figuras += f"<img class='grafico' src='{nome}' alt='{nome}'>"
    return (f"<p>Fração paralelizável estimada: f = {virgula(resumo['f'], 5)} · {s['n']} execuções por configuração.</p>"
            "<table class='dados'><tr><th>Configuração</th><th>Tempo total (s)</th><th>Speedup</th>"
            f"<th>Eficiência</th><th>Teto de Amdahl</th></tr>{''.join(linhas)}</table>{figuras}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera a página de resultados")
    ap.add_argument("--execucao", type=Path, default=Path("saida_par"), help="pasta de uma execução (seq ou par)")
    ap.add_argument("--entrada", type=Path, default=Path("dados") / "val2017", help="pasta das imagens originais")
    ap.add_argument("--resultados", type=Path, default=Path("resultados"))
    ap.add_argument("--site", type=Path, default=Path("site"))
    args = ap.parse_args()

    execucao = json.loads((args.execucao / "execucao.json").read_text(encoding="utf-8"))
    estatisticas = json.loads((args.execucao / "estatisticas.json").read_text(encoding="utf-8"))
    shutil.rmtree(args.site, ignore_errors=True)
    (args.site / "galeria").mkdir(parents=True)

    grafico_histograma(estatisticas, args.site / "histograma.png")
    nomes = [linha.split()[0] for linha in
             (args.execucao / "manifesto.txt").read_text(encoding="utf-8").splitlines() if linha.strip()]
    cartoes = []
    for nome in nomes[:IMAGENS_NA_GALERIA]:
        base = Path(nome).stem
        miniatura(args.entrada / nome, args.site / "galeria" / f"{base}_antes.jpg")
        miniatura(args.execucao / "imagens" / f"{base}.jpg", args.site / "galeria" / f"{base}_depois.jpg")
        cartoes.append(f"<figure><img src='galeria/{base}_antes.jpg' alt='original {base}'>"
                       f"<img src='galeria/{base}_depois.jpg' alt='processada {base}'>"
                       f"<figcaption>{html.escape(nome)}: original | processada</figcaption></figure>")

    e = execucao
    amb = e["ambiente"]
    fluxos = "1 fluxo (sequencial)" if e["versao"] == "seq" else f"{e['workers']} {e['modo']} (trava {e['trava']})"
    resumo_execucao = tabela([
        ("Versão", fluxos),
        ("Imagens processadas", str(e["imagens"])),
        ("Pixels processados", f"{e['pixels']:,}".replace(",", ".")),
        ("Tempo total", f"{virgula(e['t_total_s'])} s"),
        ("Espera pela trava", f"{virgula(1000 * e['espera_trava_s'], 1)} ms"),
        ("Média RGB do lote", " / ".join(virgula(v) for v in estatisticas["media_rgb"])),
        ("Desvio RGB do lote", " / ".join(virgula(v) for v in estatisticas["desvio_rgb"])),
        ("Impressão digital", estatisticas["impressao_digital"][:16]),
        ("Máquina", f"{amb['cpu']} · {amb['nucleos_fisicos']} núcleos físicos / {amb['nucleos_logicos']} lógicos"),
        ("Início da execução", e["inicio"]),
    ])
    pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lote de imagens: resultados</title>
<style>
  body {{ margin: 0; background: #f9f9f7; color: {TINTA}; font-family: system-ui, "Segoe UI", sans-serif; }}
  main {{ max-width: 1040px; margin: 0 auto; padding: 24px 16px 48px; }}
  h1 {{ font-size: 1.6rem; margin: 0 0 4px; }}
  h2 {{ font-size: 1.15rem; margin: 32px 0 12px; }}
  .sub, .nota {{ color: {TINTA_SECUNDARIA}; }}
  table {{ border-collapse: collapse; background: {SUPERFICIE}; margin-bottom: 12px; }}
  th, td {{ text-align: left; padding: 6px 12px; border-bottom: 1px solid {GRADE}; }}
  th {{ color: {TINTA_SECUNDARIA}; font-weight: 600; }}
  td {{ font-variant-numeric: tabular-nums; }}
  img.grafico {{ width: 100%; max-width: 820px; display: block; margin: 12px 0; }}
  .galeria {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }}
  figure {{ margin: 0; background: {SUPERFICIE}; padding: 8px; border: 1px solid {GRADE}; border-radius: 8px; }}
  figure img {{ width: calc(50% - 4px); height: auto; vertical-align: top; }}
  figcaption {{ color: {TINTA_SECUNDARIA}; font-size: 0.85rem; margin-top: 4px; }}
</style>
</head>
<body>
<main>
  <h1>Processamento de imagens em lote</h1>
  <p class="sub">Resultados servidos na porta 8000 · página gerada em {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
  <h2>Última execução</h2>
  {resumo_execucao}
  <h2>Desempenho (bateria de medições)</h2>
  {secao_desempenho(args.resultados, args.site)}
  <h2>Histograma global do lote</h2>
  <img class="grafico" src="histograma.png" alt="Histograma global por canal">
  <h2>Antes e depois ({len(cartoes)} primeiras imagens)</h2>
  <div class="galeria">{''.join(cartoes)}</div>
</main>
</body>
</html>
"""
    (args.site / "index.html").write_text(pagina, encoding="utf-8")
    print(f"Site gerado em '{args.site / 'index.html'}'.")
    print("Para servir na porta 8000: python -m http.server 8000 --directory site --bind 0.0.0.0")


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- Lê `execucao.json`, `estatisticas.json` e `manifesto.txt` da pasta indicada em `--execucao` (formato da seção
  2.4) e, se existirem, `resultados\resumo.json`, `speedup.png` e `tempos.png` da Pessoa 4.
- O histograma é desenhado em três painéis, um por canal, em "% dos pixels". Os picos em 0 e 255 são efeito do
  ajuste de contraste, que satura 1% em cada ponta.
- A pasta `site\` é apagada e recriada a cada execução (ela está no `.gitignore`).

**Como testar** (depois do M2):

```powershell
python par.py --limite 100
python gerar_site.py --execucao saida_par
python -m http.server 8000 --directory site --bind 0.0.0.0
```

Abra `http://localhost:8000` no navegador da própria máquina: aparecem as seções "Última execução", "Desempenho",
"Histograma global do lote" e "Antes e depois". Pare o servidor com Ctrl+C.

### 5.7 `demo.ps1`: os comandos da apresentação

**Para que serve.** Cada parte da apresentação roda um comando curto e já testado, sem digitar caminhos na hora.
O script mostra o comando antes de executar (em ciano), para o professor ver o que está rodando.

```powershell
<#
.SYNOPSIS
  Comandos da apresentacao, na ordem. Dono: Pessoa 3.
.EXAMPLE
  .\demo.ps1 -Etapa preparar
  .\demo.ps1 -Etapa seq
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("preparar", "seq", "corrida", "estavel", "par", "verificar", "site", "servir")]
    [string]$Etapa,
    [string]$Python = (Join-Path $PSScriptRoot ".venv\Scripts\python.exe")
)

# ===== AJUSTE AQUI depois da calibracao (Pessoa 1) e da bateria (Pessoa 4) =====
$N = 5000                       # --limite calibrado: a sequencial deve levar ~4 min
$P = 8                          # processos da demonstracao (o melhor resultado da bateria)
$Entrada = "dados\val2017"
# ===============================================================================

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Rodar([string[]]$Argumentos) {
    Write-Host ""
    Write-Host ("> python " + ($Argumentos -join " ")) -ForegroundColor Cyan
    & $Python @Argumentos
    if ($LASTEXITCODE -ne 0) {
        Write-Host "O comando terminou com erro (codigo $LASTEXITCODE)." -ForegroundColor Red
    }
}

switch ($Etapa) {
    "preparar" {
        Remove-Item -Recurse -Force saida_seq, saida_par, saida_estavel_1, saida_estavel_2 -ErrorAction SilentlyContinue
        Rodar @("aquecer_cache.py", $Entrada)
    }
    "seq" {
        Rodar @("seq.py", "--entrada", $Entrada, "--saida", "saida_seq", "--limite", "$N")
    }
    "corrida" {
        Rodar @("teste_corrida.py")
    }
    "estavel" {
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_estavel_1", "--limite", "300", "--progresso", "0")
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_estavel_2", "--limite", "300", "--progresso", "0")
        Rodar @("verificar.py", "saida_estavel_1", "saida_estavel_2")
    }
    "par" {
        Rodar @("par.py", "--entrada", $Entrada, "--saida", "saida_par", "--limite", "$N", "--workers", "$P")
    }
    "verificar" {
        Rodar @("verificar.py", "saida_seq", "saida_par")
    }
    "site" {
        Rodar @("gerar_site.py", "--execucao", "saida_par", "--entrada", $Entrada)
    }
    "servir" {
        Rodar @("-m", "http.server", "8000", "--directory", "site", "--bind", "0.0.0.0")
    }
}
```

**Etapas**

| Etapa | Quem roda, quando | O que faz |
|---|---|---|
| `preparar` | P3, antes de começar | Apaga as saídas antigas e aquece o cache |
| `seq` | P1, aos ~0:20, no terminal 1 | Sequencial com N imagens (~4 min) |
| `corrida` | P2, na parte 2, no terminal 2 | `teste_corrida.py` |
| `estavel` | P2, na parte 2, no terminal 2 | Duas paralelas com 300 imagens + verificação |
| `par` | P4, na parte 4, no terminal 2 | Paralela com N imagens e P processos |
| `verificar` | P4, na parte 4 | `verificar.py saida_seq saida_par` |
| `site` e `servir` | P3, se sobrar tempo ou na arguição | Gera e serve a página na porta 8000 |

**Ajuste obrigatório:** depois da calibração, troque `$N = 5000` pelo N da Pessoa 1; depois da bateria, troque
`$P = 8` pelo número de processos com menor tempo na `resultados\tabela_tempos.md` da Pessoa 4. Suba no Git.

**Como testar:** na máquina da demo, rode cada etapa na ordem da tabela, cada uma com
`.\demo.ps1 -Etapa <nome>`, e confira que nenhuma termina com "O comando terminou com erro". Se o PowerShell
disser que a execução de scripts está desabilitada, rode uma vez
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force`.

### 5.8 Slides e ensaios

Cada um entrega os seus slides até domingo, 14:00; você monta a apresentação (Google Slides ou PowerPoint), com
fonte de pelo menos 24 no texto e 20 no código.

| # | Slide | Quem |
|---|---|---|
| 1 | Capa: título, nomes, disciplina, data | P3 |
| 2 | O problema (fotos antes/depois, entrada) | P1 |
| 3 | Por que se divide (unidade de trabalho, volume) | P1 |
| 4 | A seção crítica (trecho da `mesclar()` com a trava) | P2 |
| 5 | Por que funciona (teste de corrida; trava grossa) | P2 |
| 6 | Os recursos (ficha da máquina + tabela de regras) | P3 |
| 7 | A execução (o que observar na tela) | P4 |
| 8 | O ganho (gráfico speedup × Amdahl × ideal) | P4 |
| 9 | O que limitou o ganho | P4 |
| 10 | Encerramento: link do repositório | P3 |

**Ensaios:** cronometre cada parte (a referência é a tabela da seção 1.7) e mire em **9:30** no total; estourar
mais de 2 minutos desconta. No ensaio 2, faça a arguição simulada: cada pessoa responde 3 perguntas da seção
9.2 sobre partes que não apresentou.

### 5.9 Checklist do dia (segunda, antes da aula)

- [ ] Link do repositório e PDF já no ambiente virtual (P4).
- [ ] Máquina da demo na tomada, "Melhor desempenho", "Não incomodar" ligado, programas fechados.
- [ ] `git pull` feito; `$N` e `$P` certos no `demo.ps1`.
- [ ] Regras de firewall reaplicadas com o IP da rede da sala (5.4) e o `sshd` rodando.
- [ ] `.\demo.ps1 -Etapa preparar` rodado; dois terminais abertos na pasta do projeto, com o ambiente virtual
  ativado e fonte grande.
- [ ] `wf.msc` aberto e filtrado pelo grupo "Lote Imagens"; Gerenciador de Tarefas aberto na aba Desempenho.
- [ ] `infra\ficha_maquina.md` aberto numa janela, para a parte 3.
- [ ] Máquina reserva ligada, com repositório, ambiente e dados.

### 5.10 Apêndice: plano B na nuvem (só se o professor exigir o console da AWS)

Se o professor disser que o critério de acesso exige o console da nuvem: no AWS Academy Learner Lab (regiões
`us-east-1` e `us-west-2`, instâncias até o tamanho `large`, com 2 vCPUs), crie uma instância `c5.large` ou
`m5.large` com Ubuntu 24.04 e 20 GB de disco. No grupo de segurança, deixe só **SSH 22 com origem "Meu IP"** e
**TCP 8000 com origem 0.0.0.0/0**. Conecte por SSH, instale com `sudo apt install -y python3-venv git`, clone o
repositório e rode os mesmos comandos com `python3`. Mostre ao vivo: a instância, a zona, o tipo e as regras.
No dia, atualize a regra SSH para o IP da rede da sala e nunca use 0.0.0.0/0 na porta 22. Com 2 vCPUs, o
speedup máximo é 2, por isso a medição principal continua na máquina local.

## 6. Testes de aceitação (definição de pronto)

**6.1 Repositório:** os outros três clonaram, criaram o ambiente virtual e rodaram
`python -c "import PIL, numpy, matplotlib, psutil; print('ambiente ok')"` sem erro.

**6.2 Ficha:** `python ficha_maquina.py` na máquina da demo mostra o processador certo e cria
`infra\ficha_maquina.md`.

**6.3 Acesso:**

- [ ] `.\infra\firewall_windows.ps1 -IpEquipe <ip>` (como administrador) termina mostrando as duas regras do
  grupo "Lote Imagens", a da 22 com a origem restrita, e `DefaultInboundAction` = `Block` nos três perfis.
- [ ] Da máquina autorizada: `Test-NetConnection <ip-da-demo> -Port 22` → `TcpTestSucceeded : True`.
- [ ] De uma máquina não autorizada: `-Port 22` → `False`; `-Port 8000` (com o servidor rodando) → `True`.
- [ ] `wf.msc` filtrado por "Lote Imagens" mostra as duas regras.

**6.4 Site:** `python gerar_site.py --execucao saida_par` termina com `Site gerado em 'site\index.html'`; com
`python -m http.server 8000 --directory site --bind 0.0.0.0` rodando, a página abre em `http://localhost:8000`
e no celular, em `http://<ip-da-demo>:8000`.

**6.5 Demonstração:** todas as etapas do `demo.ps1` rodam na máquina da demo sem erro; no ensaio, a sequencial
disparada aos ~0:20 termina antes dos 6:00.

## 7. Sua seção do relatório: "4. Recursos provisionados" (≈ ¾ de página)

Escreva em `relatorio\secao4_recursos.md` e entregue à Pessoa 4 até domingo, 14:00. Os dados vêm de
`infra\ficha_maquina.md` e `infra\regras_de_acesso.md`.

> **4. Recursos provisionados**
>
> Com autorização do professor, a aplicação foi executada localmente, na máquina descrita abaixo, preparada
> pela equipe. As versões sequencial e paralela foram medidas nessa mesma máquina, com a mesma entrada.
>
> | Item | Valor |
> |---|---|
> | Processador | [[da ficha]] |
> | Núcleos físicos / lógicos | [[x]] / [[y]] |
> | Memória | [[z]] GB |
> | Sistema operacional | [[da ficha]] |
> | Python / Pillow / NumPy | [[versões]] |
>
> **Controle de acesso.** O papel do grupo de segurança foi feito pelo Firewall do Windows, com ação padrão de
> entrada "Bloquear" em todos os perfis e duas regras de permissão, criadas pelo script
> `infra/firewall_windows.ps1`:
>
> | Porta | O que fica na porta | Origem permitida |
> |---|---|---|
> | 8000/TCP | Serviço: página de resultados do lote | Qualquer origem |
> | 22/TCP | Administração remota: SSH (OpenSSH Server) | Somente [[IP]], máquina do integrante que administra |
>
> A porta administrativa não aceita conexões de nenhuma outra origem. O acesso foi testado com
> `Test-NetConnection`: a partir da máquina autorizada, a porta 22 respondeu; a partir de outra máquina da mesma
> rede, não; a porta 8000 respondeu às duas.

## 8. Sua parte da apresentação (4:00–6:00)

**Antes de começar (enquanto o professor se organiza):** `.\demo.ps1 -Etapa preparar`; dois terminais abertos;
`wf.msc` filtrado; Gerenciador de Tarefas na aba Desempenho → CPU; `infra\ficha_maquina.md` aberto.

**Roteiro falado (~2 min):**

- (4:00) "O professor liberou a execução local, então a nossa 'instância' é esta máquina." Mostre a ficha:
  "processador [[...]], [[x]] núcleos físicos e [[y]] lógicos, [[z]] GB de RAM, Windows [[...]], Python
  [[...]]."
- (4:30) Mostre o Gerenciador de Tarefas: "a versão sequencial que a [[Pessoa 1]] disparou está rodando agora:
  vejam que ela ocupa um núcleo só."
- (4:50) Abra o `wf.msc` já filtrado: "O papel do grupo de segurança é do Firewall do Windows. A entrada é
  bloqueada por padrão. Só há duas permissões: a porta 8000, que é o nosso serviço, a página de resultados,
  aberta; e a porta 22, a administração por SSH, liberada só para este endereço", e abra a aba Escopo da regra.
- (5:30) "Porta administrativa aberta para qualquer origem seria falha de projeto. Por isso ela só aceita o IP
  de quem administra, e testamos: da máquina autorizada responde, de outra máquina não."

## 9. Arguição

### 9.1 O que você precisa dominar na sua parte

- O que é um grupo de segurança e qual é o equivalente local (firewall com negação padrão + regras de
  permissão).
- O que fica em cada porta e por que a administrativa é restrita (menor privilégio).
- Diferença entre núcleo físico e lógico (Hyper-Threading) e por que isso limita o speedup.
- Por que a medição exige tomada e modo de desempenho (clock variável na bateria).
- Por que o cache de disco muda o tempo da primeira execução (pergunta 20 do banco).
- Como o `demo.ps1` garante que a sequencial e a paralela usam a mesma entrada (o mesmo `$N`).

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
| "a execução de scripts foi desabilitada neste sistema" | Política de execução do PowerShell | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force` (ou `-Scope Process -ExecutionPolicy Bypass` na janela de administrador) |
| Erro dizendo que o script contém uma instrução `#requires` para execução como Administrador | PowerShell aberto sem administrador | Abra o PowerShell com "Executar como administrador" |
| `Test-NetConnection` na porta 8000 dá `False` | Servidor não está rodando, redes diferentes ou Wi-Fi com isolamento entre aparelhos | Rode `python -m http.server 8000 --directory site --bind 0.0.0.0`; confira os IPs; use o roteador do celular |
| Porta 22 dá `False` até da máquina autorizada | `sshd` parado, IP errado na regra ou a máquina autorizada mudou de IP | `Start-Service sshd`; `ipconfig` na máquina autorizada; rode o script de novo com o IP certo |
| `Add-WindowsCapability` falha | Sem internet ou sem administrador | Rode como administrador, com internet; se não der, apresente as regras sem o serviço SSH e explique |
| `demo.ps1` diz que não acha o Python | Ambiente virtual não criado na máquina da demo | Seção 2.1, passo 4, na máquina da demo |
| Site sem a seção de desempenho | A P4 ainda não rodou o `analise.py` | Normal antes da bateria; rode `.\demo.ps1 -Etapa site` de novo depois |
