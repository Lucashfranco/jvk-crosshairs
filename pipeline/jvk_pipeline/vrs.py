"""Times e elencos a partir do Valve Regional Standings (VRS).

A Valve publica o ranking no GitHub (github.com/ValveSoftware/counter-strike_regional_standings),
um arquivo Markdown por atualização em `live/<ano>/standings_global_<data>.md`.
"""

from __future__ import annotations

import json
import re
import unicodedata
import urllib.request
from dataclasses import dataclass

REPO = "ValveSoftware/counter-strike_regional_standings"
_RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
_API = f"https://api.github.com/repos/{REPO}/contents/"
_FILE_RE = re.compile(r"^standings_global_(\d{4}_\d{2}_\d{2})\.md$")
_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*-?\d+\s*\|([^|]+)\|([^|]+)\|")


@dataclass(frozen=True)
class RankedTeam:
    rank: int
    name: str
    slug: str
    roster: tuple[str, ...]


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def parse_standings(markdown: str, top: int = 20) -> list[RankedTeam]:
    teams = []
    for line in markdown.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        name = m.group(2).strip()
        roster = tuple(p.strip() for p in m.group(3).split(",") if p.strip())
        teams.append(RankedTeam(int(m.group(1)), name, slugify(name), roster))
    teams.sort(key=lambda t: t.rank)
    return teams[:top]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "jvk-crosshairs"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def latest_standings_path() -> str:
    years = sorted(e["name"] for e in json.loads(_get(_API + "live")) if e["type"] == "dir")
    for year in reversed(years):
        files = [e["name"] for e in json.loads(_get(f"{_API}live/{year}")) if _FILE_RE.match(e["name"])]
        if files:
            return f"live/{year}/{max(files)}"
    raise RuntimeError("nenhum arquivo de standings encontrado no repositório da Valve")


def fetch_top_teams(top: int = 20) -> tuple[str, list[RankedTeam]]:
    path = latest_standings_path()
    return path, parse_standings(_get(_RAW + path).decode("utf-8"), top)
