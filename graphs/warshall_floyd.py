"""
warshall_floyd.py · Algoritmo de Warshall-Floyd (sin interfaz)
──────────────────────────────────────────────────────────────
Calcula las distancias mínimas entre TODOS los pares de nodos usando dos
matrices, igual que en el ejemplo del Excel:

    D  (matriz de distancias)  → empieza con los pesos de la matriz de adyacencia
                                  (∞ si no hay arista, "null" en la diagonal)
    P  (matriz de recorridos)  → P[i][j] = j al inicio; cuando pasar por el
                                  pivote k mejora el camino, P[i][j] = k

En la iteración k (pivote = nodo k) para cada par (i, j):
        si  D[i][k] + D[k][j] < D[i][j]   →   D[i][j] = D[i][k] + D[k][j]
                                              P[i][j] = k

Se guarda una "foto" (frame) de ambas matrices en cada iteración, además
del estado inicial. Cada mejora queda registrada en frame["lines"].
"""
import numpy as np

from graph import ADJ, INF, IDX, NODES

NAME = "Warshall-Floyd"
KEY = "floyd"
SUPPORTS_STOP = False     # siempre calcula todos los pares
HAS_MATRICES = True       # main.py mostrará las pestañas Distancias / Recorridos


def initial_matrices():
    """D⁰ y P⁰ a partir de la matriz de adyacencia."""
    n = len(NODES)
    D = np.full((n, n), INF)
    D[ADJ > 0] = ADJ[ADJ > 0]
    np.fill_diagonal(D, 0)
    P = np.tile(np.arange(n), (n, 1))           # P[i][j] = j
    return D, P


def reconstruct(P, D, i, j):
    """Camino i → j (índices de nodos) usando la matriz de recorridos."""
    if D[i, j] == INF:
        return []
    if i == j:
        return [i]
    k = int(P[i, j])
    if k == j:                                   # sin intermedio: arista directa
        return [i, j]
    return reconstruct(P, D, i, k)[:-1] + reconstruct(P, D, k, j)


def solve(src, dst, stop_at_dst=True):
    n = len(NODES)
    s, t = IDX[src], IDX[dst]
    D, P = initial_matrices()
    sym = bool(np.array_equal(D, D.T))           # grafo no dirigido → no duplicar líneas
    frames = []
    tot = {"eval": 0, "imp": 0}

    def count(mask):
        return int(np.triu(mask, 1).sum()) if sym else int(mask.sum())

    def snap(kind, k, msg, changed, lines):
        frames.append(dict(
            kind=kind, k=k, cur=k, edge=None, ok=True, msg=msg,
            visited=set(range(k + 1)) if k is not None else set(),
            dist=[int(x) if x < INF else INF for x in D[s]], prev=None,
            D=D.copy(), P=P.copy(), changed=changed, lines=lines,
            rows=None, band=(k, k) if k is not None else None, fixed=None, mode="floyd",
            evaluated=tot["eval"], improved=tot["imp"]))

    snap("init", None, "Matrices iniciales  (D⁰ distancias · P⁰ recorridos)", frozenset(), [])

    for k in range(n):
        col, row = D[:, k].copy(), D[k, :].copy()
        cand = col[:, None] + row[None, :]       # D[i][k] + D[k][j] para todo (i, j)
        valid = np.isfinite(cand)
        valid[k, :] = valid[:, k] = False
        np.fill_diagonal(valid, False)
        mask = valid & (cand < D)
        tot["eval"] += count(valid)
        tot["imp"] += count(mask)

        lines = []
        for i, j in np.argwhere(mask):
            if sym and i > j:
                continue
            old = "∞" if D[i, j] == INF else int(D[i, j])
            lines.append((f"D[{NODES[i]}][{NODES[j]}]:  {old} → {int(cand[i, j])}"
                          f"   (= {int(col[i])} + {int(row[j])}, vía {NODES[k]})", True))
        D[mask] = cand[mask]
        P[mask] = k
        changed = frozenset((int(i), int(j)) for i, j in np.argwhere(mask))
        snap("iter", k,
             f"Iteración {k + 1}  ·  pivote {NODES[k]}  ·  {count(mask)} mejoras",
             changed, lines)

    path = reconstruct(P, D, s, t)
    total = int(D[s, t]) if D[s, t] < INF else INF
    return frames, path, total


def stats(frames, k, done, path, total):
    n = len(NODES)
    f = frames[max(k, 0)]
    it = (f["k"] + 1) if (k >= 0 and f["k"] is not None) else 0
    ev, imp = (f["evaluated"], f["improved"]) if k >= 0 else (0, 0)
    dist = (str(total) if path else "∞") if done else "…"
    return [("iteración", f"{it}/{n}"),
            ("mejoras", str(imp)),
            ("evaluaciones", str(ev)),
            ("distancia", dist)]