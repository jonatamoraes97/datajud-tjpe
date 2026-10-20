import json
import os
from datetime import datetime
from pathlib import Path

import psycopg
import requests


ENDPOINT = (
    "https://api-publica.datajud.cnj.jus.br/"
    "api_publica_tjpe/_search"
)

PERIODO_INICIO = 20260501000000
PERIODO_FIM_EXCLUSIVO = 20260801000000
QUANTIDADE_PROCESSOS = 1000
TAMANHO_PAGINA = 200

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "samples"
    / "processos_maio_julho_2026.json"
)


def exigir_variavel(nome):
    valor = os.getenv(nome)
    if not valor:
        raise SystemExit(f"Erro: a variável {nome} não foi definida.")
    return valor


def converter_inteiro(valor):
    if valor in (None, ""):
        return None
    return int(valor)


def converter_data_compacta(valor):
    return datetime.strptime(str(valor), "%Y%m%d%H%M%S")


def converter_data_iso(valor):
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def achatar_lista(valor):
    itens = []
    for item in valor or []:
        if isinstance(item, list):
            itens.extend(achatar_lista(item))
        else:
            itens.append(item)
    return itens


def coletar_processos(api_key):
    registros = []
    search_after = None
    numero_pagina = 0

    cabecalhos = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json",
    }

    with requests.Session() as sessao:
        while len(registros) < QUANTIDADE_PROCESSOS:
            numero_pagina += 1
            quantidade_pagina = min(
                TAMANHO_PAGINA,
                QUANTIDADE_PROCESSOS - len(registros),
            )

            consulta = {
                "size": quantidade_pagina,
                "query": {
                    "range": {
                        "dataAjuizamento": {
                            "gte": PERIODO_INICIO,
                            "lt": PERIODO_FIM_EXCLUSIVO,
                        }
                    }
                },
                "sort": [
                    {
                        "id.keyword": {
                            "order": "asc"
                        }
                    }
                ],
            }

            if search_after is not None:
                consulta["search_after"] = search_after

            resposta = sessao.post(
                ENDPOINT,
                headers=cabecalhos,
                json=consulta,
                timeout=60,
            )
            resposta.raise_for_status()

            pagina = resposta.json()["hits"]["hits"]
            if not pagina:
                break

            registros.extend(pagina)
            search_after = pagina[-1]["sort"]

            print(
                f"Página {numero_pagina}: "
                f"{len(pagina)} processos | "
                f"total={len(registros)}"
            )

    if len(registros) < QUANTIDADE_PROCESSOS:
        raise SystemExit(
            "A consulta retornou menos de 1.000 processos "
            "para o período escolhido."
        )

    conteudo = {
        "periodo_inicio": "2026-05-01",
        "periodo_fim_exclusivo": "2026-08-01",
        "quantidade": len(registros),
        "registros": registros,
    }

    ARQUIVO_SAIDA.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"JSON salvo em: {ARQUIVO_SAIDA}")
    return registros


def carregar_json_salvo():
    if not ARQUIVO_SAIDA.exists():
        return None

    conteudo = json.loads(ARQUIVO_SAIDA.read_text(encoding="utf-8"))
    registros = conteudo.get("registros") or []

    if len(registros) < QUANTIDADE_PROCESSOS:
        return None

    print(
        f"Usando o JSON já coletado: "
        f"{len(registros)} processos"
    )
    return registros[:QUANTIDADE_PROCESSOS]


def inserir_codigo_nome(cursor, tabela, item):
    comandos = {
        "classe": """
            insert into classe (codigo, nome)
            values (%s, %s)
            on conflict (codigo) do update set nome = excluded.nome
        """,
        "sistema": """
            insert into sistema (codigo, nome)
            values (%s, %s)
            on conflict (codigo) do update set nome = excluded.nome
        """,
        "formato": """
            insert into formato (codigo, nome)
            values (%s, %s)
            on conflict (codigo) do update set nome = excluded.nome
        """,
        "assunto": """
            insert into assunto (codigo, nome)
            values (%s, %s)
            on conflict (codigo) do update set
                nome = coalesce(excluded.nome, assunto.nome)
        """,
    }

    cursor.execute(
        comandos[tabela],
        (converter_inteiro(item["codigo"]), item.get("nome")),
    )


def inserir_orgao(cursor, orgao):
    codigo = orgao.get("codigo", orgao.get("codigoOrgao"))
    nome = orgao.get("nome", orgao.get("nomeOrgao"))

    if codigo is None or nome is None:
        return None

    codigo = converter_inteiro(codigo)
    municipio = converter_inteiro(orgao.get("codigoMunicipioIBGE"))

    cursor.execute(
        """
        insert into orgao_julgador (
            codigo,
            nome,
            codigo_municipio_ibge
        )
        values (%s, %s, %s)
        on conflict (codigo) do update set
            nome = excluded.nome,
            codigo_municipio_ibge = coalesce(
                excluded.codigo_municipio_ibge,
                orgao_julgador.codigo_municipio_ibge
            )
        """,
        (codigo, nome, municipio),
    )

    return codigo


