-- JVK Crosshairs: esquema inicial.
-- Leitura pública (anon) para o site; escrita só pela service_role (GitHub Actions).

create table public.teams (
  id          bigint generated always as identity primary key,
  slug        text not null unique,
  name        text not null,
  rank        int,                       -- posição no ranking usado (Valve Regional Standings)
  logo_url    text,
  active      boolean not null default true,
  updated_at  timestamptz not null default now()
);

create table public.players (
  steamid     text primary key,          -- SteamID64
  nickname    text not null,
  team_id     bigint references public.teams(id) on delete set null,
  updated_at  timestamptz not null default now()
);
create index players_team_id_idx on public.players(team_id);

create table public.crosshairs (
  id          bigint generated always as identity primary key,
  steamid     text not null references public.players(steamid) on delete cascade,
  code        text not null,             -- código como veio da demo (CS... ou CSGO-...)
  format      text not null,             -- cs2-v1, legacy-v1, legacy-v3, legacy-v4
  params      jsonb not null,            -- parâmetros decodificados (usados no preview)
  console     text not null,             -- comandos prontos para o console
  source      text not null,             -- origem: nome do arquivo/partida
  first_seen  timestamptz not null default now(),
  last_seen   timestamptz not null default now(),
  unique (steamid, code)
);
create index crosshairs_steamid_last_seen_idx on public.crosshairs(steamid, last_seen desc);

-- Mira atual de cada jogador = a vista mais recentemente.
create view public.current_crosshairs with (security_invoker = true) as
select distinct on (c.steamid)
  c.steamid, p.nickname, p.team_id, c.code, c.format, c.params, c.console, c.last_seen
from public.crosshairs c
join public.players p on p.steamid = c.steamid
order by c.steamid, c.last_seen desc;

create table public.matches_processed (
  match_id      text primary key,        -- identificador da partida/arquivo na fonte
  source        text not null,
  status        text not null check (status in ('ok', 'erro', 'bloqueado', 'ignorado')),
  error         text,
  players_found int not null default 0,
  processed_at  timestamptz not null default now()
);

create table public.pipeline_runs (
  id           bigint generated always as identity primary key,
  started_at   timestamptz not null default now(),
  finished_at  timestamptz,
  status       text not null default 'rodando' check (status in ('rodando', 'ok', 'parcial', 'erro', 'bloqueado')),
  demos_ok     int not null default 0,
  demos_erro   int not null default 0,
  log          text
);

alter table public.teams             enable row level security;
alter table public.players           enable row level security;
alter table public.crosshairs        enable row level security;
alter table public.matches_processed enable row level security;
alter table public.pipeline_runs     enable row level security;

create policy "leitura publica" on public.teams      for select to anon, authenticated using (true);
create policy "leitura publica" on public.players    for select to anon, authenticated using (true);
create policy "leitura publica" on public.crosshairs for select to anon, authenticated using (true);
-- matches_processed e pipeline_runs ficam sem policy: só a service_role acessa.
