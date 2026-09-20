# Pessoa 2: versão paralela e sincronização

**Projeto:** Processamento de imagens em lote · Sistemas Distribuídos e Paralelos · Projeto de Solução Distribuída, Etapa 1

**Seus arquivos:** `estado.py`, `par.py`, `teste_corrida.py`

**Sua prioridade:** o `estado.py` e o `teste_corrida.py` não dependem de ninguém, então comece por eles. O
`par.py` precisa do `comum.py` e do `pipeline.py` da Pessoa 1 (marco M1, sábado, 15:30).

## Como usar este documento

**Para você (Pessoa 2):** este arquivo tem tudo o que você precisa: o contexto do trabalho (seção 1), as
regras e contratos do grupo (seção 2), a sua parte (seções 3 a 10) e o código de referência de cada arquivo
seu, já testado no Python 3.12, 3.13 e 3.14. Leia as seções 1 a 4 antes de abrir a IA e depois trabalhe na
ordem da seção 4. Os outros três integrantes têm documentos com as mesmas seções 1 e 2, então todo mundo parte
das mesmas regras.

**Para a IA:** abra uma conversa nova, anexe (ou cole) este arquivo inteiro e envie a mensagem abaixo.

> Você vai me ajudar a implementar a minha parte de um projeto em grupo. O documento anexo é a especificação e
> deve ser seguido à risca:
> 1. Sou a Pessoa 2. Implemente apenas os meus arquivos: `estado.py`, `par.py` e `teste_corrida.py`. Não crie nem edite nenhum outro arquivo.
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

Você cuida da versão paralela e de tudo o que envolve sincronização: o estado compartilhado, a trava que o
protege, a prova de que sem a trava existe condição de corrida e os modos de experimento (threads e trava
grossa) que a Pessoa 4 mede. O critério "Correção da sincronização, sem condições de corrida" (0,5) é seu.

| | |
|---|---|
| Seus arquivos | `estado.py`, `par.py`, `teste_corrida.py` |
| Relatório | Seção 2, "Estratégia de paralelização" (≈ 1 página), e seção 3, "Seção crítica e primitiva" (≈ 1 página) |
| Apresentação | Parte 2, "A seção crítica" (2:00–4:00) |
| Critério que você defende | Correção da sincronização (0,5) |
| Você depende de | P1: `comum.py` e `pipeline.py` (M1), só para o `par.py` |
| Dependem de você | Todos: `par.py` no marco M2; P4: os modos `--modo threads` e `--trava grossa` para a bateria |

## 4. Etapas de implementação

1. [ ] Preparar o PC (seção 2.1, passos 1 a 4) e começar o download do COCO (passo 5).
2. [ ] Ler a seção 5.1 (conceitos). É isso que o professor vai perguntar.
3. [ ] Criar `estado.py` (5.2), rodar o teste 6.1, fazer `git push`.
4. [ ] Criar `teste_corrida.py` (5.3), rodar o teste 6.2, fazer `git push`. **Marco M1.**
5. [ ] Depois do `git pull` com o `comum.py` e o `pipeline.py` da Pessoa 1: criar `par.py` (5.4), rodar o teste
   6.3 (paralela × sequencial = IDÊNTICO), fazer `git push`. **Marco M2.**
6. [ ] Rodar os testes 6.4 (estabilidade em 3 execuções, outros números de processos, threads e trava grossa)
   e mandar para a Pessoa 4 os tempos que você viu.
7. [ ] Anotar os números de linha da seção crítica no seu `estado.py` (a lauda pede que o relatório aponte a
   seção crítica no código).
8. [ ] Escrever as seções 2 e 3 do relatório (seção 7) e entregar à Pessoa 4 até domingo, 14:00.
9. [ ] Fazer os slides da parte 2 e entregar à Pessoa 3 até domingo, 14:00.
10. [ ] Estudar o banco de perguntas (seção 9) e participar do ensino cruzado e dos dois ensaios.

## 5. Como implementar

