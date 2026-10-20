select 'volume' as categoria, 'processos' as metrica,
       count(*)::text as valor
from processo

union all

select 'volume', 'processos_assuntos', count(*)::text
from processo_assunto

union all

select 'volume', 'movimentos', count(*)::text
from movimento

union all

select 'volume', 'complementos', count(*)::text
from movimento_complemento

union all

select 'periodo', 'menor_data_ajuizamento',
       min(data_ajuizamento)::date::text
from processo

union all

select 'periodo', 'maior_data_ajuizamento',
       max(data_ajuizamento)::date::text
from processo

union all

select 'periodo', 'processos_fora_do_periodo', count(*)::text
from processo
where data_ajuizamento < timestamp '2026-05-01'
   or data_ajuizamento >= timestamp '2026-08-01'

union all

select 'duplicidade', 'processos_duplicados', count(*)::text
from (
    select id
    from processo
    group by id
    having count(*) > 1
) duplicados

union all

select 'duplicidade', 'movimentos_duplicados', count(*)::text
from (
    select processo_id, sequencia
    from movimento
    group by processo_id, sequencia
    having count(*) > 1
) duplicados

union all

select 'duplicidade', 'complementos_duplicados', count(*)::text
from (
    select movimento_id, sequencia
    from movimento_complemento
    group by movimento_id, sequencia
    having count(*) > 1
) duplicados

union all

select 'opcional', 'assuntos_sem_nome', count(*)::text
from assunto
where nome is null

union all

select 'opcional', 'movimentos_sem_nome', count(*)::text
from movimento
where nome is null

union all

select 'opcional', 'movimentos_sem_orgao', count(*)::text
from movimento
where orgao_julgador_codigo is null

order by categoria, metrica;
