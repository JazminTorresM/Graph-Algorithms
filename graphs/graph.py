"""
graph.py · Datos del grafo del pizarrón y sus matrices
──────────────────────────────────────────────────────
Aquí vive TODO lo que comparten los algoritmos y la interfaz:
  • la lista de aristas y la posición de los nodos
  • la matriz de adyacencia (ADJ) y la matriz de incidencia (INC)
Si cambias un peso o agregas una arista, solo se toca este archivo.
"""
import numpy as np

INF = float("inf")

# ──────────────────────────────────────────────────────────────
#  GRAFO (transcrito del pizarrón). Formato: (u, v, peso[, desplazamiento])
#  El desplazamiento solo separa aristas paralelas; todas las líneas son rectas.
#  Revisa los pesos marcados con "?" contra el pizarrón original.
# ──────────────────────────────────────────────────────────────
EDGES = [
    (29, 7, 5), (29, 21, 3), (21, 24, 2), (21, 11, 2), (24, 11, 7),
    (7, 11, 5), (7, 14, 3), (7, 6, 10), (7, 1, 20),                  # 20 ?
    (11, 14, 9), (11, 10, 7), (14, 6, 5), (14, 9, 5), (14, 10, 9),
    (14, 4, 8), (6, 9, 7), (6, 15, 3), (6, 8, 4), (9, 10, 3),
    (15, 0, 8), (15, 1, 8), (15, 8, 2), (8, 1, 7), (8, 4, 15),
    (8, 12, 9), (10, 4, 6), (10, 27, 9), (10, 1, 5),
    (27, 4, 3), (27, 666, 1), (4, 18, 5), (18, 12, 4),
    (18, 666, 6), (666, 12, 7), (666, 13, 777),
    (12, 13, 9), (12, 16, 3, -0.12), (12, 16, 16, 0.12), (12, 1, 7),
    (13, 16, 3), (16, 17, 7), (16, 23, 11), (23, 1, 7), (23, 2, 3),
    (1, 2, 3), (1, 0, 2), (2, 3, 9), (2, 69, 11), (2, 17, 5),
    (17, 69, 4), (17, 70, 6), (69, 70, 8), (69, 20, 3),
    (69, 25, 6), (69, 5, 3), (69, 3, 6), (3, 5, 2), (3, 44, 80),     # 80 ?
    (0, 44, 70), (44, 5, 69), (5, 20, 2), (20, 25, 7), (25, 70, 17),
]

# Posiciones aproximadas (x, y) en pixeles de la foto del pizarrón
_PX = {
    29: (205, 330), 7: (297, 332), 21: (192, 397), 11: (245, 476),
    24: (190, 518), 14: (323, 481), 6: (417, 382), 9: (413, 476),
    10: (320, 588), 8: (516, 477), 15: (572, 371), 4: (418, 640),
    27: (328, 661), 18: (503, 637), 666: (547, 692), 12: (601, 605),
    13: (683, 686), 16: (800, 635), 1: (705, 471), 23: (736, 527),
    2: (793, 471), 0: (731, 324), 44: (833, 285), 3: (795, 370),
    5: (938, 327), 20: (1054, 397), 69: (943, 466), 25: (1055, 477),
    17: (865, 550), 70: (1026, 556),
}
POS = {n: (x / 100, -y / 100) for n, (x, y) in _PX.items()}
NODES = sorted(POS)                              # nombres de los nodos, ordenados
IDX = {n: i for i, n in enumerate(NODES)}        # nombre -> posición en las matrices


# ──────────────────────────────────────────────────────────────
#  MATRICES
# ──────────────────────────────────────────────────────────────
def build_adjacency():
    """Matriz de adyacencia ponderada (0 = sin arista; con aristas
    paralelas se conserva la de menor peso)."""
    n = len(NODES)
    A = np.zeros((n, n), dtype=int)
    for e in EDGES:
        u, v, w = e[:3]
        i, j = IDX[u], IDX[v]
        if A[i, j] == 0 or w < A[i, j]:
            A[i, j] = A[j, i] = w
    return A


def build_incidence():
    """Matriz de incidencia nodos x aristas (1 si el nodo toca la arista)."""
    B = np.zeros((len(NODES), len(EDGES)), dtype=int)
    for k, e in enumerate(EDGES):
        B[IDX[e[0]], k] = 1
        B[IDX[e[1]], k] = 1
    return B


ADJ = build_adjacency()
INC = build_incidence()
# vecinos precalculados a partir de la matriz de adyacencia
NBR = [[(int(v), int(ADJ[u, v])) for v in np.nonzero(ADJ[u])[0]]
       for u in range(len(NODES))]