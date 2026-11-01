// Parâmetros decodificados pelo pipeline (pipeline/jvk_pipeline/sharecode.py).
// As chaves seguem a biblioteca csgo-sharecode; cada formato preenche um subconjunto.
export type CrosshairParams = {
  format: "cs2-v1" | "legacy-v1" | "legacy-v3" | "legacy-v4";
  style: number;
  red: number;
  green: number;
  blue: number;
  alpha: number;
  gap: number;
  length: number;
  thickness: number;
  centerDotEnabled: boolean;
  tStyleEnabled: boolean;
  screenHeight?: number;
  outlineMode?: number; // cs2-v1, legacy-v4: 0 nenhum, 1 completo, 2 metade
  outlineEnabled?: boolean; // legacy-v1, legacy-v3
  outline?: number; // legacy-v1: espessura do contorno
  outlineRed?: number;
  outlineGreen?: number;
  outlineBlue?: number;
  outlineAlpha?: number;
  alphaEnabled?: boolean; // legacy-v1
};

export type Team = {
  id?: number;
  slug: string;
  name: string;
  rank: number | null;
  logo_url: string | null;
};

// Linha da view current_crosshairs: todo jogador do time, com a mira mais recente (code nulo = ainda sem mira).
export type PlayerCrosshair = {
  player_id: number;
  nickname: string;
  code: string | null;
  format: CrosshairParams["format"] | null;
  params: CrosshairParams | null;
  console: string | null;
  last_seen: string | null;
  source: string | null; // "Liquipedia" ou "envio #<id>"
  source_url: string | null;
  photo_url: string | null; // foto do Liquipedia, copiada para o Storage
  photo_credit: string | null; // autor e dono da foto
  country_code: string | null; // ISO 3166-1 alfa-2, minúsculo
};

export type RosterTeam = {
  slug: string;
  name: string;
  players: { id: number; nickname: string }[];
};
