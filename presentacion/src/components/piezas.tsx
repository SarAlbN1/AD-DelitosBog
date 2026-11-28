import type { ReactNode } from "react";

/** Cifra destacada con su etiqueta y, si hace falta, su fuente. */
export function Cifra({
  valor,
  etiqueta,
  detalle,
  tono = "azul",
}: {
  valor: ReactNode;
  etiqueta: ReactNode;
  detalle?: ReactNode;
  tono?: "azul" | "oxido" | "tinta" | "verde";
}) {
  const color = { azul: "text-azul", oxido: "text-oxido", tinta: "text-tinta", verde: "text-verde" }[tono];
  return (
    <div>
      <div className={`font-serif text-[64px] leading-none font-semibold tabular ${color}`}>{valor}</div>
      <div className="mt-3 text-[24px] leading-snug text-tinta">{etiqueta}</div>
      {detalle && <div className="mt-1 text-[19px] leading-snug text-gris">{detalle}</div>}
    </div>
  );
}

/** Etiqueta pequeña en versalitas, para rotular bloques. */
export function Rotulo({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`text-[17px] font-semibold uppercase tracking-[0.14em] text-gris ${className}`}>{children}</div>
  );
}

/** Panel con borde fino. Se usa solo cuando agrupa algo que se lee como unidad. */
export function Panel({
  children,
  className = "",
  tono = "blanco",
}: {
  children: ReactNode;
  className?: string;
  tono?: "blanco" | "azul" | "oxido" | "panel" | "verde";
}) {
  const fondo = {
    blanco: "bg-white border-linea",
    azul: "bg-azul-claro border-[#cfdbea]",
    oxido: "bg-oxido-claro border-[#efd2c5]",
    panel: "bg-panel border-linea",
    verde: "bg-verde-claro border-[#cde3d6]",
  }[tono];
  return <div className={`rounded-[14px] border ${fondo} ${className}`}>{children}</div>;
}

/** Fuente de una cifra o gráfico, al pie. */
export function Fuente({ children }: { children: ReactNode }) {
  return <div className="text-[16px] text-suave">Fuente: <span className="font-mono text-[15px]">{children}</span></div>;
}

/** Marca de estado: lo que está hecho, lo que no y lo que queda como trabajo futuro. */
export function Estado({ tipo, children }: { tipo: "hecho" | "parcial" | "futuro" | "no"; children: ReactNode }) {
  const estilo = {
    hecho: "bg-verde-claro text-verde",
    parcial: "bg-[#fdf3dc] text-[#8a5a0b]",
    futuro: "bg-azul-claro text-azul",
    no: "bg-oxido-claro text-oxido",
  }[tipo];
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-[3px] text-[16px] font-semibold ${estilo}`}>
      {children}
    </span>
  );
}

/** Leyenda de una gráfica: muestra de color y nombre. */
export function Leyenda({
  items,
}: {
  items: { color: string; nombre: string; discontinua?: boolean; grosor?: number }[];
}) {
  return (
    <div className="flex flex-wrap gap-x-7 gap-y-2 text-[18px] text-tinta">
      {items.map((it) => (
        <span key={it.nombre} className="inline-flex items-center gap-2">
          <svg width="30" height="10" aria-hidden>
            <line
              x1="0"
              y1="5"
              x2="30"
              y2="5"
              stroke={it.color}
              strokeWidth={it.grosor ?? 4}
              strokeDasharray={it.discontinua ? "6 4" : undefined}
            />
          </svg>
          {it.nombre}
        </span>
      ))}
    </div>
  );
}
