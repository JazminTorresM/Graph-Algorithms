"""Datos del grafo de la clase y estructuras derivadas.

- COORDS_IMG : posición (px) de cada nodo en la imagen de referencia (origen arriba-izquierda).
- ARISTAS    : aristas del grafo original (no dirigidas), usadas por A*.
- NEGATIVAS  : aristas cuyo peso pasa a ser negativo en la versión de Bellman-Ford.
- arcos()    : lista de arcos dirigidos (u, v, w), como la "Lista de Arcos" del profesor.
- matriz_adyacencia() : matriz de adyacencia (numpy) a partir de una lista de arcos.
"""
import numpy as np

ANCHO, ALTO = 1387, 797  # tamaño de la imagen de referencia (px)

COORDS_IMG = {
    0: (872, 97),    1: (872, 351),   2: (1013, 351),  3: (1013, 198),
    4: (482, 625),   5: (1180, 159),  6: (472, 199),   7: (247, 51),
    8: (599, 351),   9: (472, 317),   10: (321, 492),  11: (194, 311),
    12: (721, 512),  13: (833, 755),  14: (317, 318),  15: (697, 199),
    16: (926, 644),  17: (1053, 531), 18: (575, 625),  20: (1330, 243),
    21: (53, 199),   23: (922, 463),  24: (53, 428),   25: (1330, 428),
    27: (297, 648),  29: (53, 51),    44: (1013, 47),  66: (672, 761),
    69: (1180, 351), 70: (1262, 584),
}

NODOS = sorted(COORDS_IMG)

# Posición para dibujar (eje y hacia arriba).
POS = {n: (x, ALTO - y) for n, (x, y) in COORDS_IMG.items()}

# (u, v, peso) — grafo original. 12-16 está duplicada (pesos 3 y 16), como en la imagen.
ARISTAS = [
    (29, 7, 5), (29, 21, 3), (7, 11, 5), (7, 14, 3), (7, 6, 10), (7, 1, 20),
    (21, 11, 2), (21, 24, 2), (24, 11, 7), (11, 14, 9), (11, 10, 7),
    (14, 6, 5), (14, 9, 5), (14, 10, 9), (14, 4, 8),
    (6, 15, 3), (6, 9, 7), (6, 8, 4),
    (15, 0, 8), (15, 8, 2), (15, 1, 8),
    (0, 44, 70), (0, 1, 2), (44, 3, 80), (44, 5, 69),
    (3, 5, 2), (3, 2, 9), (3, 69, 6),
    (5, 20, 2), (5, 69, 3), (20, 69, 3), (20, 25, 7),
    (69, 25, 6), (69, 70, 8), (69, 17, 4), (69, 2, 11), (25, 70, 17),
    (1, 2, 3), (1, 8, 7), (1, 10, 5), (1, 12, 7), (1, 23, 7),
    (2, 23, 3), (2, 17, 5),
    (8, 12, 9), (8, 4, 15),
    (9, 10, 3), (10, 4, 6), (10, 27, 9),
    (27, 4, 3), (27, 66, 1), (4, 18, 5),
    (18, 12, 4), (18, 66, 6),
    (12, 66, 7), (12, 13, 9), (12, 16, 3), (12, 16, 16),
    (23, 16, 11), (17, 16, 7), (17, 70, 6), (16, 13, 3), (66, 13, 777),
]

# Aristas que cambian de signo en la versión de Bellman-Ford: (u, v, nuevo_peso).
# En modo "dirigido" el orden (u, v) indica el único sentido que se conserva (u -> v).
NEGATIVAS = [
    (21, 11, -2), (6, 9, -7), (24, 11, -7), (9, 10, -3),
    (3, 69, -6), (23, 16, -11), (66, 13, -777),
]


# Aristas que forman un ciclo negativo en CUALQUIER sentido en que se oriente, porque existe
# otro camino positivo más corto que su valor absoluto entre sus extremos:
#   3-69  (-6)  : 3-5-69 cuesta 2+3 = 5   ->  -6 + 5 < 0
#   66-13 (-777): 66-18-12-13 cuesta 19   ->  -777 + 19 < 0
CONFLICTIVAS = [(3, 69), (66, 13)]

MODOS = {
    "literal":  "Todas las aristas bidireccionales con el mismo peso (incluidas las negativas). "
                "Toda arista negativa forma un ciclo negativo u->v->u.",
    "dirigido": "Las 7 aristas negativas en un solo sentido (el de NEGATIVAS). "
                "Sigue habiendo ciclo negativo por 3-69 y 66-13.",
    "viable":   "Como 'dirigido', pero 3-69 y 66-13 conservan su peso positivo original. "
                "Sin ciclos negativos: existe camino mínimo.",
}


def arcos(negativas=False, modo="literal", positivas=()):
    """Devuelve la lista de arcos dirigidos (u, v, w).

    negativas : si True usa los pesos de NEGATIVAS (versión Bellman-Ford).
    modo      : "literal" | "dirigido" | "viable" (ver MODOS).
    positivas : pares (u, v) extra que conservan su peso original positivo.
    """
    if modo not in MODOS:
        raise ValueError(f"modo desconocido: {modo!r} (opciones: {', '.join(MODOS)})")
    positivas = {frozenset(p) for p in positivas}
    if modo == "viable":
        positivas |= {frozenset(p) for p in CONFLICTIVAS}
    neg = {frozenset((u, v)): (u, v, w) for u, v, w in NEGATIVAS}
    res = []
    for u, v, w in ARISTAS:
        k = frozenset((u, v))
        if negativas and k in neg and k not in positivas:
            a, b, wn = neg[k]
            res.append((a, b, wn))
            if modo == "literal":
                res.append((b, a, wn))
        else:
            res += [(u, v, w), (v, u, w)]
    return res


def matriz_adyacencia(lista_arcos, nodos=NODOS):
    """Matriz de adyacencia (n x n). inf = sin arco. Con arcos paralelos se conserva el menor peso."""
    idx = {n: i for i, n in enumerate(nodos)}
    M = np.full((len(nodos), len(nodos)), np.inf)
    for u, v, w in lista_arcos:
        i, j = idx[u], idx[v]
        M[i, j] = min(M[i, j], w)
    return M


def lineas_dibujo(lista_arcos):
    """Agrupa arcos en líneas dibujables: dict(u, v, w, dirigida, rad).

    Un par de arcos opuestos con igual peso es una sola línea sin flecha;
    un arco sin su opuesto es una línea con flecha; arcos paralelos se dibujan curvos.
    """
    grupos = {}
    for u, v, w in lista_arcos:
        grupos.setdefault((min(u, v), max(u, v), w), set()).add((u, v))
    lineas, por_par = [], {}
    for (a, b, w), dirs in grupos.items():
        dirigida = len(dirs) == 1
        u, v = next(iter(dirs)) if dirigida else (a, b)
        por_par.setdefault((a, b), []).append(len(lineas))
        lineas.append(dict(u=u, v=v, w=w, dirigida=dirigida, rad=0.0))
    for idxs in por_par.values():
        if len(idxs) > 1:
            for k, i in enumerate(idxs):
                lineas[i]["rad"] = 0.14 if k % 2 == 0 else -0.14
    return lineas


def clave_arista(u, v, w):
    """Clave para resaltar una línea del dibujo."""
    return (min(u, v), max(u, v), w)
