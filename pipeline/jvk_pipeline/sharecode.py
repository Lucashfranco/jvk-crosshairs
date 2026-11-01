"""Decodificação dos códigos de mira do CS2.

Porte para Python da biblioteca csgo-sharecode (MIT, github.com/akiver/csgo-sharecode).
Dois formatos existem:
- `CS` + 44 caracteres: formato atual do CS2 (cs2-v1), desde a atualização de 30/09/2026.
- `CSGO-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx`: formato legado (legacy-v1, v3, v4), que o CS2 não
  importa mais, mas ainda pode aparecer em demos antigas.

As chaves do dicionário decodificado seguem os nomes da biblioteca original (camelCase),
porque o front-end em TypeScript consome o mesmo JSON.
"""

from __future__ import annotations

import re

DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789"
_BASE = len(DICTIONARY)

_CS2_RE = re.compile(rf"^CS[{DICTIONARY}]{{44}}$")
_LEGACY_RE = re.compile(rf"^CSGO(-?[{DICTIONARY}]{{5}}){{5}}$")


class InvalidCrosshairShareCode(ValueError):
    pass


def _chars_to_bytes(chars: str, byte_length: int) -> list[int]:
    # O código é um número em base 57, com o caractere menos significativo primeiro.
    big = 0
    for ch in reversed(chars):
        big = big * _BASE + DICTIONARY.index(ch)
    if big >= 1 << (byte_length * 8):
        raise InvalidCrosshairShareCode("código fora do tamanho esperado")
    return list(big.to_bytes(byte_length, "big"))


def _assert_checksum(b: list[int]) -> None:
    if b[0] != sum(b[1:]) % 256:
        raise InvalidCrosshairShareCode("checksum inválido")


def _int8(v: int) -> int:
    return v - 0x100 if v >= 0x80 else v


def _int16(v: int) -> int:
    return v - 0x10000 if v >= 0x8000 else v


def _clamp(v, lo, hi):
    return min(max(v, lo), hi)


# --- cs2-v1 -------------------------------------------------------------------------------

def _decode_cs2_v1(b: list[int]) -> dict:
    screen_height = b[2] | (b[3] << 8)
    if screen_height == 0:
        raise InvalidCrosshairShareCode("screen height zero")
    # Bytes 18 a 21: campo de bits little-endian com quatro valores de 7 bits + flag no bit 28.
    bits = b[18] | (b[19] << 8) | (b[20] << 16) | (b[21] << 24)
    return {
        "format": "cs2-v1",
        "style": min(b[4] & 0x1F, 9),
        "followRecoil": (b[4] & 0x20) == 0x20,
        "centerDotEnabled": (b[4] & 0x40) == 0x40,
        "tStyleEnabled": (b[4] & 0x80) == 0x80,
        "outlineMode": min(b[13] >> 6, 2),
        "red": b[5],
        "green": b[6],
        "blue": b[7],
        "alpha": b[8],
        "outlineRed": b[9],
        "outlineGreen": b[10],
        "outlineBlue": b[11],
        "outlineAlpha": b[12],
        "gap": _clamp(_int16(b[14] | (b[15] << 8)), -3840, 3840),
        "length": b[16],
        "thickness": min(b[13] & 0x3F, 32),
        "dynamicSpreadLimit": b[17],
        "splitDistance": bits & 0x7F,
        "innerSplitAlpha": min((bits >> 7) & 0x7F, 100) / 100,
        "outerSplitAlpha": (min((bits >> 14) & 0x7F, 70) + 30) / 100,
        "splitSizeRatio": min((bits >> 21) & 0x7F, 100) / 100,
        "screenHeight": max(screen_height, 240),
        "scopeDotScale": min((b[22] + 10) / 100, 2),
        "scopeDotUseCrosshairColor": ((bits >> 28) & 1) == 1,
    }


