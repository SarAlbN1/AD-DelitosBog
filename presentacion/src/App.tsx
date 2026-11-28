import { Presentador } from "./components/Presentador";
import { VistaImpresion } from "./components/VistaImpresion";
import { DIAPOSITIVAS } from "./slides";

/** `?modo=impresion` muestra la vista para el PDF; sin parámetros, el modo presentación. */
export default function App() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("modo") === "impresion") {
    return <VistaImpresion diapositivas={DIAPOSITIVAS} imprimir={params.get("imprimir") === "1"} />;
  }
  return <Presentador diapositivas={DIAPOSITIVAS} />;
}