Crie cada arquivo na raiz do projeto (`C:\projetos\lote-imagens\`) com **exatamente** o código de referência.
Ele foi testado no Python 3.12, 3.13 e 3.14, sempre com o método de início `spawn`, que é o do Windows.

### 5.1 Conceitos que você vai usar (leia antes de codar)

**Por que processos, e não threads.** No CPython, o GIL deixa só uma thread executar código Python por vez em
cada processo. O Pillow solta o GIL em algumas operações (decodificar, redimensionar, unsharp), mas o filtro de
mediana, que é cerca de 2/3 do tempo de cada imagem, segura o GIL. Resultado medido no protótipo: com 2 fluxos,
processos deram de 1,7× a 2,0× e threads ~1,2×. Cada processo tem o seu próprio interpretador e o seu próprio GIL.

**O que o `spawn` do Windows muda.** Cada processo filho é um `python.exe` novo que importa os módulos do zero.
Ele **não herda** as variáveis do processo pai. Consequências que o código já trata:

1. O `par.py` precisa de `if __name__ == "__main__": main()`. Sem isso, cada filho executaria o programa
   inteiro de novo ao importar o módulo.
2. As funções entregues ao `Pool` precisam estar no nível do módulo, para poderem ser encontradas pelo nome.
3. A trava e a memória compartilhada chegam aos filhos pelo `initializer` do `Pool`, na criação de cada
   processo. Passar a trava como argumento de uma tarefa dá
   `RuntimeError: Lock objects should only be shared between processes through inheritance`.

O código usa `mp.get_context("spawn")` explicitamente, para ter o mesmo comportamento em qualquer sistema.

**Memória compartilhada.** `ctx.RawArray("q", 768)` cria 768 inteiros de 64 bits numa memória que todos os
processos enxergam. O `"q"` é importante: no Windows, `"l"` teria só 32 bits. `RawArray` não tem trava própria:
a proteção é a nossa `Lock`, explícita, que o relatório aponta. `np.frombuffer(...)` cria uma "visão" NumPy
sobre essa memória, sem copiar nada, para somar os 768 valores de uma vez.

**Condição de corrida e seção crítica.** `_hist[:] += hist_local` é, na prática, ler o valor atual, somar e
escrever de volta. Se dois processos leem o mesmo valor antigo ao mesmo tempo, um sobrescreve a soma do outro e
uma atualização se perde. A seção crítica é esse trecho; a `Lock` garante que só um processo o executa por vez.

**Granularidade da trava.** A trava cobre só a soma (microssegundos), e o processamento da imagem (dezenas de
milissegundos) fica fora dela. Se a trava cobrisse o trabalho inteiro, o programa continuaria correto, mas
serial: é o experimento `--trava grossa`, que a lauda cita como exemplo do que não fazer.

**`Pool`, `imap_unordered` e `chunksize`.** O `Pool` cria p processos e distribui as tarefas. O
`imap_unordered` entrega cada resultado assim que fica pronto, em qualquer ordem, então quem termina pega mais
trabalho (balanceamento dinâmico). O `chunksize=4` manda 4 imagens por envio, o que reduz as idas e vindas pelo
canal entre processos. Usamos `multiprocessing.Pool` (e não `ProcessPoolExecutor`) porque ele tem um irmão
para threads com a mesma interface, o `ThreadPool`, e isso deixa a comparação justa.

### 5.2 `estado.py`: o estado compartilhado e a seção crítica

**Para que serve.** Guarda o histograma global (768 inteiros) e 4 contadores (imagens, pixels, nanossegundos
esperando a trava e nanossegundos com a trava na mão) e oferece a função `mesclar()`, a única que escreve no
estado global dentro do programa.

```python
"""Estado global compartilhado entre os fluxos + a SEÇÃO CRÍTICA que o protege.

Dono: Pessoa 2.
O estado global é o histograma RGB do lote inteiro (768 inteiros) e 4 contadores.
Ele fica em memória compartilhada SEM trava própria (RawArray): quem protege é a nossa trava.
"""
from __future__ import annotations

import time

import numpy as np

N_BINS = 768
# posições do vetor de contadores
IMAGENS, PIXELS, ESPERA_NS, DENTRO_NS = 0, 1, 2, 3
N_CONTADORES = 4

_trava = None   # multiprocessing.Lock (modo processos) ou threading.Lock (modo threads)
_hist = None    # np.ndarray int64 com 768 posições, sobre a memória compartilhada
_cont = None    # np.ndarray int64 com 4 posições, sobre a memória compartilhada


def criar_memoria(ctx):
    """Cria a memória compartilhada. "q" = inteiro de 64 bits ("l" teria só 32 bits no Windows)."""
    hist_raw = ctx.RawArray("q", N_BINS)
    cont_raw = ctx.RawArray("q", N_CONTADORES)
    return hist_raw, cont_raw


def iniciar(trava, hist_raw, cont_raw) -> None:
    """initializer do Pool: roda UMA vez em cada processo filho (no modo threads, uma vez só)."""
    global _trava, _hist, _cont
    _trava = trava
    _hist = np.frombuffer(hist_raw, dtype=np.int64)
    _cont = np.frombuffer(cont_raw, dtype=np.int64)


def somar_sem_protecao(hist_local, n_pixels: int) -> None:
    """As escritas no estado global. No programa, só são chamadas com a trava na mão.
    O teste_corrida.py chama esta função sem a trava de propósito, para mostrar a corrida."""
    _hist[:] += hist_local
    _cont[IMAGENS] += 1
    _cont[PIXELS] += n_pixels


def mesclar(hist_local, n_pixels: int) -> None:
    """Soma o resultado de UMA imagem no estado global, protegido pela trava."""
    t0 = time.perf_counter_ns()
    with _trava:                                           # ===== INÍCIO DA SEÇÃO CRÍTICA =====
        t1 = time.perf_counter_ns()
        somar_sem_protecao(hist_local, n_pixels)
        _cont[ESPERA_NS] += t1 - t0                        # tempo esperando a trava ficar livre
        _cont[DENTRO_NS] += time.perf_counter_ns() - t1    # tempo com a trava na mão
    #                                                      ===== FIM DA SEÇÃO CRÍTICA =====


def trava_do_estado():
    """A trava, para o experimento de trava grossa do par.py (não use em outro lugar)."""
    return _trava


def registrar_tempos_trava(espera_ns: int, dentro_ns: int) -> None:
    """Soma tempos de trava medidos fora de mesclar(). Só chame com a trava na mão."""
    _cont[ESPERA_NS] += espera_ns
    _cont[DENTRO_NS] += dentro_ns


def ler(hist_raw, cont_raw) -> tuple[np.ndarray, dict]:
    """Lê o estado final. Só chame depois que TODOS os fluxos terminaram."""
    hist = np.frombuffer(hist_raw, dtype=np.int64).copy()
    cont = np.frombuffer(cont_raw, dtype=np.int64).copy()
    return hist, {
        "imagens": int(cont[IMAGENS]),
        "pixels": int(cont[PIXELS]),
        "espera_trava_s": int(cont[ESPERA_NS]) / 1e9,
        "dentro_trava_s": int(cont[DENTRO_NS]) / 1e9,
    }
```

**A seção crítica está nas linhas 49 a 54 do `estado.py`** (do `with _trava:` até o comentário
de fim), dentro da função `mesclar()`. Confira os números no seu arquivo: é isso que o relatório cita.

**Explicação de cada função**

- `criar_memoria(ctx)`: cria as duas áreas de memória compartilhada. É chamada uma vez, no processo principal.
- `iniciar(trava, hist_raw, cont_raw)`: é o `initializer` do `Pool`. Roda uma vez em cada processo filho, guarda
  a trava e cria as visões NumPy. No modo threads, é chamada uma vez só, no processo principal, porque as
  threads dividem o mesmo processo.
- `somar_sem_protecao(...)`: as três escritas no estado global. No programa, só é chamada com a trava na mão
  (dentro de `mesclar()` e no experimento de trava grossa). O `teste_corrida.py` chama sem a trava de propósito.
- `mesclar(...)`: mede quanto tempo esperou pela trava, entra na seção crítica, soma e mede quanto tempo ficou
  lá dentro. Esses dois tempos vão para o relatório: mostram que a espera na seção crítica não limitou o ganho.
- `trava_do_estado()` e `registrar_tempos_trava(...)`: usadas só pelo experimento de trava grossa do `par.py`.
- `ler(...)`: copia o estado final. Só pode ser chamada depois que todos os fluxos terminaram.

### 5.3 `teste_corrida.py`: a prova de que a trava é necessária

**Para que serve.** Sem a trava, a corrida quase nunca aparece no programa de verdade, porque a seção crítica
dura microssegundos a cada dezenas de milissegundos. Este teste força a disputa: 4 processos fazem 20.000 somas
cada um no mesmo estado global, primeiro com `somar_sem_protecao()` (sem trava) e depois com `mesclar()` (a
seção crítica real). O resultado certo é contador = 80.000 e cada posição do histograma = 80.000.

```python
"""Mostra a condição de corrida no estado global: as MESMAS somas, sem a trava e com a trava.

Dono: Pessoa 2.   Uso:  python teste_corrida.py
Cada processo faz M somas de um histograma de teste (768 posições valendo 1) no estado global.
Resultado certo: contador = P x M e cada posição do histograma = P x M.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import time

import numpy as np

import estado


def trabalhador(trava, barreira, hist_raw, cont_raw, somas: int, usar_trava: bool) -> None:
    estado.iniciar(trava, hist_raw, cont_raw)
    local = np.ones(estado.N_BINS, dtype=np.int64)
    barreira.wait()                              # todos começam juntos, para disputarem de verdade
    for _ in range(somas):
        if usar_trava:
            estado.mesclar(local, 1)             # a seção crítica real do programa
        else:
            estado.somar_sem_protecao(local, 1)  # as mesmas linhas, sem a trava


def rodada(ctx, processos: int, somas: int, usar_trava: bool) -> dict:
    trava = ctx.Lock()
    barreira = ctx.Barrier(processos)
    hist_raw, cont_raw = estado.criar_memoria(ctx)
    filhos = [ctx.Process(target=trabalhador, args=(trava, barreira, hist_raw, cont_raw, somas, usar_trava))
              for _ in range(processos)]
    t0 = time.perf_counter()
    for filho in filhos:
        filho.start()
    for filho in filhos:
        filho.join()
    hist, contadores = estado.ler(hist_raw, cont_raw)
    esperado = processos * somas
    return {
        "esperado": esperado,
        "contador": contadores["imagens"],
        "soma": int(hist.sum()),
        "posicoes_erradas": int((hist != esperado).sum()),
        "segundos": time.perf_counter() - t0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Demonstra a condição de corrida no estado global")
    ap.add_argument("-p", "--processos", type=int, default=4)
    ap.add_argument("-m", "--somas", type=int, default=20000, help="somas feitas por cada processo")
    ap.add_argument("-r", "--rodadas", type=int, default=3)
    args = ap.parse_args()
    ctx = mp.get_context("spawn")

    print(f"{args.processos} processos x {args.somas} somas cada | esperado: contador = "
          f"{args.processos * args.somas} e soma do histograma = {args.processos * args.somas * estado.N_BINS}")
    for usar_trava in (False, True):
        for i in range(1, args.rodadas + 1):
            r = rodada(ctx, args.processos, args.somas, usar_trava)
            ok = r["contador"] == r["esperado"] and r["posicoes_erradas"] == 0
            print(f"{'COM trava' if usar_trava else 'SEM trava'} | rodada {i}: contador {r['contador']:>8}/{r['esperado']}"
                  f" | posições erradas {r['posicoes_erradas']:>3}/{estado.N_BINS}"
                  f" | {'OK' if ok else 'PERDEU ATUALIZAÇÕES'} ({r['segundos']:.1f} s)", flush=True)
    print("Conclusão: sem a trava o resultado muda a cada rodada; com a trava é sempre o esperado.")


if __name__ == "__main__":
    main()
```

**Explicação dos trechos importantes**

- A `Barrier` faz os 4 processos começarem as somas juntos. Com `spawn`, cada processo leva um tempo para
  nascer, e sem a barreira eles poderiam quase não se sobrepor.
- Sem a trava, o teste chama exatamente as mesmas linhas de soma do programa, só que sem a proteção. A única
  diferença entre as duas metades do teste é a trava.
- "Posições erradas 768/768" quer dizer que todas as posições do histograma perderam alguma atualização.

**Saída esperada** (exemplo real; os números "SEM trava" mudam a cada rodada, e é exatamente isso que o teste
mostra):

```text
4 processos x 20000 somas cada | esperado: contador = 80000 e soma do histograma = 61440000
SEM trava | rodada 1: contador    67910/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.4 s)
SEM trava | rodada 2: contador    75834/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.4 s)
SEM trava | rodada 3: contador    60072/80000 | posições erradas 768/768 | PERDEU ATUALIZAÇÕES (0.4 s)
COM trava | rodada 1: contador    80000/80000 | posições erradas   0/768 | OK (1.7 s)
COM trava | rodada 2: contador    80000/80000 | posições erradas   0/768 | OK (1.8 s)
COM trava | rodada 3: contador    80000/80000 | posições erradas   0/768 | OK (1.9 s)
Conclusão: sem a trava o resultado muda a cada rodada; com a trava é sempre o esperado.
```

No protótipo, 23 de 23 rodadas sem trava perderam atualizações, e 23 de 23 com trava bateram exatamente.

### 5.4 `par.py`: a versão paralela

**Para que serve.** Faz o mesmo que o `seq.py`, só que dividindo as imagens entre p processos. Grava a pasta de
saída no mesmo formato e imprime o mesmo resumo, com três medidas a mais: espera pela trava, cauda e ocupação.

```python
"""Versão PARALELA: divide as imagens entre vários processos (ou threads, só para comparação).

Dono: Pessoa 2.   Uso:  python par.py --entrada dados/val2017 --saida saida_par --limite 5000 --workers 8
Experimentos:        --modo threads      (compara com threads)
                     --trava grossa      (trava o trabalho inteiro: correto, mas serial)
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import threading
import time
from functools import partial
from multiprocessing.pool import ThreadPool
from pathlib import Path

import numpy as np

import estado
from comum import (ENTRADA_PADRAO, Progresso, agora_iso, gravar_json, gravar_resultados, imprimir_resumo,
                   info_ambiente, listar_imagens, preparar_saida)
from pipeline import processar_imagem


def identificar_fluxo() -> str:
    """Identifica quem processou a tarefa: processo + thread."""
    return f"{os.getpid()}-{threading.get_ident()}"


def tarefa_trava_fina(caminho: str, pasta_saida: str):
    """Processa a imagem FORA da trava; só a soma no estado global fica DENTRO dela."""
    inicio = time.perf_counter()
    nome, sha256, hist, pixels = processar_imagem(Path(caminho), Path(pasta_saida))
    estado.mesclar(np.asarray(hist, dtype=np.int64), pixels)   # única escrita no estado global
    return nome, sha256, identificar_fluxo(), inicio, time.perf_counter()


def tarefa_trava_grossa(caminho: str, pasta_saida: str):
    """EXPERIMENTO (não usar na demo): a trava cobre o trabalho inteiro, então tudo vira serial."""
    inicio = time.perf_counter()
    t0 = time.perf_counter_ns()
    with estado.trava_do_estado():
        t1 = time.perf_counter_ns()
        nome, sha256, hist, pixels = processar_imagem(Path(caminho), Path(pasta_saida))
        estado.somar_sem_protecao(np.asarray(hist, dtype=np.int64), pixels)
        estado.registrar_tempos_trava(t1 - t0, time.perf_counter_ns() - t1)
    return nome, sha256, identificar_fluxo(), inicio, time.perf_counter()


def ler_argumentos() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Processamento de imagens em lote - versão paralela")
    ap.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO, help="pasta com as imagens .jpg")
    ap.add_argument("--saida", type=Path, default=Path("saida_par"), help="pasta onde gravar os resultados")
    ap.add_argument("--limite", type=int, default=None, help="usar só as N primeiras imagens (ordem alfabética)")
    ap.add_argument("-w", "--workers", type=int, default=os.cpu_count(), help="número de fluxos (padrão: núcleos lógicos)")
    ap.add_argument("--chunksize", type=int, default=4, help="imagens enviadas por vez a cada fluxo")
    ap.add_argument("--modo", choices=["processos", "threads"], default="processos")
    ap.add_argument("--trava", choices=["fina", "grossa"], default="fina")
    ap.add_argument("--progresso", type=int, default=250, help="imprimir andamento a cada N imagens (0 = nunca)")
    return ap.parse_args()


