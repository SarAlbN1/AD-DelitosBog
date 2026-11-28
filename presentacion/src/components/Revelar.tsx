import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useModo } from "../hooks/modo";

interface Props {
  children: ReactNode;
  /** Orden de aparición: cada paso suma 0,12 s de retraso. */
  paso?: number;
  className?: string;
  desde?: "abajo" | "izquierda" | "nada";
}

/** Entrada progresiva y discreta. En impresión se dibuja directamente en su estado final. */
export function Revelar({ children, paso = 0, className, desde = "abajo" }: Props) {
  const { impresion } = useModo();
  if (impresion) return <div className={className}>{children}</div>;
  const inicial = desde === "abajo" ? { opacity: 0, y: 18 } : desde === "izquierda" ? { opacity: 0, x: -18 } : { opacity: 0 };
  return (
    <motion.div
      className={className}
      initial={inicial}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{ duration: 0.45, delay: 0.1 + paso * 0.12, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
