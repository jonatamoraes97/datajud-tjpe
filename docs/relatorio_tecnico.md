# Relatório técnico — Pipeline DataJud TJPE

## Resumo técnico

Foi implementado e validado um pipeline em Python que extrai 1.000 processos do TJPE da API pública DataJud, normaliza o JSON e carrega nove tabelas relacionadas no PostgreSQL. O recorte cobre os três meses completos de maio, junho e julho de 2026. As validações encontraram zero duplicidades, zero registros órfãos e zero processos fora do período. O Alteryx não pôde ser executado por falta de acesso à licença; por isso, a entrega inclui uma especificação explícita do workflow equivalente, sem afirmar que foi testado na ferramenta.

## A carga produziu 1.000 processos íntegros

| Métrica | Definição | Resultado |
|---|---|---:|
| Processos | Linhas em `processo` | 1.000 |
| Associações | Linhas em `processo_assunto` | 1.258 |
| Movimentos | Linhas em `movimento` | 16.315 |
| Complementos | Linhas em `movimento_complemento` | 11.464 |
| Duplicidades | Violações das chaves naturais testadas | 0 |
| Órfãos | Filhos sem pai nas quatro relações | 0 |
| Fora do período | Ajuizamento antes de maio ou a partir de agosto | 0 |

Evidência: [captura da carga](../evidencias/04_carga_1000_concluida.png), [integridade referencial](../evidencias/05_integridade_referencial.png) e [resumo de validação](../evidencias/06_resumo_validacao.png).

## O recorte e as métricas foram definidos antes da carga

O conjunto analisado contém processos do índice público do TJPE com `dataAjuizamento` entre `20260501000000` inclusive e `20260801000000` exclusive. A unidade principal é um processo único pelo campo `id`. Movimento é cada item posicional da lista `movimentos`; complemento é cada item de `complementosTabelados`; associação é cada par único entre processo e assunto.

A API foi consultada com páginas de 200 registros, ordenação estável por `id.keyword` e continuação por `search_after`. Cinco páginas completaram o limite de 1.000 processos. O JSON bruto foi salvo para permitir reprocessamento sem depender novamente da API.

## A normalização separou repetições e preservou a estrutura

O esquema em 3FN separa classe, sistema, formato, órgão julgador e assunto. `processo` referencia as dimensões; `movimento` referencia o processo; `movimento_complemento` referencia o movimento; e `processo_assunto` resolve a relação muitos-para-muitos. As chaves estrangeiras impedem filhos sem pai e as restrições únicas evitam repetir sequências dentro do mesmo pai.

O [DER](der.md), a [descrição da modelagem](modelagem_relacional.md) e o [DDL](../sql/01_schema.sql) permitem auditar a estrutura.

## As ausências foram tratadas como qualidade da origem

A carga encontrou 4 assuntos distintos sem nome e 112 movimentos sem nome. Esses campos foram mantidos como `NULL`, pois são opcionais na prática e preencher valores artificiais prejudicaria a fidelidade. Também foi identificado um processo com uma lista adicional envolvendo os assuntos; o pipeline achata listas recursivamente antes da normalização.

Não foram encontrados movimentos sem órgão no recorte final, embora o esquema permita o campo nulo porque a exploração inicial mostrou que ele pode não aparecer. A ausência de complementos gera zero linhas filhas, o que é diferente de um erro.

## Método de execução e validação

1. explorar cinco registros e mapear tipos e listas;
2. testar duas páginas e confirmar IDs únicos;
3. criar as nove tabelas no PostgreSQL;
4. coletar cinco páginas de 200 processos;
5. normalizar e carregar dentro de uma transação;
6. validar volumes, período, duplicidades, campos opcionais e integridade referencial.

A versão atual realiza carga completa com `TRUNCATE ... RESTART IDENTITY CASCADE`. Esse método é adequado ao volume do case, deixa o reprocessamento determinístico e reduz a complexidade de uma primeira versão.

## Limitações e robustez

- Os 1.000 registros não são uma amostra aleatória nem representam todo o TJPE.
- O total `gte` retornado pela API é um limite inferior.
- A robustez foi verificada por chaves, período, ausência de duplicidade e relações; não houve teste de carga em escala de produção.
- O pipeline lida com listas adicionais de assuntos e campos opcionais observados, mas uma mudança estrutural futura da API pode exigir atualização.
- A especificação Alteryx não equivale a uma execução real na ferramenta.

## Próximos passos recomendados

1. implementar e executar o workflow no Alteryx quando a licença estiver disponível;
2. comparar os volumes do Alteryx com o mesmo JSON bruto e as consultas SQL;
3. evoluir para carga incremental por `dataHoraUltimaAtualizacao`;
4. adicionar uma tabela de controle de execução e registros rejeitados se o pipeline for usado em produção.

## Perguntas ainda abertas

- Qual é a frequência real de atualização esperada para o processo seletivo?
- A empresa espera manter histórico de versões do mesmo processo ou apenas o estado mais recente?
- Há uma política definida para retenção do JSON bruto e para rotação da chave pública?

Fontes: [documentação pública DataJud](https://datajud-wiki.cnj.jus.br/api-publica/), arquivo bruto `samples/processos_maio_julho_2026.json`, scripts e consultas desta entrega.

