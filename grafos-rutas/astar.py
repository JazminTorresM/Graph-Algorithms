"""A* paso a paso con captura de cada avance (AStar_pasoX.png).

Un paso = un avance: se saca de la lista abierta el nodo con menor f = g + h y se expande.
  paso 0  : estado inicial
  paso k  : k-ésima expansión (la última es la meta y muestra el camino final)

Uso:  python astar.py --inicio 7 --fin 18
"""
import argparse
import heapq
import itertools
import math
from textwrap import fill

import networkx as nx

import estilo as E
import grafo as G

PREFIJO = "AStar"


# ----------------------------------------------------------------------------- heurísticas
def euclidiana(a, b):
    (x1, y1), (x2, y2) = G.COORDS_IMG[a], G.COORDS_IMG[b]
    return math.hypot(x1 - x2, y1 - y2)


def manhattan(a, b):
    (x1, y1), (x2, y2) = G.COORDS_IMG[a], G.COORDS_IMG[b]
    return abs(x1 - x2) + abs(y1 - y2)


HEURISTICAS = {"euclidiana": euclidiana, "manhattan": manhattan}


def escala_admisible(heuristica="euclidiana"):
    """Mayor factor s tal que s*h(u,v) <= peso(u,v) en todas las aristas (h admisible y consistente)."""
    h = HEURISTICAS[heuristica]
    return min(w / h(u, v) for u, v, w in G.ARISTAS)


# ----------------------------------------------------------------------------- búsqueda
def buscar(inicio, fin, h):
    """Generador: produce un estado (dict) por paso. h(n) = heurística hacia 'fin'."""
    M = G.matriz_adyacencia(G.arcos(negativas=False))
    nodos = G.NODOS
    idx = {n: i for i, n in enumerate(nodos)}
    vecinos = {
        n: [(nodos[j], int(M[idx[n], j])) for j in range(len(nodos)) if M[idx[n], j] != math.inf]
        for n in nodos
    }

    g = {inicio: 0}
    padre = {inicio: None}
    abiertos, cerrados = {inicio}, set()
    cont = itertools.count()
    heap = [(h(inicio), h(inicio), next(cont), inicio)]

    def camino_a(n):
        ruta = []
        while n is not None:
            ruta.append(n)
            n = padre[n]
        return ruta[::-1]

    def estado(paso, actual, nuevos, terminado):
        return dict(
            paso=paso, actual=actual, nuevos=list(nuevos), terminado=terminado,
            abiertos={n: (g[n], h(n), g[n] + h(n)) for n in abiertos},
            cerrados=sorted(cerrados), padre=dict(padre), g=dict(g),
            camino=camino_a(actual) if actual is not None else [inicio],
        )

    yield estado(0, None, [], False)
    paso = 0
    while heap:
        f, _, _, u = heapq.heappop(heap)
        if u in cerrados or abs(f - (g[u] + h(u))) > 1e-9:
            continue  # entrada vieja de la cola
        abiertos.discard(u)
        cerrados.add(u)
        paso += 1
        if u == fin:
            yield estado(paso, u, [], True)
            return
        nuevos = []
        for v, w in vecinos[u]:
            ng = g[u] + w
            if v not in g or ng < g[v]:
                g[v], padre[v] = ng, u
                cerrados.discard(v)  # reabrir si se mejora un nodo ya cerrado
                abiertos.add(v)
                heapq.heappush(heap, (ng + h(v), h(v), next(cont), v))
                nuevos.append(v)
        yield estado(paso, u, nuevos, False)
    yield estado(paso + 1, None, [], True)  # sin camino


# ----------------------------------------------------------------------------- dibujo
def _peso(M, idx, u, v):
    return int(M[idx[u], idx[v]])


