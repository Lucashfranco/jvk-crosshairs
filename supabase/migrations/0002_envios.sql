-- JVK Crosshairs: envios da comunidade.
-- Os elencos vêm do Valve Regional Standings, que só traz o nick dos jogadores. Por isso o jogador
-- passa a ter um id próprio e o SteamID fica opcional (preenchido quando vier de uma demo).

drop view public.current_crosshairs;

alter table public.crosshairs drop constraint crosshairs_steamid_fkey;
alter table public.crosshairs drop constraint crosshairs_steamid_code_key;
drop index public.crosshairs_steamid_last_seen_idx;
alter table public.crosshairs drop column steamid;

alter table public.players drop constraint players_pkey;
alter table public.players add column id bigint generated always as identity primary key;
alter table public.players alter column steamid drop not null;
alter table public.players add constraint players_steamid_key unique (steamid);
create unique index players_nickname_key on public.players (lower(nickname));

alter table public.crosshairs add column player_id bigint not null references public.players(id) on delete cascade;
alter table public.crosshairs add constraint crosshairs_player_code_key unique (player_id, code);
create index crosshairs_player_last_seen_idx on public.crosshairs(player_id, last_seen desc);

-- Todos os jogadores, com a mira mais recente quando existir (code nulo = ainda sem mira).
create view public.current_crosshairs with (security_invoker = true) as
select p.id as player_id, p.nickname, p.team_id, c.code, c.format, c.params, c.console, c.last_seen
from public.players p
left join lateral (
  select code, format, params, console, last_seen
  from public.crosshairs
  where player_id = p.id
  order by last_seen desc
  limit 1
) c on true;

create table public.submissions (
  id            bigint generated always as identity primary key,
  player_id     bigint not null references public.players(id) on delete cascade,
  code          text not null check (code ~ '^(CS[A-Za-z0-9]{44}|CSGO(-[A-Za-z0-9]{5}){5})$'),
  source_url    text check (source_url is null or (char_length(source_url) <= 300 and source_url ~* '^https?://\S+$')),
  status        text not null default 'pendente'
                check (status in ('pendente', 'aprovado', 'rejeitado', 'publicado', 'invalido')),
  note          text check (char_length(note) <= 500),  -- motivo da rejeição ou resultado do pipeline
  created_at    timestamptz not null default now(),
  processed_at  timestamptz
);
create index submissions_player_id_idx on public.submissions(player_id);
create index submissions_status_idx on public.submissions(status);
-- O mesmo código para o mesmo jogador só entra uma vez na fila.
create unique index submissions_pendente_key on public.submissions(player_id, code) where status = 'pendente';

alter table public.submissions enable row level security;

-- O público só cria envios pendentes; ler, aprovar e publicar é com a service_role.
create policy "envio publico" on public.submissions for insert to anon, authenticated
  with check (status = 'pendente' and note is null and processed_at is null);