def encode_cs2(c: dict) -> str:
    """Gera o código `CS…` (cs2-v1) a partir dos parâmetros: o inverso de _decode_cs2_v1."""
    b = [0] * 32
    b[1] = 1
    b[2], b[3] = c["screenHeight"] & 0xFF, c["screenHeight"] >> 8
    b[4] = c["style"] | c["followRecoil"] << 5 | c["centerDotEnabled"] << 6 | c["tStyleEnabled"] << 7
    b[5:13] = [c["red"], c["green"], c["blue"], c["alpha"],
               c["outlineRed"], c["outlineGreen"], c["outlineBlue"], c["outlineAlpha"]]
    b[13] = c["thickness"] | c["outlineMode"] << 6
    gap = c["gap"] & 0xFFFF
    b[14], b[15] = gap & 0xFF, gap >> 8
    b[16] = c["length"]
    b[17] = c["dynamicSpreadLimit"]
    bits = (c["splitDistance"] | round(c["innerSplitAlpha"] * 100) << 7 | round(c["outerSplitAlpha"] * 100 - 30) << 14
            | round(c["splitSizeRatio"] * 100) << 21 | c["scopeDotUseCrosshairColor"] << 28)
    b[18:22] = list(bits.to_bytes(4, "little"))
    b[22] = round(c["scopeDotScale"] * 100) - 10
    if any(not 0 <= v <= 255 for v in b):
        raise InvalidCrosshairShareCode("parâmetro fora do intervalo do formato cs2-v1")
    b[0] = sum(b[1:]) % 256
    big = int.from_bytes(bytes(b), "big")
    chars = []
    for _ in range(44):
        big, r = divmod(big, _BASE)
        chars.append(DICTIONARY[r])
    return "CS" + "".join(chars)


# Valores padrão do CS2 para o que o formato antigo (CS:GO) não guarda.
_CS2_DEFAULTS = {
    "outlineRed": 0, "outlineGreen": 0, "outlineBlue": 0, "outlineAlpha": 255,
    "dynamicSpreadLimit": 0, "screenHeight": 1080, "scopeDotScale": 1.0, "scopeDotUseCrosshairColor": False,
}
LEGACY_SCREEN_HEIGHT = 1080
# Cores fixas do CS:GO (cl_crosshaircolor 0 a 4); a 5 usa o RGB do código.
_LEGACY_COLORS = {0: (250, 50, 50), 1: (50, 250, 50), 2: (250, 250, 50), 3: (50, 50, 250), 4: (50, 250, 250)}
# Estilos do CS:GO (0 padrão, 1 padrão estático, 2 clássico, 3 clássico dinâmico, 4 clássico estático,
# 5 legado) -> estilos do CS2 desde 09/2026 (0 cruz dinâmica, 2 cruz dinâmica legado, 4 cruz estática).
_LEGACY_STYLES = {0: 0, 1: 4, 2: 4, 3: 0, 4: 4, 5: 2}


def convert_legacy(c: dict) -> dict:
    """Converte uma mira legacy-v1 (unidades do CS:GO) para parâmetros cs2-v1 em pixels de 1080p.

    A Valve não publicou a conversão. Segundo os guias da comunidade, o tamanho e a espessura antigos
    valiam altura da tela / 480 pixels por unidade, e o espaço antigo valia 4 + gap pixels.
    O resultado pode diferir 1 px da mira original.
    """
    if c["format"] != "legacy-v1":
        raise ValueError(f"conversão só para legacy-v1, não {c['format']}")
    unit = LEGACY_SCREEN_HEIGHT / 480
    red, green, blue = _LEGACY_COLORS.get(c["color"], (c["red"], c["green"], c["blue"]))
    return {
        "format": "cs2-v1",
        **_CS2_DEFAULTS,
        "style": _LEGACY_STYLES.get(c["style"], 4),
        "followRecoil": c["followRecoil"],
        "centerDotEnabled": c["centerDotEnabled"],
        "tStyleEnabled": c["tStyleEnabled"],
        "outlineMode": 1 if c["outlineEnabled"] else 0,
        "red": red, "green": green, "blue": blue,
        "alpha": c["alpha"] if c["alphaEnabled"] else 255,
        "gap": max(0, round(4 + c["gap"])),
        "length": _clamp(round(c["length"] * unit), 0, 255),
        "thickness": _clamp(round(c["thickness"] * unit), 1, 32),
        "splitDistance": c["splitDistance"],
        "innerSplitAlpha": c["innerSplitAlpha"],
        "outerSplitAlpha": _clamp(c["outerSplitAlpha"], 0.3, 1.0),
        "splitSizeRatio": c["splitSizeRatio"],
    }


# --- legado ---------------------------------------------------------------------------------

