"""Menú interactivo: elige algoritmo, nodo de inicio y de fin (a elección del usuario).

    python main.py                       # menú
    python main.py astar -i 7 -f 18      # directo (equivale a python astar.py ...)
    python main.py bellman -i 18 -f 7
"""
import sys

import astar
import bellman_ford
import grafo as G


def pedir_nodo(texto, defecto, validos):
    while True:
        r = input(f"{texto} [{defecto}]: ").strip()
        n = defecto if r == "" else r
        if n.lstrip("-").isdigit() and int(n) in validos:
            return int(n)
        print(f"  Nodo inválido. Disponibles: {validos}")


def menu():
    print("Recorrido de grafos\n  1) A*\n  2) Bellman-Ford\n  3) Ambos")
    op = input("Algoritmo [3]: ").strip() or "3"
    # A* usa el grafo original (nodo 66); Bellman-Ford, el grafo dirigido de la imagen (nodo 666)
    validos = {"1": G.NODOS, "2": G.grafo_bf()["nodos"]}.get(
        op, sorted(set(G.NODOS) & set(G.grafo_bf()["nodos"])))
    i = pedir_nodo("Nodo de inicio", 7, validos)
    f = pedir_nodo("Nodo de fin", 18, validos)
    if op in ("1", "3"):
        astar.ejecutar(i, f)
    if op in ("2", "3"):
        print("\nBellman-Ford: capturas a generar\n"
              "  1) una por cada arco revisado (317 para 7 → 18; ~2 min, ~105 MB)\n"
              "  2) solo cuando un arco mejora una distancia (38)")
        solo = (input("Opción [1]: ").strip() or "1") == "2"
        bellman_ford.ejecutar(i, f, solo_mejoras=solo)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("astar", "bellman"):
        modulo = astar if sys.argv[1] == "astar" else bellman_ford
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        modulo.main()
    else:
        menu()
