import type { CrosshairParams } from "@/lib/types";

// Área mostrada no preview, em pixels de uma tela 1080p, e tamanho final na página.
// Iguais: a mira aparece no tamanho real que tem no jogo em 1080p, sem ampliar.
const AREA = 160;
const SIZE = 160;

type Shape = { x: number; y: number; w: number; h: number };

/** Mede a mira em pixels de 1080p. O formato legacy-v1 (CS:GO) usa unidades próprias: conversão aproximada. */
function measure(p: CrosshairParams) {
  if (p.format === "legacy-v1") {
    return {
      length: p.length * 2,
      thickness: Math.max(1, Math.round(p.thickness * 2)),
      gap: p.gap * 2 + 4,
      approximate: true,
    };
  }
  // O jogo desenha em pixels inteiros; sem arredondar, as bordas ficam borradas.
  const scale = 1080 / (p.screenHeight || 1080);
  return {
    length: Math.round(p.length * scale),
    thickness: Math.max(1, Math.round(p.thickness * scale)),
    gap: Math.round(p.gap * scale),
    approximate: false,
  };
}

function outlineWidth(p: CrosshairParams): number {
  if (p.format === "legacy-v1") return p.outlineEnabled ? (p.outline ?? 1) : 0;
  if (p.outlineMode !== undefined) return p.outlineMode === 0 ? 0 : p.outlineMode === 2 ? 0.5 : 1;
  return p.outlineEnabled ? 1 : 0;
}

/** Estilos fora da cruz clássica (círculo, quadrado) são desenhados de forma ilustrativa. */
export function isApproximate(p: CrosshairParams): boolean {
  const crossStyles = p.format === "legacy-v1" ? true : [0, 2, 4, 5, 6].includes(p.style);
  return measure(p).approximate || !crossStyles;
}

export function CrosshairPreview({ params: p, label }: { params: CrosshairParams; label: string }) {
  const { length, thickness, gap } = measure(p);
  const color = `rgba(${p.red},${p.green},${p.blue},${p.format === "legacy-v1" && !p.alphaEnabled ? 1 : p.alpha / 255})`;
  const outline = outlineWidth(p);
  const outlineColor =
    p.outlineRed !== undefined
      ? `rgba(${p.outlineRed},${p.outlineGreen},${p.outlineBlue},${(p.outlineAlpha ?? 255) / 255})`
      : "#000";

  const half = thickness / 2;
  const inner = Math.max(gap, -half);
  const shapes: Shape[] = [];
  const circle = p.format !== "legacy-v1" && (p.style === 1 || p.style === 3);
  const square = p.format !== "legacy-v1" && p.style >= 7;
  const dotOnly = p.format !== "legacy-v1" && p.style === 6;

  if (!circle && !square && !dotOnly && length > 0) {
    shapes.push({ x: inner, y: -half, w: length, h: thickness }); // direita
    shapes.push({ x: -inner - length, y: -half, w: length, h: thickness }); // esquerda
    shapes.push({ x: -half, y: inner, w: thickness, h: length }); // baixo
    if (!p.tStyleEnabled) shapes.push({ x: -half, y: -inner - length, w: thickness, h: length }); // cima
  }
  if (p.centerDotEnabled || dotOnly) shapes.push({ x: -half, y: -half, w: thickness, h: thickness });

  const radius = Math.max(gap + length / 2, 2);
  const extent = Math.max(Math.abs(inner) + length, radius + thickness, AREA / 2 - 4) + outline + 4;
  const view = Math.max(AREA, extent * 2);

  return (
    <svg
      role="img"
      aria-label={label}
      viewBox={`${-view / 2} ${-view / 2} ${view} ${view}`}
      width={SIZE}
      height={SIZE}
      shapeRendering="crispEdges"
      className="rounded-lg bg-[radial-gradient(circle_at_30%_20%,#5b6470,#2b3038_60%,#1b1e24)]"
    >
      {circle && (
        <circle r={radius} fill="none" stroke={color} strokeWidth={thickness} shapeRendering="geometricPrecision" />
      )}
      {square && (
        <rect
          x={-radius}
          y={-radius}
          width={radius * 2}
          height={radius * 2}
          fill="none"
          stroke={color}
          strokeWidth={thickness}
        />
      )}
      {outline > 0 &&
        shapes.map((s, i) => (
          <rect
            key={`o${i}`}
            x={s.x - outline}
            y={s.y - outline}
            width={s.w + outline * 2}
            height={s.h + outline * 2}
            fill={outlineColor}
          />
        ))}
      {shapes.map((s, i) => (
        <rect key={i} x={s.x} y={s.y} width={s.w} height={s.h} fill={color} />
      ))}
    </svg>
  );
}