def _decode_legacy_v1(b: list[int]) -> dict:
    return {
        "format": "legacy-v1",
        "gap": _int8(b[2]) / 10,
        "outline": b[3] / 2,
        "red": b[4],
        "green": b[5],
        "blue": b[6],
        "alpha": b[7],
        "splitDistance": b[8] & 7,
        "followRecoil": ((b[8] >> 4) & 8) == 8,
        "fixedCrosshairGap": _int8(b[9]) / 10,
        "color": b[10] & 7,
        "outlineEnabled": (b[10] & 8) == 8,
        "innerSplitAlpha": (b[10] >> 4) / 10,
        "outerSplitAlpha": (b[11] & 0xF) / 10,
        "splitSizeRatio": (b[11] >> 4) / 10,
        "thickness": b[12] / 10,
        "centerDotEnabled": ((b[13] >> 4) & 1) == 1,
        "deployedWeaponGapEnabled": ((b[13] >> 4) & 2) == 2,
        "alphaEnabled": ((b[13] >> 4) & 4) == 4,
        "tStyleEnabled": ((b[13] >> 4) & 8) == 8,
        "style": (b[13] & 0xF) >> 1,
        "length": b[14] / 10,
    }


def _decode_pixel(b: list[int]) -> dict:
    bits = b[10] | (b[11] << 8) | (b[12] << 16) | (b[13] << 24)
    return {
        "style": b[2] & 0xF,
        "followRecoil": (b[2] & 0x10) == 0x10,
        "centerDotEnabled": (b[2] & 0x40) == 0x40,
        "tStyleEnabled": (b[2] & 0x80) == 0x80,
        "red": b[3],
        "green": b[4],
        "blue": b[5],
        "alpha": b[6],
        "gap": b[7],
        "length": b[8],
        "dynamicSpreadLimit": b[9],
        "splitDistance": bits & 0x7F,
        "innerSplitAlpha": ((bits >> 7) & 0x1F) / 20,
        "outerSplitAlpha": (((bits >> 12) & 0xF) + 6) / 20,
        "splitSizeRatio": ((bits >> 16) & 0x7F) / 100,
        "thickness": (bits >> 23) & 0x1F,
        "screenHeight": b[14] | (b[15] << 8),
    }


def _decode_legacy(code: str) -> dict:
    b = _chars_to_bytes(code.replace("CSGO", "").replace("-", ""), 18)
    _assert_checksum(b)
    if b[1] == 1:
        return _decode_legacy_v1(b)
    if b[1] == 3:
        return {"format": "legacy-v3", **_decode_pixel(b), "outlineEnabled": (b[2] & 0x20) == 0x20}
    if b[1] == 4:
        return {"format": "legacy-v4", **_decode_pixel(b), "outlineMode": (b[13] >> 4) & 3}
    raise InvalidCrosshairShareCode(f"versão {b[1]} desconhecida")


# --- API pública ----------------------------------------------------------------------------

def is_crosshair_code(code: str) -> bool:
    return bool(_CS2_RE.match(code) or _LEGACY_RE.match(code))


def decode(code: str) -> dict:
    """Decodifica um código de mira. Lança InvalidCrosshairShareCode se for inválido."""
    code = code.strip()
    if _CS2_RE.match(code):
        b = _chars_to_bytes(code[2:], 32)
        _assert_checksum(b)
        if b[1] != 1:
            raise InvalidCrosshairShareCode(f"versão {b[1]} desconhecida")
        return _decode_cs2_v1(b)
    if _LEGACY_RE.match(code):
        return _decode_legacy(code)
    raise InvalidCrosshairShareCode("formato não reconhecido")


def _fmt(v) -> str:
    # Mesma saída do JavaScript: booleanos viram 0/1 e 1.0 vira "1".
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


_CS2_CONVARS = [
    ("cl_crosshair_drawoutline", "outlineMode"),
    ("cl_crosshair_dynamic_maxdist_splitratio", "splitSizeRatio"),
    ("cl_crosshair_dynamic_splitalpha_innermod", "innerSplitAlpha"),
    ("cl_crosshair_dynamic_splitalpha_outermod", "outerSplitAlpha"),
    ("cl_crosshair_dynamic_splitdist", "splitDistance"),
    ("cl_crosshair_dynamic_spread_limit", "dynamicSpreadLimit"),
    ("cl_crosshair_gap", "gap"),
    ("cl_crosshair_length", "length"),
    ("cl_crosshair_recoil", "followRecoil"),
    ("cl_crosshair_screen_height", "screenHeight"),
    ("cl_crosshair_t", "tStyleEnabled"),
    ("cl_crosshair_thickness", "thickness"),
    ("cl_crosshaircolor_a", "alpha"),
    ("cl_crosshaircolor_b", "blue"),
    ("cl_crosshaircolor_g", "green"),
    ("cl_crosshaircolor_r", "red"),
    ("cl_crosshairdot", "centerDotEnabled"),
    ("cl_crosshairoutline_a", "outlineAlpha"),
    ("cl_crosshairoutline_b", "outlineBlue"),
    ("cl_crosshairoutline_g", "outlineGreen"),
    ("cl_crosshairoutline_r", "outlineRed"),
    ("cl_crosshairstyle", "style"),
    ("cl_ironsight_dot_scale", "scopeDotScale"),
    ("cl_ironsight_usecrosshaircolor", "scopeDotUseCrosshairColor"),
]

