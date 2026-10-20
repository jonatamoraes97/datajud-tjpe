-- 1. Quantidades carregadas
select
    (select count(*) from processo) as processos,
    (select count(*) from classe) as classes,
    (select count(*) from sistema) as sistemas,
    (select count(*) from formato) as formatos,
    (select count(*) from orgao_julgador) as orgaos,
    (select count(*) from assunto) as assuntos_distintos,
    (select count(*) from processo_assunto) as processos_assuntos,
    (select count(*) from movimento) as movimentos,
    (select count(*) from movimento_complemento) as complementos;

-- 2. Período carregado
select
    min(data_ajuizamento)::date as menor_data_ajuizamento,
    max(data_ajuizamento)::date as maior_data_ajuizamento,
    count(*) filter (
        where data_ajuizamento < timestamp '2026-05-01'
           or data_ajuizamento >= timestamp '2026-08-01'
    ) as processos_fora_do_periodo
from processo;

-- 3. Duplicidades nas chaves de negócio
select
    (
        select count(*)
        from (
            select id
            from processo
            group by id
            having count(*) > 1
        ) duplicados
    ) as processos_duplicados,
    (
        select count(*)
        from (
            select processo_id, sequencia
            from movimento
            group by processo_id, sequencia
            having count(*) > 1
        ) duplicados
    ) as movimentos_duplicados,
    (
        select count(*)
        from (
            select movimento_id, sequencia
            from movimento_complemento
            group by movimento_id, sequencia
            having count(*) > 1
        ) duplicados
    ) as complementos_duplicados;

-- 4. Campos opcionais encontrados
select
    (select count(*) from assunto where nome is null) as assuntos_sem_nome,
    (select count(*) from movimento where nome is null) as movimentos_sem_nome,
    (
        select count(*)
        from movimento
        where orgao_julgador_codigo is null
    ) as movimentos_sem_orgao;

-- 5. Integridade referencial
select 'movimento_sem_processo' as teste, count(*) as problemas
from movimento m
left join processo p on p.id = m.processo_id
where p.id is null

union all

select 'complemento_sem_movimento', count(*)
from movimento_complemento mc
left join movimento m on m.movimento_id = mc.movimento_id
where m.movimento_id is null

union all

select 'processo_assunto_sem_processo', count(*)
from processo_assunto pa
left join processo p on p.id = pa.processo_id
where p.id is null

union all

select 'processo_assunto_sem_assunto', count(*)
from processo_assunto pa
left join assunto a on a.codigo = pa.assunto_codigo
where a.codigo is null;
