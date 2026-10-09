# Recorrido de grafos: A* y Bellman-Ford

Recorre el grafo de la clase paso a paso y guarda una imagen (1920×1080 PNG) por cada paso.

## Uso

```bash
pip install -r requirements.txt

python main.py                                  # menú: algoritmo, inicio y fin (por defecto 7 → 18)
python astar.py -i 7 -f 18                      # solo A*
python bellman_ford.py -i 7 -f 18 --modo viable # solo Bellman-Ford
```

Las capturas quedan en `capturas/`: `AStar_paso0.png`, `AStar_paso1.png`, … y
`BellmanFord_paso0.png`, `BellmanFord_paso1.png`, … (cada corrida borra las anteriores del mismo algoritmo).
Inicio y fin son intercambiables (`-i 18 -f 7`).

## Qué es un paso

| Algoritmo | Paso |
|---|---|
| A* | `paso0` = estado inicial; cada paso siguiente = una expansión (nodo con menor f = g + h). El último paso es la meta con el camino marcado. |
| Bellman-Ford | `paso0` = inicialización; cada paso = una pasada completa sobre todos los arcos. El último paso = verificación de ciclo negativo + camino mínimo (o el ciclo). |

Bellman-Ford sigue el formato del profesor: grafo, *Lista de Arcos*, tablas V / d / Π y recuadro «Paso».
Se detiene antes si una pasada no mejora nada; `--completo` fuerza las V−1 pasadas.

## Aristas negativas en Bellman-Ford (importante)

Con aristas bidireccionales y el mismo peso de ida y vuelta, **toda arista negativa es un ciclo negativo** (u→v→u).
Además, 3-69 (−6) y 66-13 (−777) forman ciclo negativo en cualquier sentido, porque hay un camino positivo más
corto entre sus extremos (3-5-69 cuesta 5; 66-18-12-13 cuesta 19). Por eso hay tres modos (`--modo`):

| Modo | Qué hace | Resultado 7 → 18 |
|---|---|---|
| `literal` (por defecto) | Todo bidireccional, mismo peso | Detecta ciclo negativo 66↔13 |
| `dirigido` | Las 7 negativas en un solo sentido | Detecta ciclo negativo 13→12→66→13 |
| `viable` | Como `dirigido`, pero 3-69 y 66-13 conservan su peso positivo | Camino 7→14→6→9→10→1→2→23→16→12→18, costo 5 |

El sentido de cada arista negativa se define en `NEGATIVAS` (`grafo.py`): `(u, v, peso)` = solo `u → v`.
Cada corrida se comprueba contra `networkx` y lo imprime.

## Heurística de A*

Distancia euclidiana entre las posiciones de los nodos en la imagen (`COORDS_IMG` en `grafo.py`).
Los pesos del grafo no son proporcionales a esas distancias, así que la heurística **no es admisible** y A* no
siempre da el camino óptimo (para 7↔18 sí; en todos los pares de nodos, ~42 %). El programa lo avisa al final
comparando con Dijkstra. Opciones: `--heuristica manhattan`, `--escala admisible` (siempre óptimo, pero h ≈ 0).

## Archivos

| Archivo | Contenido |
|---|---|
| `grafo.py` | Coordenadas, aristas, negativas, lista de arcos, matriz de adyacencia (numpy) |
| `estilo.py` | Paleta EVA-01 y dibujo del grafo (matplotlib, sin ventanas) |
| `astar.py` | A* paso a paso (vecinos desde la matriz de adyacencia) |
| `bellman_ford.py` | Bellman-Ford por pasadas (lista de arcos) |
| `main.py` | Menú interactivo |

Pesos transcritos de la imagen del grafo; si alguno no coincide con el de la clase, corrígelo en `ARISTAS` / `NEGATIVAS`.
