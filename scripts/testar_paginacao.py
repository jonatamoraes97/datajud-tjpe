import json
import os
from pathlib import Path

import requests


ENDPOINT = (
    "https://api-publica.datajud.cnj.jus.br/"
    "api_publica_tjpe/_search"
)

ARQUIVO_SAIDA = (
    Path(__file__).resolve().parents[1]
    / "samples"
    / "teste_paginacao.json"
)


def consultar_pagina(api_key, search_after=None):
    consulta = {
        "size": 5,
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                "id.keyword": {
                    "order": "asc"
                }
            }
        ]
    }

    if search_after is not None:
        consulta["search_after"] = search_after

    cabecalhos = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json",
    }

    resposta = requests.post(
        ENDPOINT,
        headers=cabecalhos,
        json=consulta,
        timeout=30,
    )
    resposta.raise_for_status()

    return resposta.json()


def main():
    api_key = os.getenv("DATAJUD_API_KEY")

    if not api_key:
        raise SystemExit(
            "Erro: a variável DATAJUD_API_KEY não foi definida."
        )

    primeira_pagina = consultar_pagina(api_key)
    registros_pagina_1 = primeira_pagina["hits"]["hits"]

    if not registros_pagina_1:
        raise SystemExit("A primeira página não retornou registros.")

    ultimo_sort = registros_pagina_1[-1]["sort"]

    segunda_pagina = consultar_pagina(
        api_key,
        search_after=ultimo_sort,
    )
    registros_pagina_2 = segunda_pagina["hits"]["hits"]

    ids_pagina_1 = {
        registro["_source"]["id"]
        for registro in registros_pagina_1
    }
    ids_pagina_2 = {
        registro["_source"]["id"]
        for registro in registros_pagina_2
    }

    ids_repetidos = ids_pagina_1.intersection(ids_pagina_2)

    resultado = {
        "primeira_pagina": primeira_pagina,
        "segunda_pagina": segunda_pagina,
        "validacao": {
            "quantidade_pagina_1": len(registros_pagina_1),
            "quantidade_pagina_2": len(registros_pagina_2),
            "ultimo_sort_pagina_1": ultimo_sort,
            "ids_repetidos": sorted(ids_repetidos),
        },
    }

    ARQUIVO_SAIDA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Registros da página 1: {len(registros_pagina_1)}")
    print(f"Registros da página 2: {len(registros_pagina_2)}")
    print(f"IDs repetidos: {len(ids_repetidos)}")
    print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()