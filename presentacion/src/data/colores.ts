// Un color fijo por modelo en toda la presentación. Las familias comparten tono:
// árboles en azules, modelos de series en verdes, regresión en ocre y la barra en gris.
export const COLOR = {
  observado: "#111827",
  gradiente_histogramas: "#1d64b4",
  bosque_aleatorio: "#8ab4e0",
  ets: "#2f7d5b",
  sarima: "#86bc9c",
  regresion_lineal: "#b7791f",
  barra: "#9aa0a6",
  oxido: "#b4441a",
  azul: "#174778",
  gris: "#5b6472",
  linea: "#e3e1db",
} as const;

export const NOMBRE: Record<string, string> = {
  gradiente_histogramas: "Gradiente por histogramas",
  bosque_aleatorio: "Bosque aleatorio",
  ets: "ETS",
  sarima: "SARIMA",
  regresion_lineal: "Regresión lineal",
  barra: "Ingenuo estacional (barra)",
};

export const MODELOS_FINALES = [
  "gradiente_histogramas",
  "ets",
  "sarima",
  "bosque_aleatorio",
  "regresion_lineal",
] as const;