def carregar_postgresql(registros, senha_postgres):
    totais = {
        "processos": 0,
        "assuntos": 0,
        "movimentos": 0,
        "complementos": 0,
    }

    with psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "datajud"),
        user=os.getenv("PGUSER", "postgres"),
        password=senha_postgres,
    ) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                truncate table
                    movimento_complemento,
                    processo_assunto,
                    movimento,
                    processo,
                    assunto,
                    orgao_julgador,
                    classe,
                    sistema,
                    formato
                restart identity cascade
                """
            )

            for registro in registros:
                fonte = registro["_source"]

                inserir_codigo_nome(cursor, "classe", fonte["classe"])
                inserir_codigo_nome(cursor, "sistema", fonte["sistema"])
                inserir_codigo_nome(cursor, "formato", fonte["formato"])

                orgao_processo_codigo = inserir_orgao(
                    cursor,
                    fonte["orgaoJulgador"],
                )

                cursor.execute(
                    """
                    insert into processo (
                        id,
                        tribunal,
                        grau,
                        numero_processo,
                        data_ajuizamento,
                        nivel_sigilo,
                        classe_codigo,
                        sistema_codigo,
                        formato_codigo,
                        orgao_julgador_codigo,
                        data_hora_ultima_atualizacao,
                        timestamp_origem
                    )
                    values (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        fonte["id"],
                        fonte["tribunal"],
                        fonte["grau"],
                        fonte["numeroProcesso"],
                        converter_data_compacta(fonte["dataAjuizamento"]),
                        fonte["nivelSigilo"],
                        converter_inteiro(fonte["classe"]["codigo"]),
                        converter_inteiro(fonte["sistema"]["codigo"]),
                        converter_inteiro(fonte["formato"]["codigo"]),
                        orgao_processo_codigo,
                        converter_data_iso(
                            fonte["dataHoraUltimaAtualizacao"]
                        ),
                        converter_data_iso(fonte["@timestamp"]),
                    ),
                )
                totais["processos"] += 1

                for assunto in achatar_lista(fonte.get("assuntos")):
                    inserir_codigo_nome(cursor, "assunto", assunto)
                    cursor.execute(
                        """
                        insert into processo_assunto (
                            processo_id,
                            assunto_codigo
                        )
                        values (%s, %s)
                        on conflict do nothing
                        """,
                        (
                            fonte["id"],
                            converter_inteiro(assunto["codigo"]),
                        ),
                    )
                    totais["assuntos"] += 1

                for sequencia_movimento, movimento in enumerate(
                    achatar_lista(fonte.get("movimentos")),
                    start=1,
                ):
                    orgao_movimento = movimento.get("orgaoJulgador") or {}
                    orgao_movimento_codigo = inserir_orgao(
                        cursor,
                        orgao_movimento,
                    )

                    cursor.execute(
                        """
                        insert into movimento (
                            processo_id,
                            sequencia,
                            codigo,
                            data_hora,
                            nome,
                            orgao_julgador_codigo
                        )
                        values (%s, %s, %s, %s, %s, %s)
                        returning movimento_id
                        """,
                        (
                            fonte["id"],
                            sequencia_movimento,
                            converter_inteiro(movimento["codigo"]),
                            converter_data_iso(movimento["dataHora"]),
                            movimento.get("nome"),
                            orgao_movimento_codigo,
                        ),
                    )
                    movimento_id = cursor.fetchone()[0]
                    totais["movimentos"] += 1

                    for sequencia_complemento, complemento in enumerate(
                        achatar_lista(
                            movimento.get("complementosTabelados")
                        ),
                        start=1,
                    ):
                        cursor.execute(
                            """
                            insert into movimento_complemento (
                                movimento_id,
                                sequencia,
                                codigo,
                                descricao,
                                valor,
                                nome
                            )
                            values (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                movimento_id,
                                sequencia_complemento,
                                converter_inteiro(complemento["codigo"]),
                                complemento["descricao"],
                                converter_inteiro(complemento["valor"]),
                                complemento["nome"],
                            ),
                        )
                        totais["complementos"] += 1

    return totais


def main():
    senha_postgres = exigir_variavel("PGPASSWORD")

    registros = carregar_json_salvo()
    if registros is None:
        api_key = exigir_variavel("DATAJUD_API_KEY")
        registros = coletar_processos(api_key)
    totais = carregar_postgresql(registros, senha_postgres)

    print("\nCarga concluída:")
    for nome, quantidade in totais.items():
        print(f"{nome}: {quantidade}")


if __name__ == "__main__":
    main()
