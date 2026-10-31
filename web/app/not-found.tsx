import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="font-display text-3xl font-bold">Não encontrado</h1>
      <p className="mt-2 text-muted">Esse time não está na nossa lista.</p>
      <Link href="/" className="mt-6 inline-block text-accent hover:underline">
        Ver todos os times
      </Link>
    </div>
  );
}
