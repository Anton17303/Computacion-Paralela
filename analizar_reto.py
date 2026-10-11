#!/usr/bin/env python3
"""
Lab 12 — Reto opcional: resume las corridas independientes de ./lab12 suma hechas
con los tamanos[] modificados y marca si hubo S > p repetible.

Uso:
    python3 analizar_reto.py [carpeta_con_csv]
Espera: suma_reto_run*.csv (el enunciado pide al menos 5 corridas)
No inventa nada: si hay menos de 5 corridas, lo avisa.
"""
import glob
import os
import statistics
import sys
from collections import defaultdict

from analizar_partes12 import leer

MIN_CORRIDAS = 5


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join("resultados", "reto")
    archivos = sorted(glob.glob(os.path.join(d, "suma_reto_run*.csv")))
    print(f"corridas: {len(archivos)}")
    if len(archivos) < MIN_CORRIDAS:
        print(f"!! hay menos de {MIN_CORRIDAS} corridas, el reto no cuenta")
    if not archivos:
        return

    s_por = defaultdict(list)
    c_seq = defaultdict(list)
    for a in archivos:
        for r in leer(a):
            s_por[(r["N"], r["p"])].append(r["S"])
            if r["p"] == 1:
                # costo secuencial por elemento, para ver si la memoria limita
                c_seq[r["N"]].append(r["t_seq"] / r["N"] * 1e9)

    print("\nN | MiB | p | S mediana | S min | S max | S>p en todas | S>p en alguna")
    for (n, p), v in sorted(s_por.items()):
        todas = "SI" if all(x > p for x in v) else "no"
        print(f"{n} | {n * 8 / 2**20:g} | {p} | {statistics.median(v):.3f} | {min(v):.3f} | "
              f"{max(v):.3f} | {todas} | {sum(x > p for x in v)}/{len(v)}")

    print("\ncosto secuencial por elemento (ns), mediana de las corridas:")
    for n, v in sorted(c_seq.items()):
        print(f"  N={n} ({n * 8 / 2**20:g} MiB): {statistics.median(v):.3f} ns  "
              f"(min {min(v):.3f}, max {max(v):.3f})")


if __name__ == "__main__":
    main()
