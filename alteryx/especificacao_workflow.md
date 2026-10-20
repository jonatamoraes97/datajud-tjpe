# Especificação do workflow no Alteryx

## Status

Esta é a especificação do fluxo equivalente ao pipeline Python. O workflow não foi executado no Alteryx porque o acesso à licença permaneceu pendente durante o prazo do teste. A implementação funcional e validada foi realizada em Python e PostgreSQL.

## Desenho do fluxo

```text
Text Input / constantes
        |
Formula: URL, período, tamanho da página e token
        |
Download: POST na API TJPE
        |
JSON Parse
        |
Macro iterativa: obter hits e enviar search_after à próxima página
        |
Select + Formula: tipos e datas
        |
        +--> Processo e dimensões --> Unique --> Output Data
        +--> Assuntos -------------> Unique --> Output Data
        +--> Movimentos -----------> Unique --> Output Data
        +--> Complementos ---------> Unique --> Output Data
```

## Ferramentas e configuração

1. **Text Input**: uma linha com endpoint, data inicial `20260501000000`, data final `20260801000000` e tamanho da página `200`.
2. **Formula**: montar o corpo JSON da consulta e os cabeçalhos `Content-Type: application/json` e `Authorization: APIKey ...`. A chave deve ficar em uma constante do workflow, nunca escrita no canvas ou publicada.
3. **Download**: realizar `POST` em `https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search`.
4. **JSON Parse**: abrir `hits.hits`, guardar `_source` e o valor de `sort` do último registro.
5. **Macro iterativa**: enquanto houver registros e o limite de 1.000 não tiver sido atingido, acrescentar o último `sort` como `search_after` da próxima requisição.
6. **Select e Formula**: renomear campos, ajustar tipos e converter datas.
7. **Unique**: remover repetições por chave natural antes da carga.
8. **Output Data**: gravar no PostgreSQL seguindo a ordem indicada abaixo.

## Ramificações para normalização

| Saída | Origem no JSON | Chave usada |
|---|---|---|
| `classe` | `_source.classe` | `codigo` |
| `sistema` | `_source.sistema` | `codigo` |
| `formato` | `_source.formato` | `codigo` |
| `orgao_julgador` | `_source.orgaoJulgador` e órgão do movimento | `codigo` |
| `assunto` | `_source.assuntos[]` | `codigo` |
| `processo` | `_source` | `id` |
| `processo_assunto` | processo + `_source.assuntos[]` | processo e assunto |
| `movimento` | `_source.movimentos[]` | processo e sequência |
| `movimento_complemento` | `movimentos[].complementosTabelados[]` | movimento e sequência |

Para abrir listas, usar uma combinação de **JSON Parse**, **Text To Columns** quando necessário e **Cross Tab/Transpose** apenas se a versão do Alteryx exigir. As listas de assuntos devem ser achatadas antes da geração das saídas, pois foi encontrado um caso com uma lista extra envolvendo os assuntos.

## Regras de qualidade

- ausência de `complementosTabelados` significa zero complementos, não erro;
- `assunto.nome`, `movimento.nome` e o órgão do movimento podem ser nulos;
- número do processo deve permanecer texto;
- usar `DateTimeParse` para `yyyyMMddHHmmss` e para datas ISO 8601;
- aplicar `Unique` em processo, processo–assunto, movimento por sequência e complemento por sequência;
- rejeitar em uma saída de auditoria registros sem as chaves obrigatórias.

## Ordem da carga no PostgreSQL

1. `classe`, `sistema`, `formato`, `orgao_julgador`, `assunto`;
2. `processo`;
3. `processo_assunto` e `movimento`;
4. `movimento_complemento`.

Essa ordem respeita as chaves estrangeiras. Para uma carga completa, o **Pre-SQL Statement** da primeira saída pode executar o `TRUNCATE` definido no pipeline Python. Em produção, a recomendação seria carregar tabelas temporárias e concluir tudo em uma transação controlada.

## Como concluir quando houver acesso

1. criar o workflow e a macro de paginação;
2. testar com 5 registros e comparar com `samples/resposta_inicial.json`;
3. testar duas páginas e confirmar zero IDs repetidos;
4. executar os 1.000 registros;
5. rodar `sql/04_resumo_validacao.sql` e comparar com os resultados desta entrega;
6. salvar o `.yxmd` e capturar o canvas completo e a tela de execução sem erros.

