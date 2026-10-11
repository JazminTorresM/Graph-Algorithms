"""
dijkstra.py · Algoritmo de Dijkstra (sin interfaz)
──────────────────────────────────────────────────
Trabaja sobre la matriz de adyacencia (a través de NBR) y registra TODOS
los pasos: cada nodo que se visita y cada arista que se evalúa.

Además arma dos tablas (matrices) con una fila por iteración, como en la
tabla clásica de Dijkstra hecha a mano:
    D  (distancias)   D[it][v] = mejor distancia conocida al nodo v tras la iteración it
    P  (recorridos)   P[it][v] = nodo anterior a v en el mejor camino conocido (-1 = ninguno)
La iteración it es la visita del it-ésimo nodo; las filas futuras quedan en blanco (NaN).

Contrato que main.py espera de cualquier algoritmo:
    NAME, KEY, SUPPORTS_STOP, HAS_MATRICES
    solve(src, dst, stop_at_dst) -> (frames, path, total)
    stats(frames, k, done, path, total) -> [(etiqueta, valor), ...]
"""
import heapq

import numpy as np

from graph import INF, IDX, NBR, NODES

NAME = "Dijkstra"
KEY = "dijkstra"
SUPPORTS_STOP = True      # tiene sentido "detener al llegar al destino"
HAS_MATRICES = True       # main.py mostrará las pestañas Distancias / Recorridos


def solve(src, dst, stop_at_dst=True):
    n = len(NODES)
    s, t = IDX[src], IDX[dst]
    dist = [INF] * n
    prev = [None] * n
    dist[s] = 0
    done = set()
    heap = [(0, s)]
    frames = []
    it = -1                                   # iteración actual (una por nodo visitado)

    def snap(kind, cur, edge=None, msg="", ok=None):
        frames.append(dict(kind=kind, cur=cur, edge=edge, msg=msg, ok=ok, it=it,
                           visited=set(done), dist=list(dist), prev=list(prev)))

    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        it += 1
        snap("visit", u, msg=f"Visita {NODES[u]}  ·  d = {d}")
        if u == t and stop_at_dst:
            break
        for v, w in NBR[u]:
            if v in done:
                continue
            nd = d + w
            if nd < dist[v]:
                old = "∞" if dist[v] == INF else dist[v]
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
                snap("relax", u, (u, v),
                     f"{NODES[u]} → {NODES[v]}   +{w}   {old} → {nd}  ✓", True)
            else:
                snap("relax", u, (u, v),
                     f"{NODES[u]} → {NODES[v]}   +{w}   {nd} ≥ {dist[v]}  ✕", False)

    _attach_tables(frames, n)

    path = []
    if dist[t] < INF:
        c = t
        while c is not None:
            path.append(c)
            c = prev[c]
        path.reverse()
    return frames, path, dist[t]


def _attach_tables(frames, n):
    """Agrega a cada frame las tablas D y P (una fila por iteración) para la interfaz."""
    order = [f["cur"] for f in frames if f["kind"] == "visit"]
    n_it = len(order)
    last_of = {f["it"]: i for i, f in enumerate(frames)}     # último frame de cada iteración
    fixed = [INF] * n                                          # iteración en que cada nodo queda definitivo
    for r, u in enumerate(order):
        fixed[u] = r
    rows = [f"{r + 1} · {NODES[u]}" for r, u in enumerate(order)]

    def dvec(dist):
        return np.array(dist, dtype=float)

    def pvec(prev):
        return np.array([-1 if p is None else p for p in prev], dtype=float)

    final_d = [dvec(frames[last_of[r]]["dist"]) for r in range(n_it)]
    final_p = [pvec(frames[last_of[r]]["prev"]) for r in range(n_it)]
    for f in frames:
        it = f["it"]
        D = np.full((n_it, n), np.nan)
        P = np.full((n_it, n), np.nan)
        for r in range(it):
            D[r], P[r] = final_d[r], final_p[r]
        D[it], P[it] = dvec(f["dist"]), pvec(f["prev"])
        # celdas que cambiaron respecto a la fila anterior (en todas las filas ya mostradas)
        changed = frozenset((r, v) for r in range(it + 1) for v in range(n)
                            if D[r, v] != (D[r - 1, v] if r > 0 else INF))
        f.update(D=D, P=P, rows=rows, band=(it, f["cur"]), changed=changed,
                 fixed=fixed, mode="steps")


def stats(frames, k, done, path, total):
    """Los cuatro números que se muestran arriba a la derecha del grafo."""
    n = len(frames)
    all_vis = sum(1 for f in frames if f["kind"] == "visit")
    vis = sum(1 for f in frames[:k + 1] if f["kind"] == "visit")
    rel = k + 1 - vis
    dist = (str(total) if path else "∞") if done else "…"
    return [("paso", f"{k + 1}/{n}"),
            ("nodos visitados", f"{vis}/{all_vis}"),
            ("aristas evaluadas", f"{rel}/{n - all_vis}"),
            ("distancia", dist)]