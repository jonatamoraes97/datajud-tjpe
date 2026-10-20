# Diagrama Entidade-Relacionamento

O diagrama apresenta as tabelas, as chaves principais e os relacionamentos usados para transformar o JSON do DataJud em um modelo relacional.

```mermaid
erDiagram
    CLASSE ||--o{ PROCESSO : classifica
    SISTEMA ||--o{ PROCESSO : utiliza
    FORMATO ||--o{ PROCESSO : define
    ORGAO_JULGADOR ||--o{ PROCESSO : julga
    PROCESSO ||--o{ MOVIMENTO : possui
    ORGAO_JULGADOR o|--o{ MOVIMENTO : informa
    MOVIMENTO ||--o{ MOVIMENTO_COMPLEMENTO : possui
    PROCESSO ||--o{ PROCESSO_ASSUNTO : relaciona
    ASSUNTO ||--o{ PROCESSO_ASSUNTO : relaciona

    CLASSE {
        bigint codigo PK
        text nome
    }
    SISTEMA {
        bigint codigo PK
        text nome
    }
    FORMATO {
        bigint codigo PK
        text nome
    }
    ORGAO_JULGADOR {
        bigint codigo PK
        text nome
        bigint codigo_municipio_ibge
    }
    ASSUNTO {
        bigint codigo PK
        text nome
    }
    PROCESSO {
        text id PK
        text numero_processo
        timestamp data_ajuizamento
        bigint classe_codigo FK
        bigint sistema_codigo FK
        bigint formato_codigo FK
        bigint orgao_julgador_codigo FK
    }
    MOVIMENTO {
        bigint movimento_id PK
        text processo_id FK
        integer sequencia
        bigint codigo
        timestamptz data_hora
        bigint orgao_julgador_codigo FK
    }
    MOVIMENTO_COMPLEMENTO {
        bigint movimento_complemento_id PK
        bigint movimento_id FK
        integer sequencia
        bigint codigo
        bigint valor
    }
    PROCESSO_ASSUNTO {
        text processo_id PK, FK
        bigint assunto_codigo PK, FK
    }
```

O relacionamento entre processo e assunto é muitos-para-muitos e foi resolvido pela tabela associativa `processo_assunto`. O órgão julgador do movimento é opcional porque esse objeto não aparece em todos os resultados da API.



