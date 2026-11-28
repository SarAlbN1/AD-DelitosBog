import katex from "katex";
import { useMemo } from "react";

interface Props {
  tex: string;
  bloque?: boolean;
  className?: string;
}

/** Fórmula con KaTeX, renderizada en el propio HTML: no depende de red ni de scripts externos. */
export function Formula({ tex, bloque = false, className }: Props) {
  const html = useMemo(
    () => katex.renderToString(tex, { displayMode: bloque, throwOnError: true, output: "html" }),
    [tex, bloque],
  );
  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}
