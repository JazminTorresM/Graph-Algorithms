"""Menú interactivo: elige algoritmo, nodo de inicio y de fin (a elección del usuario).

    python main.py                       # menú
    python main.py astar -i 7 -f 18      # directo (equivale a python astar.py ...)
    python main.py bellman -i 18 -f 7 --modo viable
"""
import sys

import astar
import bellman_ford
import grafo as G


def pedir_nodo(texto, defecto):
    while True:
        r = input(f"{texto} [{defecto}]: ").strip()
        n = defecto if r == "" else r
        if n.lstrip("-").isdigit() and int(n) in G.COORDS_IMG:
            return int(n)
        print(f"  Nodo inválido. Disponibles: {G.NODOS}")


def pedir_modo():
    claves = list(G.MODOS)
    print("\nAristas negativas en Bellman-Ford:")
    for i, k in enumerate(claves, 1):
        print(f"  {i}) {k}: {G.MODOS[k]}")
    r = input("Modo [1]: ").strip() or "1"
    return claves[int(r) - 1] if r.isdigit() and 1 <= int(r) <= len(claves) else claves[0]


def menu():
    print("Recorrido de grafos\n  1) A*\n  2) Bellman-Ford\n  3) Ambos")
    op = input("Algoritmo [3]: ").strip() or "3"
    i = pedir_nodo("Nodo de inicio", 7)
    f = pedir_nodo("Nodo de fin", 18)
    if op in ("1", "3"):
        astar.ejecutar(i, f)
    if op in ("2", "3"):
        bellman_ford.ejecutar(i, f, pedir_modo())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("astar", "bellman"):
        modulo = astar if sys.argv[1] == "astar" else bellman_ford
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        modulo.main()
    else:
        menu()
