import Image from "next/image";
import type { PlayerCrosshair, Team } from "@/lib/types";

// As imagens já chegam reduzidas e em WebP pelo job semanal (pipeline/jvk_pipeline/images.py),
// então são servidas direto do Storage do Supabase, sem a otimização da Vercel.

function initials(name: string) {
  const words = name.replace(/[^\p{L}\p{N} ]/gu, "").split(" ").filter(Boolean);
  return (words.length > 1 ? words[0][0] + words[1][0] : name.slice(0, 2)).toUpperCase();
}

export function TeamLogo({ team, size }: { team: Team; size: number }) {
  if (team.logo_url) {
    return (
      <Image
        src={team.logo_url}
        alt={`Logo ${team.name}`}
        width={size}
        height={size}
        unoptimized
        className="shrink-0 object-contain"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <span
      aria-hidden
      className="font-display flex shrink-0 items-center justify-center rounded-lg bg-accent/15 font-bold text-accent"
      style={{ width: size, height: size, fontSize: size * 0.38 }}
    >
      {initials(team.name)}
    </span>
  );
}

export function Flag({ code }: { code: string | null }) {
  if (!code) return null;
  const name = new Intl.DisplayNames(["pt-BR"], { type: "region" }).of(code.toUpperCase()) ?? code;
  return <span className={`fi fi-${code} shrink-0 rounded-[2px]`} role="img" aria-label={name} title={name} />;
}

/** Foto do jogador no topo do card; sem foto, um fundo com a inicial do nick. */
export function PlayerPhoto({ player }: { player: PlayerCrosshair }) {
  return (
    <div className="relative aspect-[3/2] w-full overflow-hidden rounded-lg bg-gradient-to-br from-accent/25 to-bg">
      {player.photo_url ? (
        <Image
          src={player.photo_url}
          alt={`Foto de ${player.nickname}`}
          fill
          unoptimized
          sizes="(min-width: 1280px) 220px, (min-width: 640px) 50vw, 100vw"
          className="object-cover object-top"
        />
      ) : (
        <span aria-hidden className="font-display absolute inset-0 flex items-center justify-center text-5xl font-bold text-accent/60">
          {player.nickname.slice(0, 1).toUpperCase()}
        </span>
      )}
    </div>
  );
}
