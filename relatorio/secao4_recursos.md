# 4. Recursos provisionados

Toda a execução, medição e demonstração acontecem numa máquina local preparada pela equipe, sem uso de nuvem
(premissa combinada com o professor). O equivalente ao "grupo de segurança" pedido na lauda é o Firewall do
Windows, configurado por regras próprias do projeto.

**Máquina da demonstração**

| Item | Valor |
|---|---|
| Processador | 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz |
| Núcleos físicos | 4 |
| Núcleos lógicos (threads de hardware) | 8 |
| Memória RAM | 23,7 GB |
| Sistema operacional | Windows 11 (build 10.0.26200) |
| Python | 3.13.15 (instalação padrão, com GIL) |
| Pillow | 12.3.0 |
| NumPy | 2.5.3 |

A ficha completa, gerada automaticamente por `ficha_maquina.py`, fica em `infra/ficha_maquina.md`. A frequência
de clock relatada pelo Windows em repouso (1382 MHz) é menor que a base de 2,40 GHz porque o sistema reduz o
clock quando a CPU está ociosa; durante o processamento, o Turbo Boost eleva a frequência acima da base, o que
é discutido como um dos fatores de hardware na seção 6.

**Controle de acesso.** As regras de entrada do Firewall do Windows funcionam como o equivalente local de um
grupo de segurança na nuvem: por padrão, toda conexão de entrada é bloqueada, e só as portas explicitamente
liberadas aceitam tráfego.

| Porta | Protocolo | O que fica nela | Origem permitida |
|---|---|---|---|
| 8000 | TCP | Serviço: página de resultados (`python -m http.server 8000`) | Qualquer origem (é o serviço) |
| 22 | TCP | Administração: SSH (OpenSSH Server do Windows) | Só o IP de quem administra |
| Todas as outras | — | — | Bloqueadas (ação padrão de entrada = Bloquear) |

As regras são criadas por `infra/firewall_windows.ps1 -IpEquipe <ip>`, rodado como administrador, e ficam
agrupadas sob o nome "Lote Imagens" no Firewall do Windows com Segurança Avançada (`wf.msc`), o que permite
mostrá-las ao vivo na apresentação. O script também restringe a regra `OpenSSH-Server-In-TCP`, criada
automaticamente pela instalação do OpenSSH Server, que por padrão não limita a origem.

No dia da apresentação, o IP autorizado na porta 22 é atualizado para o IP da rede da sala de aula (o endereço
muda conforme a rede), e a máquina volta a ficar apenas com a porta 8000 aberta para o público e a 22 restrita
à equipe. Os detalhes de cada regra, incluindo o IP configurado no momento, ficam em
`infra/regras_de_acesso.md`.

**Por que núcleos físicos e lógicos importam.** A máquina tem 4 núcleos físicos e 8 lógicos, por Hyper-Threading
(dois fluxos de hardware compartilhando as unidades de execução de cada núcleo físico). Isso explica por que o
speedup medido cresce de forma quase linear até p = 4 e depois desacelera até p = 8, discutido nas seções 5 e
6: acima do número de núcleos físicos, os fluxos adicionais competem pelas mesmas unidades de execução, em vez
de ganhar capacidade de processamento nova.
