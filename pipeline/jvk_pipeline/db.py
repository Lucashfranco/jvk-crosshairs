"""Cliente mínimo para a API REST (PostgREST) do Supabase, só com a biblioteca padrão."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class SupabaseError(RuntimeError):
    pass


class Rest:
    def __init__(self, url: str, key: str):
        self.root = url.rstrip("/")
        self.base = self.root + "/rest/v1/"
        self.key = key

    def upload(self, bucket: str, path: str, data: bytes, content_type: str) -> str:
        """Grava (ou substitui) um arquivo no Storage e devolve a URL pública dele."""
        req = urllib.request.Request(
            f"{self.root}/storage/v1/object/{bucket}/{path}", data=data, method="POST",
            headers={"apikey": self.key, "Authorization": f"Bearer {self.key}",
                     "Content-Type": content_type, "x-upsert": "true", "Cache-Control": "max-age=31536000"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60):
                pass
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise SupabaseError(f"upload {bucket}/{path}: {e.code} {detail}") from None
        return f"{self.root}/storage/v1/object/public/{bucket}/{path}"

    def request(self, method: str, path: str, body=None, prefer: str | None = None):
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                raw = res.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise SupabaseError(f"{method} {path.split('?')[0]}: {e.code} {detail}") from None
        return json.loads(raw) if raw else None

    def select(self, path: str) -> list[dict]:
        return self.request("GET", path)

    def insert(self, table: str, rows, on_conflict: str | None = None, ignore_duplicates: bool = False) -> list[dict]:
        """Insere linhas. Com on_conflict, atualiza a existente (ou a mantém, se ignore_duplicates)."""
        path, prefer = table, "return=representation"
        if on_conflict:
            path += f"?on_conflict={on_conflict}"
            prefer += ",resolution=" + ("ignore-duplicates" if ignore_duplicates else "merge-duplicates")
        return self.request("POST", path, rows, prefer)

    def update(self, path: str, values: dict) -> None:
        self.request("PATCH", path, values, "return=minimal")
