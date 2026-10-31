import { cacheLife } from "next/cache";
import sample from "./sample-data.json";
import type { PlayerCrosshair, Team } from "./types";

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Sem Supabase configurado o site usa dados de exemplo (marcados na interface).
export const usingSampleData = !SUPABASE_URL || !SUPABASE_KEY;

type SampleTeam = Team & { players: PlayerCrosshair[] };
const sampleTeams = sample.teams as SampleTeam[];

async function rest<T>(path: string): Promise<T> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: { apikey: SUPABASE_KEY!, Authorization: `Bearer ${SUPABASE_KEY}` },
  });
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
    `current_crosshairs?select=steamid,nickname,code,format,params,console,last_seen&team_id=eq.${team.id}&order=nickname.asc`,
  );
  return { team, players };
}
