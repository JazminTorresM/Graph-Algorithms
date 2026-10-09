"""
main.py · Interfaz de caminos mínimos (Dijkstra · Warshall-Floyd)
─────────────────────────────────────────────────────────────────
Archivos del proyecto (deben estar en la misma carpeta):
    graph.py            datos del grafo + matrices de adyacencia e incidencia
    dijkstra.py         algoritmo de Dijkstra
    warshall_floyd.py   algoritmo de Warshall-Floyd (matrices de distancias y recorridos)
    main.py             esta interfaz

Ejecutar:   python main.py
Requisitos: pip install numpy pillow      (Tkinter ya viene con Python)

• Arriba a la derecha cambias de algoritmo.
• Selección de inicio / fin desde la barra inferior (o clic en los nodos).
• Exporta una imagen PNG por cada paso (botón «Exportar imágenes»).
Atajos:  espacio = reproducir · ← → = paso · Inicio / Fin = reiniciar / saltar al final
En el grafo:  clic = nodo de inicio · clic derecho (o Shift+clic) = nodo final

Para agregar otro algoritmo: crea un archivo como dijkstra.py (NAME, KEY,
SUPPORTS_STOP, HAS_MATRICES, solve(), stats()) y añádelo a ALGORITHMS.
"""
import math
import os
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import numpy as np

import dijkstra
import warshall_floyd
from graph import ADJ, EDGES, IDX, INC, INF, NODES, POS

ALGORITHMS = [dijkstra, warshall_floyd]      # ← aquí se registran los algoritmos
HEADER_KINDS = ("visit", "init", "iter")     # pasos "principales" (los demás son detalle)

# ──────────────────────────────────────────────────────────────
#  PALETA (menta + tinta verde oscuro, un solo acento cálido)
# ──────────────────────────────────────────────────────────────
FONT, MONO = "Segoe UI", "Consolas"

BG, SURF = "#f3f9f6", "#ffffff"
CARD, PALE = "#edf6f1", "#d9f3e6"
INK, MUTED, DIM, LINE = "#1e3a30", "#7d968c", "#c4d4cc", "#e2ece7"
ACCENT, ACCENT_D = "#34c38f", "#239a70"
AMBER, AMBER_D = "#f2a03d", "#d9822b"
EDGE_C, TREE_C, PILL_T = "#dbe8e2", "#a7ddc6", "#9db3a9"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """a·(1-t) + b·t"""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(ra[i] * (1 - t) + rb[i] * t) for i in range(3))


def rr(c, x1, y1, x2, y2, r=12, **kw):
    """Rectángulo redondeado."""
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


