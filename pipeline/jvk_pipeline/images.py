"""Fotos dos jogadores e logos dos times, copiadas do Liquipedia para o Storage do Supabase.

O site não aponta para os arquivos do Liquipedia: cada imagem é reduzida para no máximo 256 px,
convertida para WebP e guardada no bucket `imagens`. Uma imagem só é baixada de novo quando o
arquivo indicado no Liquipedia muda (colunas *_source).
"""

from __future__ import annotations

import hashlib
import io
from collections import Counter

from PIL import Image

from . import liquipedia
from .db import Rest

BUCKET = "imagens"
PHOTO_SIZE = 480  # as fotos ocupam a largura do card
LOGO_SIZE = 256
# Valor de photo_source/logo_source para uma imagem retirada a pedido do dono: o job não baixa de novo.
BLOCKED = "bloqueado"


def to_webp(data: bytes, max_size: int = LOGO_SIZE) -> bytes:
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
        img.thumbnail((max_size, max_size))
        out = io.BytesIO()
        img.save(out, "WEBP", quality=85, method=6)
    return out.getvalue()


def storage_path(folder: str, key: str | int, source: str) -> str:
    # O nome do arquivo de origem entra no caminho: imagem nova = URL nova, sem cache velho no navegador.
    return f"{folder}/{key}-{hashlib.sha1(source.encode()).hexdigest()[:10]}.webp"


def team_pages(players: list[dict], pages: dict[str, tuple[str, str]]) -> dict[int, str]:
    """Página do Liquipedia de cada time (team_id -> título), pelo time mais citado nas páginas dos jogadores.

    Só contam jogadores cujo time na página bate com o do VRS, a mesma conferência usada nas miras.
    """
    votes: dict[int, Counter] = {}
    for p in players:
        page = pages.get(p["nickname"])
        team = liquipedia.parse_player_page(page[1])[0] if page else None
        if team and liquipedia.team_matches(team, p["team_name"], p["team_slug"]):
            votes.setdefault(p["team_id"], Counter())[team] += 1
    return {team_id: c.most_common(1)[0][0] for team_id, c in votes.items()}


def plan_images(players: list[dict], pages: dict[str, tuple[str, str]]) -> tuple[dict[int, str], dict[int, str]]:
    """Arquivos das fotos (player_id -> arquivo) e códigos de país (player_id -> código) dos jogadores confirmados."""
    photos, countries = {}, {}
    for p in players:
        page = pages.get(p["nickname"])
        if not page:
            continue
        team = liquipedia.parse_player_page(page[1])[0]
        if not liquipedia.team_matches(team, p["team_name"], p["team_slug"]):
            continue  # pode ser outra pessoa com o mesmo nick
        image, country = liquipedia.parse_player_profile(page[1])
        if image:
            photos[p["id"]] = image
        if country:
            countries[p["id"]] = country
    return photos, countries


def logo_candidates(logo: str) -> list[str]:
    """A infobox costuma apontar a logo com o nome escrito ("full"); a versão só com o símbolo vem primeiro."""
    icon = logo.replace(" full ", " ")
    return [icon, logo] if icon != logo else [logo]


def _copy(db: Rest, folder: str, key: int | str, source: str, url: str, max_size: int) -> str:
    data = to_webp(liquipedia.download(url), max_size)
    return db.upload(BUCKET, storage_path(folder, key, source), data, "image/webp")


def sync_images(db: Rest, players: list[dict], pages: dict[str, tuple[str, str]]) -> str:
    """players: {id, nickname, team_id, team_name, team_slug, photo_source, country_code} dos times ativos."""
    photos, countries = plan_images(players, pages)
    by_id = {p["id"]: p for p in players}
    photos = {pid: f for pid, f in photos.items() if by_id[pid].get("photo_source") != BLOCKED}

    team_titles = team_pages(players, pages)
    teams = {t["id"]: t for t in db.select("teams?select=id,slug,logo_source&active=eq.true")}
    logos = {}
    team_wiki = liquipedia.fetch_pages(sorted(set(team_titles.values())))
    for team_id, title in team_titles.items():
        logo = liquipedia.parse_team_logo(team_wiki[title][1]) if title in team_wiki else None
        if logo and team_id in teams and teams[team_id].get("logo_source") != BLOCKED:
            logos[team_id] = logo

    pending = {f for pid, f in photos.items() if by_id[pid].get("photo_source") != f}
    for tid, logo in logos.items():
        if teams[tid].get("logo_source") not in logo_candidates(logo):
            pending.update(logo_candidates(logo))
    files = liquipedia.fetch_files(sorted(pending)) if pending else {}
    for tid, logo in logos.items():
        logos[tid] = next((c for c in logo_candidates(logo) if c in files), teams[tid].get("logo_source") or logo)

    errors, new_photos, new_logos = [], 0, 0
    for pid, source in photos.items():
        values = {}
        if by_id[pid].get("photo_source") != source and source in files:
            url, credit = files[source]
            try:
                values = {"photo_url": _copy(db, "jogadores", pid, source, url, PHOTO_SIZE), "photo_source": source,
                          "photo_credit": credit}
                new_photos += 1
            except Exception as e:  # uma imagem com problema não derruba o job
                errors.append(f"foto de {by_id[pid]['nickname']}: {e}")
        if countries.get(pid) and by_id[pid].get("country_code") != countries[pid]:
            values["country_code"] = countries[pid]
        if values:
            db.update(f"players?id=eq.{pid}", values)
    for tid, source in logos.items():
        if teams[tid].get("logo_source") == source or source not in files:
            continue
        try:
            logo_url = _copy(db, "times", teams[tid]["slug"], source, files[source][0], LOGO_SIZE)
            db.update(f"teams?id=eq.{tid}", {"logo_url": logo_url, "logo_source": source})
            new_logos += 1
        except Exception as e:
            errors.append(f"logo do time {teams[tid]['slug']}: {e}")

    lines = [f"Imagens: {len(photos)} jogadores com foto ({new_photos} novas), "
             f"{len(logos)} times com logo ({new_logos} novas)"]
    return "\n".join(lines + [f"  erro: {e}" for e in errors])
