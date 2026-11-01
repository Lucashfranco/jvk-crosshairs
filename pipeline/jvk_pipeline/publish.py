"""Job semanal: atualiza times e elencos pelo VRS, busca as miras no Liquipedia e publica os envios aprovados.

Uso (GitHub Actions ou local):
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python -m jvk_pipeline.publish

A chave é a secret (service_role) do Supabase: só a service_role lê e altera `submissions`.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import liquipedia, sharecode, vrs
from .db import Rest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RosterChanges:
    inserts: list[dict] = field(default_factory=list)  # {nickname, team_id}
    moves: list[tuple[int, int]] = field(default_factory=list)  # (player_id, team_id)
    releases: list[int] = field(default_factory=list)  # player_id que saiu de um time ativo


def plan_roster_changes(players: list[dict], rosters: dict[int, tuple[str, ...]]) -> RosterChanges:
    """Compara os jogadores do banco com os elencos do VRS (team_id -> nicks).

    O jogador é identificado pelo nick sem diferenciar maiúsculas, igual ao índice único do banco.
    """
    by_nick = {p["nickname"].lower(): p for p in players}
    changes = RosterChanges()
    listed = set()
    for team_id, roster in rosters.items():
        for nick in roster:
            listed.add(nick.lower())
            current = by_nick.get(nick.lower())
            if current is None:
                changes.inserts.append({"nickname": nick, "team_id": team_id})
            elif current["team_id"] != team_id:
                changes.moves.append((current["id"], team_id))
    for p in players:
        if p["team_id"] in rosters and p["nickname"].lower() not in listed:
            changes.releases.append(p["id"])
    return changes


def crosshair_row(player_id: int, code: str, source: str, last_seen: str, source_url: str | None = None) -> dict:
    """Linha de crosshairs com o código decodificado. Lança InvalidCrosshairShareCode se for inválido."""
    decoded = sharecode.decode(code)
    return {
        "player_id": player_id,
        "code": code,
        "format": decoded["format"],
        "params": decoded,
        "console": sharecode.to_console(decoded),
        "source": source,
        "source_url": source_url,
        "last_seen": last_seen,
    }


def build_crosshair(submission: dict) -> tuple[dict | None, str | None]:
    """Decodifica um envio. Devolve (linha de crosshairs, None) ou (None, motivo do erro)."""
    try:
        return crosshair_row(submission["player_id"], submission["code"], f"envio #{submission['id']}", _now()), None
    except sharecode.InvalidCrosshairShareCode as e:
        return None, f"código inválido: {e}"


def sync_teams(db: Rest, top: int = 20) -> str:
    path, ranked = vrs.fetch_top_teams(top)
    rows = [{"slug": t.slug, "name": t.name, "rank": t.rank, "active": True, "updated_at": _now()} for t in ranked]
    saved = {r["slug"]: r["id"] for r in db.insert("teams", rows, on_conflict="slug")}
    db.update(f"teams?slug=not.in.({','.join(saved)})&active=eq.true", {"active": False, "rank": None})

    rosters = {saved[t.slug]: t.roster for t in ranked}
    changes = plan_roster_changes(db.select("players?select=id,nickname,team_id"), rosters)
    if changes.inserts:
        db.insert("players", changes.inserts)
    for player_id, team_id in changes.moves:
        db.update(f"players?id=eq.{player_id}", {"team_id": team_id, "updated_at": _now()})
    for player_id in changes.releases:
        db.update(f"players?id=eq.{player_id}", {"team_id": None, "updated_at": _now()})
    return (f"VRS {path}: {len(ranked)} times; {len(changes.inserts)} jogadores novos, "
            f"{len(changes.moves)} trocaram de time, {len(changes.releases)} saíram")


def sync_liquipedia(db: Rest) -> str:
    """Grava as miras do Liquipedia dos jogadores dos times ativos.

    A data da mira é a da referência no Liquipedia, então um envio mais novo da comunidade continua
    sendo a mira atual. Mira que já existe para o jogador não é tocada (ignore-duplicates).
    """
    rows = db.select("players?select=id,nickname,teams!inner(name,slug)&teams.active=eq.true&order=id.asc")
    players = [{"id": r["id"], "nickname": r["nickname"], "team_name": r["teams"]["name"],
                "team_slug": r["teams"]["slug"]} for r in rows]
    found, skipped = liquipedia.match_crosshairs(players, liquipedia.fetch_pages([p["nickname"] for p in players]))
    saved = []
    for f in found:
        try:
            saved.append(crosshair_row(f.player_id, f.code, "Liquipedia", f.date, f.url))
        except sharecode.InvalidCrosshairShareCode as e:
            skipped.append(f"jogador {f.player_id}: código do Liquipedia inválido ({e})")
    if saved:
        db.insert("crosshairs", saved, on_conflict="player_id,code", ignore_duplicates=True)
    lines = [f"Liquipedia: {len(saved)} miras de {len(players)} jogadores"]
    return "\n".join(lines + [f"  sem mira do Liquipedia: {s}" for s in skipped])


def publish_submissions(db: Rest) -> tuple[int, int]:
    published = invalid = 0
    for sub in db.select("submissions?select=id,player_id,code&status=eq.aprovado&order=id.asc"):
        row, error = build_crosshair(sub)
        if row:
            db.insert("crosshairs", row, on_conflict="player_id,code")
            db.update(f"submissions?id=eq.{sub['id']}", {"status": "publicado", "processed_at": _now()})
            published += 1
        else:
            db.update(f"submissions?id=eq.{sub['id']}", {"status": "invalido", "note": error, "processed_at": _now()})
            invalid += 1
    return published, invalid


def check_key(key: str) -> str | None:
    """Descreve o que há de errado com a chave, sem nunca mostrar o valor dela."""
    bad = [c for c in key if c.isspace() or not c.isascii() or not c.isprintable()]
    if bad:
        lines = key.count("\n") + 1
        return f"{len(key)} caracteres, {lines} linha(s), {len(bad)} caractere(s) inválido(s) (espaço, acento ou quebra de linha)"
    if not key.startswith(("sb_secret_", "eyJ")):
        return f"{len(key)} caracteres; não começa com sb_secret_ (a publishable não serve)"
    return None


def main() -> int:
    # strip: secrets colados no terminal costumam vir com quebra de linha no fim.
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not key:
        print("Defina SUPABASE_URL e SUPABASE_SERVICE_KEY.", file=sys.stderr)
        return 2
    problem = check_key(key)
    if problem:
        print(f"Chave do Supabase inválida: {problem}", file=sys.stderr)
        return 2
    db = Rest(url, key)
    run_id = db.insert("pipeline_runs", {"status": "rodando"})[0]["id"]
    log, status, published, invalid = [], "erro", 0, 0
    try:
        log.append(sync_teams(db))
        log.append(sync_liquipedia(db))
        published, invalid = publish_submissions(db)
        log.append(f"envios: {published} publicados, {invalid} inválidos")
        status = "ok" if invalid == 0 else "parcial"
    except Exception as e:  # registra a falha na execução antes de sair com erro
        log.append(f"erro: {e}")
        raise
    finally:
        # demos_ok/demos_erro guardam os envios publicados/inválidos enquanto a fonte for a comunidade.
        db.update(f"pipeline_runs?id=eq.{run_id}", {
            "status": status, "finished_at": _now(), "demos_ok": published, "demos_erro": invalid, "log": "\n".join(log),
        })
        print("\n".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
