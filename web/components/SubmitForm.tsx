"use client";

import { useActionState, useEffect, useRef, useState, startTransition } from "react";
import { submitCrosshair, type SubmitState } from "@/app/enviar/actions";
import type { RosterTeam } from "@/lib/types";

const field =
  "w-full rounded-lg border border-line bg-bg px-3 py-2 text-ink placeholder:text-muted/70 focus:border-accent focus:outline-none";

export function SubmitForm({ rosters, defaultPlayerId }: { rosters: RosterTeam[]; defaultPlayerId?: number }) {
  const initialTeam = rosters.find((t) => t.players.some((p) => p.id === defaultPlayerId))?.slug ?? "";
  const [teamSlug, setTeamSlug] = useState(initialTeam);
  const [playerId, setPlayerId] = useState(initialTeam ? String(defaultPlayerId) : "");
  const [state, formAction, pending] = useActionState<SubmitState, FormData>(submitCrosshair, null);
  const players = rosters.find((t) => t.slug === teamSlug)?.players ?? [];
  const formRef = useRef<HTMLFormElement>(null);

  // Depois de um envio aceito, limpa só o código e o link (time e jogador ficam para o próximo).
  useEffect(() => {
    if (!state?.ok || !formRef.current) return;
    for (const name of ["code", "source_url"]) (formRef.current.elements.namedItem(name) as HTMLInputElement).value = "";
  }, [state]);

  return (
    <form
      ref={formRef}
      // Chamada manual em vez de action={...}: com action o React limpa o formulário mesmo quando o envio dá erro.
      onSubmit={(e) => {
        e.preventDefault();
        const data = new FormData(e.currentTarget);
        startTransition(() => formAction(data));
      }}
      className="flex max-w-xl flex-col gap-4 rounded-xl border border-line bg-card p-5"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm">
          Time
          <select
            className={field}
            value={teamSlug}
            onChange={(e) => {
              setTeamSlug(e.target.value);
              setPlayerId("");
            }}
            required
          >
            <option value="">Escolha o time</option>
            {rosters.map((t) => (
              <option key={t.slug} value={t.slug}>
                {t.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Jogador
          <select
            name="player_id"
            className={field}
            value={playerId}
            onChange={(e) => setPlayerId(e.target.value)}
            disabled={!teamSlug}
            required
          >
            <option value="">Escolha o jogador</option>
            {players.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nickname}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm">
        Código da mira
        <input
          name="code"
          className={`${field} font-mono text-sm`}
          placeholder="CS… ou CSGO-xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"
          autoComplete="off"
          spellCheck={false}
          maxLength={60}
          required
        />
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span>
          Onde você viu essa mira? <span className="text-muted">(opcional)</span>
        </span>
        <input
          name="source_url"
          type="url"
          className={field}
          placeholder="Link de clipe, VOD, print ou post"
          maxLength={300}
        />
        <span className="text-xs text-muted">Um link ajuda a revisão a aprovar mais rápido.</span>
      </label>

      {/* Armadilha para robôs: fica fora da tela e longe do teclado. */}
      <input name="website" tabIndex={-1} autoComplete="off" aria-hidden="true" className="absolute -left-[9999px] h-0 w-0" />

      <button
        type="submit"
        disabled={pending}
        className="rounded-lg bg-accent px-4 py-2 font-semibold text-white transition-colors hover:bg-accent-strong disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {pending ? "Enviando…" : "Enviar mira"}
      </button>

      <p aria-live="polite" className={`text-sm ${state?.ok ? "text-ink" : "text-red-300"}`}>
        {state?.message}
      </p>
    </form>
  );
}
