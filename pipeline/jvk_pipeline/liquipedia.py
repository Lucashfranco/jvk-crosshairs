"""Miras publicadas no Liquipedia (seção "Crosshair table" da página de cada jogador).

Acesso só pela API MediaWiki, seguindo os termos (liquipedia.net/api-terms-of-use):
User-Agent identificado, gzip, no máximo 1 requisição a cada 2 segundos e até 50 páginas por
requisição. O texto do Liquipedia é CC-BY-SA: o site credita e linka a página de cada jogador.
Também vêm daqui as fotos dos jogadores e as logos dos times (ver images.py).
"""

from __future__ import annotations

import gzip
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

import pycountry

API = "https://liquipedia.net/counterstrike/api.php"
COMMONS_API = "https://liquipedia.net/commons/api.php"  # descrição e licença dos arquivos de imagem
PAGE_URL = "https://liquipedia.net/counterstrike/"
USER_AGENT = "jvk-crosshairs/1.0 (https://github.com/Lucashfranco/jvk-crosshairs)"
MIN_INTERVAL = 2.5  # segundos entre requisições (o limite é 2)
BATCH = 50

# Nome do time no Liquipedia quando ele não contém o nome usado pelo VRS (slug do VRS -> nomes).
TEAM_ALIASES = {"inner-circle": ("ic esports",)}

_CROSSHAIR_RE = re.compile(r"\{\{\s*Crosshair table(.*?)\n\}\}", re.S | re.I)
_INFOBOX_RE = re.compile(r"\{\{\s*Infobox player(.*?)\n\}\}", re.S | re.I)
_TEAM_INFOBOX_RE = re.compile(r"\{\{\s*Infobox team(.*?)\n\}\}", re.S | re.I)
_FILEINFO_RE = re.compile(r"\{\{\s*FileInfo(.*?)\n\}\}", re.S | re.I)

# Nome do país na infobox -> código ISO, quando o pycountry não reconhece o nome usado pelo Liquipedia.
COUNTRY_ALIASES = {"russia": "ru", "turkey": "tr", "kosovo": "xk", "czech republic": "cz", "vietnam": "vn"}

_last_request = 0.0


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


def parse_player_profile(wikitext: str) -> tuple[str | None, str | None]:
    """Devolve (arquivo da foto, código do país) da infobox de um jogador."""
    infobox = _INFOBOX_RE.search(wikitext)
    if not infobox:
        return None, None
    country = _field(infobox.group(1), "country")
    return _field(infobox.group(1), "image"), country_code(country) if country else None


def country_code(name: str) -> str | None:
    code = COUNTRY_ALIASES.get(name.strip().lower())
    if code:
        return code
    try:
        return pycountry.countries.lookup(name.strip()).alpha_2.lower()
    except LookupError:
        return None


def parse_team_logo(wikitext: str) -> str | None:
    """Arquivo da logo na infobox do time; prefere a versão para fundo escuro, como o do site."""
    infobox = _TEAM_INFOBOX_RE.search(wikitext)
    if not infobox:
        return None
    return _field(infobox.group(1), "imagedark") or _field(infobox.group(1), "image")


def _plain(wiki: str) -> str:
    """Tira a marcação wiki de um campo curto: [url texto] -> texto, [[a|b]] -> b, negrito e itálico."""
    wiki = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", wiki)
    wiki = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", wiki)
    wiki = re.sub(r"\[https?://\S+\]", "", wiki)
    wiki = re.sub(r"<[^>]+>|'{2,}", "", wiki)
    return " ".join(wiki.split())


def parse_file_credit(wikitext: str) -> str | None:
    """Crédito da imagem pelo FileInfo do Liquipedia: autor e dono dos direitos, quando houver."""
    info = _FILEINFO_RE.search(wikitext)
    if not info:
        return None
    parts = []
    for name in ("author", "copyright"):
        # A linha inteira: o valor pode ter "|" dentro de links ([[página|texto]]).
        m = re.search(rf"^\s*\|\s*{name}\s*=(.*)$", info.group(1), re.M)
        value = _plain(m.group(1)) if m else ""
        if value and value not in parts:
            parts.append(value)
    return " / ".join(parts) or None


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


def _fetch(url: str) -> bytes:
    """GET no Liquipedia respeitando o intervalo mínimo entre requisições (API e arquivos)."""
    global _last_request
    wait = _last_request + MIN_INTERVAL - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            raw = res.read()
            if res.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
    finally:
        _last_request = time.monotonic()
    return raw


def _get(params: dict, api: str = API) -> dict:
    return json.loads(_fetch(api + "?" + urllib.parse.urlencode(params)))


def download(url: str) -> bytes:
    if not url.startswith("https://liquipedia.net/"):
        raise ValueError(f"imagem fora do Liquipedia: {url}")
    return _fetch(url)


def fetch_pages(titles: list[str], api: str = API) -> dict[str, tuple[str, str]]:
    """Busca o wikitext das páginas. Devolve {título pedido: (título final, wikitext)}; páginas inexistentes ficam de fora."""
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(titles), BATCH):
        batch = titles[i:i + BATCH]
        data = _get({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "redirects": 1, "format": "json", "formatversion": 2, "titles": "|".join(batch),
        }, api)["query"]
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


def fetch_files(names: list[str]) -> dict[str, tuple[str, str | None]]:
    """URL e crédito de cada arquivo de imagem. Devolve {nome: (url, crédito)}; arquivos inexistentes ficam de fora."""
    titles = [f"File:{n}" for n in names]
    urls: dict[str, str] = {}
    for i in range(0, len(titles), BATCH):
        data = _get({
            "action": "query", "prop": "imageinfo", "iiprop": "url", "format": "json", "formatversion": 2,
            "titles": "|".join(titles[i:i + BATCH]),
        })["query"]
        hops = {n["from"]: n["to"] for n in data.get("normalized", [])}
        info = {p["title"]: p["imageinfo"][0]["url"] for p in data["pages"] if p.get("imageinfo")}
        for title in titles[i:i + BATCH]:
            url = info.get(hops.get(title, title))
            if url:
                urls[title] = url
    pages = fetch_pages(list(urls), COMMONS_API)
    return {t.removeprefix("File:"): (url, parse_file_credit(pages[t][1]) if t in pages else None)
            for t, url in urls.items()}


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
