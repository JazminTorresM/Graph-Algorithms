# Recorrido de grafos: A* y Bellman-Ford

Recorre el grafo de la clase paso a paso y guarda una imagen (1920×1080 PNG) por cada paso.

## Uso

Requiere Python 3.8+. En Windows usa `py` en lugar de `python` si el comando no se reconoce.

```bash
pip install -r requirements.txt

python main.py                    # menú: algoritmo, inicio y fin (por defecto 7 → 18)
python astar.py -i 7 -f 18        # solo A*
python bellman_ford.py -i 7 -f 18 # solo Bellman-Ford
```

Las capturas quedan en `capturas/`: `AStar_paso0.png`, `AStar_paso1.png`, … y
`BellmanFord_paso0.png`, `BellmanFord_paso1.png`, … (cada corrida borra las anteriores del mismo algoritmo).
Inicio y fin son intercambiables (`-i 18 -f 7`).

## Qué es un paso

| Algoritmo | Paso |
|---|---|
| A* | `paso0` = estado inicial; cada paso siguiente = una expansión (nodo con menor f = g + h). El último paso es la meta con el camino marcado. |
| Bellman-Ford | `paso0` = inicialización; cada paso siguiente = **un arco revisado** (relajación), en el orden de la Lista de Arcos; la imagen lo rotula «Paso i.j» (pasada i, arco j). El último paso = verificación de ciclo negativo + camino mínimo. |

Bellman-Ford sigue el formato del profesor: grafo, *Lista de Arcos* (arco actual resaltado; verde = mejoró,
gris = sin mejora, tenue = pendiente), tablas V / d / Π y recuadro «Paso i.j» con la cuenta d[u] + w < d[v].
El nombre del archivo es el número de captura (`BellmanFord_paso130.png` puede ser «Paso 2.9»).

Para 7 → 18 (grafo `dirigido`) son **317 capturas** (~105 MB, ~100 s con 2 núcleos; usa varios procesos en paralelo).
Opciones de `bellman_ford.py`:

| Opción | Efecto |
|---|---|
| `--solo-mejoras` | Solo los arcos que mejoran d[v] (38 capturas) |
| `--detalle pasada` | Una captura por pasada completa (7 capturas) |
| `--completo` | Hace siempre las V−1 pasadas (por defecto se detiene al converger) |
| `--procesos N` | Procesos en paralelo (`1` = sin paralelo) |
| `--grafo base` | Usa el grafo original con 5 negativas en lugar del dirigido |

`capturas/` está en `.gitignore`: no se sube al repo.

## Grafo de Bellman-Ford (`--grafo`)

| Valor | Grafo |
|---|---|
| `dirigido` (por defecto) | Imagen «Bellman-Ford · Grafo dirigido con pesos negativos»: 63 arcos, cada arista con un solo sentido. Negativos: 11→21 (−2), 11→24 (−7), 6→9 (−7), 9→10 (−3), 5→20 (−2), 3→69 (−6), 23→16 (−11), 666→13 (−777). En esa imagen el nodo 66 se llama **666**. |
| `base` | Grafo original bidireccional + 5 negativas dirigidas (21→11, 6→9, 24→11, 9→10, 23→16); 3-69 y 66-13 conservan su peso positivo. |

Los arcos están en `ARCOS_DIRIGIDO` (`grafo.py`); para renombrar 666 a 66 basta cambiarlo ahí.
Con aristas bidireccionales del mismo peso toda arista negativa sería un ciclo negativo (u→v→u), por eso se usan grafos dirigidos.

Grafo `dirigido`, 7 → 18: **no hay ciclo negativo** (ni siquiera con −777: 13 no puede volver a 666).
Camino 7→14→4→18, costo 16. Solo se alcanzan 21 de los 30 nodos desde 7 (0, 1, 6, 9, 10, 15, 23, 27 y 44 quedan en ∞),
así que 6→9, 9→10 y 23→16 no se usan. Con otro origen sí se ven las negativas, p. ej. `-i 15 -f 18`: 15→6→9→10→4→18, costo 4.
Cada corrida se comprueba contra `networkx`.

## Heurística de A*

Distancia euclidiana entre las posiciones de los nodos en la imagen (`COORDS_IMG` en `grafo.py`).
Los pesos no son proporcionales a esas distancias, así que la heurística no es admisible y A* no siempre da el
camino óptimo. El programa lo avisa al final comparando con Dijkstra.

Comparación sobre los 870 pares de nodos (escala 1):

| Heurística | Camino óptimo | Sobrecosto medio | Expansiones medias | 7 → 18 |
|---|---|---|---|---|
| Euclidiana | 42 % | 36 % | 4.2 | costo 16 (óptimo) |
| Manhattan | 37 % | 49 % | 4.3 | costo 34 (no óptimo) |

Otras opciones: `--heuristica manhattan`, `--escala admisible` (siempre óptimo, pero h ≈ 0 y ~15 expansiones).

## Archivos

| Archivo | Contenido |
|---|---|
| `grafo.py` | Coordenadas, aristas, negativas, lista de arcos, matriz de adyacencia (numpy) |
| `estilo.py` | Paleta EVA-01 y dibujo del grafo (matplotlib, sin ventanas) |
| `astar.py` | A* paso a paso (vecinos desde la matriz de adyacencia) |
| `bellman_ford.py` | Bellman-Ford por pasadas (lista de arcos) |
| `main.py` | Menú interactivo |

Pesos y sentidos transcritos de las imágenes; si alguno no coincide con el de la clase, corrígelo en `ARISTAS` / `ARCOS_DIRIGIDO`.
