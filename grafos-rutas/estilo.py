"""Estilo visual (paleta tipo EVA-01) y funciones de dibujo comunes a A* y Bellman-Ford."""
import glob
import os
import sys

import matplotlib

matplotlib.use("Agg")  # sin ventanas: solo escribe archivos PNG
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

import grafo as G

try:  # evita errores de codificación al imprimir ✔ → en consolas que no son UTF-8
    sys.stdout.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

DPI = 100
TAM = (19.2, 10.8)  # 1920 x 1080 px
RADIO = 19          # radio de nodo (unidades del dibujo = px de la imagen original)

# Paleta EVA-01: morados intensos/oscuros, verde fosforescente, grises claros/blancos.
C = dict(
    fondo="#0f0820",
    panel="#1a0e33",
    borde="#7a45c9",
    morado_osc="#34195f",
    morado="#6a35b8",
    morado_cl="#a679e8",
    verde="#8cff3c",
    verde_osc="#4fc41f",
    gris="#bcbbd0",
    gris_cl="#e3e2ef",
    blanco="#f8f8fd",
    arista="#6f5c9c",
    texto="#e3e2ef",
    tenue="#9b8dc4",
)

# estado de nodo -> (relleno, borde, texto)
NODO = {
    "normal":  (C["morado_osc"], C["morado_cl"], C["gris_cl"]),
    "alcanzado": (C["morado"], C["morado_cl"], C["blanco"]),
    "abierto": (C["morado"], C["verde"], C["blanco"]),
    "cerrado": (C["gris_cl"], C["blanco"], C["fondo"]),
    "actual":  (C["verde"], C["blanco"], C["fondo"]),
    "camino":  (C["verde_osc"], C["blanco"], C["fondo"]),
    "cambio":  (C["verde"], C["blanco"], C["fondo"]),
    "ciclo":   (C["blanco"], C["verde"], C["fondo"]),
}

# estado de arista -> (color, grosor, brillo, discontinua)
ARISTA = {
    "normal": (C["arista"], 1.3, False, False),
    "arbol":  (C["morado_cl"], 2.2, False, False),
    "activa": (C["verde"], 2.6, False, False),
    "camino": (C["verde"], 4.2, True, False),
    "ciclo":  (C["blanco"], 3.6, True, True),
}


def nueva_figura():
    fig = plt.figure(figsize=TAM, dpi=DPI, facecolor=C["fondo"])
    return fig


def panel(fig, rect, borde=None):
    """Eje rectangular con fondo de panel y marco morado. rect = [x, y, ancho, alto] (0-1)."""
    ax = fig.add_axes(rect, facecolor=C["panel"])
    for s in ax.spines.values():
        s.set_color(borde or C["borde"])
        s.set_linewidth(1.6)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return ax


def eje_grafo(fig, rect):
    ax = panel(fig, rect)
    m = 45
    ax.set_xlim(-m, G.ANCHO + m)
    ax.set_ylim(-m, G.ALTO + m)
    ax.set_aspect("equal", adjustable="box")
    return ax


def titulo(fig, texto, derecha=""):
    fig.text(0.012, 0.965, texto, color=C["verde"], fontsize=17, fontweight="bold",
             family="DejaVu Sans Mono", va="center")
    if derecha:
        fig.text(0.988, 0.965, derecha, color=C["gris"], fontsize=12, family="DejaVu Sans Mono",
                 va="center", ha="right")


def _punto_medio(p, q, rad):
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    dx, dy = q[0] - p[0], q[1] - p[1]
    return mx + 0.5 * rad * dy, my - 0.5 * rad * dx