def dibujar_paso(est, inicio, fin, lineas, M, nombre_h, escala, carpeta):
    idx = {n: i for i, n in enumerate(G.NODOS)}
    paso, actual = est["paso"], est["actual"]
    encontrado = est["terminado"] and actual == fin

    fig = E.nueva_figura()
    E.titulo(fig, f"A*  ·  {inicio} → {fin}",
             f"heurística: {nombre_h} x{escala:g}   |   paso {paso}")
    ax = E.eje_grafo(fig, [0.008, 0.02, 0.725, 0.915])
    info = E.panel(fig, [0.74, 0.02, 0.252, 0.915])

    # estados de nodos y aristas
    en = {}
    for n in est["cerrados"]:
        en[n] = "cerrado"
    for n in est["abiertos"]:
        en[n] = "abierto"
    if actual is not None:
        en[actual] = "actual"
    ea = {}
    if actual is not None:
        for v in est["nuevos"]:
            ea[G.clave_arista(actual, v, _peso(M, idx, actual, v))] = "arbol"
    ruta = est["camino"]
    for a, b in zip(ruta, ruta[1:]):
        ea[G.clave_arista(a, b, _peso(M, idx, a, b))] = "camino" if encontrado else "activa"
    if encontrado:
        for n in ruta:
            en[n] = "camino"

    sub = {n: f"f={f:.0f}" for n, (_, _, f) in est["abiertos"].items()}
    sub.update({n: f"g={est['g'][n]:g}" for n in est["cerrados"] if n != actual})
    if actual is not None:
        sub[actual] = f"g={est['g'][actual]:g}"
    E.dibujar_grafo(ax, lineas, en, ea, sub, inicio, fin)

    # panel de información
    t = E.texto_mono
    t(info, 0.05, 0.975, f"PASO {paso}", E.C["verde"], 18, "bold")
    if actual is None and not est["terminado"]:
        t(info, 0.05, 0.935, f"Inicio: nodo {inicio}\nMeta:   nodo {fin}", E.C["gris_cl"])
        t(info, 0.05, 0.89, "Lista abierta = {" + str(inicio) + "}", E.C["gris_cl"])
    elif actual is None:
        t(info, 0.05, 0.935, "No existe camino.", E.C["blanco"], 12, "bold")
    else:
        gg = est["g"][actual]
        hh = HEURISTICAS[nombre_h](actual, fin) * escala
        ff = gg + hh
        t(info, 0.05, 0.935, ("META alcanzada: nodo " if encontrado else "Expande nodo ") + str(actual),
          E.C["blanco"], 12, "bold")
        t(info, 0.05, 0.905, f"g={gg:g}  h={hh:.1f}  f={ff:.1f}", E.C["gris_cl"])
    t(info, 0.05, 0.865, "Camino: " + " → ".join(map(str, ruta)), E.C["verde"], 10.5)
    if encontrado:
        t(info, 0.05, 0.835, f"Costo total = {est['g'][fin]:g}", E.C["verde"], 12, "bold")

    t(info, 0.05, 0.775, "ABIERTOS (menor f primero)", E.C["morado_cl"], 10.5, "bold")
    t(info, 0.05, 0.752, f"{'nodo':>4} {'g':>6} {'h':>8} {'f':>8}", E.C["tenue"], 10)
    filas = sorted(est["abiertos"].items(), key=lambda kv: (kv[1][2], kv[1][1]))
    y = 0.730
    for n, (gg, hh, ff) in filas[:15]:
        t(info, 0.05, y, f"{n:>4} {gg:>6g} {hh:>8.1f} {ff:>8.1f}", E.C["gris_cl"], 10)
        y -= 0.0215
    if len(filas) > 15:
        t(info, 0.05, y, f"… +{len(filas) - 15} más", E.C["tenue"], 10)
    if not filas:
        t(info, 0.05, y, "(vacía)", E.C["tenue"], 10)

    cer = ", ".join(map(str, est["cerrados"])) or "—"
    t(info, 0.05, 0.37, "CERRADOS", E.C["morado_cl"], 10.5, "bold")
    t(info, 0.05, 0.347, fill(cer, 36), E.C["gris_cl"], 10)

    # leyenda
    y = 0.185
    t(info, 0.05, y + 0.03, "LEYENDA", E.C["morado_cl"], 10.5, "bold")
    for clave, texto in [("actual", "nodo expandido"), ("abierto", "abierto (borde verde)"),
                         ("cerrado", "cerrado"), ("camino", "camino final")]:
        fc, ec, _ = E.NODO[clave]
        info.scatter([0.075], [y - 0.012], s=130, fc=fc, ec=ec, lw=1.6, transform=info.transAxes)
        t(info, 0.12, y - 0.001, texto, E.C["gris_cl"], 10)
        y -= 0.03
    t(info, 0.05, y - 0.005, "◯ continuo: inicio   ◯ discontinuo: meta", E.C["tenue"], 9)

    return E.guardar(fig, carpeta, PREFIJO, paso)


