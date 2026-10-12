"""Arma el video del proyecto a partir del guion aprobado (video/guion.md).

Uso (desde la raíz, con el entorno bbc-ir y ffmpeg instalado):
    python src/video/voz.py                  # narración -> video/audio/
    python src/video/render.py --fotogramas  # un fotograma por escena -> video/salida/fotogramas/
    python src/video/render.py               # video completo -> video/salida/bbc_news_ir.mp4

Todas las cifras se leen de reports/ y data/processed/ al momento de renderizar;
los rankings de la escena 7 salen de ejecutar src/buscar.py. Nada va escrito a mano.
"""
import argparse
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "src" / "video"))

VIDEO = RAIZ / "video"
SALIDA = VIDEO / "salida"
TMP = VIDEO / "_tmp"
W, H, FPS = 1920, 1080, 30
MX = 120                      # margen lateral
ENTRADA, COLA = 0.3, 0.4      # silencio antes y después de cada narración
CREDITOS_S = 4.5
EQUIPO = "Datisa"            # nombre que firma el video (la materia se toma de la presentación)

FUENTES = Path("/System/Library/Fonts/Supplemental")
TTF = {
    "titulo": FUENTES / "Georgia Bold.ttf",
    "cuerpo": FUENTES / "Arial.ttf",
    "negrita": FUENTES / "Arial Bold.ttf",
    "mono": FUENTES / "Courier New Bold.ttf",
}
NOMBRE = {"w2v": "Word2Vec", "svd": "SVD", "lda": "LDA", "bm25": "BM25", "tfidf": "TF-IDF", "count": "Conteo"}
CATEGORIA = {"sport": "Deporte", "business": "Negocios", "politics": "Política",
             "tech": "Tecnología", "entertainment": "Entretenimiento"}
ARCHIVO = {  # clip, inicio (s), duración (s), filtro de encuadre
    1: ("lvrj_press/clip.webm", 0.0, 12.0, "fps=30,scale=1920:1080"),
    6: ("tidningstryck_1937/clip.ogv", 66.0, 10.0, "fps=30,scale=1920:-2,crop=1920:1080"),
    10: ("tidningstryck_1937/clip.ogv", 88.0, 12.0, "fps=30,scale=1920:-2,crop=1920:1080"),
}


# ---------------------------------------------------------------- datos reales
def cargar_datos() -> dict:
    from buscar import buscar

    rep = RAIZ / "reports"
    estilo = json.loads((RAIZ / "presentacion" / "estilo.json").read_text(encoding="utf-8"))
    portada = json.loads((RAIZ / "presentacion" / "slides.json").read_text(encoding="utf-8"))[0]
    raw = json.loads((rep / "eda_raw.json").read_text())
    limp = json.loads((rep / "limpieza.json").read_text())
    corp = json.loads((rep / "eda_corpus.json").read_text())
    evalu = json.loads((rep / "evaluacion.json").read_text())
    met = pd.read_csv(rep / "metricas.csv")
    por_consulta = pd.read_csv(rep / "metricas_por_consulta.csv")
    consultas = pd.read_csv(RAIZ / "data" / "processed" / "consultas.csv")

    q = consultas[consultas.query_id == "auto_023"].iloc[0]
    tops, ap = {}, {}
    for m in ("bm25", "w2v"):
        r = buscar(q["query"], m, 6)
        tops[m] = r[r.doc_id != q["doc_origen"]].head(5)[["category", "titulo"]].to_dict("records")
        ap[m] = float(por_consulta[(por_consulta.query_id == "auto_023") & (por_consulta.metodo == m)].ap_at_10.iloc[0])
    comp = evalu["comparaciones_pareadas_map"]["w2v-svd"]
    return {
        "pal": estilo["paleta"], "cat": estilo["categorias"], "portada": portada,
        "n_docs": raw["n_docs"], "conteo_cat": raw["conteo_categorias"],
        "duplicados": limp["duplicados"], "n_limpio": limp["n_despues"],
        "heaps_K": corp["heaps_K"], "heaps_beta": corp["heaps_beta"], "N": corp["N"],
        "n_consultas": evalu["n_consultas"], "n_auto": int((consultas.tipo == "auto").sum()),
        "n_metodos": met.metodo.nunique(),
        "map_manual": met[met.tipo == "manual"].set_index("metodo").map_at_10.sort_values(ascending=False),
        "map_total": met[met.tipo == "total"].set_index("metodo").map_at_10.sort_values(ascending=False),
        "consulta": q["query"], "tops": tops, "ap": ap,
        "dif": comp["dif_media_map"] * 100, "ic": [v * 100 for v in comp["ic95"]],
    }


