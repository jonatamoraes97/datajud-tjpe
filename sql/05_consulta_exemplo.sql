-- Consulta simples para demonstrar os relacionamentos do modelo.
-- Retorna dez processos com classe, órgão e quantidades relacionadas.

select
    p.numero_processo,
    p.data_ajuizamento::date as data_ajuizamento,
    c.nome as classe,
    o.nome as orgao_julgador,
    count(distinct pa.assunto_codigo) as quantidade_assuntos,
    count(distinct m.movimento_id) as quantidade_movimentos
from processo p
join classe c
  on c.codigo = p.classe_codigo
join orgao_julgador o
  on o.codigo = p.orgao_julgador_codigo
left join processo_assunto pa
  on pa.processo_id = p.id
left join movimento m
  on m.processo_id = p.id
group by
    p.id,
    p.numero_processo,
    p.data_ajuizamento,
    c.nome,
    o.nome
order by
    p.data_ajuizamento,
    p.numero_processo
limit 10;

