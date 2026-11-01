import type { Metadata } from "next";
import { Suspense } from "react";
import { SubmitForm } from "@/components/SubmitForm";
import { getRosters } from "@/lib/data";

export const metadata: Metadata = {
  title: "Enviar mira | JVK Crosshairs",
  description: "Mande o código de mira de um pro de CS2 para entrar no JVK Crosshairs.",
};

export default function SubmitPage({ searchParams }: PageProps<"/enviar">) {
  return (
    <>
      <h1 className="font-display text-3xl font-bold">Enviar mira</h1>
      <p className="mt-2 mb-6 max-w-2xl text-muted">
        Viu a mira de um pro numa stream, num vídeo ou nas configurações dele? Mande o código aqui. Cada envio é revisado
        antes de aparecer no site.
      </p>
      <Suspense fallback={<p className="text-muted">Carregando times…</p>}>
        {searchParams.then(({ jogador }) => (
          <Form jogador={typeof jogador === "string" ? Number(jogador) : undefined} />
        ))}
      </Suspense>
    </>
  );
}

async function Form({ jogador }: { jogador?: number }) {
  const rosters = await getRosters();
  return <SubmitForm rosters={rosters} defaultPlayerId={jogador} />;
}
