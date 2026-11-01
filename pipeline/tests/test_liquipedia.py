from jvk_pipeline.liquipedia import Found, match_crosshairs, page_url, parse_player_page, team_matches

# Mesma estrutura das páginas de jogador do Liquipedia (conteúdo fictício).
PAGE = """{{Infobox player
|id=fulano
|name=Fulano de Tal
|team=Team Exemplo
|status=Active
}}
==Gear and settings==
{{Crosshair table
|date=2023-05-01
|ref=<ref>{{cite web|date=2023-05-01|url=https://example.com|title=Partida}}</ref>
|share_code=CSGO-AAAAA-AAAAA-AAAAA-AAAAA-AAAAA
}}
{{Crosshair table
|date=2025-12-04
|ref=<ref>{{cite_web|date=2025-12-04|url=https://example.com/2
|publisher=Exemplo}}</ref>
|share_code=CSGO-tsJdC-2PFX6-fw8qD-6GDaX-rYCUM
}}
"""


def test_parse_player_page():
    team, crosshairs = parse_player_page(PAGE)
    assert team == "Team Exemplo"
    assert crosshairs == [
        ("2023-05-01", "CSGO-AAAAA-AAAAA-AAAAA-AAAAA-AAAAA"),
        ("2025-12-04", "CSGO-tsJdC-2PFX6-fw8qD-6GDaX-rYCUM"),
    ]


def test_parse_page_sem_mira_nem_infobox():
    assert parse_player_page("texto qualquer") == (None, [])


def test_team_matches():
    assert team_matches("Team Spirit", "Spirit", "spirit")
    assert team_matches("9z Team", "9z", "9z")
    assert team_matches("Luminosity Gaming", "Luminosity", "luminosity")
    assert team_matches("IC Esports", "Inner Circle", "inner-circle")  # apelido
    assert not team_matches("Astralis", "FUT", "fut")
    assert not team_matches(None, "Spirit", "spirit")
    assert not team_matches("---", "Spirit", "spirit")


def test_match_crosshairs_pega_a_mais_recente_e_confere_o_time():
    players = [
        {"id": 1, "nickname": "fulano", "team_name": "Exemplo", "team_slug": "exemplo"},
        {"id": 2, "nickname": "ryu", "team_name": "Astralis", "team_slug": "astralis"},
        {"id": 3, "nickname": "sumido", "team_name": "Exemplo", "team_slug": "exemplo"},
        {"id": 4, "nickname": "novato", "team_name": "Exemplo", "team_slug": "exemplo"},
    ]
    pages = {
        "fulano": ("Fulano", PAGE),
        "ryu": ("Ryu", "{{Infobox player\n|id=Ryu\n|status=Retired\n}}\n" + PAGE.split("}}", 1)[1]),
        "novato": ("Novato", "{{Infobox player\n|team=Exemplo\n}}\n"),
    }
    found, skipped = match_crosshairs(players, pages)
    assert found == [Found(1, "CSGO-tsJdC-2PFX6-fw8qD-6GDaX-rYCUM", "2025-12-04", page_url("Fulano"))]
    assert [s.split(":")[0] for s in skipped] == ["ryu", "sumido", "novato"]


def test_page_url():
    assert page_url("Ninjas in Pyjamas") == "https://liquipedia.net/counterstrike/Ninjas_in_Pyjamas"
