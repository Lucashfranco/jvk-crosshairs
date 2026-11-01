-- Logos dos times e fotos dos jogadores, copiadas do Liquipedia para o Storage pelo job semanal.
-- *_source guarda o nome do arquivo no Liquipedia: o job só baixa de novo quando ele muda.

alter table public.teams add column logo_source text;

alter table public.players
  add column photo_url    text,
  add column photo_source text,
  add column photo_credit text,              -- autor e dono da foto, como estão no Liquipedia
  add column country_code text check (country_code ~ '^[a-z]{2}$');

-- Colunas novas no fim: create or replace view só aceita acrescentar.
create or replace view public.current_crosshairs with (security_invoker = true) as
select p.id as player_id, p.nickname, p.team_id, c.code, c.format, c.params, c.console, c.last_seen,
       c.source, c.source_url, p.photo_url, p.photo_credit, p.country_code
from public.players p
left join lateral (
  select code, format, params, console, last_seen, source, source_url
  from public.crosshairs where player_id = p.id order by last_seen desc limit 1
) c on true;

-- Bucket público: qualquer um lê pela URL pública; só a service_role grava (sem policies em storage.objects).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('imagens', 'imagens', true, 1048576, array['image/webp'])
on conflict (id) do nothing;