# ------------------------------------------------------------------ utilidades
@lru_cache(maxsize=None)
def fuente(tipo: str, px: int):
    return ImageFont.truetype(str(TTF[tipo]), px)


def rgb(hexa: str):
    hexa = hexa.lstrip("#")
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def tramo(t, a, b):
    """Progreso suavizado 0..1 de t entre los instantes a y b."""
    if b <= a:
        return 1.0 if t >= a else 0.0
    x = min(1.0, max(0.0, (t - a) / (b - a)))
    return 1 - (1 - x) ** 3


def pct(v):
    return f"{v * 100:.2f}%"


class Lienzo:
    """Capa RGBA sobre la que dibuja cada escena; el alfa hace las entradas suaves."""

    def __init__(self, pal):
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.pal = pal

    def color(self, c, a=1.0):
        base = rgb(self.pal[c]) if c in self.pal else rgb(c)
        return base + (int(255 * min(1.0, max(0.0, a))),)

    def texto(self, xy, s, tipo, px, c, a=1.0, ancla="la", sube=0):
        if a <= 0:
            return
        x, y = xy
        self.d.text((x, y + sube * (1 - a)), s, font=fuente(tipo, px), fill=self.color(c, a), anchor=ancla)

    def ancho(self, s, tipo, px):
        return self.d.textlength(s, font=fuente(tipo, px))

    def caja(self, xyxy, c, a=1.0, r=0, borde=None, grosor=2):
        if a <= 0:
            return
        self.d.rounded_rectangle(xyxy, radius=r, fill=self.color(c, a) if c else None,
                                 outline=self.color(borde, a) if borde else None, width=grosor)

    def linea(self, puntos, c, grosor, a=1.0):
        if a > 0 and len(puntos) > 1:
            self.d.line(puntos, fill=self.color(c, a), width=grosor, joint="curve")


def partir(lz, s, tipo, px, ancho_max):
    lineas, actual = [], ""
    for palabra in s.split():
        prueba = f"{actual} {palabra}".strip()
        if lz.ancho(prueba, tipo, px) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    return lineas + [actual]


def recortar(lz, s, tipo, px, ancho_max):
    if lz.ancho(s, tipo, px) <= ancho_max:
        return s
    while s and lz.ancho(s + "…", tipo, px) > ancho_max:
        s = s[:-1]
    return s.rstrip() + "…"


# --------------------------------------------------------------------- escenas
def e1(lz, t, D, osc):
    n = int(round(D["n_docs"] * tramo(t, 0.5, 3.2)))
    lz.texto((MX, 250), f"{n:,}", "titulo", 300, "acento", tramo(t, 0.3, 0.9))
    lz.texto((MX + 8, 590), "noticias de la BBC", "cuerpo", 58, "fondo", tramo(t, 3.2, 3.9), sube=20)
    x = MX + 8
    for i, (cat, k) in enumerate(sorted(D["conteo_cat"].items(), key=lambda kv: -kv[1])):
        a = tramo(t, 4.2 + 0.25 * i, 4.9 + 0.25 * i)
        etiqueta = f"{CATEGORIA[cat]} {k:,}"
        lz.texto((x, 720), etiqueta, "cuerpo", 34, "neutro", a, sube=14)
        x += lz.ancho(etiqueta, "cuerpo", 34) + 56


