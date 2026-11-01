-- JVK Crosshairs: de onde veio cada mira.
-- source: "Liquipedia" ou "envio #<id>"; source_url: página de origem (o Liquipedia é CC-BY-SA e exige crédito).

alter table public.crosshairs add column source_url text;

create or replace view public.current_crosshairs with (security_invoker = true) as
select p.id as player_id, p.nickname, p.team_id, c.code, c.format, c.params, c.console, c.last_seen,
       c.source, c.source_url
from public.players p
left join lateral (
  select code, format, params, console, last_seen, source, source_url
  from public.crosshairs
  where player_id = p.id
  order by last_seen desc
  limit 1
) c on true;