_LEGACY_V1_CONVARS = [
    ("cl_crosshair_drawoutline", "outlineEnabled"),
    ("cl_crosshair_dynamic_maxdist_splitratio", "splitSizeRatio"),
    ("cl_crosshair_dynamic_splitalpha_innermod", "innerSplitAlpha"),
    ("cl_crosshair_dynamic_splitalpha_outermod", "outerSplitAlpha"),
    ("cl_crosshair_dynamic_splitdist", "splitDistance"),
    ("cl_crosshair_outlinethickness", "outline"),
    ("cl_crosshair_t", "tStyleEnabled"),
    ("cl_crosshairalpha", "alpha"),
    ("cl_crosshaircolor", "color"),
    ("cl_crosshaircolor_b", "blue"),
    ("cl_crosshaircolor_g", "green"),
    ("cl_crosshaircolor_r", "red"),
    ("cl_crosshairdot", "centerDotEnabled"),
    ("cl_crosshairgap", "gap"),
    ("cl_crosshairgap_useweaponvalue", "deployedWeaponGapEnabled"),
    ("cl_crosshairsize", "length"),
    ("cl_crosshairstyle", "style"),
    ("cl_crosshairthickness", "thickness"),
    ("cl_crosshairusealpha", "alphaEnabled"),
    ("cl_fixedcrosshairgap", "fixedCrosshairGap"),
    ("cl_crosshair_recoil", "followRecoil"),
]

_PIXEL_CONVARS = [
    ("cl_crosshair_drawoutline", "outline"),
    ("cl_crosshair_dynamic_maxdist_splitratio", "splitSizeRatio"),
    ("cl_crosshair_dynamic_splitalpha_innermod", "innerSplitAlpha"),
    ("cl_crosshair_dynamic_splitalpha_outermod", "outerSplitAlpha"),
    ("cl_crosshair_dynamic_splitdist", "splitDistance"),
    ("cl_crosshair_dynamic_spread_limit", "dynamicSpreadLimit"),
    ("cl_crosshair_gap", "gap"),
    ("cl_crosshair_length", "length"),
    ("cl_crosshair_recoil", "followRecoil"),
    ("cl_crosshair_screen_height", "screenHeight"),
    ("cl_crosshair_t", "tStyleEnabled"),
    ("cl_crosshair_thickness", "thickness"),
    ("cl_crosshaircolor_a", "alpha"),
    ("cl_crosshaircolor_b", "blue"),
    ("cl_crosshaircolor_g", "green"),
    ("cl_crosshaircolor_r", "red"),
    ("cl_crosshairdot", "centerDotEnabled"),
    ("cl_crosshairstyle", "style"),
]


def to_convars(crosshair: dict) -> list[tuple[str, str]]:
    """Lista de (comando, valor) na mesma ordem da biblioteca original."""
    fmt = crosshair["format"]
    if fmt == "cs2-v1":
        table = _CS2_CONVARS
    elif fmt == "legacy-v1":
        table = _LEGACY_V1_CONVARS
    else:
        values = dict(crosshair)
        values["outline"] = crosshair["outlineMode"] if fmt == "legacy-v4" else crosshair["outlineEnabled"]
        return [(cvar, _fmt(values[key])) for cvar, key in _PIXEL_CONVARS]
    return [(cvar, _fmt(crosshair[key])) for cvar, key in table]


def to_console(crosshair: dict) -> str:
    """Texto pronto para colar no console do CS2 (uma linha, comandos separados por ;)."""
    return "; ".join(f'{cvar} "{value}"' for cvar, value in to_convars(crosshair))
