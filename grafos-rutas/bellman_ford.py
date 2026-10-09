"""Bellman-Ford por pasadas, con el formato del profesor (grafo, Lista de Arcos, V/d/Π, Paso).

Un paso = una pasada completa sobre todos los arcos (relajación en el orden de la lista).
  paso 0   : inicialización  d[origen]=0, d[v]=∞, Π[v]=nil
  paso k   : k-ésima pasada (se detiene antes si una pasada no mejora nada)
  último   : verificación de ciclo negativo + camino mínimo (o el ciclo, si existe)

Uso:  python bellman_ford.py --inicio 7 --fin 18 --modo viable
"""
import argparse
import math
from textwrap import fill

import networkx as nx
from matplotlib.patches import Rectangle

import estilo as E
import grafo as G

PREFIJO = "BellmanFord"
INF = math.inf


# ----------------------------------------------------------------------------- algoritmo
def hallar_ciclo(arcos, d, pi, n):
    """Pasada extra sobre copias; si algún arco aún relaja, devuelve el ciclo negativo [a, b, ..., a]."""
    d2, pi2, x = dict(d), dict(pi), None
    for u, v, w in arcos:
        if d2[u] != INF and d2[u] + w < d2[v]:
            d2[v], pi2[v], x = d2[u] + w, u, v
    if x is None:
        return None
    for _ in range(n):  # retroceder n veces garantiza estar dentro del ciclo
        if pi2[x] is None:
            return None
        x = pi2[x]
    ciclo, y = [x], pi2[x]
    while y != x:
        ciclo.append(y)
        y = pi2[y]
    ciclo.append(x)
    return ciclo[::-1]


def correr(arcos, nodos, origen, parar_si_converge=True):
    """Generador: un estado por paso (inicio, pasadas, final)."""
    d = {n: INF for n in nodos}
    pi = {n: None for n in nodos}
    pw = {n: None for n in nodos}  # peso del arco usado para llegar a n
    d[origen] = 0

    def snap(tipo, paso, cambios, **extra):
        return dict(tipo=tipo, paso=paso, d=dict(d), pi=dict(pi), pw=dict(pw),
                    cambios=cambios, **extra)

    yield snap("inicio", 0, [])
    ultima, convergio = 0, False
    for k in range(1, len(nodos)):
        cambios = []
        for u, v, w in arcos:
            if d[u] != INF and d[u] + w < d[v]:
                cambios.append((u, v, w, d[v], d[u] + w))
                d[v], pi[v], pw[v] = d[u] + w, u, w
        ultima = k
        yield snap("pasada", k, cambios)
        if not cambios and parar_si_converge:
            convergio = True
            break
    yield snap("final", ultima + 1, [], ciclo=hallar_ciclo(arcos, d, pi, len(nodos)),
               convergio=convergio)


def camino_hasta(pi, destino):
    ruta, n = [], destino
    while n is not None:
        ruta.append(n)
        n = pi[n]
    return ruta[::-1]


# ----------------------------------------------------------------------------- dibujo
def _fmt(x):
    return "∞" if x == INF else str(x)


def tabla(ax, nodos, est, cambiados, origen):
    """Tablas V / d / Π (dos bloques de 15 columnas)."""
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    for b, grupo in enumerate([nodos[:15], nodos[15:]]):
        ytop = 7 if b == 0 else 3
        for r, nombre in enumerate(["V", "d", "Π"]):
            y = ytop - 1 - r
            ax.add_patch(Rectangle((0, y), 1, 1, fc=E.C["morado_osc"], ec=E.C["borde"], lw=1))
            ax.text(0.5, y + 0.5, nombre, ha="center", va="center", color=E.C["verde"],
                    fontsize=13, fontweight="bold", family="DejaVu Sans Mono")
            for c, n in enumerate(grupo, start=1):
                ch = n in cambiados and r > 0
                ax.add_patch(Rectangle((c, y), 1, 1, fc=E.C["verde"] if ch else E.C["panel"],
                                       ec=E.C["borde"], lw=1))
                val = (str(n) if r == 0 else _fmt(est["d"][n]) if r == 1
                       else "nil" if est["pi"][n] is None else str(est["pi"][n]))
                col = E.C["fondo"] if ch else (E.C["blanco"] if n == origen and r == 0 else E.C["gris_cl"])
                ax.text(c + 0.5, y + 0.5, val, ha="center", va="center", color=col,
                        fontsize=10.5 if len(val) < 6 else 8.5, family="DejaVu Sans Mono",
                        fontweight="bold" if r == 0 else "normal")


