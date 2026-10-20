begin;

create table if not exists classe (
    codigo bigint primary key,
    nome text not null
);

create table if not exists sistema (
    codigo bigint primary key,
    nome text not null
);

create table if not exists formato (
    codigo bigint primary key,
    nome text not null
);

create table if not exists orgao_julgador (
    codigo bigint primary key,
    nome text not null,
    codigo_municipio_ibge bigint
);

create table if not exists assunto (
    codigo bigint primary key,
    nome text
);

create table if not exists processo (
    id text primary key,
    tribunal text not null,
    grau text not null,
    numero_processo text not null,
    data_ajuizamento timestamp not null,
    nivel_sigilo smallint not null check (nivel_sigilo >= 0),
    classe_codigo bigint not null references classe (codigo),
    sistema_codigo bigint not null references sistema (codigo),
    formato_codigo bigint not null references formato (codigo),
    orgao_julgador_codigo bigint not null references orgao_julgador (codigo),
    data_hora_ultima_atualizacao timestamptz not null,
    timestamp_origem timestamptz not null,
    data_carga timestamptz not null default current_timestamp
);

create table if not exists movimento (
    movimento_id bigint generated always as identity primary key,
    processo_id text not null references processo (id) on delete cascade,
    sequencia integer not null,
    codigo bigint not null,
    data_hora timestamptz not null,
    nome text,
    orgao_julgador_codigo bigint references orgao_julgador (codigo),
    unique (processo_id, sequencia)
);

create table if not exists movimento_complemento (
    movimento_complemento_id bigint generated always as identity primary key,
    movimento_id bigint not null references movimento (movimento_id) on delete cascade,
    sequencia integer not null,
    codigo bigint not null,
    descricao text not null,
    valor bigint not null,
    nome text not null,
    unique (movimento_id, sequencia)
);

create table if not exists processo_assunto (
    processo_id text not null references processo (id) on delete cascade,
    assunto_codigo bigint not null references assunto (codigo),
    primary key (processo_id, assunto_codigo)
);

create index if not exists processo_classe_codigo_idx
    on processo (classe_codigo);
create index if not exists processo_sistema_codigo_idx
    on processo (sistema_codigo);
create index if not exists processo_formato_codigo_idx
    on processo (formato_codigo);
create index if not exists processo_orgao_julgador_codigo_idx
    on processo (orgao_julgador_codigo);
create index if not exists processo_data_ajuizamento_idx
    on processo (data_ajuizamento);
create index if not exists movimento_orgao_julgador_codigo_idx
    on movimento (orgao_julgador_codigo);
create index if not exists processo_assunto_assunto_codigo_idx
    on processo_assunto (assunto_codigo);

commit;
