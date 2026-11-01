import io

from PIL import Image

from jvk_pipeline.images import logo_candidates, plan_images, storage_path, team_pages, to_webp
from jvk_pipeline.liquipedia import country_code, parse_file_credit, parse_player_profile, parse_team_logo

# Mesma estrutura das páginas do Liquipedia (conteúdo fictício).
PLAYER = """{{Person Tabs|player=1}}
{{Infobox player
|id=fulano
|image=Fulano at Evento 2026.jpg
|country=Russia
|team=Team Exemplo
}}
"""

TEAM = """{{Infobox team
|name=Team Exemplo
|image=Team Exemplo lightmode.png
|imagedark=Team Exemplo darkmode.png
|location=Serbia
}}
"""

FILE = """== Summary ==
{{FileInfo
|featured=fulano
|license=permission
|author=Fulana de Tal
|copyright=[https://example.com/ BLAST]
|note=Uso permitido ao Liquipedia.
}}"""


def test_parse_player_profile():
    assert parse_player_profile(PLAYER) == ("Fulano at Evento 2026.jpg", "ru")
    assert parse_player_profile("sem infobox") == (None, None)
    assert parse_player_profile("{{Infobox player\n|id=x\n|image=\n}}") == (None, None)


def test_country_code():
    assert country_code("Brazil") == "br"
    assert country_code("Russia") == "ru"  # o pycountry só conhece "Russian Federation"
    assert country_code("Bosnia and Herzegovina") == "ba"
    assert country_code("Atlântida") is None


def test_parse_team_logo_prefere_versao_escura():
    assert parse_team_logo(TEAM) == "Team Exemplo darkmode.png"
    assert parse_team_logo(TEAM.replace("|imagedark=Team Exemplo darkmode.png\n", "")) == "Team Exemplo lightmode.png"
    assert parse_team_logo(PLAYER) is None


def test_parse_file_credit():
    assert parse_file_credit(FILE) == "Fulana de Tal / BLAST"
    assert parse_file_credit("{{FileInfo\n|author=[[Fulano|Fulano Silva]]\n|copyright=\n}}") == "Fulano Silva"
    assert parse_file_credit("{{FileInfo\n|license=fairuselogo\n|author=\n}}") is None
    assert parse_file_credit("nada") is None


PLAYERS = [
    {"id": 1, "nickname": "fulano", "team_id": 10, "team_name": "Exemplo", "team_slug": "exemplo"},
    {"id": 2, "nickname": "xara", "team_id": 10, "team_name": "Exemplo", "team_slug": "exemplo"},  # página de outra pessoa
    {"id": 3, "nickname": "sumido", "team_id": 10, "team_name": "Exemplo", "team_slug": "exemplo"},
]
PAGES = {
    "fulano": ("Fulano", PLAYER),
    "xara": ("Xara", PLAYER.replace("Team Exemplo", "Outro Time").replace("Fulano at", "Xara at")),
}


def test_plan_images_so_com_o_time_confirmado():
    photos, countries = plan_images(PLAYERS, PAGES)
    assert photos == {1: "Fulano at Evento 2026.jpg"}
    assert countries == {1: "ru"}


def test_team_pages():
    assert team_pages(PLAYERS, PAGES) == {10: "Team Exemplo"}


def test_to_webp_reduz_e_mantem_transparencia():
    src = io.BytesIO()
    Image.new("RGBA", (800, 400), (139, 92, 246, 0)).save(src, "PNG")
    with Image.open(io.BytesIO(to_webp(src.getvalue()))) as out:
        assert out.format == "WEBP" and out.size == (256, 128) and out.mode == "RGBA"


def test_storage_path_muda_com_o_arquivo():
    a, b = storage_path("jogadores", 7, "a.jpg"), storage_path("jogadores", 7, "b.jpg")
    assert a.startswith("jogadores/7-") and a.endswith(".webp") and a != b


def test_logo_candidates_prefere_so_o_simbolo():
    assert logo_candidates("Team Spirit 2022 full darkmode.png") == [
        "Team Spirit 2022 darkmode.png", "Team Spirit 2022 full darkmode.png"]
    assert logo_candidates("G2 Esports darkmode.png") == ["G2 Esports darkmode.png"]


class FakeDb:
    def __init__(self, teams):
        self.teams, self.updates, self.uploads = teams, [], []

    def select(self, path):
        return self.teams

    def update(self, path, values):
        self.updates.append((path, values))

    def upload(self, bucket, path, data, content_type):
        self.uploads.append(path)
        return f"https://x/{path}"


def test_sync_images_respeita_bloqueio(monkeypatch):
    from jvk_pipeline import images, liquipedia

    monkeypatch.setattr(liquipedia, "fetch_pages", lambda titles, api=None: {"Team Exemplo": ("Team Exemplo", TEAM)})
    monkeypatch.setattr(liquipedia, "fetch_files", lambda names: {n: (f"https://liquipedia.net/{n}", None) for n in names})
    monkeypatch.setattr(liquipedia, "download", lambda url: b"")
    monkeypatch.setattr(images, "to_webp", lambda data, size=0: b"webp")

    players = [{**PLAYERS[0], "photo_source": images.BLOCKED, "country_code": "ru"}]
    db = FakeDb([{"id": 10, "slug": "exemplo", "logo_source": images.BLOCKED}])
    images.sync_images(db, players, PAGES)
    assert db.uploads == [] and db.updates == []

    players[0]["photo_source"] = None
    db = FakeDb([{"id": 10, "slug": "exemplo", "logo_source": None}])
    images.sync_images(db, players, PAGES)
    assert len(db.uploads) == 2 and db.uploads[0].startswith("jogadores/1-") and db.uploads[1].startswith("times/exemplo-")
