"""
dijkstra.py · Algoritmo de Dijkstra (sin interfaz)
──────────────────────────────────────────────────
Trabaja sobre la matriz de adyacencia (a través de NBR) y registra TODOS
los pasos: cada nodo que se visita y cada arista que se evalúa.

Contrato que main.py espera de cualquier algoritmo:
    NAME, KEY, SUPPORTS_STOP, HAS_MATRICES
    solve(src, dst, stop_at_dst) -> (frames, path, total)
    stats(frames, k, done, path, total) -> [(etiqueta, valor), ...]
"""
import heapq

from graph import INF, IDX, NBR, NODES

NAME = "Dijkstra"
KEY = "dijkstra"
SUPPORTS_STOP = True      # tiene sentido "detener al llegar al destino"
HAS_MATRICES = False      # no genera matrices intermedias propias


def solve(src, dst, stop_at_dst=True):
    n = len(NODES)
    s, t = IDX[src], IDX[dst]
    dist = [INF] * n
    prev = [None] * n
    dist[s] = 0
    done = set()
    heap = [(0, s)]
    frames = []

    def snap(kind, cur, edge=None, msg="", ok=None):
        frames.append(dict(kind=kind, cur=cur, edge=edge, msg=msg, ok=ok,
                           visited=set(done), dist=list(dist), prev=list(prev)))

    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
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

    path = []
    if dist[t] < INF:
        c = t
        while c is not None:
            path.append(c)
            c = prev[c]
        path.reverse()
    return frames, path, dist[t]


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