def main() -> None:
    args = ler_argumentos()
    if args.workers < 1 or args.chunksize < 1:
        raise SystemExit("ERRO: --workers e --chunksize precisam ser >= 1.")
    inicio = agora_iso()
    t0 = time.perf_counter()

    # 1) PREPARO (serial): lista as imagens e cria as pastas
    imagens = listar_imagens(args.entrada, args.limite)
    preparar_saida(args.saida)
    t1 = time.perf_counter()

    # 2) PROCESSAMENTO PARALELO
    ctx = mp.get_context("spawn")            # o mesmo método de início do Windows, em qualquer sistema
    hist_raw, cont_raw = estado.criar_memoria(ctx)
    if args.modo == "processos":
        trava = ctx.Lock()
        pool = ctx.Pool(args.workers, initializer=estado.iniciar, initargs=(trava, hist_raw, cont_raw))
    else:
        trava = threading.Lock()
        estado.iniciar(trava, hist_raw, cont_raw)   # threads dividem o mesmo processo: inicia uma vez só
        pool = ThreadPool(args.workers)
    tarefa = tarefa_trava_fina if args.trava == "fina" else tarefa_trava_grossa

    manifesto: dict[str, str] = {}
    ocupado: dict[str, float] = {}       # tempo que cada fluxo passou dentro de tarefas
    ultimo_fim: dict[str, float] = {}    # quando cada fluxo terminou sua última tarefa
    primeiro_inicio = float("inf")
    progresso = Progresso(len(imagens), args.progresso)
    with pool:
        funcao = partial(tarefa, pasta_saida=str(args.saida))
        caminhos = [str(p) for p in imagens]
        for nome, sha256, fluxo, t_ini, t_fim in pool.imap_unordered(funcao, caminhos, chunksize=args.chunksize):
            manifesto[nome] = sha256
            ocupado[fluxo] = ocupado.get(fluxo, 0.0) + (t_fim - t_ini)
            ultimo_fim[fluxo] = max(ultimo_fim.get(fluxo, 0.0), t_fim)
            primeiro_inicio = min(primeiro_inicio, t_ini)
            progresso.avancar()
        pool.close()
        pool.join()
    t2 = time.perf_counter()

    # 3) FINAL (serial): lê o estado global e grava os resultados
    histograma, contadores = estado.ler(hist_raw, cont_raw)
    estatisticas = gravar_resultados(args.saida, manifesto, histograma, contadores["imagens"], contadores["pixels"])
    t3 = time.perf_counter()

    fim_da_ultima = max(ultimo_fim.values())
    janela = fim_da_ultima - primeiro_inicio
    execucao = {
        "versao": "par", "modo": args.modo, "trava": args.trava, "workers": args.workers,
        "chunksize": args.chunksize,
        "entrada": str(args.entrada), "saida": str(args.saida), "limite": args.limite,
        "imagens": contadores["imagens"], "pixels": contadores["pixels"],
        "t_total_s": t3 - t0, "t_preparo_s": t1 - t0, "t_processamento_s": t2 - t1, "t_final_s": t3 - t2,
        "espera_trava_s": contadores["espera_trava_s"], "dentro_trava_s": contadores["dentro_trava_s"],
        "inicio_primeira_tarefa_s": primeiro_inicio - t1,
        "cauda_s": fim_da_ultima - min(ultimo_fim.values()),
        "ocupacao": sum(ocupado.values()) / (args.workers * janela),
        "fluxos_usados": len(ocupado),
        "media_rgb": estatisticas["media_rgb"], "desvio_rgb": estatisticas["desvio_rgb"],
        "impressao_digital": estatisticas["impressao_digital"],
        "inicio": inicio, "ambiente": info_ambiente(),
    }
    gravar_json(Path(args.saida) / "execucao.json", execucao)
    imprimir_resumo(execucao)


