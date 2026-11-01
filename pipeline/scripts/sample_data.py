"""Gera web/lib/sample-data.json: dados de EXEMPLO para o site rodar sem Supabase.

Usa códigos de mira dos vetores de teste (não são miras de jogadores reais).
Uso: python pipeline/scripts/sample_data.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))

from jvk_pipeline import sharecode  # noqa: E402

CODES = [
    "CSoYQNXCQtL5b44fPZKwPPZZCUpsywopyvJW3koh75uFih",
    "CSGO-tsJdC-2PFX6-fw8qD-6GDaX-rYCUM",
    "CSGO-G8oAC-RyvWc-Hi3CZ-voSwn-QJbfE",
    "CSGO-MnUCC-89iG7-2cVar-wy7Yn-amCpF",
    "CSGO-sP6xU-TSyN9-sZcO5-2D48M-UppkP",
    "CSGO-cA4U9-hiJwT-Wo9NA-YmTS8-WfH4C",
    "CSGO-Cn37R-YE7vo-pLCAL-aURmZ-z6zkG",
    "CSGO-9JzcN-4dZtA-DdXis-8qz5T-rCnkP",
    "CSGO-vcmKL-TWb8f-ddSDD-qM2Xx-T66VH",
    None,
]


def player(i: int, code: str | None) -> dict:
    profile = {"player_id": i, "nickname": f"Jogador {i}", "photo_url": None, "photo_credit": None, "country_code": "br"}
    if code is None:  # jogador ainda sem mira cadastrada
        keys = ("code", "format", "params", "console", "last_seen", "source", "source_url")
        return {**profile, **dict.fromkeys(keys)}
    decoded = sharecode.decode(code)
    return {
        **profile,
        "code": code,
        "format": decoded["format"],
        "params": decoded,
        "console": sharecode.to_console(decoded),
        "last_seen": "2026-10-31T00:00:00Z",
        "source": "envio #0",
        "source_url": None,
    }


teams = []
for t in range(2):
    teams.append({
        "slug": f"time-exemplo-{t + 1}",
        "name": f"Time Exemplo {t + 1}",
        "rank": t + 1,
        "logo_url": None,
        "players": [player(t * 5 + i + 1, CODES[t * 5 + i]) for i in range(5)],
    })

out = ROOT / "web" / "lib" / "sample-data.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"teams": teams}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"ok: {out}")
