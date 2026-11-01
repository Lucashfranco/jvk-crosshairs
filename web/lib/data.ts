import { cacheLife } from "next/cache";
import sample from "./sample-data.json";
import type { PlayerCrosshair, RosterTeam, Team } from "./types";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Sem Supabase configurado o site usa dados de exemplo (marcados na interface).
export const usingSampleData = !SUPABASE_URL || !SUPABASE_KEY;

type SampleTeam = Team & { players: PlayerCrosshair[] };
const sampleTeams = sample.teams as SampleTeam[];

function headers(extra?: Record<string, string>) {
  return { apikey: SUPABASE_KEY!, Authorization: `Bearer ${SUPABASE_KEY}`, ...extra };
}

async function rest<T>(path: string): Promise<T> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, { headers: headers() });
  if (!res.ok) throw new Error(`Supabase ${res.status} em ${path.split("?")[0]}`);
  return res.json() as Promise<T>;
}

export async function getTeams(): Promise<Team[]> {
  "use cache";
  cacheLife("hours");
  if (usingSampleData) return sampleTeams.map(({ slug, name, rank, logo_url }) => ({ slug, name, rank, logo_url }));
  return rest<Team[]>("teams?select=id,slug,name,rank,logo_url&active=eq.true&order=rank.asc.nullslast,name.asc");
}

export async function getTeam(slug: string): Promise<{ team: Team; players: PlayerCrosshair[] } | null> {
  "use cache";
  cacheLife("hours");
  if (usingSampleData) {
    const found = sampleTeams.find((t) => t.slug === slug);
    if (!found) return null;
    const { players, ...team } = found;
    return { team, players };
  }
  const [team] = await rest<Team[]>(`teams?select=id,slug,name,rank,logo_url&slug=eq.${encodeURIComponent(slug)}`);
  if (!team) return null;
  const players = await rest<PlayerCrosshair[]>(
    `current_crosshairs?select=player_id,nickname,code,format,params,console,last_seen,source,source_url&team_id=eq.${team.id}&order=nickname.asc`,
  );
  return { team, players };
}

// Times ativos com seus jogadores, para o formulário de envio.
export async function getRosters(): Promise<RosterTeam[]> {
  "use cache";
  cacheLife("hours");
  if (usingSampleData) {
    return sampleTeams.map((t) => ({
      slug: t.slug,
      name: t.name,
      players: t.players.map((p) => ({ id: p.player_id, nickname: p.nickname })),
    }));
  }
  const [teams, players] = await Promise.all([
    getTeams(),
    rest<{ id: number; nickname: string; team_id: number }[]>(
      "players?select=id,nickname,team_id&team_id=not.is.null&order=nickname.asc",
    ),
  ]);
  return teams.map((t) => ({
    slug: t.slug,
    name: t.name,
    players: players.filter((p) => p.team_id === t.id).map(({ id, nickname }) => ({ id, nickname })),
  }));
}

export type InsertResult = "ok" | "duplicado" | "erro";

// Envio da comunidade. A RLS só permite inserir com status pendente; ninguém de fora lê a fila.
export async function insertSubmission(row: {
  player_id: number;
  code: string;
  source_url: string | null;
}): Promise<InsertResult> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/submissions`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json", Prefer: "return=minimal" }),
    body: JSON.stringify(row),
  });
  if (res.ok) return "ok";
  const body = await res.text();
  // 23505 = violação de unicidade: o mesmo código já está pendente para esse jogador.
  if (res.status === 409 && body.includes('"23505"')) return "duplicado";
  console.error(`Supabase ${res.status} ao salvar envio: ${body.slice(0, 300)}`);
  return "erro";
}
