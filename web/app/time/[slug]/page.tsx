import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { CopyButton } from "@/components/CopyButton";
import { CrosshairPreview, isApproximate } from "@/components/CrosshairPreview";
import { getTeam, getTeams } from "@/lib/data";
import type { PlayerCrosshair } from "@/lib/types";

export async function generateStaticParams() {
  const teams = await getTeams();
  return teams.map((t) => ({ slug: t.slug }));
}

export default function TeamPage({ params }: PageProps<"/time/[slug]">) {
  return (
    <>
      <Link href="/" className="text-sm text-muted hover:text-ink">
        ← Todos os times
      </Link>
      <Suspense fallback={<p className="mt-6 text-muted">Carregando time…</p>}>
        {params.then(({ slug }) => (
          <TeamContent slug={slug} />
        ))}
      </Suspense>
    </>
  );
}

async function TeamContent({ slug }: { slug: string }) {
  const data = await getTeam(slug);
  if (!data) notFound();
  const { team, players } = data;

  return (
    <>
      <h1 className="font-display mt-4 mb-6 text-3xl font-bold">
        {team.rank != null && <span className="mr-3 text-accent">#{team.rank}</span>}
        {team.name}
      </h1>
      {players.length === 0 ? (
        <p className="rounded-xl border border-line bg-card p-6 text-muted">
          Ainda não temos as miras deste time. Elas aparecem depois que uma partida dele for processada.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {players.map((p) => (
            <PlayerCard key={p.steamid} player={p} />
          ))}
        </ul>
      )}
    </>
  );
}

function PlayerCard({ player }: { player: PlayerCrosshair }) {
  const legacy = player.format !== "cs2-v1";
  return (
    <li className="flex flex-col items-center gap-3 rounded-xl border border-line bg-card p-4">
      <h2 className="font-display text-xl font-bold">{player.nickname}</h2>
      <CrosshairPreview params={player.params} label={`Prévia da mira de ${player.nickname}`} />
      {isApproximate(player.params) && <p className="text-xs text-muted">Prévia aproximada</p>}
      <code className="w-full truncate rounded-md bg-bg px-2 py-1 text-center text-xs text-muted" title={player.code}>
        {player.code}
      </code>
      <div className="flex w-full flex-col gap-2">
        <CopyButton text={player.console} label="Copiar comandos" primary />
        <CopyButton text={player.code} label="Copiar código" />
      </div>
      {legacy && (
        <p className="text-center text-xs text-muted">
          Código no formato antigo (CSGO-): o CS2 não importa mais. Use os comandos.
        </p>
      )}
    </li>
  );
}
