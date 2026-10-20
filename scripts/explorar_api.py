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
    / "resposta_inicial.json"
)


def main():
    api_key = os.getenv("DATAJUD_API_KEY") #Ler a chave de API

    if not api_key:
        raise SystemExit(
            "Erro: a variável DATAJUD_API_KEY não foi definida."
        )

#Limitar a primeira exploração a 5 registros
    consulta = {
        "size": 5,
        "query": {
            "match_all": {} #Solicitação sem filtros
        }
    }

    cabecalhos = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json",
    }

#Requisição POST para o endpoint da API do DataJud
    try:
        resposta = requests.post(
            ENDPOINT,
            headers=cabecalhos,
            json=consulta,
            timeout=30,
        )
        resposta.raise_for_status() #Levanta uma exceção se a resposta HTTP indicar um erro
    except requests.RequestException as erro:
        raise SystemExit(f"Erro ao consultar o DataJud: {erro}") from erro

    dados = resposta.json()
    registros = dados.get("hits", {}).get("hits", [])

    ARQUIVO_SAIDA.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Status HTTP: {resposta.status_code}")
    print(f"Registros recebidos: {len(registros)}")
    print(f"Amostra salva em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()