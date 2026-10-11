#!/usr/bin/env python3
"""
Lab 12 — Partes 3 y 4: calcula, a partir de los CSV originales, todos los números
que piden (comparación de schedules, trapecios, modelo de Gustafson).

Uso:
    python3 analizar_partes34.py [carpeta_con_csv]
Espera: desb_static.csv desb_dynamic.csv desb_guided.csv gustafson.csv
No inventa nada: si falta un archivo, lo avisa.
"""
import os
import sys

from analizar_partes12 import amdahl, leer

ITERS = 1000  # igual que ITERS en lab12_speedup.c, costo(i) = 1 + 2*ITERS*i/W
SCHEDULES = ["static", "dynamic", "guided"]


def costo(i, w):
    # misma fórmula entera que el .c
    return 1 + int((2.0 * ITERS * i) / w)


def fraccion_max_trapecio(p):
    # el último bloque es el más caro: área del trapecio / área total
    return (1 + 2 * ITERS * (p - 0.5) / p) / (p * (1 + ITERS))


def fraccion_max_exacta(p, w):
    # suma real de costo(i) por bloque contiguo; solo vale si p divide a w
    q = w // p
    bloques = [sum(costo(i, w) for i in range(k * q, (k + 1) * q)) for k in range(p)]
    return max(bloques) / sum(bloques)


def parte3(d):
    datos = {}
    for s in SCHEDULES:
        ruta = os.path.join(d, f"desb_{s}.csv")
        if os.path.exists(ruta):
            datos[s] = {r["p"]: r for r in leer(ruta)}
        else:
            print(f"!! falta {ruta}")
    if not datos:
        return

    pmax = min(max(rs) for rs in datos.values())
    w = next(iter(datos.values()))[1]["N"]

    print("## P3.1: S(pmax) por schedule\n")
    for s, rs in datos.items():
        r = rs[pmax]
        print(f"  {s:8s} p={pmax}: Tp = {r['t_par']:.6f}  S = {r['S']:.3f}  E = {r['E']:.3f}")
    if "static" in datos:
        st = datos["static"][pmax]["S"]
        for s in ("dynamic", "guided"):
            if s in datos:
                x = datos[s][pmax]["S"]
                print(f"  {s} vs static: ΔS = {x - st:+.3f}  ({100 * (x - st) / st:+.1f}%)")
    if "dynamic" in datos and "guided" in datos:
        dy, gu = datos["dynamic"][pmax]["S"], datos["guided"][pmax]["S"]
        print(f"  guided vs dynamic: ΔS = {gu - dy:+.3f}  ({100 * (gu - dy) / dy:+.1f}%)")

    if "static" in datos:
        rs = datos["static"]
        print("\n## P3.2: hilo más cargado con static (W = %d)\n" % w)
        for p in sorted({2, 4, pmax}):
            if w % p:
                print(f"  p={p}: no divide a W, se omite el cálculo exacto")
                continue
            ft, fe = fraccion_max_trapecio(p), fraccion_max_exacta(p, w)
            r = rs[p]
            print(f"  p={p}: fracción trapecio = {ft:.4f}  exacta = {fe:.4f}  "
                  f"-> S predicho = 1/f = {1 / fe:.3f}  S medido = {r['S']:.3f}  "
                  f"error = {100 * (r['S'] - 1 / fe) * fe:+.1f}%")

        print("\n## P3.3: espera de los hilos con static (E predicho = 1/(p·f))\n")
        for p in sorted({2, 4, 8, pmax}):
            if w % p:
                continue
            e_pred = 1 / (p * fraccion_max_exacta(p, w))
            r = rs[p]
            print(f"  p={p}: E predicho = {e_pred:.3f}  E medido = {r['E']:.3f}  "
                  f"-> los hilos esperan ~{100 * (1 - r['E']):.0f}% del tiempo")
        print("\n  E static por p: " + "  ".join(f"p{p}={rs[p]['E']:.3f}" for p in sorted(rs)))

    print("\n## P3.4: costo de repartir en tiempo de ejecución (p = 1)\n")
    for s, rs in datos.items():
        r = rs[1]
        pct = 100 * (r["t_par"] - r["t_seq"]) / r["t_seq"]
        print(f"  {s:8s}: t_seq = {r['t_seq']:.6f}  t_par(1) = {r['t_par']:.6f}  ({pct:+.2f}%)")
    if "dynamic" in datos:
        print(f"  dynamic reparte {w // 64} bloques de 64 iteraciones (W/64)")


def parte4(d):
    ruta = os.path.join(d, "gustafson.csv")
    if not os.path.exists(ruta):
        print(f"!! falta {ruta}")
        return
    rs = sorted(leer(ruta), key=lambda r: r["p"])
    r1, rn = rs[0], rs[-1]
    pmax = rn["p"]

    print("\n## P4.1: evolución de t_seq y t_par\n")
    print(f"  t_seq: {r1['t_seq']:.6f} -> {rn['t_seq']:.6f}  (x{rn['t_seq'] / r1['t_seq']:.2f})")
    print(f"  t_par: {r1['t_par']:.6f} -> {rn['t_par']:.6f}  (x{rn['t_par'] / r1['t_par']:.2f})")

    # con p = 1 la parte secuencial es w_seq / (w_seq + w_por_hilo)
    w_seq = int(r1["param"].split("=")[1])
    fp = 1 - w_seq / r1["N"]
    print("\n## P4.2: Amdahl con la fp de p = 1\n")
    print(f"  fp = 1 - {w_seq}/{r1['N']} = {fp:.4f};  límite 1/(1-fp) = {1 / (1 - fp):.2f};  "
          f"Amdahl S({pmax}) = {amdahl(fp, pmax):.3f};  medido S({pmax}) = {rn['S']:.3f}")

    print("\n## P4.3 y P4.4: s = t_parte_seq / t_par y modelo S = s + (1-s)·p\n")
    print("  p | t_seq | t_par | t_parte_seq | s | S medido | S modelo | error")
    ss = []
    for r in rs:
        s = r["t_parte_seq"] / r["t_par"]
        ss.append(s)
        sm = s + (1 - s) * r["p"]
        print(f"  {r['p']} | {r['t_seq']:.6f} | {r['t_par']:.6f} | {r['t_parte_seq']:.6f} | "
              f"{s:.4f} | {r['S']:.3f} | {sm:.3f} | {100 * (r['S'] - sm) / sm:+.1f}%")
    print(f"\n  s: mín = {min(ss):.4f}  máx = {max(ss):.4f}  promedio = {sum(ss) / len(ss):.4f}")


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    parte3(d)
    parte4(d)


if __name__ == "__main__":
    main()
