import Link from "next/link";
import { TeamLogo } from "@/components/Images";
import { getTeams } from "@/lib/data";

export default async function Home() {
  const teams = await getTeams();

  return (
    <>
      <section className="mb-8">
        <h1 className="font-display text-3xl font-bold sm:text-4xl">Miras dos pros de CS2</h1>
        <p className="mt-2 max-w-2xl text-muted">
          Escolha um time, veja a mira de cada jogador e copie o código ou os comandos de console.
        </p>
      </section>

      {teams.length === 0 ? (
        <p className="rounded-xl border border-line bg-card p-6 text-muted">Nenhum time cadastrado ainda.</p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {teams.map((team) => (
            <li key={team.slug}>
              <Link
                href={`/time/${team.slug}`}
                className="flex items-center gap-3 rounded-xl border border-line bg-card p-4 transition-colors hover:border-accent hover:bg-card-hover focus-visible:outline-2 focus-visible:outline-accent"
              >
                <span className="font-display w-8 text-right text-lg text-accent">
                  {team.rank != null ? `#${team.rank}` : "–"}
                </span>
                <TeamLogo team={team} size={32} />
                <span className="font-display truncate text-lg font-medium">{team.name}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
