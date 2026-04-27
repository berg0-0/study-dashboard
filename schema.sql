-- ============================================================
-- ENEM Study Queue Dashboard — Supabase DDL
-- ============================================================

create table if not exists estado_sistema (
    id            integer primary key default 1,
    indice_bloco_atual integer not null default 0
        check (indice_bloco_atual >= 0 and indice_bloco_atual <= 9)
);

-- Seed the single control row (run once)
insert into estado_sistema (id, indice_bloco_atual)
values (1, 0)
on conflict (id) do nothing;

-- ============================================================

create table if not exists progresso_questoes (
    id             bigserial primary key,
    materia        text not null,
    quantidade     integer not null check (quantidade > 0),
    data_registro  timestamptz not null default now()
);

create index if not exists idx_pq_data on progresso_questoes (data_registro);
create index if not exists idx_pq_materia on progresso_questoes (materia);

-- ============================================================

create table if not exists log_tempo (
    id               bigserial primary key,
    data_registro    date not null default current_date,
    minutos_estudados integer not null check (minutos_estudados > 0)
);

create index if not exists idx_lt_data on log_tempo (data_registro);