def e2(lz, t, D, osc):
    lz.texto((MX, 230), "Necesitas una sola.", "titulo", 76, "tinta", tramo(t, 0.2, 1.0), sube=20)
    a = tramo(t, 1.0, 1.6)
    lz.caja((MX, 450, W - MX, 570), "superficie", a, r=60, borde="neutro", grosor=3)
    q = D["consulta"]
    n = int(len(q) * min(1.0, max(0.0, (t - 1.8) / 4.0)))
    visto = q[:n]
    lz.texto((MX + 60, 510), visto, "mono", 40, "tinta", a, ancla="lm")
    if n < len(q) or int(t * 2) % 2 == 0:
        cx = MX + 60 + lz.ancho(visto, "mono", 40) + 4
        lz.caja((cx, 484, cx + 4, 536), "acento", a)
    hechas = len(visto.split()) if n else 0
    for i in range(8):
        x0 = MX + 60 + i * 74
        lz.caja((x0, 630, x0 + 54, 646), "acento" if i < hechas else "neutro", a, r=8)
    lz.texto((MX + 60, 680), "ocho palabras de un titular real · consulta auto_023", "cuerpo", 30,
             "tinta_suave", tramo(t, 5.8, 6.6))


def _barras(lz, t, serie, titulo, pie, destacado, t_destacar):
    lz.texto((MX, 150), titulo, "titulo", 60, "tinta", tramo(t, 0.2, 0.9), sube=18)
    x0, ancho_max, y0, alto, paso = 440, 1100, 290, 62, 96
    for i, (m, v) in enumerate(serie.items()):
        y = y0 + i * paso
        p = tramo(t, 0.7 + 0.18 * i, 2.2 + 0.18 * i)
        resaltar = m == destacado and t >= t_destacar
        lz.texto((x0 - 30, y + alto / 2), NOMBRE[m], "negrita" if resaltar else "cuerpo", 36,
                 "tinta", tramo(t, 0.5 + 0.18 * i, 1.1 + 0.18 * i), ancla="rm")
        lz.caja((x0, y, x0 + max(2, ancho_max * v * p), y + alto), "acento" if resaltar else "neutro", 1.0, r=6)
        # la cifra aparece solo cuando la barra llegó a su valor real (nunca porcentajes intermedios)
        lz.texto((x0 + ancho_max * v + 22, y + alto / 2), pct(v), "negrita" if resaltar else "cuerpo", 34,
                 "acento_texto" if resaltar else "tinta_suave", tramo(t, 2.2 + 0.18 * i, 2.6 + 0.18 * i), ancla="lm")
    lz.texto((MX, 875), pie, "cuerpo", 26, "tinta_suave", tramo(t, 2.4, 3.2))


def e3(lz, t, D, osc):
    _barras(lz, t, D["map_manual"], "Con consultas cortas, todos aciertan",
            "MAP@10 en las 15 consultas manuales · reports/metricas.csv", "count", 6.2)


def e4(lz, t, D, osc):
    lz.texto((MX, 180), "Ya hicimos ese recorrido", "titulo", 64, "fondo", tramo(t, 0.2, 1.0), sube=18)
    cifras = [(f"{D['n_metodos']}", "métodos", "fondo", 2.2), (f"{D['n_consultas']}", "consultas", "acento", 3.6),
              (f"{D['n_limpio']:,}", "documentos", "fondo", 5.0)]
    xs = [MX, 620, 1160]
    for (num, etq, c, t0), x in zip(cifras, xs):
        a = tramo(t, t0, t0 + 0.7)
        lz.texto((x, 330), num, "titulo", 200, c, a, sube=30)
        lz.texto((x + 6, 570), etq, "cuerpo", 40, "neutro", a)
    x = MX
    for i, m in enumerate(D["map_total"].index):
        a = tramo(t, 6.4 + 0.15 * i, 7.0 + 0.15 * i)
        ancho = lz.ancho(NOMBRE[m], "cuerpo", 32) + 56
        lz.caja((x, 720, x + ancho, 784), None, a, r=32, borde="neutro", grosor=2)
        lz.texto((x + ancho / 2, 752), NOMBRE[m], "cuerpo", 32, "fondo", a, ancla="mm")
        x += ancho + 24
    lz.texto((MX, 830), "un mismo preprocesamiento para el corpus y para la consulta", "cuerpo", 30,
             "neutro", tramo(t, 7.4, 8.2))


