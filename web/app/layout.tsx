import type { Metadata } from "next";
import { Inter, Oxanium } from "next/font/google";
import Link from "next/link";
import { usingSampleData } from "@/lib/data";
import "flag-icons/css/flag-icons.min.css";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const oxanium = Oxanium({ variable: "--font-oxanium", subsets: ["latin"], weight: ["500", "700"] });

export const metadata: Metadata = {
  title: "JVK Crosshairs: miras dos pros de CS2",
  description: "Copie a mira dos jogadores profissionais de CS2 dos times do top 20 mundial.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${inter.variable} ${oxanium.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col font-sans">
        <header className="border-b border-line">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="font-display text-xl font-bold tracking-wide">
              JVK <span className="text-accent">Crosshairs</span>
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link href="/enviar" className="font-semibold text-accent hover:text-ink">
                Enviar mira
              </Link>
              <span className="hidden text-muted sm:inline">por JVK Performance</span>
            </nav>
          </div>
        </header>
        {usingSampleData && (
          <div className="border-b border-accent/40 bg-accent/10 px-4 py-2 text-center text-sm text-ink">
            Dados de exemplo: os times e jogadores abaixo não são reais. O banco ainda não foi conectado.
          </div>
        )}
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-line px-4 py-6 text-center text-xs text-muted">
          Miras do{" "}
          <a
            href="https://liquipedia.net/counterstrike/Liquipedia:Copyrights"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-accent"
          >
            Liquipedia (CC BY-SA)
          </a>{" "}
          e enviadas pela comunidade. Fotos e logos via Liquipedia, de seus respectivos donos. Ranking: Valve
          Regional Standings. Não afiliado à Valve.
        </footer>
      </body>
    </html>
  );
}
