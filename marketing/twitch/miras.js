// Miras de alguns pros (do site, nov/2026) e o desenho delas em SVG, igual à prévia do site:
// pixels de uma tela 1080p, arredondados como o jogo desenha.
const PROS = [
  { nick: "donk", style: 4, length: 2, thickness: 2, gap: 1, rgb: [37, 255, 0], dot: false, h: 960 },
  { nick: "ZywOo", style: 4, length: 2, thickness: 2, gap: 2, rgb: [0, 233, 255], dot: false, h: 768 },
  { nick: "m0NESY", style: 8, length: 4, thickness: 2, gap: 0, rgb: [0, 255, 246], dot: true, h: 960 },
  { nick: "NiKo", style: 4, length: 2, thickness: 2, gap: 2, rgb: [0, 255, 145], dot: false, h: 960 },
  { nick: "ropz", style: 4, length: 4, thickness: 1, gap: 2, rgb: [0, 255, 0], dot: false, h: 1080 },
  { nick: "FalleN", style: 4, length: 3, thickness: 2, gap: 0, rgb: [213, 255, 21], dot: false, h: 960 },
];

// view: quantos pixels de tela o quadro mostra (menor = mais zoom).
function crosshairSvg(p, view) {
  const s = 1080 / p.h;
  const len = Math.round(p.length * s), th = Math.max(1, Math.round(p.thickness * s)), gap = Math.round(p.gap * s);
  const half = th / 2, inner = Math.max(gap, -half);
  const fill = `rgb(${p.rgb.join(",")})`;
  const r = (x, y, w, h) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}"/>`;
  let out = "";
  if (p.style >= 7) {
    const rad = Math.max(gap + len / 2, 2);
    out += `<rect x="${-rad}" y="${-rad}" width="${rad * 2}" height="${rad * 2}" fill="none" stroke="${fill}" stroke-width="${th}"/>`;
  } else {
    out += r(inner, -half, len, th) + r(-inner - len, -half, len, th) + r(-half, inner, th, len) + r(-half, -inner - len, th, len);
  }
  if (p.dot) out += r(-half, -half, th, th);
  return `<svg viewBox="${-view / 2} ${-view / 2} ${view} ${view}">${out}</svg>`;
}

function fillScope(el, p, view) {
  el.innerHTML = crosshairSvg(p, view) + `<div class="who">${p.nick}</div>`;
}