# ──────────────────────────────────────────────────────────────
#  SELECTOR DESPLEGABLE DE NODOS (cuadrícula de fichas)
# ──────────────────────────────────────────────────────────────
class NodePopup(tk.Frame):
    """Panel que se despliega dentro de la ventana, justo encima del botón."""

    def __init__(self, app, current, on_pick, on_close, accent):
        super().__init__(app, bg=SURF, highlightbackground=LINE, highlightthickness=1)
        tk.Label(self, text="SELECCIONA UN NODO", bg=SURF, fg=MUTED,
                 font=(FONT, 8, "bold")).grid(row=0, column=0, columnspan=5,
                                              sticky="w", padx=14, pady=(12, 6))
        x = tk.Label(self, text="✕", bg=SURF, fg=MUTED, cursor="hand2",
                     font=(FONT, 10, "bold"))
        x.grid(row=0, column=5, sticky="e", padx=(0, 10), pady=(10, 4))
        x.bind("<Enter>", lambda e: x.configure(fg=INK))
        x.bind("<Leave>", lambda e: x.configure(fg=MUTED))
        x.bind("<Button-1>", lambda e: on_close())
        for i, n in enumerate(NODES):
            sel = n == current
            lb = tk.Label(self, text=str(n), width=4, pady=5, cursor="hand2",
                          bg=accent if sel else CARD,
                          fg="white" if sel else INK, font=(FONT, 10, "bold"))
            lb.grid(row=1 + i // 6, column=i % 6, padx=3, pady=3)
            if not sel:
                lb.bind("<Enter>", lambda e, w=lb: w.configure(bg=PALE))
                lb.bind("<Leave>", lambda e, w=lb: w.configure(bg=CARD))
            lb.bind("<Button-1>", lambda e, n=n: on_pick(n))
        tk.Frame(self, height=10, bg=SURF).grid(row=99, column=0)


# ──────────────────────────────────────────────────────────────
#  VISTA DE MATRIZ (mapa de calor con cabeceras fijas)
# ──────────────────────────────────────────────────────────────
class MatrixView(tk.Frame):
    """Matriz estática (adyacencia / incidencia). Las subclases cambian
    cómo se pinta cada celda sobrescribiendo _prep(), cell() y _describe()."""
    CW, CH, HW = 36, 28, 52
    ROUNDED = True

    def __init__(self, master, M, rows, cols, kind):
        super().__init__(master, bg=SURF)
        self.M, self.rows, self.cols, self.kind = M, rows, cols, kind
        self.marks = frozenset()
        self.hover = None
        nr, nc = M.shape
        W, H = nc * self.CW, nr * self.CH

        self.info = tk.Label(self, bg=SURF, fg=MUTED, anchor="w", font=(FONT, 10))
        self.info.grid(row=0, column=0, columnspan=3, sticky="ew", padx=22, pady=(16, 10))
        self.corner = tk.Canvas(self, width=self.HW, height=self.CH, bg=SURF,
                                highlightthickness=0)
        self.colh = tk.Canvas(self, height=self.CH, bg=SURF, highlightthickness=0,
                              scrollregion=(0, 0, W, self.CH))
        self.rowh = tk.Canvas(self, width=self.HW, bg=SURF, highlightthickness=0,
                              scrollregion=(0, 0, self.HW, H))
        self.body = tk.Canvas(self, bg=SURF, highlightthickness=0,
                              scrollregion=(0, 0, W, H),
                              xscrollincrement=self.CW, yscrollincrement=self.CH,
                              xscrollcommand=self._xset, yscrollcommand=self._yset)
        self.xs = ttk.Scrollbar(self, orient="horizontal", command=self.body.xview)
        self.ys = ttk.Scrollbar(self, orient="vertical", command=self.body.yview)
        self.corner.grid(row=1, column=0)
        self.colh.grid(row=1, column=1, sticky="ew")
        self.rowh.grid(row=2, column=0, sticky="ns")
        self.body.grid(row=2, column=1, sticky="nsew")
        self.ys.grid(row=2, column=2, sticky="ns")
        self.xs.grid(row=3, column=1, sticky="ew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.body.bind("<Motion>", self._motion)
        self.body.bind("<Leave>", lambda e: self._set_hover(None))
        self.body.bind("<MouseWheel>", lambda e: self.body.yview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        self.body.bind("<Shift-MouseWheel>", lambda e: self.body.xview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        self.body.bind("<Button-4>", lambda e: self.body.yview_scroll(-1, "units"))
        self.body.bind("<Button-5>", lambda e: self.body.yview_scroll(1, "units"))
        self._reset_info()
        self.draw()

    def _xset(self, a, b):
        self.xs.set(a, b)
        self.colh.xview_moveto(a)

    def _yset(self, a, b):
        self.ys.set(a, b)
        self.rowh.yview_moveto(a)

    # --- textos ---
    def _reset_info(self):
        if self.kind == "adj":
            self.info.config(text="Pasa el mouse sobre una celda · el valor es el peso de la "
                                  "arista · las celdas verdes forman el camino final")
        else:
            self.info.config(text="Filas = nodos · columnas = aristas · 1 = el nodo toca la "
                                  "arista · las celdas verdes forman el camino final")

    def _describe(self, r_, c_):
        v = int(self.M[r_, c_])
        if self.kind == "adj":
            return (f"{self.rows[r_]}  ↔  {self.cols[c_]}   ·   peso {v}" if v
                    else f"{self.rows[r_]}  ↔  {self.cols[c_]}   ·   sin arista directa")
        u, w, p = EDGES[c_][:3]
        return (f"nodo {self.rows[r_]}  ·  arista {self.cols[c_]} ({u}–{w}, peso {p})"
                + ("  ·  incide ✓" if v else "  ·  no incide"))

    # --- pintura de celdas (se sobrescribe en subclases) ---
    def _prep(self):
        self.lmax = math.log1p(max(1, int(self.M.max())))

    def cell(self, r_, c_):
        """→ (texto, relleno o None, color del texto, negrita)"""
        v = int(self.M[r_, c_])
        if not v:
            return "·", None, DIM, False
        if (r_, c_) in self.marks:
            return str(v), ACCENT, "white", True
        t = .12 + .30 * (math.log1p(v) / self.lmax if self.kind == "adj" else .5)
        return str(v), mix(SURF, ACCENT, t), INK, True

    def _over(self):
        pass

    def set_marks(self, marks):
        marks = frozenset(marks)
        if marks != self.marks:
            self.marks = marks
            self.draw()

    def draw(self):
        CW, CH = self.CW, self.CH
        nr, nc = self.M.shape
        for cv in (self.body, self.colh, self.rowh, self.corner):
            cv.delete("all")
        for c_, name in enumerate(self.cols):
            self.colh.create_text(c_ * CW + CW / 2, CH / 2, text=name, fill=MUTED,
                                  font=(FONT, 9, "bold"))
        for r_, name in enumerate(self.rows):
            self.rowh.create_text(self.HW / 2, r_ * CH + CH / 2, text=name,
                                  fill=MUTED, font=(FONT, 9, "bold"))
        self._prep()
        for r_ in range(nr):
            for c_ in range(nc):
                text, fill, fg, bold = self.cell(r_, c_)
                x0, y0 = c_ * CW, r_ * CH
                if fill:
                    if self.ROUNDED:
                        rr(self.body, x0 + 2, y0 + 2, x0 + CW - 2, y0 + CH - 2, 7,
                           fill=fill, outline="")
                    else:
                        self.body.create_rectangle(x0 + 1, y0 + 1, x0 + CW - 1, y0 + CH - 1,
                                                   fill=fill, outline="")
                size = 10 if text == "·" else (9 if len(text) < 4 else 8)
                self.body.create_text(x0 + CW / 2, y0 + CH / 2, text=text, fill=fg,
                                      font=(FONT, size, "bold" if bold else "normal"))
        self._over()
        self._draw_hover()

    # --- mouse ---
    def _motion(self, e):
        c_ = int(self.body.canvasx(e.x) // self.CW)
        r_ = int(self.body.canvasy(e.y) // self.CH)
        nr, nc = self.M.shape
        self._set_hover((r_, c_) if 0 <= r_ < nr and 0 <= c_ < nc else None)

    def _set_hover(self, h):
        if h == self.hover:
            return
        self.hover = h
        self._draw_hover()
        if h is None:
            self._reset_info()
            return
        self.info.config(text=self._describe(*h), fg=INK)

    def _draw_hover(self):
        self.body.delete("hover")
        if self.hover is None:
            self.info.config(fg=MUTED)
            return
        r_, c_ = self.hover
        nr, nc = self.M.shape
        CW, CH = self.CW, self.CH
        self.body.create_rectangle(0, r_ * CH, nc * CW, (r_ + 1) * CH,
                                   outline=ACCENT, tags="hover")
        self.body.create_rectangle(c_ * CW, 0, (c_ + 1) * CW, nr * CH,
                                   outline=ACCENT, tags="hover")


class FloydView(MatrixView):
    """Matriz de distancias (D) o de recorridos (P) de Warshall-Floyd,
    una foto por iteración. Banda ámbar = fila y columna del pivote ·
    verde = celdas que mejoraron en esa iteración."""
    ROUNDED = False

    def __init__(self, master, kind):
        self.pivot, self.changed, self.focus = None, frozenset(), None
        names = [str(n) for n in NODES]
        super().__init__(master, np.zeros((len(NODES), len(NODES))), names, names, kind)

    def show(self, M, pivot, changed, focus):
        self.M, self.pivot, self.changed, self.focus = M, pivot, changed, focus
        self.draw()

    def _reset_info(self):
        if self.kind == "dist":
            self.info.config(text="D = distancias mínimas conocidas · null = diagonal · ∞ = aún sin "
                                  "camino · verde = mejoró en esta iteración · banda ámbar = pivote")
        else:
            self.info.config(text="P = nodo intermedio del camino · si es igual a la columna la ruta "
                                  "es directa · verde = cambió en esta iteración · banda ámbar = pivote")

    def _describe(self, r_, c_):
        a, b, v = self.rows[r_], self.cols[c_], self.M[r_, c_]
        extra = "  ·  mejoró en esta iteración" if (r_, c_) in self.changed else ""
        if self.kind == "dist":
            if r_ == c_:
                return f"D[{a}][{b}]  ·  diagonal (null)"
            return (f"D[{a}][{b}] = ∞  ·  aún sin camino" if v == INF
                    else f"D[{a}][{b}] = {int(v)}{extra}")
        k = int(v)
        if r_ == c_:
            return f"P[{a}][{b}]  ·  diagonal"
        return (f"P[{a}][{b}] = {NODES[k]}  ·  ruta directa{extra}" if k == c_
                else f"P[{a}][{b}] = {NODES[k]}  ·  el camino pasa por {NODES[k]}{extra}")

    def _prep(self):
        fin = self.M[np.isfinite(self.M)]
        self.lmax = math.log1p(max(1, int(fin.max()) if fin.size else 1))

    def cell(self, r_, c_):
        v = self.M[r_, c_]
        band = self.pivot is not None and (r_ == self.pivot or c_ == self.pivot)
        base = mix(SURF, AMBER, .16) if band else None
        if self.kind == "dist":
            if r_ == c_:
                text, fill, fg, bold = "null", base, DIM, False
            elif v == INF:
                text, fill, fg, bold = "∞", base, DIM, False
            else:
                text, bold, fg = str(int(v)), True, INK
                fill = mix(base or SURF, ACCENT, .10 + .28 * math.log1p(v) / self.lmax)
        else:
            k = int(v)
            text, fg, bold, fill = str(NODES[k]), INK, k != c_, base
            if k != c_:
                fill = mix(base or SURF, ACCENT, .22)
        if (r_, c_) in self.changed:
            fill, fg, bold = ACCENT, "white", True
        return text, fill, fg, bold

    def _over(self):
        if self.focus is not None:
            r_, c_ = self.focus
            self.body.create_rectangle(c_ * self.CW + 1, r_ * self.CH + 1,
                                       (c_ + 1) * self.CW - 1, (r_ + 1) * self.CH - 1,
                                       outline=AMBER_D, width=2)


# ──────────────────────────────────────────────────────────────
#  APLICACIÓN
# ──────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Caminos mínimos · Grafo")
        self.geometry("1400x860")
        self.minsize(1200, 720)
        self.configure(bg=BG)

        self.algo = ALGORITHMS[0]
        self.src, self.dst = 7, 18
        self.stop = True
        self.interval = 420
        self.frames, self.path, self.total = [], [], None
        self.k = -1
        self.playing = False
        self.pix, self.R, self.scale = {}, 16, 100
        self.cw = self.ch = 0
        self.hover = None
        self.popup = None
        self._popup_born = 0.0
        self.tab = "graph"
        self._dirty = {}
        self.f_msg = tkfont.Font(family=FONT, size=10)
        self.f_tab = tkfont.Font(family=FONT, size=10)
        self.f_btn = tkfont.Font(family=FONT, size=10, weight="bold")
        self.f_seg = tkfont.Font(family=FONT, size=9, weight="bold")
        self.f_brand = tkfont.Font(family=FONT, size=15, weight="bold")
        self.f_leg = tkfont.Font(family=FONT, size=9)

        self._style()
        self._build()
        self.run()

    # ---------- estilo ttk (solo scrollbars) ----------
    def _style(self):
        st = ttk.Style(self)
        st.theme_use("clam")
        for o in ("Vertical", "Horizontal"):
            st.configure(f"{o}.TScrollbar", background=CARD, troughcolor=SURF,
                         bordercolor=SURF, lightcolor=CARD, darkcolor=CARD,
                         arrowcolor=MUTED, relief="flat", arrowsize=12)
            st.map(f"{o}.TScrollbar", background=[("active", PALE)])

    # ---------- construcción ----------
    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.head = tk.Canvas(self, height=68, bg=BG, highlightthickness=0)
        self.head.grid(row=0, column=0, sticky="ew")
        self.head.bind("<Configure>", lambda e: self.draw_head())

        stack = tk.Frame(self, bg=BG)
        stack.grid(row=1, column=0, sticky="nsew", padx=28)
        stack.grid_rowconfigure(0, weight=1)
        stack.grid_columnconfigure(0, weight=1)

        self.dock = tk.Canvas(self, height=96, bg=BG, highlightthickness=0)
        self.dock.grid(row=2, column=0, sticky="ew")
        self.dock.bind("<Configure>", lambda e: self.draw_dock())

        names = [str(n) for n in NODES]
        self.pages = {}
        self.gc = tk.Canvas(stack, bg=BG, highlightthickness=0)
        self.pages["graph"] = self.gc
        self.adjv = MatrixView(stack, ADJ, names, names, "adj")
        self.pages["adj"] = self.adjv
        self.incv = MatrixView(stack, INC, names,
                               [f"e{i + 1}" for i in range(len(EDGES))], "inc")
        self.pages["inc"] = self.incv
        self.distv = FloydView(stack, "dist")          # solo se muestran con Warshall-Floyd
        self.pages["dist"] = self.distv
        self.pathv = FloydView(stack, "path")
        self.pages["path"] = self.pathv

        logf = tk.Frame(stack, bg=SURF)
        self.log = tk.Text(logf, bg=SURF, fg=INK, bd=0, padx=26, pady=22,
                           font=(MONO, 10), wrap="none", highlightthickness=0,
                           spacing1=3, cursor="arrow")
        sb = ttk.Scrollbar(logf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)
        for tag, col in (("visit", AMBER_D), ("ok", ACCENT_D), ("no", DIM),
                         ("end", ACCENT_D), ("head", MUTED), ("num", DIM)):
            self.log.tag_config(tag, foreground=col)
        self.log.tag_config("big", foreground=INK, font=(MONO, 11, "bold"))
        self.pages["log"] = logf

        for p in self.pages.values():
            p.grid(row=0, column=0, sticky="nsew")
        self.gc.bind("<Configure>", self._on_gc_resize)
        self.gc.bind("<Motion>", self._on_gc_motion)
        self.gc.bind("<Button-1>", self._on_gc_click)
        self.gc.bind("<Shift-Button-1>", self._on_gc_click_end)
        self.gc.bind("<Button-3>", self._on_gc_click_end)
        self.gc.bind("<Button-2>", self._on_gc_click_end)

        self.bind("<space>", lambda e: self.toggle_play())
        self.bind("<Right>", lambda e: self.next())
        self.bind("<Left>", lambda e: self.prev())
        self.bind("<Home>", lambda e: self.reset())
        self.bind("<End>", lambda e: self.to_end())
        self.bind("<Button-1>", self._maybe_close_popup, add="+")
        self.bind("<Escape>", lambda e: self.close_popup())
        self.show_tab("graph")

    def tabs(self):
        """Pestañas visibles según el algoritmo activo."""
        t = [("graph", "Grafo"), ("adj", "Adyacencia"), ("inc", "Incidencia")]
        if self.algo.HAS_MATRICES:
            t += [("dist", "Distancias"), ("path", "Recorridos")]
        return t + [("log", "Pasos")]

    def show_tab(self, key):
        self.tab = key
        tk.Misc.tkraise(self.pages[key])
        self.draw_head()
        self._flush()

    def set_algo(self, mod):
        if mod is self.algo:
            return
        self.close_popup()
        self.playing = False
        self.algo = mod
        if self.tab not in [k for k, _ in self.tabs()]:
            self.tab = "graph"
            tk.Misc.tkraise(self.pages["graph"])
        self.run()
        self.draw_head()

    # ---------- cabecera: marca, pestañas, algoritmo y exportar ----------
    def draw_head(self):
        c = self.head
        c.delete("all")
        W = max(c.winfo_width(), 800)
        c.create_oval(30, 29, 42, 41, fill=ACCENT, outline="")
        c.create_text(54, 35, text="Caminos mínimos", anchor="w", fill=INK, font=self.f_brand)
        x = 54 + self.f_brand.measure("Caminos mínimos") + 40
        f = self.f_tab
        for key, label in self.tabs():
            w = f.measure(label)
            tag = f"tab_{key}"
            active = key == self.tab
            c.create_text(x, 35, text=label, anchor="w", font=f,
                          fill=INK if active else MUTED, tags=(tag, tag + "_t"))
            if active:
                c.create_line(x, 54, x + w, 54, fill=ACCENT, width=2, capstyle="round")
            c.create_rectangle(x - 10, 16, x + w + 10, 58, fill="", outline="", tags=(tag,))
            c.tag_bind(tag, "<Button-1>", lambda e, k=key: self.show_tab(k))
            if not active:
                c.tag_bind(tag, "<Enter>", lambda e, t=tag: (
                    c.itemconfig(t + "_t", fill=INK), c.config(cursor="hand2")))
                c.tag_bind(tag, "<Leave>", lambda e, t=tag: (
                    c.itemconfig(t + "_t", fill=MUTED), c.config(cursor="")))
            x += w + 26
        # exportar
        lab = "Exportar imágenes"
        w = self.f_btn.measure(lab) + 36
        bx = W - 28 - w
        rr(c, bx, 19, bx + w, 51, 16, fill=SURF, outline=LINE, tags=("exp", "exp_bg"))
        c.create_text(bx + w / 2, 35, text=lab, font=self.f_btn, fill=ACCENT_D, tags=("exp",))
        c.tag_bind("exp", "<Button-1>", lambda e: self.export_images())
        c.tag_bind("exp", "<Enter>", lambda e: (
            c.itemconfig("exp_bg", fill=PALE), c.config(cursor="hand2")))
        c.tag_bind("exp", "<Leave>", lambda e: (
            c.itemconfig("exp_bg", fill=SURF), c.config(cursor="")))
        # selector de algoritmo (control segmentado)
        widths = [self.f_seg.measure(a.NAME) + 30 for a in ALGORITHMS]
        total = sum(widths) + 8
        sx = bx - 16 - total
        rr(c, sx, 17, sx + total, 53, 18, fill=CARD, outline="")
        px = sx + 4
        for a, w in zip(ALGORITHMS, widths):
            tag = f"alg_{a.KEY}"
            on = a is self.algo
            rr(c, px, 21, px + w, 49, 14, fill=ACCENT if on else CARD, outline="",
               tags=(tag, tag + "_bg"))
            c.create_text(px + w / 2, 35, text=a.NAME, font=self.f_seg,
                          fill="white" if on else MUTED, tags=(tag, tag + "_t"))
            c.tag_bind(tag, "<Button-1>", lambda e, m=a: self.set_algo(m))
            if not on:
                c.tag_bind(tag, "<Enter>", lambda e, t=tag: (
                    c.itemconfig(t + "_t", fill=INK), c.config(cursor="hand2")))
                c.tag_bind(tag, "<Leave>", lambda e, t=tag: (
                    c.itemconfig(t + "_t", fill=MUTED), c.config(cursor="")))
            px += w

    # ---------- lógica ----------
    def run(self):
        self.playing = False
        self.frames, self.path, self.total = self.algo.solve(self.src, self.dst, self.stop)
        self.k = -1
        self.refresh()

    def reset(self):
        self.playing = False
        self.k = -1
        self.refresh()

    def next(self):
        if self.k < len(self.frames) - 1:
            self.k += 1
            self.refresh()
        else:
            self.playing = False
            self.draw_dock()

    def prev(self):
        self.playing = False
        if self.k >= 0:
            self.k -= 1
            self.refresh()

    def to_end(self):
        self.playing = False
        self.k = len(self.frames) - 1
        self.refresh()

    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            if self.k >= len(self.frames) - 1:
                self.k = -1
                self.refresh()
            self._tick()
        self.draw_dock()

    def _tick(self):
        if not self.playing:
            return
        if self.k < len(self.frames) - 1:
            self.next()
            self.after(int(self.interval), self._tick)
        else:
            self.playing = False
            self.draw_dock()

    def swap(self):
        self.src, self.dst = self.dst, self.src
        self.run()

    def toggle_stop(self):
        self.stop = not self.stop
        self.run()

    @property
    def done(self):
        return self.k >= 0 and self.k == len(self.frames) - 1

    def refresh(self):
        self.draw_graph()
        self.draw_dock()
        adj, inc = set(), set()
        if self.done and len(self.path) > 1:
            for a, b in zip(self.path, self.path[1:]):
                adj.update({(a, b), (b, a)})
                for kk, e in enumerate(EDGES):
                    if {IDX[e[0]], IDX[e[1]]} == {a, b} and e[2] == ADJ[a, b]:
                        inc.update({(a, kk), (b, kk)})
                        break
        self.adjv.set_marks(adj)
        self.incv.set_marks(inc)
        self._dirty = {"log": True, "dist": True, "path": True}
        self._flush()

    def _flush(self):
        """Actualiza solo la pestaña visible (las demás se ponen al día al abrirlas)."""
        key = self.tab
        if not self._dirty.get(key):
            return
        if key == "log":
            self.update_log()
        elif key in ("dist", "path") and self.algo.HAS_MATRICES and self.frames:
            f = self.frames[max(self.k, 0)]
            focus = (IDX[self.src], IDX[self.dst]) if self.done else None
            view, mat = (self.distv, "D") if key == "dist" else (self.pathv, "P")
            view.show(f[mat], f["k"], f["changed"], focus)
        self._dirty[key] = False

    # ---------- exportar cada paso como imagen ----------
    def _grab(self):
        from PIL import ImageGrab
        x, y = self.winfo_rootx(), self.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        shot = ImageGrab.grab()
        r = shot.width / self.winfo_screenwidth()  # corrige pantallas con escala (125 %, 150 %…)
        return shot.crop((int(x * r), int(y * r), int((x + w) * r), int((y + h) * r)))

    def export_images(self):
        try:
            import PIL.ImageGrab  # noqa: F401
        except ImportError:
            messagebox.showinfo("Falta Pillow",
                                "Para exportar imágenes instala Pillow:\n\npip install pillow")
            return
        folder = filedialog.askdirectory(title="Carpeta donde guardar las imágenes")
        if not folder:
            return
        out = os.path.join(folder, f"{self.algo.KEY}_{self.src}_a_{self.dst}")
        os.makedirs(out, exist_ok=True)
        self.close_popup()
        self.playing = False
        old_k, old_tab = self.k, self.tab
        self.show_tab("graph")
        self.attributes("-topmost", True)
        self.lift()
        self.update()
        n = len(self.frames)
        try:
            for i in range(n):
                self.k = i
                self.refresh()
                self.title(f"Exportando {i + 1}/{n}…")
                self.update_idletasks()
                self.update()
                self._grab().save(os.path.join(out, f"paso_{i + 1:03d}.png"))
        finally:
            self.attributes("-topmost", False)
            self.title("Caminos mínimos · Grafo")
            self.k = old_k
            self.show_tab(old_tab)
            self.refresh()
        messagebox.showinfo("Listo", f"Se guardaron {n} imágenes en:\n{out}")

    # ---------- selector de nodos ----------
    def open_picker(self, which, x, y_top):
        self.close_popup()
        cur = self.src if which == "src" else self.dst
        self.popup = NodePopup(self, cur, lambda n: self.pick(which, n), self.close_popup,
                               ACCENT if which == "src" else INK)
        self.update_idletasks()
        pw = self.popup.winfo_reqwidth()
        sx = self.dock.winfo_x() + x - 8
        sx = max(12, min(sx, self.winfo_width() - pw - 12))   # que no se salga de la ventana
        sy = self.dock.winfo_y() + y_top - 6                  # justo encima del botón
        self.popup.place(x=sx, y=sy, anchor="sw")
        self.popup.lift()
        self._popup_born = time.monotonic()  # el mismo clic que lo abre no debe cerrarlo

    def pick(self, which, n):
        self.close_popup()
        if which == "src":
            self.src = n
        else:
            self.dst = n
        self.run()

    def close_popup(self):
        if self.popup is not None:
            try:
                self.popup.destroy()
            except tk.TclError:
                pass
            self.popup = None

    def _maybe_close_popup(self, e):
        if self.popup is None or time.monotonic() - self._popup_born < 0.25:
            return
        if not str(e.widget).startswith(str(self.popup)):
            self.close_popup()

    # ---------- eventos del grafo ----------
    def _node_at(self, x, y):
        lim = (self.R + 5) ** 2
        for n, (px, py) in self.pix.items():
            if (px - x) ** 2 + (py - y) ** 2 <= lim:
                return n
        return None

    def _on_gc_motion(self, e):
        n = self._node_at(e.x, e.y)
        if n != self.hover:
            self.hover = n
            self.gc.config(cursor="hand2" if n is not None else "")

    def _on_gc_click(self, e):
        n = self._node_at(e.x, e.y)
        if n is not None:
            self.src = n
            self.run()

    def _on_gc_click_end(self, e):
        n = self._node_at(e.x, e.y)
        if n is not None:
            self.dst = n
            self.run()

    def _on_gc_resize(self, e):
        self.cw, self.ch = e.width, e.height
        xs = [p[0] for p in POS.values()]
        ys = [p[1] for p in POS.values()]
        wx, wy = max(xs) - min(xs), max(ys) - min(ys)
        top, bottom, side = 128, 104, 72
        aw, ah = self.cw - 2 * side, self.ch - top - bottom
        self.scale = max(40, min(aw / wx, ah / wy))
        ox = (self.cw - wx * self.scale) / 2
        oy = top + (ah - wy * self.scale) / 2
        self.pix = {n: (ox + (x - min(xs)) * self.scale,
                        oy + (max(ys) - y) * self.scale)
                    for n, (x, y) in POS.items()}
        self.R = max(12, min(19, self.scale * 0.16))
        self.hover = None
        self.draw_bg()
        self.draw_graph()

    # ---------- fondo del lienzo ----------
    def draw_bg(self):
        c, w, h = self.gc, self.cw, self.ch
        c.delete("bg")
        rr(c, 1, 1, w - 1, h - 1, 26, fill=SURF, outline="", tags="bg")
        items = [("Inicio", ACCENT, "fill"), ("Fin", INK, "fill"),
                 ("Actual", AMBER, "ring"), ("Visitado", ACCENT, "ring"),
                 ("Camino", ACCENT, "line")]
        x = 40
        for label, col, shape in items:
            if shape == "fill":
                c.create_oval(x, h - 38, x + 10, h - 28, fill=col, outline="", tags="bg")
            elif shape == "ring":
                c.create_oval(x, h - 38, x + 10, h - 28, fill=SURF, outline=col,
                              width=2, tags="bg")
            else:
                c.create_line(x - 2, h - 33, x + 12, h - 33, fill=col, width=3,
                              capstyle="round", tags="bg")
            c.create_text(x + 18, h - 33, text=label, anchor="w", fill=MUTED,
                          font=(FONT, 9), tags="bg")
            x += 18 + self.f_leg.measure(label) + 24
        c.create_text(w - 40, h - 33, anchor="e", fill=DIM, font=(FONT, 9), tags="bg",
                      text="clic: inicio   ·   clic derecho: fin")
        c.tag_lower("bg")

    # ---------- dibujo del grafo ----------
    def draw_graph(self):
        c = self.gc
        c.delete("graph")
        if not self.pix:
            return
        n_all = len(NODES)
        fr = self.frames[self.k] if self.k >= 0 else None
        visited = fr["visited"] if fr else set()
        dist = fr["dist"] if fr else [INF] * n_all
        prev = fr["prev"] if fr and fr.get("prev") is not None else [None] * n_all
        cur = fr["cur"] if fr else None
        cur_key = (frozenset(fr["edge"]) if fr and fr.get("edge") else None)
        done = self.done
        s_i, d_i = IDX[self.src], IDX[self.dst]

        path_keys = set()
        if done and len(self.path) > 1:
            path_keys = {frozenset(p) for p in zip(self.path, self.path[1:])}
        path_pos = {p: i for i, p in enumerate(self.path)} if done else {}
        tree = {frozenset((v, p)) for v, p in enumerate(prev)
                if p is not None and v in visited}

        # encabezado: ruta, camino y estadísticas
        c.create_text(40, 36, anchor="nw", fill=INK, font=(FONT, 24, "bold"),
                      text=f"{self.src}  →  {self.dst}", tags="graph")
        if done and self.path:
            sub = (f"distancia {self.total}   ·   "
                   + "  →  ".join(str(NODES[i]) for i in self.path))
        elif done:
            sub = "no existe camino entre estos nodos"
        elif self.k >= 0:
            sub = f"{self.algo.NAME}  ·  en proceso…"
        else:
            sub = f"{self.algo.NAME}  ·  pulsa reproducir para comenzar"
        c.create_text(42, 80, anchor="nw", fill=MUTED, font=(FONT, 10),
                      text=sub, tags="graph")
        stats = self.algo.stats(self.frames, self.k, done, self.path, self.total)
        sx = self.cw - 40 - 124 * len(stats)
        for i, (lab, val) in enumerate(stats):
            x = sx + i * 124
            c.create_text(x, 40, anchor="nw", text=val, fill=INK,
                          font=(FONT, 17, "bold"), tags="graph")
            c.create_text(x, 68, anchor="nw", text=lab, fill=MUTED,
                          font=(FONT, 9), tags="graph")

        # aristas
        items = []
        for e in EDGES:
            u, v, w = e[:3]
            off = e[3] if len(e) > 3 else 0
            key = frozenset((IDX[u], IDX[v]))
            z, col, wd, wcol = 0, EDGE_C, 1.5, PILL_T
            if key in tree:
                z, col, wd, wcol = 1, TREE_C, 2.4, MUTED
            if cur_key and key == cur_key:
                z, col, wd, wcol = 2, AMBER, 3, AMBER_D
            if key in path_keys:
                z, col, wd, wcol = 3, ACCENT, 4, INK
            items.append((z, u, v, w, off, col, wd, wcol))
        items.sort(key=lambda t: t[0])
        pills = []
        sc = self.scale
        for z, u, v, w, off, col, wd, wcol in items:
            x1, y1 = self.pix[u]
            x2, y2 = self.pix[v]
            dx, dy = x2 - x1, y2 - y1
            L = math.hypot(dx, dy) or 1
            ox, oy = -dy / L * off * sc, dx / L * off * sc
            x1, y1, x2, y2 = x1 + ox, y1 + oy, x2 + ox, y2 + oy
            c.create_line(x1, y1, x2, y2, fill=col, width=wd, capstyle="round",
                          tags="graph")
            pills.append(((x1 + x2) / 2, (y1 + y2) / 2, str(w), wcol, z))
        for mx, my, txt, wcol, z in pills:
            tw = len(txt) * 6 + 10
            rr(c, mx - tw / 2, my - 8, mx + tw / 2, my + 8, 8, fill=SURF,
               outline="", tags="graph")
            c.create_text(mx, my, text=txt, fill=wcol,
                          font=(FONT, 8, "bold" if z >= 2 else "normal"), tags="graph")

        # nodos
        R = self.R
        for name in NODES:
            i = IDX[name]
            x, y = self.pix[name]
            ring, fill, tcol, rw = "#d3e2db", SURF, MUTED, 1.5
            if dist[i] < INF:
                ring, fill, tcol, rw = TREE_C, SURF, INK, 2
            if i in visited:
                ring, fill, tcol, rw = ACCENT, PALE, INK, 2
            if i == cur and not done:
                ring, fill, tcol, rw = AMBER, SURF, INK, 3
            if done and i in path_pos:
                ring, fill, tcol, rw = ACCENT, mix(ACCENT, SURF, .7), INK, 2.5
            if i == s_i:
                ring, fill, tcol = ACCENT, ACCENT, "white"
            if i == d_i:
                ring, fill, tcol = INK, INK, "white"
            c.create_oval(x - R, y - R, x + R, y + R, fill=fill, outline=ring,
                          width=rw, tags="graph")
            c.create_text(x, y, text=str(name), fill=tcol,
                          font=(FONT, 9 if name < 100 else 8, "bold"), tags="graph")
            if dist[i] < INF:
                c.create_text(x, y - R - 9, text=str(dist[i]), fill=MUTED,
                              font=(FONT, 8, "bold"), tags="graph")

        # mensaje del paso (texto simple, sin cápsulas)
        if done:
            msg = (f"Camino mínimo encontrado  ·  distancia {self.total}" if self.path
                   else "Sin camino posible")
            col = ACCENT_D
        elif fr:
            msg = fr["msg"]
            col = (AMBER_D if fr["kind"] in HEADER_KINDS
                   else (ACCENT_D if fr["ok"] else MUTED))
        else:
            msg, col = "", MUTED
        if msg:
            c.create_text(self.cw / 2, self.ch - 66, text=msg, fill=col,
                          font=self.f_msg, tags="graph")

    # ---------- barra inferior (controles) ----------
    def _btn(self, c, x1, y1, x2, y2, tag, cmd, fill=CARD, hover=PALE, r=12):
        rr(c, x1, y1, x2, y2, r, fill=fill, outline="", tags=(tag, tag + "_bg"))
        c.tag_bind(tag, "<Button-1>", lambda e: cmd())
        c.tag_bind(tag, "<Enter>", lambda e: (c.itemconfig(tag + "_bg", fill=hover),
                                              c.config(cursor="hand2")))
        c.tag_bind(tag, "<Leave>", lambda e: (c.itemconfig(tag + "_bg", fill=fill),
                                              c.config(cursor="")))

    def _icon(self, c, kind, cx, cy, s, col, tag):
        t = (tag,)
        if kind == "play":
            c.create_polygon(cx - s * .3, cy - s * .5, cx - s * .3, cy + s * .5,
                             cx + s * .55, cy, fill=col, outline="", tags=t)
        elif kind == "pause":
            for dx in (-.34, .08):
                c.create_rectangle(cx + s * dx, cy - s * .45, cx + s * (dx + .26),
                                   cy + s * .45, fill=col, outline="", tags=t)
        else:
            d = -1 if kind in ("prev", "first") else 1
            c.create_polygon(cx - d * s * .3, cy - s * .42, cx - d * s * .3, cy + s * .42,
                             cx + d * s * .4, cy, fill=col, outline="", tags=t)
            if kind in ("first", "last"):
                bx = cx + d * s * .55
                c.create_rectangle(bx - s * .07, cy - s * .42, bx + s * .07, cy + s * .42,
                                   fill=col, outline="", tags=t)

    def draw_dock(self):
        c = self.dock
        c.delete("all")
        W = c.winfo_width()
        if W < 100:
            return
        pw = min(W - 56, 1060)
        x0, x1 = (W - pw) / 2, (W + pw) / 2
        y0, y1 = 12, 80
        rr(c, x0, y0, x1, y1, 30, fill=SURF, outline="")
        cy = (y0 + y1) / 2

        # ruta: inicio ⇄ fin
        cx = x0 + 22
        for which, label, val, col in (("src", "INICIO", self.src, ACCENT),
                                       ("dst", "FIN", self.dst, INK)):
            tag = f"sel_{which}"
            self._btn(c, cx, cy - 25, cx + 98, cy + 25, tag,
                      lambda w=which, xx=cx: self.open_picker(w, xx, y0),
                      fill=CARD, hover=PALE, r=16)
            c.create_oval(cx + 13, cy - 14, cx + 20, cy - 7, fill=col, outline="",
                          tags=(tag,))
            c.create_text(cx + 26, cy - 11, text=label, anchor="w", fill=MUTED,
                          font=(FONT, 7, "bold"), tags=(tag,))
            c.create_text(cx + 13, cy + 9, text=str(val), anchor="w", fill=INK,
                          font=(FONT, 15, "bold"), tags=(tag,))
            c.create_text(cx + 84, cy + 9, text="▾", fill=MUTED, font=(FONT, 9),
                          tags=(tag,))
            cx += 98
            if which == "src":
                self._btn(c, cx + 8, cy - 14, cx + 36, cy + 14, "swap", self.swap,
                          fill=SURF, hover=PALE, r=14)
                c.create_text(cx + 22, cy, text="⇄", fill=MUTED, font=(FONT, 11),
                              tags=("swap",))
                cx += 44
        c.create_line(cx + 18, cy - 20, cx + 18, cy + 20, fill=LINE)

        # transporte
        tx = cx + 38
        for kind, cmd, w in (("first", self.reset, 36), ("prev", self.prev, 36),
                             ("play", self.toggle_play, 48), ("next", self.next, 36),
                             ("last", self.to_end, 36)):
            tag = f"b_{kind}"
            if kind == "play":
                self._btn(c, tx, cy - 24, tx + w, cy + 24, tag, cmd, fill=ACCENT,
                          hover=ACCENT_D, r=24)
                self._icon(c, "pause" if self.playing else "play", tx + w / 2, cy, 17,
                           "white", tag)
            else:
                self._btn(c, tx, cy - 18, tx + w, cy + 18, tag, cmd, fill=SURF,
                          hover=PALE, r=18)
                self._icon(c, kind, tx + w / 2, cy, 13, INK, tag)
            tx += w + 6
        c.create_line(tx + 12, cy - 20, tx + 12, cy + 20, fill=LINE)

        # velocidad
        sx0 = tx + 34
        c.create_text(sx0, cy, text="velocidad", anchor="w", fill=MUTED, font=(FONT, 9))
        s0, s1 = sx0 + 68, sx0 + 68 + 120
        frac = 1 - (self.interval - 60) / (1100 - 60)
        c.create_line(s0, cy, s1, cy, fill=LINE, width=4, capstyle="round")
        c.create_line(s0, cy, s0 + (s1 - s0) * frac, cy, fill=ACCENT, width=4,
                      capstyle="round")
        kx = s0 + (s1 - s0) * frac
        c.create_oval(kx - 7, cy - 7, kx + 7, cy + 7, fill=SURF, outline=ACCENT, width=3,
                      tags=("slider",))
        c.create_rectangle(s0 - 8, cy - 14, s1 + 8, cy + 14, fill="", outline="",
                           tags=("slider",))

        def drag(e):
            f = max(0.0, min(1.0, (e.x - s0) / (s1 - s0)))
            self.interval = 1100 - f * (1100 - 60)
            self.draw_dock()
        c.tag_bind("slider", "<Button-1>", drag)
        c.tag_bind("slider", "<B1-Motion>", drag)

        # interruptor «detener al llegar» (solo para algoritmos que lo admiten)
        if self.algo.SUPPORTS_STOP:
            lab = "Detener al llegar"
            lw = self.f_leg.measure(lab)
            ex = x1 - 24 - lw - 50
            on = self.stop
            rr(c, ex, cy - 10, ex + 36, cy + 10, 10, fill=ACCENT if on else DIM,
               outline="", tags=("sw",))
            kx = ex + 26 if on else ex + 10
            c.create_oval(kx - 7, cy - 7, kx + 7, cy + 7, fill="white", outline="",
                          tags=("sw",))
            c.create_text(ex + 48, cy, text=lab, anchor="w", fill=INK, font=(FONT, 9),
                          tags=("sw",))
            c.tag_bind("sw", "<Button-1>", lambda e: self.toggle_stop())
            c.tag_bind("sw", "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind("sw", "<Leave>", lambda e: c.config(cursor=""))
        else:
            c.create_text(x1 - 28, cy, text="calcula todos los pares", anchor="e",
                          fill=MUTED, font=(FONT, 9))

    # ---------- pestaña Pasos ----------
    def update_log(self):
        t = self.log
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", f"{self.algo.NAME}   ·   inicio {self.src}  →  fin {self.dst}\n\n", "big")
        for n, f in enumerate(self.frames[:self.k + 1], 1):
            if f["kind"] in HEADER_KINDS:
                t.insert("end", f"{n:>3}  ", "num")
                t.insert("end", f["msg"] + "\n", "visit")
                lines = f.get("lines", [])
                for msg, ok in lines[:80]:
                    t.insert("end", f"       {msg}\n", "ok" if ok else "no")
                if len(lines) > 80:
                    t.insert("end", f"       … y {len(lines) - 80} mejoras más\n", "head")
            else:
                t.insert("end", f"{n:>3}  ", "num")
                t.insert("end", "     " + f["msg"] + "\n", "ok" if f["ok"] else "no")
        if self.done:
            if self.path:
                t.insert("end", "\nCamino más corto:  "
                         + "  →  ".join(str(NODES[i]) for i in self.path)
                         + f"     (distancia {self.total})\n", "end")
            t.insert("end", f"Pasos totales: {len(self.frames)}\n", "head")
        t.see("end")
        t.config(state="disabled")


if __name__ == "__main__":
    App().mainloop()