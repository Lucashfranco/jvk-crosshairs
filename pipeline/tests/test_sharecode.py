"""Compara o decodificador com vetores gerados pela biblioteca original csgo-sharecode@7.0.1."""

import json
from pathlib import Path

import pytest

from jvk_pipeline import sharecode

VECTORS = json.loads((Path(__file__).parent / "fixtures" / "crosshair_vectors.json").read_text(encoding="utf-8"))


def _js_convars(text: str) -> list[tuple[str, str]]:
    pairs = []
    for line in text.strip().splitlines():
        cvar, value = line.split(" ", 1)
        pairs.append((cvar, value.strip('"')))
    return pairs


@pytest.mark.parametrize("vector", VECTORS["valid"], ids=lambda v: v["code"])
def test_decode_igual_referencia(vector):
    assert sharecode.decode(vector["code"]) == vector["decoded"]


@pytest.mark.parametrize("vector", VECTORS["valid"], ids=lambda v: v["code"])
def test_convars_igual_referencia(vector):
    assert sharecode.to_convars(sharecode.decode(vector["code"])) == _js_convars(vector["convars"])


@pytest.mark.parametrize("code", VECTORS["invalid"])
def test_codigo_invalido(code):
    with pytest.raises(sharecode.InvalidCrosshairShareCode):
        sharecode.decode(code)


def test_formatos_cobertos():
    formats = {v["decoded"]["format"] for v in VECTORS["valid"]}
    assert {"cs2-v1", "legacy-v1", "legacy-v3", "legacy-v4"} <= formats


def test_console_uma_linha():
    code = next(v["code"] for v in VECTORS["valid"] if v["decoded"]["format"] == "cs2-v1")
    line = sharecode.to_console(sharecode.decode(code))
    assert "\n" not in line and line.startswith('cl_crosshair_drawoutline "')


# Códigos gerados pelo próprio CS2 (os outros vetores cs2-v1 são sintéticos, com bytes fora do limite).
GAME_CODES = [v["code"] for v in VECTORS["valid"] if v["code"].startswith("CS") and not v["code"].startswith("CSGO")
              and sharecode.decode(v["code"])["screenHeight"] > 240] + ["CSiZFOGVSZTtnaB5Z3eooMmO3rffxNJhTSYP8ZGhoJMTsc"]


@pytest.mark.parametrize("code", GAME_CODES)
def test_encode_cs2_reproduz_o_codigo_do_jogo(code):
    assert sharecode.encode_cs2(sharecode.decode(code)) == code


@pytest.mark.parametrize("vector", [v for v in VECTORS["valid"] if not v["code"].startswith("CSGO")], ids=lambda v: v["code"])
def test_encode_cs2_ida_e_volta(vector):
    decoded = sharecode.decode(vector["code"])
    assert sharecode.decode(sharecode.encode_cs2(decoded)) == decoded


def test_convert_legacy():
    # donk (Liquipedia): tamanho 1, gap -4, espessura 1, estilo clássico estático, cor 5 (RGB próprio).
    old = sharecode.decode("CSGO-AkTYm-syAcf-UKom7-tGKdM-mOJvM")
    assert (old["length"], old["gap"], old["thickness"], old["style"]) == (1.0, -4.0, 1.0, 4)
    new = sharecode.convert_legacy(old)
    assert (new["length"], new["gap"], new["thickness"], new["style"]) == (2, 0, 2, 4)
    assert new["screenHeight"] == 1080 and new["format"] == "cs2-v1"
    code = sharecode.encode_cs2(new)
    assert code.startswith("CS") and not code.startswith("CSGO") and sharecode.decode(code) == new
    assert 'cl_crosshair_length "2"' in sharecode.to_console(new)


def test_convert_legacy_cor_fixa_e_contorno():
    old = {**sharecode.decode("CSGO-AkTYm-syAcf-UKom7-tGKdM-mOJvM"), "color": 2, "outlineEnabled": True, "style": 5}
    new = sharecode.convert_legacy(old)
    assert (new["red"], new["green"], new["blue"]) == (250, 250, 50)
    assert new["outlineMode"] == 1 and new["style"] == 2
