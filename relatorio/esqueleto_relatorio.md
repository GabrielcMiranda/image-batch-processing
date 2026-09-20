# Esqueleto do relatório (montagem: Pessoa 4)

Máximo de 6 páginas. Margens de 2 cm, fonte 11 pt, espaçamento simples.
Cole aqui as seções que cada um entregar até domingo, 14:00, e exporte em
`relatorio\relatorio_etapa1.pdf`.

---

## Cabeçalho (P4)

**Processamento de imagens em lote: versão sequencial e versão paralela**

Projeto de Solução Distribuída - Etapa 1
Sistemas Distribuídos e Paralelos (070080) · Prof. Fábio Rocha de Araújo
Turma: [[CC6NA / CC6MA]] · Data: [[dd/mm/2026]]

Integrantes: [[P1]], [[P2]], [[P3]], [[P4]]

Repositório: [[link do repositório]]

---

## 1. Problema e dados (P1, 0,75 pág.)

Tem que conter: **o problema**; o dataset; a unidade de trabalho; o volume de entrada; como o
resultado é verificado.

[[colar aqui]]

---

## 2. Estratégia de paralelização (P2, 1 pág.)

Tem que conter: **a estratégia**; **processos x threads justificado pela natureza do trabalho**,
com números.

[[colar aqui]]

---

## 3. Seção crítica e primitiva (P2, 1 pág.)

Tem que conter: **a seção crítica no código (arquivo e linhas) e a primitiva que a protege**; o
teste de corrida; a prova de resultado estável.

[[colar aqui]]

---

## 4. Recursos provisionados (P3, 0,75 pág.)

Tem que conter: **os recursos** (a máquina); **o que fica em cada porta e a origem de cada regra**.

[[colar aqui]]

---

## 5. Medição e speedup (P4, 1,5 pág.)

Tem que conter: **tempos medidos** (mais de uma vez, mesma máquina e mesma entrada); **speedup**;
**teto de Amdahl**. Figura obrigatória: `resultados\speedup.png`.

[[colar de relatorio\secao5_medicao.md]]

---

## 6. O que limitou o ganho (P4, 0,75 pág.)

Tem que conter: **o que limitou** - comunicação, divisão desigual, espera na seção crítica e
hardware.

[[colar de relatorio\secao6_limites.md]]

---

## Conferência antes de exportar (P4)

- [ ] No máximo 6 páginas.
- [ ] O link do repositório está no cabeçalho.
- [ ] Todos os itens em negrito acima aparecem no texto.
- [ ] As duas tabelas da `resultados\tabela_tempos.md` estão coladas.
- [ ] A figura `speedup.png` está inserida (largura ~14 cm) e legendada; `tempos.png` se couber.
- [ ] O trecho da `mesclar()` com números de linha (P2) está na seção 3.
- [ ] PDF salvo como `relatorio\relatorio_etapa1.pdf` e subido no Git.
- [ ] Segunda, até 12:00: PDF e link postados no ambiente virtual.
