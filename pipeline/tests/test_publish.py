from jvk_pipeline import sharecode
from jvk_pipeline.publish import build_crosshair, plan_roster_changes
from jvk_pipeline.vrs import parse_standings, slugify

# Trecho do formato real de live/2026/standings_global_2026_10_05.md (repositório da Valve).
STANDINGS = """### Standings as of 2026_10_05<br />
<br />

| Standing | Points | Team Name            | Roster                                                |                                  |
| :- | -: | :- | :- | :- |
| 2        |   1931 | Legacy               | arT, dumau, latto, n1ssim, try                        | [details](details/x.md)          |
| 1        |   2046 | Spirit               | donk, magixx, sh1ro, tN1R, zont1x                     | [details](details/y.md)          |
| 18       |   1534 | Ninjas in Pyjamas    | adamb, Krimbo, sjuush, stavn, xKacpersky              | [details](details/z.md)          |
"""


def test_parse_standings_ordena_e_corta():
    teams = parse_standings(STANDINGS, top=2)
    assert [(t.rank, t.name, t.slug) for t in teams] == [(1, "Spirit", "spirit"), (2, "Legacy", "legacy")]
    assert teams[0].roster == ("donk", "magixx", "sh1ro", "tN1R", "zont1x")


def test_parse_standings_nome_com_espacos():
    nip = parse_standings(STANDINGS)[-1]
    assert (nip.name, nip.slug, len(nip.roster)) == ("Ninjas in Pyjamas", "ninjas-in-pyjamas", 5)


def test_slugify():
    assert slugify("100 Thieves") == "100-thieves"
    assert slugify("Ünited  Team!") == "united-team"


def test_plan_roster_changes():
    players = [
        {"id": 1, "nickname": "donk", "team_id": 10},       # continua
        {"id": 2, "nickname": "Sh1ro", "team_id": 99},      # mudou de time (nick com outra caixa)
        {"id": 3, "nickname": "chopper", "team_id": 10},    # saiu do time ativo
        {"id": 4, "nickname": "s1mple", "team_id": None},   # sem time, fica como está
        {"id": 5, "nickname": "outro", "team_id": 77},      # time fora do top, fica como está
    ]
    changes = plan_roster_changes(players, {10: ("donk", "sh1ro", "zont1x"), 99: ("art",)})
    assert changes.inserts == [{"nickname": "zont1x", "team_id": 10}, {"nickname": "art", "team_id": 99}]
    assert changes.moves == [(2, 10)]
    assert changes.releases == [3]


def test_build_crosshair_valido():
    code = "CSoYQNXCQtL5b44fPZKwPPZZCUpsywopyvJW3koh75uFih"
    row, error = build_crosshair({"id": 7, "player_id": 3, "code": code})
    assert error is None
    decoded = sharecode.decode(code)
    assert row["player_id"] == 3 and row["code"] == code and row["source"] == "envio #7"
    assert row["format"] == "cs2-v1" and row["params"] == decoded
    assert row["console"] == sharecode.to_console(decoded)


def test_build_crosshair_checksum_errado():
    # Mesmo formato, último caractere trocado: passa na regex do banco mas não decodifica.
    row, error = build_crosshair({"id": 8, "player_id": 3, "code": "CSoYQNXCQtL5b44fPZKwPPZZCUpsywopyvJW3koh75uFij"})
    assert row is None and error.startswith("código inválido")
