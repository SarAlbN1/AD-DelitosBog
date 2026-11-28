// Formato numérico del informe: coma decimal y punto de miles (es-CO).
const cache = new Map<number, Intl.NumberFormat>();

export function num(x: number, decimales = 0): string {
  let f = cache.get(decimales);
  if (!f) {
    f = new Intl.NumberFormat("es-CO", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
    cache.set(decimales, f);
  }
  return f.format(x).replace(/ /g, " ");
}

export const pct = (x: number, decimales = 1): string => `${num(x, decimales)} %`;

/** Valor p separado en mantisa y exponente, para escribirlo con <sup>: 2·10<sup>−9</sup>. */
export function valorP(p: number): { texto: string; exponente?: string } {
  if (p >= 0.001) return { texto: num(p, 3) };
  const exp = Math.floor(Math.log10(p));
  const man = Math.round(p / 10 ** exp);
  return { texto: `${man}·10`, exponente: String(exp).replace("-", "−") };
}

const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
export const mesCorto = (iso: string): string => {
  const [a, m] = iso.split("-");
  return `${MESES[Number(m) - 1]} ${a.slice(2)}`;
};
export const fechaCorta = (iso: string): string => {
  const [, m, d] = iso.split("-");
  return `${Number(d)} ${MESES[Number(m) - 1]}`;
};
