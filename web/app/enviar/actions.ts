"use server";

import { insertSubmission, usingSampleData } from "@/lib/data";
import { normalizeCrosshairCode } from "@/lib/sharecode";

export type SubmitState = { ok: boolean; message: string } | null;

const RECEIVED = "Recebido! A mira passa por revisão e, se aprovada, entra no site na próxima atualização semanal.";

export async function submitCrosshair(_prev: SubmitState, formData: FormData): Promise<SubmitState> {
  // Campo invisível: só robôs preenchem. Respondemos como sucesso para não dar pista.
  if (formData.get("website")) return { ok: true, message: RECEIVED };
  if (usingSampleData) return { ok: false, message: "Envios desativados: o site está com dados de exemplo." };

  const playerId = Number(formData.get("player_id"));
  if (!Number.isInteger(playerId) || playerId <= 0) return { ok: false, message: "Escolha o time e o jogador." };

  const code = normalizeCrosshairCode(String(formData.get("code") ?? ""));
  if (!code) {
    return { ok: false, message: "Esse código de mira não é válido. Confira se copiou ele inteiro (CS… ou CSGO-…)." };
  }

  const sourceUrl = String(formData.get("source_url") ?? "").trim();
  if (sourceUrl && !(sourceUrl.length <= 300 && /^https?:\/\/\S+$/i.test(sourceUrl))) {
    return { ok: false, message: "O link precisa começar com http:// ou https://." };
  }

  const result = await insertSubmission({ player_id: playerId, code, source_url: sourceUrl || null });
  if (result === "duplicado") return { ok: true, message: "Esse código já está na fila de revisão para esse jogador." };
  if (result === "erro") return { ok: false, message: "Não conseguimos salvar agora. Tente de novo em alguns minutos." };
  return { ok: true, message: RECEIVED };
}
