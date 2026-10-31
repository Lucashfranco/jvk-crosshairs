import json
import os
from pathlib import Path

import pandas as pd
import pytest

from jvk_pipeline.extract import extract_crosshairs

VECTORS = json.loads((Path(__file__).parent / "fixtures" / "crosshair_vectors.json").read_text(encoding="utf-8"))
CS2_CODE = next(v["code"] for v in VECTORS["valid"] if v["decoded"]["format"] == "cs2-v1")
LEGACY_CODE = next(v["code"] for v in VECTORS["valid"] if v["decoded"]["format"] == "legacy-v4")


class FakeParser:
    def __init__(self, rows, freeze_ticks=(100, 200)):
        self.rows = rows
        self.freeze_ticks = freeze_ticks
        self.asked_ticks = None

    def parse_event(self, name):
        assert name == "round_freeze_end"
        return pd.DataFrame({"tick": list(self.freeze_ticks)})

    def parse_ticks(self, props, ticks=None):
        self.asked_ticks = ticks
        return pd.DataFrame(self.rows, columns=["tick", "steamid", "name", "crosshair_code", "team_clan_name"])


def test_fica_com_ultimo_codigo_valido_e_time_mais_comum():
    parser = FakeParser([
        (100, 765611, "fallen", LEGACY_CODE, "FURIA"),
        (200, 765611, "fallen", CS2_CODE, "FURIA"),
        (100, 765622, "yuurih", CS2_CODE, "FURIA"),
        (200, 765622, "yuurih", "lixo", ""),
        (200, 765633, "sem_mira", None, "FURIA"),
    ])
    result = {p.steamid: p for p in extract_crosshairs("x.dem", parser=parser)}

    assert parser.asked_ticks == [100, 200]
    assert set(result) == {"765611", "765622"}
    assert result["765611"].code == CS2_CODE
    assert result["765611"].decoded["format"] == "cs2-v1"
    assert result["765622"].code == CS2_CODE  # o código inválido do último tick é ignorado
    assert result["765622"].team == "FURIA"
    assert result["765611"].console.startswith('cl_crosshair_drawoutline "')


def test_sem_eventos_le_todos_os_ticks():
    parser = FakeParser([(5, 1, "a", CS2_CODE, "")], freeze_ticks=())
    result = extract_crosshairs("x.dem", parser=parser)
    assert parser.asked_ticks is None
    assert result[0].team is None


DEMO = os.environ.get("JVK_TEST_DEMO")


@pytest.mark.skipif(not DEMO, reason="defina JVK_TEST_DEMO com o caminho de uma demo .dem real")
def test_demo_real():
    result = extract_crosshairs(DEMO)
    assert len(result) >= 10
    assert all(p.decoded["format"] for p in result)
