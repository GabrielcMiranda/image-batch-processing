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