def e5(lz, t, D, osc):
    a = tramo(t, 0.3, 1.0)
    lz.texto((MX, 300), f"{D['n_docs']:,}", "titulo", 130, "neutro", a)
    ancho = lz.ancho(f"{D['n_docs']:,}", "titulo", 130)
    lz.caja((MX - 10, 392, MX - 10 + (ancho + 20) * tramo(t, 1.4, 2.0), 400), "tinta_suave", a)
    lz.texto((MX, 470), f"{D['n_limpio']:,}", "titulo", 130, "tinta", tramo(t, 2.0, 2.8), sube=24)
    lz.texto((MX + 4, 650), f"{D['duplicados']} duplicados fuera", "negrita", 44, "tinta_suave", tramo(t, 2.4, 3.2))
    # Ley de Heaps: curva ajustada V = K * n^beta
    gx0, gx1, gy0, gy1 = 1040, 1780, 800, 330
    ag = tramo(t, 4.2, 4.9)
    lz.linea([(gx0, gy1 - 20), (gx0, gy0), (gx1, gy0)], "neutro", 3, ag)
    lz.texto((gx1, gy0 + 20), "tokens leídos", "cuerpo", 26, "tinta_suave", ag, ancla="ra")
    lz.texto((gx0, gy1 - 62), "palabras distintas", "cuerpo", 26, "tinta_suave", ag)
    vmax = D["heaps_K"] * D["N"] ** D["heaps_beta"]
    p = tramo(t, 4.8, 7.4)
    pts = []
    for i in range(int(120 * p) + 1):
        n = D["N"] * i / 120
        v = D["heaps_K"] * n ** D["heaps_beta"] if n else 0
        pts.append((gx0 + (gx1 - gx0) * i / 120, gy0 - (gy0 - gy1) * v / vmax))
    lz.linea(pts, "acento", 7, 1.0)
    lz.texto((gx0 + 330, 610), f"β = {D['heaps_beta']:.4f}", "titulo", 68, "acento_texto", tramo(t, 6.6, 7.4), sube=18)
    lz.texto((gx0, 875), "Ley de Heaps, curva ajustada · reports/eda_corpus.json", "cuerpo", 26,
             "tinta_suave", tramo(t, 6.9, 7.6))


def e6(lz, t, D, osc):
    lz.texto((MX, 240), f"{D['n_auto']}", "titulo", 320, "acento", tramo(t, 1.6, 2.4), sube=30)
    lz.texto((MX + 8, 600), "titulares de 8 palabras", "cuerpo", 60, "fondo", tramo(t, 2.6, 3.4), sube=18)
    lz.texto((MX + 8, 700), "sin el documento del que salieron", "cuerpo", 44, "neutro", tramo(t, 4.6, 5.4), sube=14)


