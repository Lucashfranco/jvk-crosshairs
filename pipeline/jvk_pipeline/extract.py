"""Extrai a mira de cada jogador de uma demo do CS2 com o demoparser2."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from . import sharecode

PROPS = ["crosshair_code", "team_clan_name"]


@dataclass
class PlayerCrosshair:
    steamid: str
    name: str
    team: str | None
    code: str
    decoded: dict
    console: str


def _sample_ticks(parser) -> list[int] | None:
    """Ticks do fim do freeze time de cada round: o jogador já está em jogo com a mira final."""
    try:
        events = parser.parse_event("round_freeze_end")
    except Exception:
        return None
    if events is None or len(events) == 0:
        return None
    return sorted({int(t) for t in events["tick"]})


def extract_crosshairs(dem_path: str | Path, parser=None) -> list[PlayerCrosshair]:
    """Retorna a última mira válida de cada jogador da demo.

    `parser` permite injetar um parser falso nos testes; por padrão usa DemoParser.
    """
    if parser is None:
        from demoparser2 import DemoParser

        parser = DemoParser(str(dem_path))

    ticks = _sample_ticks(parser)
    df = parser.parse_ticks(PROPS, ticks=ticks) if ticks else parser.parse_ticks(PROPS)
    df = df.sort_values("tick")

    result: list[PlayerCrosshair] = []
    for steamid, rows in df.groupby("steamid", sort=False):
        teams = Counter(t for t in rows["team_clan_name"] if isinstance(t, str) and t.strip())
        # Percorre do último tick para o primeiro e fica com o primeiro código válido.
        for _, row in rows.iloc[::-1].iterrows():
            code = row["crosshair_code"]
            if not isinstance(code, str) or not sharecode.is_crosshair_code(code):
                continue
            try:
                decoded = sharecode.decode(code)
            except sharecode.InvalidCrosshairShareCode:
                continue
            result.append(
                PlayerCrosshair(
                    steamid=str(steamid),
                    name=str(row["name"]),
                    team=teams.most_common(1)[0][0] if teams else None,
                    code=code,
                    decoded=decoded,
                    console=sharecode.to_console(decoded),
                )
            )
            break
    return result
