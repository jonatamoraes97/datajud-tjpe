# Exploração da API DataJud - TJPE

## Objetivo

Iniciamos o projeto pela exploração, antes da modelagem, para identificar os tipos e as estruturas dos dados com os quais estamos trabalhando, como textos, números inteiros, datas, objetos e listas.

## Requisição inicial

- Endpoint: [Consulta pública do TJPE](https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search)
- Método HTTP: POST
- Quantidade solicitada: 5 processos
- Tipo de consulta: match_all
- Status recebido: 200

## Estrutura geral da resposta

hits.hits = lista de documentos
_index, _id e _score = metadados do Elasticsearch
_source = dados públicos do processo

## Estrutura dos processos

- Campos simples: id, tribunal, grau, numeroProcesso, dataAjuizamento,
nivelSigilo, dataHoraUltimaAtualizacao e @timestamp.
- Objetos: orgaoJulgador, classe, sistema e formato.
- Listas: movimentos e assuntos.

## Cardinalidades observadas

- Quantidade de processos: 5 processos
- Quantidade total de assuntos: 5 assuntos
- Quantidade total de movimentos: 53 movimentos
- Quantidade total de complementos: 26 complementos tabelados
- Menor e maior quantidade de movimentos por processo: maior 18, menor 3

## Variações e inconsistências observadas

- O formato Data e Hora é no formato compacto. Ex: 20260227000000 (yyyyMMddHHmmss). Ano, mês, dia, hora, minutos e segundos.  
- As informações de dataHoraUltimaAtualizacao e @timestamp vieram em ISO-8601 com UTC.
- orgaoJulgador.codigo foi inteiro no processo e texto nos movimentos.

## Campos opcionais

27 dos 53 movimentos dos processos não possuem o campo complementosTabelados

Na amostra ampliada do teste de paginação, foram analisados 10 processos e 254 movimentos. Nessa amostra, os 254 movimentos não apresentaram o objeto orgaoJulgador e 81 não apresentaram complementosTabelados. Isso confirmou que esses campos devem ser tratados como opcionais.

## Limitações da exploração

hits.total.value = 10000
hits.total.relation = "gte"
A API informa que existem pelo menos 10.000 documentos correspondentes à consulta, mas esse valor não representa uma contagem exata. Apesar disso, somente 5 processos foram solicitados e retornados nesta exploração inicial.

Essa primeira exploração de dados foi feita utilizando inicialmente 5 processos, então em momento algum esses processos representam o total da base de dados do sistema jurídico.

## Teste de paginação

Nesta etapa, foram consultadas duas páginas com cinco registros cada. Os resultados foram ordenados de forma crescente pelo campo id.keyword. O valor do campo sort do último registro da primeira página foi enviado no parâmetro search_after da segunda requisição, permitindo continuar a consulta a partir desse ponto. Foram obtidos 10 processos únicos, sem identificadores repetidos. Essa estratégia reduz o risco de duplicações durante a coleta de pelo menos 1.000 processos.

## Qualidade na amostra final

Na extração final de 1.000 processos não foram encontrados identificadores de processo duplicados. Foram observados 1.258 registros de assuntos, dos quais 11 não possuíam nome, e 16.315 movimentos, dos quais 112 não possuíam nome. Esses campos foram definidos como opcionais no modelo para preservar os registros sem inventar valores. Também foram encontrados 6.486 movimentos sem complementos tabelados, situação tratada como uma lista vazia durante a carga.

Um dos processos apresentou dois assuntos dentro de listas adicionais. O pipeline aplica o achatamento dessas listas antes da carga, mantendo os assuntos como registros individuais na tabela associativa.
