# Modelagem Relacional do DataJud - TJPE

## Objetivo

O objetivo desta etapa é transformar os dados JSON extraídos da API DataJud em tabelas relacionais, facilitando consultas e atualizações, reduzindo a repetição desnecessária de dados e permitindo relacionar processos, movimentos e assuntos por meio de chaves.

## Entidades identificadas

| Entidade | Origem no JSON | Motivo |
|---|---|---|
| processo | _source | É a entidade central e possui identificação própria por meio do campo id. |
| orgao_julgador | orgaoJulgador | Possui código e nome e pode aparecer em vários processos e movimentos. |
| classe | classe | Possui código e nome e pode ser compartilhada por vários processos. |
| sistema | sistema | Identifica o sistema processual utilizado, por exemplo, o PJe. |
| formato | formato | Identifica se o processo é eletrônico ou físico. |
| assunto | assuntos[] | Um processo pode possuir um ou vários assuntos. |
| movimento | movimentos[] | Um processo pode possuir vários movimentos processuais. |
| movimento_complemento | movimentos[].complementosTabelados[] | Um movimento pode possuir vários complementos ou nenhum. |
| processo_assunto | Criada na modelagem | Relaciona processos e assuntos, formando um relacionamento muitos-para-muitos. |

## Relacionamentos e cardinalidades

| Entidade de origem | Cardinalidade | Entidade de destino | Explicação |
|---|---|---|---|
| classe | 1:N | processo | Uma classe pode estar relacionada a vários processos, mas cada processo possui uma classe. |
| sistema | 1:N | processo | Um sistema pode ser utilizado por vários processos, mas cada processo possui um sistema. |
| formato | 1:N | processo | Um formato pode estar relacionado a vários processos, mas cada processo possui um formato. |
| orgao_julgador | 1:N | processo | Um órgão julgador pode estar relacionado a vários processos. |
| processo | 1:N | movimento | Um processo pode possuir vários movimentos. |
| orgao_julgador | 1:N (opcional no movimento) | movimento | Um órgão julgador pode aparecer em vários movimentos, mas o campo pode não ser enviado pela API. |
| processo | N:N | assunto | Um processo pode possuir vários assuntos e um assunto pode aparecer em vários processos. |
| processo | 1:N | processo_assunto | Um processo pode aparecer várias vezes na tabela associativa. |
| assunto | 1:N | processo_assunto | Um assunto pode aparecer várias vezes na tabela associativa. |
| movimento | 1:0..N | movimento_complemento | Um movimento pode não possuir complemento ou possuir vários. |

## Chaves primárias e estrangeiras

| Tabela | Chave primária | Chaves estrangeiras | Justificativa |
|---|---|---|---|
| processo | id | classe_codigo, sistema_codigo, formato_codigo, orgao_julgador_codigo | O campo id vem da API e identifica o processo no DataJud. |
| classe | codigo | Nenhuma | O código identifica a classe processual. |
| sistema | codigo | Nenhuma | O código identifica o sistema processual. |
| formato | codigo | Nenhuma | O código identifica o formato do processo. |
| orgao_julgador | codigo | Nenhuma | O código identifica o órgão julgador no escopo do TJPE. |
| assunto | codigo | Nenhuma | O código identifica o assunto processual. |
| processo_assunto | processo_id + assunto_codigo | processo_id, assunto_codigo | A chave composta impede que o mesmo assunto seja associado duas vezes ao mesmo processo. |
| movimento | movimento_id | processo_id, orgao_julgador_codigo (opcional) | A API não fornece um identificador exclusivo para cada movimento, portanto será criada uma chave substituta. |
| movimento_complemento | movimento_complemento_id | movimento_id | A API não fornece um identificador exclusivo para cada complemento. |

## Colunas e tipos de dados

### Tabelas de referência

| Tabela | Coluna | Tipo PostgreSQL | Obrigatória? |
|---|---|---|---|
| classe | codigo | bigint | Sim |
| classe | nome | text | Sim |
| sistema | codigo | bigint | Sim |
| sistema | nome | text | Sim |
| formato | codigo | bigint | Sim |
| formato | nome | text | Sim |
| orgao_julgador | codigo | bigint | Sim |
| orgao_julgador | nome | text | Sim |
| orgao_julgador | codigo_municipio_ibge | bigint | Não |
| assunto | codigo | bigint | Sim |
| assunto | nome | text | Não |

### Tabela processo

| Coluna | Tipo PostgreSQL | Obrigatória? | Motivo |
|---|---|---|---|
| id | text | Sim | Identificador fornecido pelo DataJud. |
| tribunal | text | Sim | Sigla do tribunal, neste caso TJPE. |
| grau | text | Sim | Grau ou instância do processo. |
| numero_processo | text | Sim | Preserva os zeros à esquerda. |
| data_ajuizamento | timestamp | Sim | A origem não informa fuso horário nesse campo. |
| nivel_sigilo | smallint | Sim | É um código numérico de pequeno domínio. |
| classe_codigo | bigint | Sim | Chave estrangeira para classe. |
| sistema_codigo | bigint | Sim | Chave estrangeira para sistema. |
| formato_codigo | bigint | Sim | Chave estrangeira para formato. |
| orgao_julgador_codigo | bigint | Sim | Chave estrangeira para órgão julgador. |
| data_hora_ultima_atualizacao | timestamptz | Sim | A API envia esse campo em ISO-8601 com UTC. |
| timestamp_origem | timestamptz | Sim | Corresponde ao campo @timestamp da API. |
| data_carga | timestamptz | Sim | Registra quando o dado foi carregado no PostgreSQL. |

### Tabelas de movimentos e assuntos

| Tabela | Coluna | Tipo PostgreSQL | Obrigatória? |
|---|---|---|---|
| movimento | movimento_id | bigint identity | Sim |
| movimento | processo_id | text | Sim |
| movimento | sequencia | integer | Sim |
| movimento | codigo | bigint | Sim |
| movimento | data_hora | timestamptz | Sim |
| movimento | nome | text | Não |
| movimento | orgao_julgador_codigo | bigint | Não |
| movimento_complemento | movimento_complemento_id | bigint identity | Sim |
| movimento_complemento | movimento_id | bigint | Sim |
| movimento_complemento | sequencia | integer | Sim |
| movimento_complemento | codigo | bigint | Sim |
| movimento_complemento | descricao | text | Sim |
| movimento_complemento | valor | bigint | Sim |
| movimento_complemento | nome | text | Sim |
| processo_assunto | processo_id | text | Sim |
| processo_assunto | assunto_codigo | bigint | Sim |

O campo sequencia registra a posição do item dentro da lista original do JSON. Ele ajuda a manter a ordem e impede que a mesma posição seja carregada duas vezes para o mesmo processo ou movimento.

## Normalização em terceira forma normal

O modelo atende à terceira forma normal porque cada tabela representa um único assunto, como processo, classe ou movimento. Os nomes de classe, sistema, formato, órgão e assunto dependem dos seus respectivos códigos e não são repetidos na tabela processo. As listas do JSON foram separadas em tabelas próprias, e o relacionamento muitos-para-muitos entre processo e assunto foi resolvido pela tabela processo_assunto.
