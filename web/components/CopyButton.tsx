"use client";

import { useState } from "react";

// Alternativa para navegadores que bloqueiam a Clipboard API (iframes, http sem TLS).
function legacyCopy(text: string): boolean {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  try {
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    area.remove();
  }
}

export function CopyButton({ text, label, primary = false }: { text: string; label: string; primary?: boolean }) {
  const [state, setState] = useState<"idle" | "ok" | "erro">("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setState("ok");
    } catch {
      setState(legacyCopy(text) ? "ok" : "erro");
    }
    setTimeout(() => setState("idle"), 1800);
  }

  return (
    <button
      type="button"
      onClick={copy}
      className={`w-full rounded-lg px-3 py-2 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
        primary
          ? "bg-accent text-white hover:bg-accent-strong"
          : "border border-line text-ink hover:border-accent hover:text-white"
      }`}
    >
      <span aria-live="polite">{state === "ok" ? "Copiado!" : state === "erro" ? "Não deu para copiar" : label}</span>
    </button>
  );
}
