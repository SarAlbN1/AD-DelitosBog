/**
 * Por qué no se baraja: con validación cruzada aleatoria, los días de prueba quedan rodeados de días de
 * entrenamiento, y con rezagos el modelo ve a sus vecinos. Con origen rodante, la prueba siempre es posterior.
 */
export function DiagramaFuga() {
  const n = 24;
  const w = 24;
  const gap = 5;
  // Patrón fijo (no aleatorio en cada render) para la partición barajada.
  const barajado = [3, 6, 7, 11, 15, 18, 21];
  const fila = (y: number, tipo: (i: number) => "ent" | "prueba" | "fuera") =>
    Array.from({ length: n }, (_, i) => {
      const t = tipo(i);
      const fill = t === "ent" ? "#c9d5e4" : t === "prueba" ? "#b4441a" : "#f0eee9";
      return <rect key={i} x={i * (w + gap)} y={y} width={w} height={40} rx={4} fill={fill} />;
    });
  const anchoTotal = n * (w + gap);
  return (
    <svg width={anchoTotal + 10} height={300} className="block">
      <text x={0} y={22} fontSize={20} fontWeight={600} fill="#b4441a">
        Validación cruzada aleatoria: no válida aquí
      </text>
      {fila(36, (i) => (barajado.includes(i) ? "prueba" : "ent"))}
      <text x={0} y={104} fontSize={17} fill="#5b6472">
        Sus vecinos están en el entrenamiento: con rezagos, el error sale optimista.
      </text>
      <text x={0} y={170} fontSize={20} fontWeight={600} fill="#2f7d5b">
        Origen rodante: la prueba siempre es posterior
      </text>
      {fila(184, (i) => (i < 17 ? "ent" : i < 20 ? "prueba" : "fuera"))}
      <line x1={17 * (w + gap) - 3} x2={17 * (w + gap) - 3} y1={176} y2={232} stroke="#14213d" strokeWidth={2} strokeDasharray="4 3" />
      <text x={17 * (w + gap) - 8} y={252} fontSize={16} fill="#14213d" textAnchor="end">
        origen del pronóstico
      </text>
      <text x={0} y={284} fontSize={17} fill="#5b6472">
        Se entrena con el pasado, se predice lo que sigue y el origen avanza.
      </text>
    </svg>
  );
}