if __name__ == "__main__":
    main()
```

**Explicação passo a passo do `main()`**

1. **Preparo (serial):** igual ao `seq.py`, com as mesmas funções da Pessoa 1.
2. **Contexto `spawn` e memória:** `mp.get_context("spawn")` e `estado.criar_memoria(ctx)`. A trava e o `Pool`
   são criados pelo mesmo contexto.
3. **Pool de processos:** `ctx.Pool(args.workers, initializer=estado.iniciar, initargs=(...))`. Cada processo
   recebe a trava e a memória uma única vez, ao nascer.
4. **Modo threads (experimento):** `ThreadPool` com `threading.Lock`, e `estado.iniciar` chamado uma vez só. O
   resto do código é idêntico, o que deixa a comparação justa.
5. **Tarefas:** `tarefa_trava_fina` processa a imagem fora da trava e chama `estado.mesclar()`.
   `tarefa_trava_grossa` (experimento) põe a trava em volta de tudo. As duas devolvem só o nome, o SHA-256,
   quem processou e os instantes de início e fim. O histograma não volta pelo canal: vai direto para a memória
   compartilhada.
6. **Coleta:** o laço do `imap_unordered` monta o manifesto e soma o tempo ocupado de cada fluxo.
   `pool.close()` e `pool.join()` esperam os processos terminarem; esse tempo entra no processamento, porque é
   custo da versão paralela.
7. **Final (serial):** lê o estado global e grava os resultados com as funções da Pessoa 1.

**As medidas extras** (vão para o `execucao.json` e para a análise da Pessoa 4):

- `espera_trava_s`: soma, em todos os processos, do tempo esperando a trava ficar livre. Perto de zero na trava
  fina; enorme na trava grossa.
- `inicio_primeira_tarefa_s`: quanto tempo o `Pool` levou para começar a primeira tarefa. É o custo de criar os
  processos (no Windows, cada um é um `python.exe` novo que importa Pillow e NumPy).
- `cauda_s`: diferença entre o primeiro e o último fluxo a terminar. Mede a divisão desigual no fim do lote.
- `ocupacao`: fração do tempo em que os fluxos estavam dentro de tarefas. Atenção: o tempo esperando a trava ou
  o GIL conta como "dentro da tarefa", então no modo threads e na trava grossa a ocupação continua alta mesmo
  sem ganho. Quem explica essa diferença são a espera pela trava e o próprio tempo total.

**Saída esperada** (exemplo real, com `--limite 100 --workers 2 --progresso 50`):

```text
      50/100 imagens ( 50.0%)       2.2 s
     100/100 imagens (100.0%)       3.8 s