# ----------------------------------------------------------------------------- ejecución
def ejecutar(inicio, fin, carpeta="capturas", heuristica="euclidiana", escala=1.0):
    if inicio not in G.COORDS_IMG or fin not in G.COORDS_IMG:
        raise ValueError(f"Nodos válidos: {G.NODOS}")
    if inicio == fin:
        raise ValueError("El inicio y la meta deben ser distintos.")
    nombre_h = heuristica
    base = HEURISTICAS[heuristica]
    h = lambda n: base(n, fin) * escala

    arcos = G.arcos(negativas=False)
    lineas = G.lineas_dibujo(arcos)
    M = G.matriz_adyacencia(arcos)
    E.limpiar_capturas(carpeta, PREFIJO)

    ultimo = None
    for est in buscar(inicio, fin, h):
        ruta_png = dibujar_paso(est, inicio, fin, lineas, M, nombre_h, escala, carpeta)
        a = est["actual"]
        print(f"[A*] paso {est['paso']:>2}: "
              + ("inicio" if a is None else f"expande {a}")
              + f" | abiertos={len(est['abiertos'])} cerrados={len(est['cerrados'])} -> {ruta_png}")
        ultimo = est

    ok = ultimo["terminado"] and ultimo["actual"] == fin
    camino, costo = (ultimo["camino"], ultimo["g"][fin]) if ok else ([], math.inf)

    # comprobación independiente con networkx (Dijkstra)
    N = nx.Graph()
    for u, v, w in G.ARISTAS:
        if not N.has_edge(u, v) or w < N[u][v]["weight"]:
            N.add_edge(u, v, weight=w)
    optimo = nx.dijkstra_path_length(N, inicio, fin)
    print("\n=== A* ===")
    print("Camino :", " -> ".join(map(str, camino)) if ok else "no existe")
    print("Costo  :", costo, f"(óptimo según networkx/Dijkstra: {optimo})",
          "✔ es óptimo" if costo == optimo else
          "⚠ NO es óptimo: la heurística no es admisible; prueba --escala admisible")
    return dict(camino=camino, costo=costo, optimo=optimo, pasos=ultimo["paso"])


def main():
    ap = argparse.ArgumentParser(description="A* paso a paso con capturas")
    ap.add_argument("-i", "--inicio", type=int, default=7)
    ap.add_argument("-f", "--fin", type=int, default=18)
    ap.add_argument("--heuristica", choices=HEURISTICAS, default="euclidiana")
    ap.add_argument("--escala", default="1",
                    help="factor sobre h (número) o 'admisible' (garantiza camino óptimo)")
    ap.add_argument("--salida", default="capturas")
    a = ap.parse_args()
    escala = escala_admisible(a.heuristica) if a.escala == "admisible" else float(a.escala)
    try:
        ejecutar(a.inicio, a.fin, a.salida, a.heuristica, escala)
    except ValueError as err:
        raise SystemExit(f"Error: {err}")


if __name__ == "__main__":
    main()
