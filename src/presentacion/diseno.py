"""Sistema de diseno propio de la presentacion (sin plantilla).

Constantes (lienzo, paleta, categorias, tipografia, layouts), retícula de 12 columnas,
utilidades de fuentes/medicion de texto con Pillow y contraste WCAG.
`python src/presentacion/diseno.py` escribe presentacion/estilo.json.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

RAIZ = Path(__file__).resolve().parents[2]
DIR_PRES = RAIZ / "presentacion"
DIR_FIG = DIR_PRES / "figuras"
DIR_SALIDA = DIR_PRES / "salida"
DIR_PREVIEW = DIR_SALIDA / "preview"
RUTA_ESTILO = DIR_PRES / "estilo.json"
RUTA_SLIDES = DIR_PRES / "slides.json"
RUTA_PPTX = DIR_SALIDA / "presentacion_final.pptx"
RUTA_CAJAS = DIR_SALIDA / "cajas.json"

# ---------------------------------------------------------------- lienzo y retícula
ANCHO, ALTO = 13.333, 7.5          # pulgadas, 16:9
MARGEN_X, MARGEN_Y = 0.6, 0.5
COLUMNAS, MEDIANIL = 12, 0.2
ANCHO_COL = (ANCHO - 2 * MARGEN_X - (COLUMNAS - 1) * MEDIANIL) / COLUMNAS
INSET = 0.1                        # margen interno de las cajas de texto
ALTO_PIE = 0.4                     # caja del pie / numero de diapositiva
Y_PIE = ALTO - MARGEN_Y - ALTO_PIE # 6.6
Y_TITULO = MARGEN_Y
Y_MAX_CONTENIDO = Y_PIE - 0.1      # limite inferior del contenido


def col_x(c: int) -> float:
    """Borde izquierdo de la columna c (1..12)."""
    return MARGEN_X + (c - 1) * (ANCHO_COL + MEDIANIL)


def span(c1: int, c2: int) -> float:
    """Ancho que ocupan las columnas c1..c2 (incluidas)."""
    n = c2 - c1 + 1
    return n * ANCHO_COL + (n - 1) * MEDIANIL


# ---------------------------------------------------------------- paleta
PALETA = {
    "fondo": "#F6F4EF",
    "fondo_oscuro": "#14213D",
    "tinta": "#1B1F24",
    "tinta_suave": "#5C6370",
    "acento": "#E07A1F",
    "acento_2": "#2A9D8F",
    "neutro": "#C9CCD1",
    # Ampliaciones documentadas (la paleta de la skill no cumple 4.5:1 con acento sobre fondo claro):
    "acento_texto": "#B05400",   # acento oscurecido, SOLO para texto sobre fondo claro (4.64:1)
    "superficie": "#FFFFFF",     # tarjetas sobre el fondo claro
    "acento_suave": "#FBE9D7",   # relleno tenue del marcador del paso clave
}
CATEGORIAS = {
    "business": "#14213D",
    "entertainment": "#E07A1F",
    "politics": "#2A9D8F",
    "sport": "#8E5572",
    "tech": "#6C8EAD",
}
NOMBRE_CATEGORIA = {"business": "Negocios", "entertainment": "Entretenimiento",
                    "politics": "Política", "sport": "Deporte", "tech": "Tecnología"}

# ---------------------------------------------------------------- tipografía
FUENTE_TITULO, FUENTE_CUERPO = "Georgia", "Calibri"
TIPOGRAFIA = {
    "titulo": FUENTE_TITULO, "cuerpo": FUENTE_CUERPO,
    "escala": {
        "titulo_portada": {"fuente": FUENTE_TITULO, "negrita": True, "pt": 44},
        "titulo": {"fuente": FUENTE_TITULO, "negrita": True, "pt": 30},
        "cifra": {"fuente": FUENTE_TITULO, "negrita": True, "pt": 110, "color": "acento"},
        "texto": {"fuente": FUENTE_CUERPO, "negrita": False, "pt": 20},
        "etiqueta": {"fuente": FUENTE_CUERPO, "negrita": False, "pt": 12, "color": "tinta_suave"},
        "minimo": {"pt": 12},
    },
}
PT_PORTADA, PT_TITULO, PT_CIFRA, PT_TEXTO, PT_ETIQUETA = 44, 30, 110, 20, 12
INTERLINEADO = 1.2   # factor usado por la revision (lineas x tamano x 1.2)

LAYOUTS = {
    "portada": "Fondo oscuro. Título 44 pt en columnas 1-9, subtítulo, equipo/materia/fecha a 12 pt; marcador de icono grande en columnas 10-12.",
    "seccion": "Fondo oscuro. Número de sección grande en acento + nombre de la sección.",
    "cifra_grande": "Título arriba; cifra de 110 pt en columnas 1-6 centrada verticalmente; frase de apoyo (máx. 20 palabras) en columnas 7-12.",
    "grafica": "Título arriba; gráfica en columnas 1-8; mensaje clave de 20 pt (máx. 25 palabras) en columnas 9-12; pie de fuente opcional.",
    "grafica_completa": "Título arriba; gráfica a todo el ancho útil; pie de fuente de 12 pt.",
    "bloques": "2 a 4 bloques en fila: marcador de icono (o imagen) + nombre 20 pt bold + frase (máx. 15 palabras).",
    "flujo": "Pasos en fila unidos por flechas RIGHT_ARROW en neutro; marcador de icono + etiqueta; el paso clave en acento.",
    "demo": "Barra de búsqueda (22 pt) y top-3 como tarjetas con rango, categoría y título.",
    "cierre": "Fondo oscuro. Frase de conclusión y recomendación.",
}


# ---------------------------------------------------------------- fuentes
def _buscar_fuente(nombres_sistema: list[str], familia_mpl: str, negrita: bool) -> str:
    for ruta in nombres_sistema:
        if Path(ruta).exists():
            return ruta
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager as fm
    return fm.findfont(fm.FontProperties(family=familia_mpl, weight="bold" if negrita else "normal"))


_SUP = "/System/Library/Fonts/Supplemental/"
_FUENTES = {
    ("Georgia", True): ([_SUP + "Georgia Bold.ttf"], "DejaVu Serif"),
    ("Georgia", False): ([_SUP + "Georgia.ttf"], "DejaVu Serif"),
    # Calibri no esta instalada en este equipo: respaldo DejaVu Sans (mas ancha que Calibri, es conservador).
    ("Calibri", True): ([_SUP + "Calibri Bold.ttf", "/Library/Fonts/Calibri Bold.ttf", "/Library/Fonts/Microsoft/Calibri Bold.ttf"], "DejaVu Sans"),
    ("Calibri", False): ([_SUP + "Calibri.ttf", "/Library/Fonts/Calibri.ttf", "/Library/Fonts/Microsoft/Calibri.ttf"], "DejaVu Sans"),
}


def ruta_fuente(familia: str, negrita: bool = False) -> str:
    nombres, resp = _FUENTES[(familia, bool(negrita))]
    return _buscar_fuente(nombres, resp, negrita)


def fuente_es_respaldo(familia: str) -> bool:
    return "DejaVu" in Path(ruta_fuente(familia, False)).name


@lru_cache(maxsize=256)
def _font(ruta: str, tam10: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(ruta, tam10)


def ancho_texto(texto: str, familia: str, negrita: bool, pt: float) -> float:
    """Ancho en puntos tipograficos (1 pt = 1/72 in)."""
    f = _font(ruta_fuente(familia, negrita), max(1, round(pt * 10)))
    return f.getlength(texto) / 10.0


def partir_lineas(texto: str, familia: str, negrita: bool, pt: float, ancho_pt: float) -> list[str]:
    """Ajuste de lineas voraz por palabras (respeta saltos de linea explicitos)."""
    lineas: list[str] = []
    for parrafo in texto.split("\n"):
        actual = ""
        for palabra in parrafo.split(" "):
            prueba = palabra if not actual else actual + " " + palabra
            if actual and ancho_texto(prueba, familia, negrita, pt) > ancho_pt:
                lineas.append(actual)
                actual = palabra
            else:
                actual = prueba
        lineas.append(actual)
    return lineas


def max_palabra(texto: str, familia: str, negrita: bool, pt: float) -> float:
    return max((ancho_texto(p, familia, negrita, pt) for p in texto.split()), default=0.0)


# ---------------------------------------------------------------- contraste WCAG
def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(hexcolor: str) -> float:
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contraste(a: str, b: str) -> float:
    la, lb = luminancia(a), luminancia(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def rgb(hexcolor: str) -> tuple[int, int, int]:
    h = hexcolor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# ---------------------------------------------------------------- estilo.json
def estilo_dict() -> dict:
    return {
        "lienzo": {"ancho_in": ANCHO, "alto_in": ALTO, "relacion": "16:9", "margen_x_in": MARGEN_X,
                   "margen_y_in": MARGEN_Y, "columnas": COLUMNAS, "medianil_in": MEDIANIL,
                   "ancho_columna_in": round(ANCHO_COL, 4), "inset_texto_in": INSET},
        "paleta": PALETA,
        "categorias": CATEGORIAS,
        "tipografia": TIPOGRAFIA,
        "layouts": LAYOUTS,
        "notas": {
            "ampliaciones_paleta": "acento_texto (#B05400) para texto sobre fondo claro porque acento (#E07A1F) da 2.74:1 sobre fondo; "
                                   "superficie (#FFFFFF) para tarjetas; acento_suave para el marcador del paso clave. "
                                   "Sobre fondo oscuro se usa acento tal cual (5.30:1).",
            "fuentes": "El .pptx declara Georgia y Calibri; en este equipo Calibri no esta instalada y las vistas previas/metricas usan DejaVu Sans.",
            "marcadores_icono": "Texto de 12 pt (minimo absoluto) en lugar de los 10 pt que menciona la skill.",
        },
    }


def guardar_estilo() -> None:
    RUTA_ESTILO.parent.mkdir(parents=True, exist_ok=True)
    RUTA_ESTILO.write_text(json.dumps(estilo_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    guardar_estilo()
    print("escrito", RUTA_ESTILO)
