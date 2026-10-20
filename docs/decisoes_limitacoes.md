# Decisões técnicas e limitações

## Decisões adotadas

### Período

Foram usados três meses civis completos: de `2026-05-01 00:00:00` inclusive até `2026-08-01 00:00:00` exclusive. Isso evita incluir agosto incompleto na data da execução.

### Volume

O limite foi fixado em 1.000 processos, atendendo ao mínimo do case sem tornar a solução desnecessariamente grande. A paginação foi feita em cinco páginas de 200 registros.

### Paginação

Foi escolhido `search_after` com ordenação por `id.keyword`. Esse método usa o valor de ordenação do último registro para buscar a próxima página e evita repetir as primeiras linhas.

### Modelagem

O modelo foi normalizado até a terceira forma normal (3FN): dados repetidos como classe, sistema, formato, órgão e assunto foram separados, enquanto listas viraram tabelas filhas ou associativas. O relacionamento entre processo e assunto é muitos-para-muitos.

### Tipos e chaves

- `processo.id` é a chave primária recebida da API;
- `numero_processo` é texto para não ser usado em operações matemáticas nem perder zeros;
- códigos são inteiros grandes (`bigint`);
- datas foram convertidas para `timestamp` ou `timestamptz`;
- movimentos e complementos usam chaves substitutas, mas também têm restrições únicas por pai e sequência.

### Nulos

Valores ausentes em campos opcionais foram armazenados como `NULL`. Não foram inventados nomes como “desconhecido”, porque isso alteraria o dado da origem.

### Estratégia de carga

A entrega usa carga completa. Antes da inserção, as nove tabelas são limpas e as identidades reiniciadas. A carga ocorre em uma transação: qualquer erro desfaz o conjunto inteiro. Essa abordagem é simples de explicar e suficiente para o volume do teste.

## Qualidade encontrada na origem

- 4 assuntos distintos sem nome;
- 112 movimentos sem nome;
- nenhum movimento sem órgão julgador no recorte final;
- um processo com assuntos envolvidos em uma lista extra;
- nenhuma duplicidade após a normalização;
- nenhum registro órfão nas quatro relações testadas.

Esses achados são descritivos do recorte de 1.000 processos e não podem ser generalizados para todo o DataJud.

## Limitações

1. A API retorna `relation: gte` no total, indicando apenas que existem pelo menos tantos resultados.
2. O recorte contém os primeiros 1.000 registros segundo a ordenação escolhida; não é uma amostra aleatória.
3. Mudanças futuras no formato JSON podem exigir adaptação do parser.
4. A chave pública da API pode mudar e deve ser fornecida por variável de ambiente.
5. Não houve execução do Alteryx por indisponibilidade de licença. O fluxo está apenas especificado.
6. Não foram feitos testes de desempenho para volumes de produção.

## Evolução incremental proposta

Uma próxima versão poderia manter uma tabela de controle com a última `dataHoraUltimaAtualizacao` carregada:

1. ler a marca d'água da última execução bem-sucedida;
2. consultar processos atualizados depois dela;
3. fazer *upsert* das dimensões e do processo;
4. apagar e recarregar assuntos, movimentos e complementos apenas dos processos alterados;
5. validar a integridade;
6. atualizar a marca d'água somente após o `COMMIT`.

A substituição dos filhos do processo simplifica o tratamento de movimentos removidos ou alterados na origem.

