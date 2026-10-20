# Case DataJud — TJPE

Projeto de extração, transformação e carga de dados da API pública do DataJud (CNJ) para um banco PostgreSQL normalizado.

## Resultado

O pipeline consultou processos do TJPE ajuizados nos três meses completos de maio a julho de 2026, paginou a API e carregou:

| Métrica | Resultado |
|---|---:|
| Processos | 1.000 |
| Relações processo–assunto | 1.258 |
| Movimentos | 16.315 |
| Complementos de movimentos | 11.464 |
| Processos, movimentos ou complementos duplicados | 0 |
| Registros órfãos nas quatro relações verificadas | 0 |
| Processos fora do período | 0 |

Foram preservados como `NULL` os valores opcionais ausentes na origem: 4 assuntos e 112 movimentos ficaram sem nome. Esses casos não representam falha de carga.

## Arquitetura

```text
API DataJud/TJPE
      |
      | POST + paginação search_after
      v
Python (extração e normalização do JSON)
      |
      | transação e carga completa
      v
PostgreSQL (9 tabelas em 3FN)
```

O Python foi usado como alternativa executável porque não foi possível obter acesso ao Alteryx dentro do prazo. A especificação do mesmo fluxo no Alteryx está em [alteryx/especificacao_workflow.md](alteryx/especificacao_workflow.md). Ela não é apresentada como workflow executado.

## Estrutura do projeto

```text
datajud-tjpe/
├── alteryx/       # especificação do workflow equivalente
├── docs/          # exploração, modelo, DER, relatório e apresentação
├── evidencias/    # capturas que comprovam a execução
├── samples/       # amostras pequenas da resposta da API
├── scripts/       # exploração, paginação e pipeline final
├── sql/           # DDL, validações e consulta de demonstração
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Modelo relacional

O JSON foi decomposto em nove tabelas:

- dimensões: `classe`, `sistema`, `formato`, `orgao_julgador` e `assunto`;
- entidade principal: `processo`;
- tabelas filhas: `movimento` e `movimento_complemento`;
- associação muitos-para-muitos: `processo_assunto`.

O modelo, as chaves e as cardinalidades estão descritos em [docs/modelagem_relacional.md](docs/modelagem_relacional.md). O DER está em [docs/der.md](docs/der.md).

## Como executar

### 1. Pré-requisitos

- Python 3.13;
- PostgreSQL 18 ou versão compatível;
- banco chamado `datajud`;
- chave pública vigente da API DataJud.

### 2. Criar e ativar o ambiente

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 3. Criar as tabelas

Conecte-se ao banco `datajud` no pgAdmin e execute [sql/01_schema.sql](sql/01_schema.sql). O arquivo [sql/02_campos_opcionais.sql](sql/02_campos_opcionais.sql) só é necessário para atualizar uma versão anterior do esquema.

### 4. Definir credenciais sem gravá-las no código

```powershell
$env:DATAJUD_API_KEY = Read-Host "Chave da API DataJud"
$env:PGPASSWORD = Read-Host "Senha do PostgreSQL"
```

As demais variáveis aceitam os padrões do arquivo `.env.example`. Se o JSON bruto já existir em `samples`, o pipeline reutiliza o arquivo e não exige uma nova chamada à API. O arquivo bruto final é gerado localmente e não é versionado no GitHub.

### 5. Executar o pipeline

```powershell
python .\scripts\pipeline.py
```

O processo faz carga completa: limpa as nove tabelas, reinicia as identidades e recarrega tudo dentro de uma transação. Se ocorrer erro, a transação é desfeita.

### 6. Validar

No pgAdmin, execute:

1. [sql/03_validacoes.sql](sql/03_validacoes.sql) para as verificações detalhadas;
2. [sql/04_resumo_validacao.sql](sql/04_resumo_validacao.sql) para um resumo único;
3. [sql/05_consulta_exemplo.sql](sql/05_consulta_exemplo.sql) para demonstrar os relacionamentos.

## Tratamentos aplicados

- paginação com ordenação estável por `id.keyword` e `search_after`;
- conversão das datas compactas e ISO 8601 para tipos temporais do PostgreSQL;
- preservação de números de processo como texto;
- achatamento de listas de assuntos que vieram aninhadas de maneira inconsistente;
- manutenção de campos opcionais ausentes como `NULL`;
- criação de uma linha de movimento por posição no JSON e de uma linha de complemento por posição dentro do movimento;
- chaves primárias, estrangeiras e restrições `UNIQUE` para impedir duplicação e registros órfãos.

## Reprocessamento e evolução incremental

A versão entregue usa carga completa porque é simples, reproduzível e adequada ao volume do case. Uma evolução incremental usaria `dataHoraUltimaAtualizacao` como marca d'água: buscar processos alterados desde a última execução, fazer *upsert* do processo e substituir seus assuntos e movimentos na mesma transação. A marca d'água só seria atualizada após sucesso.

## Limitações

- A API informou total `gte`, portanto o total retornado por ela é um limite inferior, não necessariamente a quantidade completa do índice.
- A entrega usa os primeiros 1.000 registros segundo a ordenação definida, e não pretende representar estatisticamente todo o TJPE.
- Campos opcionais ou inconsistentes dependem da qualidade da origem.
- O workflow Alteryx não foi executado porque o acesso à licença permaneceu pendente.

## Documentação

- [Relatório técnico](docs/relatorio_tecnico.md)
- [Decisões e limitações](docs/decisoes_limitacoes.md)
- [Checklist de evidências](evidencias/README.md)
- [Documentação oficial da API DataJud](https://datajud-wiki.cnj.jus.br/api-publica/)