def lista_arcos(ax, arcos, est):
    t = E.texto_mono
    n_arcos = len(arcos)
    if est["tipo"] == "inicio":
        t(ax, 0.5, 0.975, f"Lista de Arcos  ({n_arcos})", E.C["verde"], 13, "bold", ha="center")
        filas = 31
        ncols = -(-n_arcos // filas)
        ancho = 0.94 / ncols
        for i, (u, v, w) in enumerate(arcos):
            c, f = divmod(i, filas)
            t(ax, 0.03 + c * ancho, 0.93 - f * 0.0285, f"({u},{v}) {w}",
              E.C["verde"] if w < 0 else E.C["gris_cl"], 8.5 if ncols > 3 else 9.5)
        return
    if est["tipo"] == "pasada":
        t(ax, 0.5, 0.975, "Arcos que mejoraron", E.C["verde"], 13, "bold", ha="center")
        t(ax, 0.5, 0.94, f"{len(est['cambios'])} de {n_arcos} en esta pasada", E.C["tenue"], 10,
          ha="center")
        filas = 31
        for i, (u, v, w, viejo, nuevo) in enumerate(est["cambios"][:filas]):
            t(ax, 0.03, 0.90 - i * 0.0275, f"({u},{v}) {w:>4}  d[{v}]: {_fmt(viejo)}→{nuevo}",
              E.C["gris_cl"], 9)
        if len(est["cambios"]) > filas:
            t(ax, 0.03, 0.90 - filas * 0.0275, f"… +{len(est['cambios']) - filas} más", E.C["tenue"], 9)
        if not est["cambios"]:
            t(ax, 0.03, 0.90, "(ninguno)", E.C["tenue"], 10)
        return
    # final
    t(ax, 0.5, 0.975, "Verificación", E.C["verde"], 13, "bold", ha="center")
    if est["ciclo"]:
        t(ax, 0.03, 0.93, "Arcos del ciclo negativo:", E.C["blanco"], 10, "bold")
        c = est["ciclo"]
        peso = _peso_ciclo(arcos, c)
        for i, (a, b) in enumerate(zip(c, c[1:])):
            w = min(w for x, y, w in arcos if (x, y) == (a, b))
            t(ax, 0.03, 0.895 - i * 0.0275, f"({a},{b})  {w}", E.C["gris_cl"], 9.5)
        t(ax, 0.03, 0.895 - len(c) * 0.0275 - 0.01, f"Peso total = {peso}", E.C["verde"], 10.5, "bold")
    else:
        t(ax, 0.03, 0.93, "Ningún arco puede\nrelajarse más:\nno hay ciclo negativo.", E.C["gris_cl"], 10.5)


def _peso_ciclo(arcos, ciclo):
    return sum(min(w for x, y, w in arcos if (x, y) == (a, b)) for a, b in zip(ciclo, ciclo[1:]))


def descripcion(est, arcos, origen, destino, nodos):
    V, A = len(nodos), len(arcos)
    if est["tipo"] == "inicio":
        return (f"Encontrar el camino más corto del vértice {origen} a cada uno de los otros "
                f"vértices.\n\nInicialización: d[{origen}] = 0, d[v] = ∞, Π[v] = nil.\n"
                f"Cada pasada recorre los {A} arcos en orden de la lista (máx. {V - 1} pasadas).")
    if est["tipo"] == "pasada":
        m = len(est["cambios"])
        s = (f"Pasada {est['paso']} de {V - 1}: se relajan los {A} arcos de la lista.\n\n"
             f"{m} arcos mejoraron d[v]; esos nodos están en verde.")
        if m == 0:
            s += "\n\nNingún arco mejora: el algoritmo convergió, se omiten las pasadas restantes."
        return s
    if est["ciclo"]:
        c = est["ciclo"]
        return ("Verificación: un arco todavía puede relajarse tras V−1 pasadas.\n\n"
                f"CICLO NEGATIVO alcanzable desde {origen}:\n  " + " → ".join(map(str, c)) +
                f"\npeso total = {_peso_ciclo(arcos, c)}.\n\n"
                "No existe camino mínimo: d[v] baja sin límite al recorrer el ciclo.")
    if est["d"][destino] == INF:
        return f"Verificación: sin ciclos negativos.\n\nEl vértice {destino} es inalcanzable desde {origen}."
    ruta = camino_hasta(est["pi"], destino)
    return ("Verificación: ningún arco puede relajarse más → no hay ciclo negativo.\n\n"
            f"Camino mínimo {origen} → {destino}:\n" + fill(" → ".join(map(str, ruta)), 60) +
            f"\n\nCosto = d[{destino}] = {est['d'][destino]}")


def dibujar_paso(est, arcos, lineas, nodos, origen, destino, modo, carpeta):
    fig = E.nueva_figura()
    titulo_der = f"modo: {modo}   |   paso {est['paso']}"
    E.titulo(fig, f"Bellman-Ford  ·  {origen} → {destino}", titulo_der)
    ax = E.eje_grafo(fig, [0.008, 0.285, 0.735, 0.65])
    lst = E.panel(fig, [0.75, 0.285, 0.242, 0.65])
    tab = E.panel(fig, [0.008, 0.015, 0.62, 0.255])
    box = E.panel(fig, [0.635, 0.015, 0.357, 0.255])

    cambiados = {c[1] for c in est["cambios"]}
    en = {n: "alcanzado" for n in nodos if est["d"][n] != INF}
    for n in cambiados:
        en[n] = "cambio"
    ea = {}
    for v in nodos:
        if est["pi"][v] is not None:
            ea[G.clave_arista(est["pi"][v], v, est["pw"][v])] = "arbol"
    for v in cambiados:
        ea[G.clave_arista(est["pi"][v], v, est["pw"][v])] = "activa"
    if est["tipo"] == "final":
        if est["ciclo"]:
            c = est["ciclo"]
            for n in c:
                en[n] = "ciclo"
            for a, b in zip(c, c[1:]):
                w = min(w for x, y, w in arcos if (x, y) == (a, b))
                ea[G.clave_arista(a, b, w)] = "ciclo"
        elif est["d"][destino] != INF:
            ruta = camino_hasta(est["pi"], destino)
            for n in ruta:
                en[n] = "camino"
            for a, b in zip(ruta, ruta[1:]):
                ea[G.clave_arista(a, b, est["pw"][b])] = "camino"
    sub = {n: _fmt(est["d"][n]) for n in nodos if est["d"][n] != INF}
    E.dibujar_grafo(ax, lineas, en, ea, sub, origen, destino, fs_nodo=9.5)

    tabla(tab, nodos, est, cambiados, origen)
    lista_arcos(lst, arcos, est)

    box.text(0.03, 0.93, f"Paso {est['paso']}", transform=box.transAxes, va="top", ha="left",
             fontsize=19, fontweight="bold", color=E.C["verde"], family="DejaVu Sans Mono",
             bbox=dict(boxstyle="square,pad=0.35", fc=E.C["panel"], ec=E.C["blanco"], lw=1.6))
    texto = descripcion(est, arcos, origen, destino, nodos)
    E.texto_mono(box, 0.03, 0.70, "\n".join(fill(p, 62) if p else "" for p in texto.split("\n")),
                 E.C["gris_cl"], 10.5)
    return E.guardar(fig, carpeta, PREFIJO, est["paso"])


# ----------------------------------------------------------------------------- ejecución
def ejecutar(origen, destino, modo="literal", positivas=(), carpeta="capturas",
             parar_si_converge=True):
    if origen not in G.COORDS_IMG or destino not in G.COORDS_IMG:
        raise ValueError(f"Nodos válidos: {G.NODOS}")
    if origen == destino:
        raise ValueError("El inicio y el destino deben ser distintos.")
    nodos = G.NODOS
    arcos = G.arcos(negativas=True, modo=modo, positivas=positivas)
    lineas = G.lineas_dibujo(arcos)
    E.limpiar_capturas(carpeta, PREFIJO)

    ultimo = None
    for est in correr(arcos, nodos, origen, parar_si_converge):
        ruta_png = dibujar_paso(est, arcos, lineas, nodos, origen, destino, modo, carpeta)
        extra = f" | mejoras={len(est['cambios'])}" if est["tipo"] == "pasada" else ""
        print(f"[BF] paso {est['paso']:>2} ({est['tipo']}){extra} -> {ruta_png}")
        ultimo = est

    ciclo = ultimo["ciclo"]
    print("\n=== Bellman-Ford ===")
    if ciclo:
        print("CICLO NEGATIVO:", " -> ".join(map(str, ciclo)), "| peso", _peso_ciclo(arcos, ciclo))
        print("No existe camino mínimo. Prueba --modo viable para obtener un camino finito.")
    elif ultimo["d"][destino] == INF:
        print(f"El nodo {destino} es inalcanzable desde {origen}.")
    else:
        print("Camino :", " -> ".join(map(str, camino_hasta(ultimo["pi"], destino))))
        print("Costo  :", ultimo["d"][destino])

    # comprobación independiente con networkx
    D = nx.MultiDiGraph()
    D.add_nodes_from(nodos)
    D.add_weighted_edges_from(arcos)
    try:
        ref = nx.single_source_bellman_ford_path_length(D, origen)
        ok = (not ciclo) and all(ref.get(n, INF) == ultimo["d"][n] for n in nodos)
    except nx.NetworkXUnbounded:
        ok = bool(ciclo)
    print("Comprobación con networkx:", "✔ coincide" if ok else "⚠ NO coincide (revisar)")
    return dict(ciclo=ciclo, d=ultimo["d"], pi=ultimo["pi"], pasos=ultimo["paso"], coincide=ok)


def main():
    ap = argparse.ArgumentParser(description="Bellman-Ford por pasadas con capturas")
    ap.add_argument("-i", "--inicio", type=int, default=7)
    ap.add_argument("-f", "--fin", type=int, default=18)
    ap.add_argument("--modo", choices=list(G.MODOS), default="literal",
                    help="; ".join(f"{k}: {v}" for k, v in G.MODOS.items()))
    ap.add_argument("--positiva", nargs="*", default=[], metavar="U-V",
                    help="aristas que conservan su peso positivo original, p. ej. 3-69 66-13")
    ap.add_argument("--completo", action="store_true",
                    help="hacer siempre las V-1 pasadas (sin parar al converger)")
    ap.add_argument("--salida", default="capturas")
    a = ap.parse_args()
    pos = [tuple(map(int, p.split("-"))) for p in a.positiva]
    try:
        ejecutar(a.inicio, a.fin, a.modo, pos, a.salida, not a.completo)
    except ValueError as err:
        raise SystemExit(f"Error: {err}")


if __name__ == "__main__":
    main()