def e7(lz, t, D, osc):
    a = tramo(t, 0.2, 0.9)
    lz.caja((MX, 110, W - MX, 190), "superficie", a, r=40, borde="neutro", grosor=3)
    lz.texto((MX + 44, 150), D["consulta"], "mono", 32, "tinta", a, ancla="lm")
    columnas = [("bm25", MX, 1.4, 9.0), ("w2v", 990, 6.8, 10.2)]
    for m, x, t0, t_ap in columnas:
        gana = m == "w2v"
        lz.texto((x, 235), NOMBRE[m], "titulo", 50, "tinta", tramo(t, t0 - 0.4, t0 + 0.2))
        for i, fila in enumerate(D["tops"][m]):
            y = 330 + i * 96
            af = tramo(t, t0 + 0.3 * i, t0 + 0.3 * i + 0.5)
            lz.caja((x, y, x + 810, y + 80), "superficie", af, r=12, borde="neutro", grosor=2)
            lz.texto((x + 34, y + 40), str(i + 1), "titulo", 34, "tinta_suave", af, ancla="mm")
            lz.caja((x + 70, y + 16, x + 84, y + 30), D["cat"][fila["category"]], af)
            lz.texto((x + 94, y + 23), CATEGORIA[fila["category"]], "negrita", 20, "tinta_suave", af, ancla="lm")
            lz.texto((x + 70, y + 56), recortar(lz, fila["titulo"], "cuerpo", 28, 720), "cuerpo", 28, "tinta", af,
                     ancla="lm")
        lz.texto((x, 828), f"AP@10 = {D['ap'][m]:.2f}", "titulo", 54, "acento_texto" if gana else "tinta_suave",
                 tramo(t, t_ap, t_ap + 0.7), sube=16)


def e8(lz, t, D, osc):
    _barras(lz, t, D["map_total"], f"MAP@10 en las {D['n_consultas']} consultas",
            "Relevante = misma categoría que la consulta · reports/metricas.csv", "w2v", 0.0)


def e9(lz, t, D, osc):
    lz.texto((MX, 170), "Relevante = misma categoría", "titulo", 70, "fondo", tramo(t, 1.2, 2.0), sube=18)
    a = tramo(t, 4.6, 5.4)
    lz.texto((MX, 400), f"Word2Vec − SVD: +{D['dif']:.2f} puntos de MAP@10", "cuerpo", 40, "fondo", a)
    x0, x1, y = 300, 1620, 600
    lo, hi = -2.0, 10.0
    px = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    lz.linea([(x0, y), (x1, y)], "tinta_suave", 3, a)
    lz.linea([(px(0), y - 70), (px(0), y + 70)], "neutro", 3, a)
    lz.texto((px(0), y + 84), "0", "cuerpo", 30, "neutro", a, ancla="ma")
    p = tramo(t, 5.4, 6.6)
    centro, (ic0, ic1) = D["dif"], D["ic"]
    izq, der = px(centro + (ic0 - centro) * p), px(centro + (ic1 - centro) * p)
    lz.caja((izq, y - 9, der, y + 9), "acento", a, r=9)
    lz.caja((izq - 4, y - 30, izq + 4, y + 30), "acento", a)
    lz.caja((der - 4, y - 30, der + 4, y + 30), "acento", a)
    lz.d.ellipse((px(centro) - 16, y - 16, px(centro) + 16, y + 16), fill=lz.color("fondo", a))
    lz.texto((MX, 730), f"IC 95% [{ic0:.2f}, {ic1:.2f}]", "titulo", 56, "acento", tramo(t, 6.4, 7.2), sube=16)
    lz.texto((MX, 820), "incluye el 0: no declaramos ganador", "cuerpo", 36, "neutro", tramo(t, 7.6, 8.4))


def e10(lz, t, D, osc):
    a = tramo(t, 0.4, 1.3)
    lz.texto((MX, 300), "Buscar ", "titulo", 96, "fondo", a, sube=20)
    lz.texto((MX + lz.ancho("Buscar ", "titulo", 96), 300), "por tema,", "titulo", 96, "acento", a, sube=20)
    lz.texto((MX, 430), "no por palabra exacta.", "titulo", 96, "fondo", tramo(t, 1.2, 2.1), sube=20)
    lz.texto((MX + 4, 640), "Representación semántica hoy · juicios de relevancia reales mañana", "cuerpo", 38,
             "neutro", tramo(t, 4.0, 4.9))


