"""Datos del grafo de la clase y estructuras derivadas.

- COORDS_IMG : posición (px) de cada nodo en la imagen de referencia (origen arriba-izquierda).
- ARISTAS    : aristas del grafo original (no dirigidas), usadas por A*.
- NEGATIVAS  : aristas dirigidas con peso negativo en la versión de Bellman-Ford.
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

# Aristas negativas de la versión de Bellman-Ford: (u, v, nuevo_peso), solo en el sentido u -> v.
# 3-69 (-6) y 66-13 (-777) NO se incluyen: forman un ciclo negativo en cualquier sentido, porque
# hay un camino positivo más corto entre sus extremos (3-5-69 cuesta 5; 66-18-12-13 cuesta 19).
# Conservan su peso positivo original y son bidireccionales, como el resto.
NEGATIVAS = [
    (21, 11, -2), (6, 9, -7), (24, 11, -7), (9, 10, -3), (23, 16, -11),
]


def arcos(negativas=False):
    """Devuelve la lista de arcos dirigidos (u, v, w).

    Cada arista es bidireccional con el mismo peso (ida y vuelta). Con negativas=True
    (Bellman-Ford) las aristas de NEGATIVAS se conservan solo en el sentido u -> v.
    """
    neg = {frozenset((u, v)): (u, v, w) for u, v, w in NEGATIVAS}
    res = []
    for u, v, w in ARISTAS:
        k = frozenset((u, v))
        if negativas and k in neg:
            res.append(neg[k])
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


# ------------------------------------------------------------------ grafo dirigido para Bellman-Ford
# Transcrito de la imagen "Bellman-Ford · Grafo dirigido con pesos negativos": cada arista tiene un solo
# sentido. Es el mismo grafo con otras direcciones y pesos negativos (11→21 -2, 11→24 -7, 6→9 -7, 9→10 -3,
# 5→20 -2, 3→69 -6, 23→16 -11, 666→13 -777). En esa imagen el nodo 66 se llama 666.
ARCOS_DIRIGIDO = [
    (29, 7, 5), (21, 29, 3), (24, 21, 2), (11, 21, -2), (11, 24, -7), (7, 11, 5), (7, 14, 3),
    (6, 7, 10), (1, 7, 20), (6, 14, 5), (6, 9, -7), (9, 14, 5), (9, 10, -3), (6, 8, 4),
    (15, 6, 3), (15, 8, 2), (15, 1, 8), (0, 15, 8), (0, 44, 70), (1, 0, 2), (44, 3, 80),
    (44, 5, 69), (3, 5, 2), (5, 20, -2), (3, 69, -6), (2, 3, 9), (69, 5, 3), (69, 20, 3),
    (20, 25, 7), (69, 25, 6), (70, 69, 8), (25, 70, 17), (17, 70, 6), (17, 69, 4), (17, 2, 5),
    (2, 69, 11), (1, 2, 3), (23, 2, 3), (1, 23, 7), (1, 12, 7), (8, 12, 9), (4, 8, 15),
    (14, 4, 8), (10, 14, 9), (10, 11, 7), (11, 14, 9), (10, 4, 6), (10, 27, 9), (27, 4, 3),
    (27, 666, 1), (4, 18, 5), (18, 12, 4), (18, 666, 6), (666, 12, 7), (13, 12, 9),
    (666, 13, -777), (13, 16, 3), (12, 16, 3), (12, 16, 16), (23, 16, -11), (16, 17, 7),
    (10, 1, 5), (1, 8, 7),
]
COORDS_DIRIGIDO = {(666 if n == 66 else n): xy for n, xy in COORDS_IMG.items()}

GRAFOS_BF = {
    "dirigido": "Grafo dirigido de la imagen (63 arcos, nodo 666).",
    "base": "Grafo original bidireccional + 5 aristas negativas dirigidas (sin 3-69 ni 66-13).",
}


def pos_de(coords):
    """Posiciones para dibujar (eje y hacia arriba) a partir de coordenadas de imagen."""
    return {n: (x, ALTO - y) for n, (x, y) in coords.items()}


def grafo_bf(nombre="dirigido"):
    """Datos del grafo para Bellman-Ford: dict(arcos, coords, nodos, pos)."""
    if nombre == "dirigido":
        coords, lista = COORDS_DIRIGIDO, sorted(ARCOS_DIRIGIDO)
    elif nombre == "base":
        coords, lista = COORDS_IMG, arcos(negativas=True)
    else:
        raise ValueError(f"grafo desconocido: {nombre!r} (opciones: {', '.join(GRAFOS_BF)})")
    return dict(arcos=lista, coords=coords, nodos=sorted(coords), pos=pos_de(coords))
