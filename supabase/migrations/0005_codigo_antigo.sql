-- Desde a atualização de 09/2026 o CS2 não importa códigos CSGO- nem aceita os comandos antigos
-- (cl_crosshairsize etc.). O job converte cada mira antiga para o formato novo: `code` passa a ser o
-- código CS… gerado e o código original fica em legacy_code.

alter table public.crosshairs add column legacy_code text;

create or replace view public.current_crosshairs with (security_invoker = true) as
select p.id as player_id, p.nickname, p.team_id, c.code, c.format, c.params, c.console, c.last_seen,
       c.source, c.source_url, p.photo_url, p.photo_credit, p.country_code, c.legacy_code
from public.players p
left join lateral (
  select code, format, params, console, last_seen, source, source_url, legacy_code
  from public.crosshairs where player_id = p.id order by last_seen desc limit 1
) c on true;