def creditos(lz, t, D, osc):
    p = D["portada"]
    a = tramo(t, 0.2, 0.9)
    lz.texto((MX, 250), "Recuperación de información en BBC News", "titulo", 68, "fondo", a)
    lz.texto((MX, 370), f"{EQUIPO} · {p['materia']}", "cuerpo", 38, "neutro", a)
    lz.texto((MX, 560), f"Cifras tomadas de reports/ del proyecto. Evaluación con {D['n_consultas']} consultas; "
             "relevante = misma categoría.", "cuerpo", 28, "neutro", a)
    lz.texto((MX, 620), "Imágenes de archivo: AB Svensk Filmindustri, 1937 (dominio público) · "
             "Harrison Keely (CC BY 4.0), vía Wikimedia Commons.", "cuerpo", 28, "neutro", a)
    motor = VIDEO / "audio" / "motor.json"
    eleven = motor.exists() and json.loads(motor.read_text())["motor"] == "elevenlabs"
    lz.texto((MX, 680), "Narración con voz sintética de ElevenLabs (elevenlabs.io)." if eleven
             else "Narración con voz sintética.", "cuerpo", 28, "neutro", a)


ESCENAS = {1: (e1, True), 2: (e2, False), 3: (e3, False), 4: (e4, True), 5: (e5, False),
           6: (e6, True), 7: (e7, False), 8: (e8, False), 9: (e9, True), 10: (e10, True)}


# ------------------------------------------------------------------ ensamblado
def linea_de_tiempo():
    guion = json.loads((VIDEO / "escenas.json").read_text(encoding="utf-8"))
    dur = json.loads((VIDEO / "audio" / "duraciones.json").read_text())
    inicio, pistas = 0.0, []
    for e in guion:
        d = ENTRADA + dur[str(e["n"])] + COLA
        pistas.append({**e, "inicio": inicio, "dur": d})
        inicio += d
    pistas.append({"n": 0, "bloque": "", "paso": "", "narracion": "", "inicio": inicio, "dur": CREDITOS_S})
    return pistas, inicio + CREDITOS_S


def extraer_archivo():
    for n, (clip, ss, dur, filtro) in ARCHIVO.items():
        destino = TMP / f"escena_{n:02d}"
        if destino.exists() and any(destino.iterdir()):
            continue
        destino.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur), "-i",
                        str(VIDEO / "archivo" / clip), "-vf", filtro, "-q:v", "3",
                        str(destino / "%05d.jpg")], check=True)


@lru_cache(maxsize=4)
def _cuadros(n):
    return sorted((TMP / f"escena_{n:02d}").glob("*.jpg"))


def fondo(n, t, D, oscuro):
    pal = D["pal"]
    if n in ARCHIVO:
        cuadros = _cuadros(n)
        img = Image.open(cuadros[min(len(cuadros) - 1, int(t * FPS))]).convert("RGB")
        return Image.blend(img, Image.new("RGB", (W, H), rgb(pal["fondo_oscuro"])), 0.74)
    return Image.new("RGB", (W, H), rgb(pal["fondo_oscuro" if oscuro else "fondo"]))


def cuadro(pista, t, t_global, total, D):
    n = pista["n"]
    dibujar, oscuro = ESCENAS.get(n, (creditos, True))
    base = fondo(n, t, D, oscuro).convert("RGBA")
    lz = Lienzo(D["pal"])
    dibujar(lz, t, D, oscuro)
    if n:
        a = tramo(t, 0.0, 0.5)
        lz.texto((MX, 56), f"{n:02d}", "negrita", 24, "acento" if oscuro else "acento_texto", a)
        lz.texto((MX + 48, 56), f"{pista['bloque'].upper()}  ·  {pista['paso']}", "cuerpo", 24,
                 "neutro" if oscuro else "tinta_suave", a)
        lineas = partir(lz, pista["narracion"], "cuerpo", 30, 1480)
        for i, s in enumerate(lineas):
            lz.texto((W / 2, 975 + i * 42 - 21 * (len(lineas) - 1)), s, "cuerpo", 30,
                     "fondo" if oscuro else "tinta_suave", a, ancla="mm")
    lz.caja((0, H - 6, W * t_global / total, H), "acento")
    base.alpha_composite(lz.img)
    # fundido corto entre escenas
    f = min(1.0, t / 0.25, (pista["dur"] - t) / 0.25) if n else min(1.0, t / 0.4)
    if f < 1.0:
        color = rgb(D["pal"]["fondo_oscuro" if oscuro else "fondo"])
        base = Image.blend(Image.new("RGBA", (W, H), color + (255,)), base, max(0.0, f))
    return base.convert("RGB")


