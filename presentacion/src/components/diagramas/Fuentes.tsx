import { Building2, Gavel, PhoneCall } from "lucide-react";
import { Revelar } from "../Revelar";

const FUENTES = [
  {
    icono: Building2,
    nombre: "Policía Nacional",
    rol: "Fuente principal",
    fila: "Una víctima",
    tiempo: "Día del hecho",
    lugar: "Municipio (sin localidad)",
    volumen: "741.986 registros, 2020–2025",
    color: "#174778",
  },
  {
    icono: PhoneCall,
    nombre: "Línea 123",
    rol: "Complementaria",
    fila: "Un conteo de llamadas tramitadas",
    tiempo: "Mes",
    lugar: "Localidad y UPZ",
    volumen: "25.144 filas de hurto, 2018–2025",
    color: "#2f7d5b",
  },
  {
    icono: Gavel,
    nombre: "Fiscalía",
    rol: "Complementaria",
    fila: "Un par proceso–delito",
    tiempo: "Año y mes",
    lugar: "Bogotá (sin localidad)",
    volumen: "1.300.703 registros, 2018–2025",
    color: "#b7791f",
  },
];

/** Las tres fuentes y lo que representa una fila en cada una. */
export function DiagramaFuentes() {
  return (
    <div className="grid grid-cols-3 gap-8">
      {FUENTES.map((f, i) => {
        const Icono = f.icono;
        return (
          <Revelar key={f.nombre} paso={i}>
            <div className="h-full rounded-[14px] border border-linea bg-white p-8" style={{ borderTop: `6px solid ${f.color}` }}>
              <div className="flex items-center gap-4">
                <span className="flex h-14 w-14 items-center justify-center rounded-full" style={{ background: `${f.color}18` }}>
                  <Icono size={30} color={f.color} strokeWidth={1.8} />
                </span>
                <div>
                  <div className="font-serif text-[32px] leading-none font-semibold">{f.nombre}</div>
                  <div className="mt-1 text-[18px] font-semibold uppercase tracking-[0.1em]" style={{ color: f.color }}>
                    {f.rol}
                  </div>
                </div>
              </div>
              <dl className="mt-8 space-y-5 text-[25px]">
                {[
                  ["Una fila es", f.fila],
                  ["Resolución temporal", f.tiempo],
                  ["Resolución territorial", f.lugar],
                  ["Volumen", f.volumen],
                ].map(([k, v]) => (
                  <div key={k} className="border-t border-linea pt-3">
                    <dt className="text-[17px] font-semibold uppercase tracking-[0.1em] text-suave">{k}</dt>
                    <dd className="mt-1 leading-snug text-tinta">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </Revelar>
        );
      })}
    </div>
  );
}
