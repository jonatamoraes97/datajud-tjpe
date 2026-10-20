import json
from pathlib import Path
from collections import defaultdict


ARQUIVO_ENTRADA = (
    Path(__file__).resolve().parents[1]
    / "samples"
    / "resposta_inicial.json"
)


with ARQUIVO_ENTRADA.open(encoding="utf-8") as arquivo:
    dados = json.load(arquivo)


registros = dados["hits"]["hits"]

print(f"Arquivo analisado: {ARQUIVO_ENTRADA.name}")
print(f"Quantidade de processos: {len(registros)}")

print("\nResumo por processo:")

for posicao, registro in enumerate(registros, start=1):
    fonte = registro.get("_source", {})

    assuntos = fonte.get("assuntos") or []
    movimentos = fonte.get("movimentos") or []

    total_complementos = sum(
        len(movimento.get("complementosTabelados") or [])
        for movimento in movimentos
    )

    print(
        f"{posicao}. "
        f"processo={fonte.get('id')} | "
        f"assuntos={len(assuntos)} | "
        f"movimentos={len(movimentos)} | "
        f"complementos={total_complementos}"
    )

presencas = defaultdict(int)
tipos_por_campo = defaultdict(set)

for registro in registros:
    fonte = registro.get("_source", {})

    for campo, valor in fonte.items():
        presencas[campo] += 1
        tipos_por_campo[campo].add(type(valor).__name__)


print("\nCampos encontrados no _source:")

for campo in sorted(tipos_por_campo):
    ausencias = len(registros) - presencas[campo]
    tipos = ", ".join(sorted(tipos_por_campo[campo]))

    print(
        f"{campo}: "
        f"presente={presencas[campo]} | "
        f"ausente={ausencias} | "
        f"tipos={tipos}"
    )

tipos_codigo_orgao_processo = set()
tipos_codigo_orgao_movimento = set()

exemplos_datas = {}

total_movimentos = 0
movimentos_com_orgao = 0
movimentos_sem_orgao = 0
movimentos_sem_campo_complementos = 0


for registro in registros:
    fonte = registro.get("_source", {})

    for campo_data in (
        "dataAjuizamento",
        "dataHoraUltimaAtualizacao",
        "@timestamp",
    ):
        valor = fonte.get(campo_data)

        if valor is not None and campo_data not in exemplos_datas:
            exemplos_datas[campo_data] = valor

    orgao_processo = fonte.get("orgaoJulgador") or {}
    codigo_processo = orgao_processo.get("codigo")

    if codigo_processo is not None:
        tipos_codigo_orgao_processo.add(
            type(codigo_processo).__name__
        )

    for movimento in fonte.get("movimentos") or []:
        total_movimentos += 1

        orgao_movimento = movimento.get("orgaoJulgador")

        if isinstance(orgao_movimento, dict):
            movimentos_com_orgao += 1

            codigo_movimento = orgao_movimento.get("codigo")

            if codigo_movimento is not None:
                tipos_codigo_orgao_movimento.add(
                    type(codigo_movimento).__name__
                )
        else:
            movimentos_sem_orgao += 1

        if "complementosTabelados" not in movimento:
            movimentos_sem_campo_complementos += 1


print("\nInvestigação de tipos internos:")

print(
    "Tipos do código do órgão no processo:",
    sorted(tipos_codigo_orgao_processo),
)

print(
    "Tipos do código do órgão nos movimentos:",
    sorted(tipos_codigo_orgao_movimento),
)

print(f"Total de movimentos: {total_movimentos}")
print(f"Movimentos com órgão: {movimentos_com_orgao}")
print(f"Movimentos sem órgão: {movimentos_sem_orgao}")

print(
    "Movimentos sem o campo complementosTabelados:",
    movimentos_sem_campo_complementos,
)

print("\nExemplos de datas:")

for campo, valor in exemplos_datas.items():
    print(f"{campo}: {valor}")