def dibujar_grafo(ax, lineas, estado_nodo=None, estado_arista=None, sub_nodo=None,
                  inicio=None, fin=None, fs_nodo=10.5):
    """Dibuja aristas, pesos y nodos.

    lineas        : salida de grafo.lineas_dibujo().
    estado_nodo   : {nodo: clave de NODO}.
    estado_arista : {(min, max, peso): clave de ARISTA}.
    sub_nodo      : {nodo: texto bajo el nodo}.
    inicio, fin   : nodos a marcar con anillo (inicio continuo, fin discontinuo).
    """
    estado_nodo = estado_nodo or {}
    estado_arista = estado_arista or {}
    sub_nodo = sub_nodo or {}

    ax.apply_aspect()
    px_por_u = ax.transData.transform((1, 0))[0] - ax.transData.transform((0, 0))[0]
    radio_pt = RADIO * px_por_u * 72 / DPI

    # --- aristas ---
    for ln in lineas:
        u, v, w, rad = ln["u"], ln["v"], ln["w"], ln["rad"]
        p, q = G.POS[u], G.POS[v]
        color, lw, brillo, disc = ARISTA[estado_arista.get(G.clave_arista(u, v, w), "normal")]
        dirigida = ln["dirigida"]
        estilo = "-|>,head_length=7,head_width=3.5" if dirigida else "-"
        kw = dict(connectionstyle=f"arc3,rad={rad}", arrowstyle=estilo, mutation_scale=1.6,
                  shrinkA=radio_pt if dirigida else 0, shrinkB=radio_pt if dirigida else 0,
                  zorder=1)
        if brillo:  # halo: solo la línea (sin punta) para no dejar manchas junto a la flecha
            kw_halo = dict(kw, arrowstyle="-")
            ax.add_patch(FancyArrowPatch(p, q, color=color, lw=lw + 5, alpha=0.22, **kw_halo))
        ax.add_patch(FancyArrowPatch(p, q, color=color, lw=lw, linestyle="--" if disc else "-", **kw))
        mx, my = _punto_medio(p, q, rad)
        neg = w < 0
        ax.text(mx, my, str(w), ha="center", va="center", fontsize=9, zorder=2,
                fontweight="bold" if neg or estado_arista.get(G.clave_arista(u, v, w)) in ("camino", "ciclo") else "normal",
                color=C["verde"] if neg else C["gris_cl"],
                bbox=dict(boxstyle="round,pad=0.14", fc=C["panel"], ec="none", alpha=0.88))

    # --- nodos ---
    for n, (x, y) in G.POS.items():
        fc, ec, tc = NODO[estado_nodo.get(n, "normal")]
        ax.add_patch(Circle((x, y), RADIO, fc=fc, ec=ec, lw=2.2, zorder=3))
        ax.text(x, y, str(n), ha="center", va="center", fontsize=fs_nodo, fontweight="bold",
                color=tc, zorder=4)
        if n in sub_nodo:
            ax.text(x, y - RADIO - 12, sub_nodo[n], ha="center", va="center", fontsize=8.5,
                    family="DejaVu Sans Mono", color=C["verde"], zorder=5,
                    bbox=dict(boxstyle="round,pad=0.15", fc=C["fondo"], ec="none", alpha=0.85))
    if inicio is not None:
        x, y = G.POS[inicio]
        ax.add_patch(Circle((x, y), RADIO + 7, fc="none", ec=C["blanco"], lw=2.2, zorder=3))
    if fin is not None:
        x, y = G.POS[fin]
        ax.add_patch(Circle((x, y), RADIO + 7, fc="none", ec=C["blanco"], lw=2.2,
                            ls=(0, (3, 2)), zorder=3))


def texto_mono(ax, x, y, s, color=None, size=10.5, weight="normal", ha="left", va="top"):
    return ax.text(x, y, s, transform=ax.transAxes, family="DejaVu Sans Mono", fontsize=size,
                   color=color or C["texto"], fontweight=weight, ha=ha, va=va)


def limpiar_capturas(carpeta, prefijo):
    """Crea la carpeta y borra capturas viejas del mismo algoritmo (solo '<prefijo>_paso*.png')."""
    os.makedirs(carpeta, exist_ok=True)
    for f in glob.glob(os.path.join(carpeta, f"{prefijo}_paso*.png")):
        os.remove(f)


def guardar(fig, carpeta, prefijo, paso):
    ruta = os.path.join(carpeta, f"{prefijo}_paso{paso}.png")
    fig.savefig(ruta, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return ruta
