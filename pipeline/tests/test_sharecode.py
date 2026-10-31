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