========================================================================
VERSAO PARALELA | 2 processos | trava fina | chunksize 4
Imagens: 100 | pixels: 26214400
Tempo total: 3.86 s  (preparo 0.00 s | processamento 3.85 s | final 0.00 s)
Espera pela trava: 0.3 ms | dentro da trava: 1.9 ms | cauda: 0.20 s | ocupação: 97.0%
Média RGB: [126.3267, 123.4042, 127.0195] | desvio RGB: [83.9809, 78.151, 80.7383]
Impressão digital: a4a8b7e96f80fd7e
========================================================================
```

### 5.5 Os experimentos: threads e trava grossa

Servem para o relatório e para a bateria da Pessoa 4; **não entram na demonstração**. Com 2 fluxos e 100
imagens, no protótipo:

`python par.py --limite 100 --workers 2 --modo threads --saida saida_threads --progresso 0`

```text
========================================================================
VERSAO PARALELA | 2 threads | trava fina | chunksize 4
Imagens: 100 | pixels: 26214400
Tempo total: 6.00 s  (preparo 0.00 s | processamento 6.00 s | final 0.00 s)
Espera pela trava: 0.2 ms | dentro da trava: 2.1 ms | cauda: 0.25 s | ocupação: 97.9%
Média RGB: [126.3267, 123.4042, 127.0195] | desvio RGB: [83.9809, 78.151, 80.7383]
Impressão digital: a4a8b7e96f80fd7e
========================================================================
```

`python par.py --limite 100 --workers 2 --trava grossa --saida saida_grossa --progresso 0`

```text
========================================================================
VERSAO PARALELA | 2 processos | trava grossa | chunksize 4
Imagens: 100 | pixels: 26214400
Tempo total: 7.21 s  (preparo 0.00 s | processamento 7.20 s | final 0.00 s)
Espera pela trava: 6736.3 ms | dentro da trava: 6992.9 ms | cauda: 0.25 s | ocupação: 98.1%
Média RGB: [126.3267, 123.4042, 127.0195] | desvio RGB: [83.9809, 78.151, 80.7383]
Impressão digital: a4a8b7e96f80fd7e
========================================================================
```

Compare com os 3,86 s dos processos com trava fina (seção 5.4) e os 7,06 s da sequencial. As threads ficaram em
~1,2×. A trava grossa ficou **mais lenta que a sequencial**, com 6,7 s de espera pela trava: os processos
passaram o tempo esperando uns pelos outros. As três versões produziram a mesma impressão digital: todas são
corretas, e só a trava fina é paralela.

## 6. Testes de aceitação (definição de pronto)

Rode cada teste no PowerShell, na pasta do projeto, com o ambiente virtual ativado.

**6.1 `estado.py`**

```powershell
python -c "import multiprocessing as mp, numpy as np, estado; ctx = mp.get_context('spawn'); h, c = estado.criar_memoria(ctx); estado.iniciar(ctx.Lock(), h, c); estado.mesclar(np.ones(768, dtype=np.int64), 10); hist, cont = estado.ler(h, c); print(int(hist.sum()), cont['imagens'], cont['pixels'])"
```

Esperado: `768 1 10`.

**6.2 `teste_corrida.py`:** `python teste_corrida.py`. Esperado: as 3 rodadas "SEM trava" terminam com
`PERDEU ATUALIZAÇÕES`, cada uma com um valor diferente, e as 3 "COM trava" terminam com `OK` e
`contador 80000/80000`. Rode 2 ou 3 vezes para ver que o comportamento se repete.

**6.3 `par.py` × `seq.py`** (depois do M1):

```powershell
python seq.py --limite 100
python par.py --limite 100
python verificar.py saida_seq saida_par          # RESULTADO: IDÊNTICO
```

**6.4 Estabilidade e experimentos**

```powershell
python par.py --limite 300 --saida saida_a --progresso 0
python par.py --limite 300 --saida saida_b --progresso 0
python par.py --limite 300 --saida saida_c --progresso 0 --workers 2
python verificar.py saida_a saida_b              # IDÊNTICO
python verificar.py saida_a saida_c              # IDÊNTICO (número de processos diferente, mesmo resultado)
python par.py --limite 100 --modo threads --saida saida_threads --progresso 0
python par.py --limite 100 --trava grossa --saida saida_grossa --progresso 0
python verificar.py saida_seq saida_threads      # IDÊNTICO
python verificar.py saida_seq saida_grossa       # IDÊNTICO
Remove-Item -Recurse -Force saida_a, saida_b, saida_c, saida_threads, saida_grossa
```

- [ ] Todas as verificações terminam em IDÊNTICO.
- [ ] No Gerenciador de Tarefas (aba Desempenho → CPU), a versão paralela ocupa todos os núcleos, e a
  sequencial, um.
- [ ] A espera pela trava na trava fina fica em milissegundos; na trava grossa, em segundos.

## 7. Suas seções do relatório (≈ 2 páginas)

Escreva em `relatorio\secao2_estrategia.md` e `relatorio\secao3_secao_critica.md` e entregue à Pessoa 4 até
domingo, 14:00. Troque o que está entre `[[ ]]` pelos valores reais (da `resultados\tabela_tempos.md`).

> **2. Estratégia de paralelização**
>
> O problema tem paralelismo de dados: as [[N]] imagens são independentes. Usamos o padrão mestre–trabalhadores
> com um `multiprocessing.Pool` de p processos. O processo principal lista as imagens e as distribui com
> `imap_unordered` em pacotes de 4 (`chunksize=4`): cada processo que termina um pacote recebe o próximo, o que
> equilibra a carga dinamicamente. Cada processo executa a mesma função por imagem da versão sequencial e soma o
> histograma da imagem no estado global compartilhado. Ao processo principal volta apenas o nome da imagem e o
> SHA-256 do arquivo gerado. Os processos são criados pelo método `spawn`, o padrão do Windows.
>
> **Processos, e não threads, pela natureza do trabalho.** O trabalho é limitado por processador: decodificar,
> filtrar e codificar imagens. No CPython, o GIL impede que duas threads executem código Python ao mesmo tempo
> no mesmo processo. O Pillow libera o GIL em parte das operações (decodificação, redimensionamento, unsharp),
> mas o filtro de mediana, cerca de 2/3 do tempo de cada imagem, é executado segurando o GIL. Medimos na mesma
> máquina e com a mesma entrada: com [[p]] fluxos, processos levaram [[T_proc]] s (speedup [[S_proc]]) e threads
> levaram [[T_threads]] s (speedup [[S_threads]]). Cada processo tem o seu próprio interpretador e o seu próprio
> GIL, por isso escala.

> **3. Seção crítica e primitiva**
>
> **Estado compartilhado.** O histograma RGB do lote inteiro (768 inteiros de 64 bits) e quatro contadores
> (imagens, pixels, tempo de espera e tempo dentro da trava), em memória compartilhada criada com
> `multiprocessing.RawArray`, que não tem trava própria. Todos os processos escrevem nesse estado.
>
> **Seção crítica.** Função `mesclar()` do arquivo `estado.py`, linhas [[49 a 54]]: a soma do
> histograma da imagem no histograma global e a atualização dos contadores. Cada soma é uma operação de ler,
> somar e escrever; sem proteção, duas escritas simultâneas fazem uma atualização se perder.
>
> **Primitiva: `multiprocessing.Lock`.** O recurso é único e exige exclusão mútua, o caso de uma trava (um
> semáforo binário). A trava chega aos processos pelo `initializer` do `Pool`, na criação de cada um, e é
> sempre usada com `with`, o que a libera mesmo em caso de erro; como é a única trava, não há risco de
> deadlock. Ela cobre só a soma, e não o processamento: na bateria, os processos passaram em média
> [[espera]] ms esperando pela trava numa execução de [[T_par]] s.
>
> **O teste que mostra o resultado estável.** O programa `teste_corrida.py` faz 4 processos somarem 20.000 vezes
> no mesmo estado global. Sem a trava, as três rodadas terminaram com [[valores]] em vez de 80.000, um valor
> diferente a cada rodada; com a trava, as três terminaram com exatamente 80.000. No programa completo, todas as
> [[n]] execuções da bateria, sequenciais e paralelas, produziram a mesma impressão digital
> (`[[impressão]]`). Como contraexemplo, a mesma trava em volta do processamento inteiro manteve o resultado
> correto, mas levou [[T_grossa]] s (speedup [[S_grossa]]), porque os processos passaram [[espera_grossa]] s
> esperando uns pelos outros.

Inclua no relatório o trecho do `estado.py` com a função `mesclar()` inteira, com os números de linha.

## 8. Sua parte da apresentação (2:00–4:00)

**Slides (2):**

1. *A seção crítica.* O trecho da função `mesclar()` com as linhas da trava destacadas; "Primitiva:
   `multiprocessing.Lock`"; "Protege: histograma global (768 inteiros) + contadores"; "Fora da trava: o
   processamento da imagem (~60 ms). Dentro: a soma (~µs)".
2. *Por que funciona.* Pequena tabela do `teste_corrida.py` (sem trava: valores errados e diferentes; com trava:
   80.000 sempre) e a linha "trava em volta de tudo: correto, mas [[S_grossa]]×".

**Roteiro falado (~2 min):**

- (2:00) "Nosso estado compartilhado é o histograma global do lote, 768 inteiros em memória compartilhada, que
  todos os processos escrevem. A seção crítica é esta função: somar o histograma de uma imagem no global."
- (2:20) "Usamos um `multiprocessing.Lock`, uma trava de exclusão mútua: um recurso, um processo por vez. Ela
  cobre só a soma, que leva microssegundos. O processamento da imagem, que leva dezenas de milissegundos, fica
  fora. Se a trava cobrisse tudo, o programa continuaria certo, mas seria serial."
- (2:50) **Ação ao vivo**, no terminal 2: `.\demo.ps1 -Etapa corrida`. Enquanto roda: "Aqui 4 processos
  somam 20 mil vezes no mesmo estado. Sem a trava, olhem: cada rodada perde atualizações e dá um número
  diferente. Com a trava, sempre 80 mil."
- (3:30) **Ação ao vivo:** `.\demo.ps1 -Etapa estavel`. "E aqui o programa de verdade roda duas vezes com a
  mesma entrada: a impressão digital é a mesma e o verificador diz IDÊNTICO. Esse é o resultado estável."

Cronometre o `corrida` e o `estavel` na máquina da demo durante o ensaio: somados, eles não podem passar de
~1 minuto, senão a sua parte estoura os 4:00.

## 9. Arguição

### 9.1 O que você precisa dominar na sua parte

- O que é condição de corrida, com o exemplo do `+=` (ler, somar, escrever).
- Onde está a seção crítica (arquivo, função e linhas) e por que ela é tão curta.
- Por que `Lock` e não `Semaphore`, `RLock` ou monitor (`Condition`).
- Por que `RawArray` com uma trava explícita, e não `Value`/`Array` com trava própria (pergunta 11 do banco).
- Por que o tipo `"q"` (64 bits) e não `"l"` (32 bits no Windows).
- O que o `spawn` muda e por que a trava vai pelo `initializer`.
- Por que não há deadlock (uma trava, sempre com `with`, nunca aninhada).
- Por que rodar o programa sem trava e dar certo não prova nada (pergunta 8 do banco).
- O que `imap_unordered` e `chunksize` fazem.

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
| `RuntimeError: Lock objects should only be shared between processes through inheritance` | A trava foi passada como argumento de tarefa | A trava só vai pelo `initializer`/`initargs` do `Pool` (código de referência) |
| `AttributeError: Can't get attribute 'tarefa_...' on <module '__main__'>` | Função definida dentro de outra, `lambda`, ou programa rodado de dentro de um notebook ou do console interativo | Funções no nível do módulo; rode sempre `python par.py` no PowerShell |
| O programa recomeça sozinho várias vezes ou trava | Falta o `if __name__ == "__main__":` | Use o código de referência como está |
| `ModuleNotFoundError: No module named 'comum'` | Ainda não fez `git pull` depois do M1 da Pessoa 1, ou está fora da pasta do projeto | `git pull --rebase` e `cd C:\projetos\lote-imagens` |
| `verificar.py` diz DIVERGENTE entre seq e par | Pastas geradas com `--limite` diferentes, ou alguém mudou o pipeline entre as execuções | Rode as duas com o mesmo `--limite`; confira `git status` |
| A paralela não fica mais rápida | Notebook na bateria ou modo de economia de energia; `--workers 1` | Tomada, modo "Melhor desempenho"; confira o número de processos no resumo |
| `teste_corrida.py` "SEM trava" deu OK numa rodada | Raro, mas possível numa máquina muito carregada | Rode de novo; na demonstração, rode o teste inteiro (3 rodadas) |
