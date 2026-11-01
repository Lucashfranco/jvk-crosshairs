"""Miras publicadas no Liquipedia (seção "Crosshair table" da página de cada jogador).

Acesso só pela API MediaWiki, seguindo os termos (liquipedia.net/api-terms-of-use):
User-Agent identificado, gzip, no máximo 1 requisição a cada 2 segundos e até 50 páginas por
requisição. O texto do Liquipedia é CC-BY-SA: o site credita e linka a página de cada jogador.
"""

from __future__ import annotations

import gzip
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://liquipedia.net/counterstrike/api.php"
PAGE_URL = "https://liquipedia.net/counterstrike/"
USER_AGENT = "jvk-crosshairs/1.0 (https://github.com/Lucashfranco/jvk-crosshairs)"
MIN_INTERVAL = 2.5  # segundos entre requisições (o limite é 2)
BATCH = 50

# Nome do time no Liquipedia quando ele não contém o nome usado pelo VRS (slug do VRS -> nomes).
TEAM_ALIASES = {"inner-circle": ("ic esports",)}

_CROSSHAIR_RE = re.compile(r"\{\{\s*Crosshair table(.*?)\n\}\}", re.S | re.I)
_INFOBOX_RE = re.compile(r"\{\{\s*Infobox player(.*?)\n\}\}", re.S | re.I)


@dataclass(frozen=True)
class Found:
    player_id: int
    code: str
    date: str  # AAAA-MM-DD, data em que a mira foi vista segundo a referência do Liquipedia
    url: str


def _field(block: str, name: str) -> str | None:
    m = re.search(rf"^\s*\|\s*{name}\s*=([^\n|]*)", block, re.M)
    value = m.group(1).strip() if m else ""
    return value or None


def parse_player_page(wikitext: str) -> tuple[str | None, list[tuple[str, str]]]:
    """Devolve (time atual na infobox, [(data, código)]) de uma página de jogador."""
    infobox = _INFOBOX_RE.search(wikitext)
    team = _field(infobox.group(1), "team") if infobox else None
    crosshairs = []
    for m in _CROSSHAIR_RE.finditer(wikitext):
        date, code = _field(m.group(1), "date"), _field(m.group(1), "share_code")
        if date and code and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            crosshairs.append((date, code))
    return team, crosshairs


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def team_matches(lp_team: str | None, team_name: str, team_slug: str) -> bool:
    lp = _norm(lp_team or "")
    if not lp:
        return False
    names = (team_name, *TEAM_ALIASES.get(team_slug, ()))
    return any(_norm(n) and (_norm(n) in lp or lp in _norm(n)) for n in names)


def page_url(title: str) -> str:
    return PAGE_URL + urllib.parse.quote(title.replace(" ", "_"))


def _get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=60) as res:
        raw = res.read()
        if res.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    return json.loads(raw)


def fetch_pages(titles: list[str]) -> dict[str, tuple[str, str]]:
    """Busca o wikitext das páginas. Devolve {título pedido: (título final, wikitext)}; páginas inexistentes ficam de fora."""
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(titles), BATCH):
        if i:
            time.sleep(MIN_INTERVAL)
        batch = titles[i:i + BATCH]
        data = _get({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "redirects": 1, "format": "json", "formatversion": 2, "titles": "|".join(batch),
        })["query"]
        # Segue as normalizações (primeira letra maiúscula) e os redirecionamentos.
        hops = {n["from"]: n["to"] for n in data.get("normalized", []) + data.get("redirects", [])}
        pages = {p["title"]: p for p in data["pages"] if not p.get("missing")}
        for title in batch:
            final = title
            for _ in range(3):
                final = hops.get(final, final)
            page = pages.get(final)
            if page and page.get("revisions"):
                out[title] = (final, page["revisions"][0]["slots"]["main"]["content"])
    return out


def match_crosshairs(players: list[dict], pages: dict[str, tuple[str, str]]) -> tuple[list[Found], list[str]]:
    """Cruza jogadores ({id, nickname, team_name, team_slug}) com as páginas buscadas.

    Só aceita a mira quando o time da página bate com o do VRS: há nicks repetidos no Liquipedia
    (ex.: a página "Ryu" é de outro jogador), e o time é a forma de confirmar que é a pessoa certa.
    """
    found, skipped = [], []
    for p in players:
        page = pages.get(p["nickname"])
        if not page:
            skipped.append(f"{p['nickname']}: sem página")
            continue
        title, wikitext = page
        team, crosshairs = parse_player_page(wikitext)
        if not team_matches(team, p["team_name"], p["team_slug"]):
            skipped.append(f"{p['nickname']}: time no Liquipedia ({team or '-'}) diferente de {p['team_name']}")
            continue
        if not crosshairs:
            skipped.append(f"{p['nickname']}: sem mira na página")
            continue
        date, code = max(crosshairs)
        found.append(Found(p["id"], code, date, page_url(title)))
    return found, skipped
