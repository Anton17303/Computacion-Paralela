#!/usr/bin/env python3
"""
Lab 12 — Persona 1: calcula, a partir de TUS CSV originales, todos los números
que piden las Partes 1 y 2 (tabla oficial, cálculos a mano, contrastes).

Uso (en la carpeta con los CSV):
    python3 analizar_persona1.py
Espera: amdahl_fp100.csv amdahl_fp95.csv amdahl_fp90.csv amdahl_fp75.csv
        amdahl_fp50.csv suma.csv
No inventa nada: si falta un archivo o pmax < 4, lo avisa.
"""
import csv
import os
import sys

FPS = ["100", "95", "90", "75", "50"]


def leer(path):
    filas = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            r["N"], r["p"] = int(r["N"]), int(r["p"])
            for k in ("t_seq", "t_par", "t_parte_seq"):
                r[k] = float(r[k])
            r["S"] = r["t_seq"] / r["t_par"]
            r["E"] = r["S"] / r["p"]
            r["C"] = r["p"] * r["t_par"]
            r["F"] = r["S"] / r["C"]
            filas.append(r)
    return filas


def amdahl(fp, p):
    return 1.0 / ((1 - fp) + fp / p)


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    datos = {}
    for fp in FPS:
        ruta = os.path.join(d, f"amdahl_fp{fp}.csv")
        if os.path.exists(ruta):
            datos[fp] = sorted(leer(ruta), key=lambda r: r["p"])
        else:
            print(f"!! falta {ruta}")

    print("## Tabla oficial Parte 1\n")
    print("| fp | S(p=2) | S(p=4) | S(pmax) | E(pmax) | p con F máxima |")
    print("|---|---|---|---|---|---|")
    for fp, rs in datos.items():
        por_p = {r["p"]: r for r in rs}
        pmax = max(por_p)
        s2 = f"{por_p[2]['S']:.3f}" if 2 in por_p else "n/d"
        s4 = f"{por_p[4]['S']:.3f}" if 4 in por_p else "n/d (pmax<4)"
        pf = max(rs, key=lambda r: r["F"])["p"]
        print(f"| {int(fp)/100:.2f} | {s2} | {s4} | {por_p[pmax]['S']:.3f} (p={pmax}) | "
              f"{por_p[pmax]['E']:.3f} | {pf} |")

    if "90" in datos:
        rs = datos["90"]
        pmax = max(r["p"] for r in rs)
        print("\n## Cálculos a mano (fp = 0.90)\n")
        for r in [x for x in rs if x["p"] in (2, pmax)]:
            print(f"p = {r['p']}:  t_seq = {r['t_seq']:.6f}  t_par = {r['t_par']:.6f}")
            print(f"  S = Ts/Tp = {r['t_seq']:.6f}/{r['t_par']:.6f} = {r['S']:.3f}")
            print(f"  E = S/p   = {r['S']:.3f}/{r['p']} = {r['E']:.3f}")
            print(f"  C = p·Tp  = {r['p']}·{r['t_par']:.6f} = {r['C']:.6f} hilo-s")
            print(f"  F = S/C   = {r['S']:.3f}/{r['C']:.6f} = {r['F']:.3f}\n")

        print("## P1.4 y P1.6 (fp = 0.90)")
        r = rs[-1]
        pred = amdahl(0.90, pmax)
        print(f"  S predicho = 1/(0.10+0.90/{pmax}) = {pred:.3f};  S medido = {r['S']:.3f};  "
              f"error = {100*(r['S']-pred)/pred:+.1f}%")
        if pmax > 1:
            fp_est = (pmax / (pmax - 1)) * (1 - 1 / r["S"])
            print(f"  fp despejado = (p/(p-1))·(1-1/S) = {fp_est:.4f}  (nominal 0.90)")
        print(f"  P1.5: límite 1/(1-fp) = {1/0.10:.1f};  S(1000) = {amdahl(0.90,1000):.3f}")

    if "75" in datos:
        rs = {r["p"]: r for r in datos["75"]}
        pmax = max(rs)
        print("\n## P1.2 (fp = 0.75): ganancia marginal ΔS = S(p) - S(p-1)")
        for p in (2, 3, 4, pmax - 1, pmax):
            if p in rs and (p - 1) in rs and p >= 2:
                print(f"  hilo {p}: ΔS = {rs[p]['S']-rs[p-1]['S']:+.3f}")

    if "100" in datos:
        r1 = datos["100"][0]
        print("\n## P2.1 / P2.2 (amdahl_fp100, p = 1)")
        pct = 100 * (r1["t_par"] - r1["t_seq"]) / r1["t_seq"]
        print(f"  t_seq = {r1['t_seq']:.6f}  t_par(p=1) = {r1['t_par']:.6f}  "
              f"-> OpenMP 1 hilo es {pct:+.2f}% respecto al secuencial")
        pmax = datos["100"][-1]
        s_ok = pmax["t_seq"] / pmax["t_par"]
        s_trampa = r1["t_par"] / pmax["t_par"]
        print(f"  S(pmax) honesto = {s_ok:.3f};  con Ts := Tp(1) = {s_trampa:.3f}")

    ruta = os.path.join(d, "suma.csv")
    if os.path.exists(ruta):
        rs = leer(ruta)
        ps = sorted({r["p"] for r in rs})
        pmax = ps[-1]
        print("\n## Parte 2b (suma)")
        r = next(x for x in rs if x["N"] == 16 and x["p"] == pmax)
        print(f"  P2.3: N=16, p={pmax}: S = {r['S']:.4f} -> la versión paralela es {1/r['S']:.1f}x más lenta "
              f"(t_seq={r['t_seq']:.3e}s, t_par={r['t_par']:.3e}s)")
        print("  P2.6: menor N con S > 1 por p:")
        for p in ps:
            ok = [x["N"] for x in sorted(rs, key=lambda x: x["N"]) if x["p"] == p and x["S"] > 1]
            print(f"    p={p}: {ok[0] if ok else 'ninguno (S<=1 en todos los N medidos)'}")
        # modelo: Tp ≈ O + c·N/p ; N* = O / (c·(1-1/p))
        ref = next((x for x in rs if x["N"] == 65536 and x["p"] == pmax), None)
        if ref and pmax > 1:
            c = ref["t_seq"] / ref["N"]
            O = r["t_par"]
            print(f"  Estimación: O ≈ t_par(N=16) = {O:.3e}s, c = {c:.3e}s/elemento "
                  f"-> N* ≈ O/(c(1-1/p)) = {O/(c*(1-1/pmax)):.0f}")
        nmax = max(x["N"] for x in rs)
        r = next(x for x in rs if x["N"] == nmax and x["p"] == pmax)
        print(f"  P2.7: N={nmax}, p={pmax}: S = {r['S']:.3f} (ideal {pmax}), E = {r['E']:.3f}")
        print("\n  Tabla S por N y p:")
        ns = sorted({x["N"] for x in rs})
        print("  N | " + " | ".join(f"p={p}" for p in ps))
        for n in ns:
            vals = []
            for p in ps:
                x = next(y for y in rs if y["N"] == n and y["p"] == p)
                vals.append(f"{x['S']:.3f}")
            print(f"  {n} | " + " | ".join(vals))
    else:
        print(f"!! falta {ruta}")


if __name__ == "__main__":
    main()