def fotogramas(pistas, total, D):
    destino = SALIDA / "fotogramas"
    destino.mkdir(parents=True, exist_ok=True)
    minis = []
    for p in pistas:
        img = cuadro(p, p["dur"] - 0.6, p["inicio"] + p["dur"] - 0.6, total, D)
        nombre = f"escena_{p['n']:02d}.png" if p["n"] else "creditos.png"
        img.save(destino / nombre)
        minis.append(img.resize((640, 360), Image.LANCZOS))
    cols = 4
    hoja = Image.new("RGB", (cols * 660 + 20, math.ceil(len(minis) / cols) * 380 + 20), (232, 230, 225))
    for i, m in enumerate(minis):
        hoja.paste(m, (20 + (i % cols) * 660, 20 + (i // cols) * 380))
    hoja.save(destino / "hoja_de_contacto.png")
    print(f"{len(minis)} fotogramas en {destino}")


def video(pistas, total, D):
    SALIDA.mkdir(parents=True, exist_ok=True)
    mudo = TMP / "mudo.mp4"
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(mudo)], stdin=subprocess.PIPE)
    n_total = int(total * FPS)
    for k in range(n_total):
        tg = k / FPS
        p = next(x for x in reversed(pistas) if tg >= x["inicio"])
        ff.stdin.write(cuadro(p, tg - p["inicio"], tg, total, D).tobytes())
        if k % 300 == 0:
            print(f"  {tg:5.1f} / {total:.1f} s", flush=True)
    ff.stdin.close()
    ff.wait()

    voces = [p for p in pistas if p["n"]]
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(mudo)]
    filtros = []
    for i, p in enumerate(voces, start=1):
        cmd += ["-i", str(VIDEO / "audio" / f"escena_{p['n']:02d}.mp3")]
        ms = int((p["inicio"] + ENTRADA) * 1000)
        filtros.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
    mezcla = "".join(f"[a{i}]" for i in range(1, len(voces) + 1))
    filtros.append(f"{mezcla}amix=inputs={len(voces)}:normalize=0,apad[voz]")
    final = SALIDA / "bbc_news_ir.mp4"
    cmd += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[voz]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}", "-movflags", "+faststart", str(final)]
    subprocess.run(cmd, check=True)
    print(f"Video: {final} ({total:.1f} s)")


def main():
    ap = argparse.ArgumentParser(description="Arma el video del proyecto BBC News IR")
    ap.add_argument("--fotogramas", action="store_true", help="solo un fotograma por escena y hoja de contacto")
    ap.add_argument("--audio-externo", action="store_true",
                    help="los MP3 de video/audio/ se generaron a mano (web de ElevenLabs): recalcula duraciones")
    args = ap.parse_args()
    if args.audio_externo:
        from voz import AUDIO, duracion
        n_escenas = len(json.loads((VIDEO / "escenas.json").read_text(encoding="utf-8")))
        dur = {str(n): round(duracion(AUDIO / f"escena_{n:02d}.mp3"), 2) for n in range(1, n_escenas + 1)}
        (AUDIO / "duraciones.json").write_text(json.dumps(dur, indent=2), encoding="utf-8")
        (AUDIO / "motor.json").write_text(json.dumps({"motor": "elevenlabs", "voz": "web"}, indent=2), encoding="utf-8")
    D = cargar_datos()
    pistas, total = linea_de_tiempo()
    extraer_archivo()
    if args.fotogramas:
        fotogramas(pistas, total, D)
    else:
        video(pistas, total, D)


if __name__ == "__main__":
    main()
