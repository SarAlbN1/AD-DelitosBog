// Datos de la presentación. Los JSON de `generado/` los escribe scripts/preparar_datos.py a partir de
// archivos versionados de outputs/. Aquí solo se tipan y se exportan: ninguna cifra se escribe a mano.
import serieJson from "./generado/serie.json";
import embudoJson from "./generado/embudo.json";
import fuentesJson from "./generado/fuentes.json";
import territorioJson from "./generado/territorio.json";
import modelosJson from "./generado/modelos.json";
import pronosticoJson from "./generado/pronostico.json";
import interpretacionJson from "./generado/interpretacion.json";

export interface Serie {
  dias: number;
  victimas: number;
  inicio: string;
  fin: string;
  media: number;
  mensual: { mes: string; media: number }[];
  anual: { anio: number; media: number; victimas: number; dias: number; completo: boolean }[];
  dia_semana: { dia: string; media: number }[];
  por_mes: { mes: string; media: number }[];
  festivos: {
    media_en_festivo: number;
    media_en_no_festivo: number;
    n_festivos: number;
    media_lunes_festivo: number;
    media_lunes_laborable: number;
    n_lunes_festivo: number;
    n_lunes_laborable: number;
    diferencia_lunes_pct: number;
  };
}

export interface PasoEmbudo {
  paso: string;
  filas: number;
  motivo: string;
}

export interface Fuentes {
  meses: number;
  serie: Record<string, string | number | null>[];
  correlaciones: { policia_fiscalia: number; policia_linea123: number; policia_linea123_sin2020: number };
}

export interface Localidad {
  localidad: string;
  incidentes: number;
  tasa: number;
  puesto_conteo: number;
  puesto_tasa: number;
}

export interface FilaModelo {
  id: string;
  nombre: string;
  familia: "arboles" | "estadistico" | "regresion" | "comparador";
  MAE: number;
  RMSE: number;
  MAPE: number;
  MASE: number;
  delta_pct: number | null;
  p: number | null;
  mae_medio_pliegues: number | null;
  desv_pliegues: number | null;
  peor_pliegue: number | null;
  pliegues_ganados: number | null;
}

export interface Modelos {
  tabla: FilaModelo[];
  pliegues: Record<string, number>[];
  comparadores_pliegues: {
    fin_entrenamiento: string;
    fin_evaluacion: string;
    dias_entrenamiento: number;
    ingenuo: number;
    ingenuo_estacional: number;
    media_movil_7: number;
    media_movil_28: number;
  }[];
  dm: { a: string; b: string; p_hln: number; p_nw: number }[];
  festivos: {
    nombre: string;
    mae_festivo: number;
    sesgo_festivo: number;
    mae_no_festivo: number;
    sesgo_no_festivo: number;
  }[];
}

export interface DiaPronostico {
  fecha: string;
  real: number;
  gradiente_histogramas: number;
  ets: number;
  sarima: number;
  bosque_aleatorio: number;
  regresion_lineal: number;
  barra: number;
  festivo: number;
}

export interface Interpretacion {
  grupos: { grupo: string; gradiente: number; bosque: number }[];
  coeficientes: { variable: string; tipo: string; estandarizado: number; por_unidad: number }[];
}

export const serie = serieJson as Serie;
export const embudo = embudoJson as PasoEmbudo[];
export const fuentes = fuentesJson as unknown as Fuentes;
export const territorio = territorioJson as Localidad[];
export const modelos = modelosJson as unknown as Modelos;
export const pronostico = pronosticoJson as DiaPronostico[];
export const interpretacion = interpretacionJson as unknown as Interpretacion;

export const modelo = (id: string): FilaModelo => {
  const m = modelos.tabla.find((x) => x.id === id);
  if (!m) throw new Error(`modelo desconocido: ${id}`);
  return m;
};
