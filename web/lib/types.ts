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

export type PlayerCrosshair = {
  steamid: string;
  nickname: string;
  code: string;
  format: CrosshairParams["format"];
  params: CrosshairParams;
  console: string;
  last_seen: string;
};
