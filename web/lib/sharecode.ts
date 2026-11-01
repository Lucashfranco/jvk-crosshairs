// Validação do código de mira antes de aceitar um envio (mesmas regras de pipeline/jvk_pipeline/sharecode.py).
// A decodificação completa fica no pipeline; aqui só conferimos formato, tamanho e checksum.
const DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789";
const CS2_RE = new RegExp(`^CS[${DICTIONARY}]{44}$`);
const LEGACY_RE = new RegExp(`^CSGO(-?[${DICTIONARY}]{5}){5}$`);

function toBytes(chars: string, byteLength: number): number[] | null {
  // Número em base 57, com o caractere menos significativo primeiro.
  let big = BigInt(0);
  for (const ch of [...chars].reverse()) big = big * BigInt(57) + BigInt(DICTIONARY.indexOf(ch));
  const bytes: number[] = [];
  for (let i = 0; i < byteLength; i++) {
    bytes.unshift(Number(big & BigInt(255)));
    big >>= BigInt(8);
  }
  return big === BigInt(0) ? bytes : null;
}

function checksumOk(b: number[]): boolean {
  return b[0] === b.slice(1).reduce((s, v) => s + v, 0) % 256;
}

/** Devolve o código normalizado (com hífens no formato antigo) ou null se for inválido. */
export function normalizeCrosshairCode(raw: string): string | null {
  const code = raw.trim();
  if (CS2_RE.test(code)) {
    const b = toBytes(code.slice(2), 32);
    // Byte 1 = versão; bytes 2-3 = altura da tela, que não pode ser zero.
    return b && checksumOk(b) && b[1] === 1 && (b[2] | (b[3] << 8)) !== 0 ? code : null;
  }
  if (LEGACY_RE.test(code)) {
    const chars = code.slice(4).replaceAll("-", "");
    const b = toBytes(chars, 18);
    if (!b || !checksumOk(b) || ![1, 3, 4].includes(b[1])) return null;
    return "CSGO-" + chars.match(/.{5}/g)!.join("-");
  }
  return null;
}
