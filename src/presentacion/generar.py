"""Genera presentacion/salida/presentacion_final.pptx, las vistas previas y la lista de cajas.

Orden de ejecucion completo (desde la raiz del repo, con el entorno conda bbc-ir):
    conda run -n bbc-ir python src/presentacion/diseno.py      # estilo.json
    conda run -n bbc-ir python src/presentacion/graficas.py    # presentacion/figuras/*.png
    conda run -n bbc-ir python src/presentacion/generar.py     # .pptx + preview/ + cajas.json
    conda run -n bbc-ir python src/presentacion/revisar.py     # revision_automatica.json
(`generar.py` ya llama a diseno.guardar_estilo(); las graficas solo hay que rehacerlas si cambian los reportes.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu

from presentacion import diseno as D
from presentacion import layouts as L

PX_IN = 120            # 1600 px / 13.333 in
SS = 2                 # supermuestreo para suavizar formas


# ------------------------------------------------------------------ tema propio (no el "Office" por defecto)
def _aplicar_tema(prs) -> None:
    parte = prs.slide_master.part.part_related_by(RT.THEME)
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    raiz = etree.fromstring(parte.blob)
    raiz.set("name", "BBC IR")
    P = D.PALETA
    esquema = {"dk1": P["tinta"], "lt1": P["superficie"], "dk2": P["fondo_oscuro"], "lt2": P["fondo"],
               "accent1": P["acento"], "accent2": P["acento_2"], "accent3": D.CATEGORIAS["sport"],
               "accent4": D.CATEGORIAS["tech"], "accent5": P["tinta_suave"], "accent6": P["neutro"],
               "hlink": P["acento_texto"], "folHlink": P["tinta_suave"]}
    clr = raiz.find(".//a:clrScheme", ns)
    clr.set("name", "BBC IR")
    for nombre, hexa in esquema.items():
        el = clr.find(f"a:{nombre}", ns)
        for hijo in list(el):
            el.remove(hijo)
        etree.SubElement(el, "{%s}srgbClr" % ns["a"]).set("val", hexa.lstrip("#"))
    fonts = raiz.find(".//a:fontScheme", ns)
    fonts.set("name", "BBC IR")
    fonts.find("a:majorFont/a:latin", ns).set("typeface", D.FUENTE_TITULO)
    fonts.find("a:minorFont/a:latin", ns).set("typeface", D.FUENTE_CUERPO)
    parte._blob = etree.tostring(raiz, xml_declaration=True, encoding="UTF-8", standalone=True)


# ------------------------------------------------------------------ vista previa con Pillow
def _envolver(runs, familia, negrita, pt, ancho_pt):
    """Ajuste de lineas por palabras conservando el color de cada palabra."""
    palabras_par: list[list[tuple[str, str]]] = [[]]
    for txt, col in runs:
        for i, parte in enumerate(txt.split("\n")):
            if i > 0:
                palabras_par.append([])
            palabras_par[-1] += [(w, col) for w in parte.split(" ") if w]
    lineas = []
    for palabras in palabras_par:
        actual: list[tuple[str, str]] = []
        for w, col in palabras:
            prueba = " ".join(x for x, _ in actual + [(w, col)])
            if actual and D.ancho_texto(prueba, familia, negrita, pt) > ancho_pt:
                lineas.append(actual)
                actual = [(w, col)]
            else:
                actual.append((w, col))
        lineas.append(actual)
    return lineas


def _trazo_redondeado(x, y, w, h, r, paso=2.0):
    import math
    r = min(r, w / 2, h / 2)
    pts = []
    def arco(cx, cy, a0, a1):
        n = max(4, int(r * math.pi / 2 / paso))
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    arco(x + w - r, y + r, -90, 0)
    arco(x + w - r, y + h - r, 0, 90)
    arco(x + r, y + h - r, 90, 180)
    arco(x + r, y + r, 180, 270)
    pts.append(pts[0])
    return pts


def _dash(draw, pts, color, ancho, on=16, off=10):
    import math
    acum, dibujar_ = 0.0, True
    seg = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        pos = 0.0
        while pos < d:
            lim = on if dibujar_ else off
            tomar = min(lim - acum, d - pos)
            xa, ya = x0 + (x1 - x0) * pos / d, y0 + (y1 - y0) * pos / d
            xb, yb = x0 + (x1 - x0) * (pos + tomar) / d, y0 + (y1 - y0) * (pos + tomar) / d
            if dibujar_:
                draw.line([(xa, ya), (xb, yb)], fill=color, width=ancho)
            acum += tomar
            pos += tomar
            if acum >= lim - 1e-9:
                acum, dibujar_ = 0.0, not dibujar_


def _dibujar_texto(draw, c, s):
    pt = c["tamaño"]
    familia, negrita = c["fuente"], c["negrita"]
    w_pt = (c["w"] - 2 * D.INSET) * 72
    lineas = _envolver(c["runs"], familia, negrita, pt, w_pt)
    ruta = D.ruta_fuente(familia, negrita)
    f = ImageFont.truetype(ruta, max(1, round(pt * s / 72)))
    alto_l = pt * D.INTERLINEADO / 72
    total = len(lineas) * alto_l
    y0 = c["y"] + {"t": D.INSET, "m": (c["h"] - total) / 2, "b": c["h"] - D.INSET - total}[c["ancla"]]
    for i, ln in enumerate(lineas):
        texto = " ".join(w for w, _ in ln)
        ancho_ln = f.getlength(texto) / s
        x0 = c["x"] + D.INSET
        if c["align"] == "c":
            x0 = c["x"] + (c["w"] - ancho_ln) / 2
        elif c["align"] == "r":
            x0 = c["x"] + c["w"] - D.INSET - ancho_ln
        xp = x0 * s
        for k, (w, col) in enumerate(ln):
            draw.text((xp, (y0 + i * alto_l + 0.5 * (alto_l - pt / 72 * 1.17)) * s), w, font=f, fill=D.rgb(col))
            xp += f.getlength(w + (" " if k < len(ln) - 1 else ""))


def dibujar_diapositiva(cajas, ruta_png, ancho=1600, alto=900):
    s = PX_IN * SS
    im = Image.new("RGBA", (round(D.ANCHO * s), round(D.ALTO * s)), D.rgb(cajas[0]["relleno"]) + (255,))
    draw = ImageDraw.Draw(im)
    for c in cajas[1:]:
        t = c["tipo"]
        if t in ("rect", "marcador"):
            x, y, w, h = (c[k] * s for k in ("x", "y", "w", "h"))
            r = c["radio"] * s
            if c.get("relleno"):
                if r:
                    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=D.rgb(c["relleno"]))
                else:
                    draw.rectangle([x, y, x + w, y + h], fill=D.rgb(c["relleno"]))
            if c.get("borde"):
                gr = max(1, round(c["grosor"] / 72 * s))
                if c.get("dash"):
                    _dash(draw, _trazo_redondeado(x, y, w, h, r), D.rgb(c["borde"]), gr)
                elif r:
                    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, outline=D.rgb(c["borde"]), width=gr)
                else:
                    draw.rectangle([x, y, x + w, y + h], outline=D.rgb(c["borde"]), width=gr)
            if c.get("texto"):
                _dibujar_texto(draw, c, s)
        elif t == "flecha":
            x, y, w, h = (c[k] * s for k in ("x", "y", "w", "h"))
            cuerpo = x + w * 0.5
            draw.polygon([(x, y + h * 0.25), (cuerpo, y + h * 0.25), (cuerpo, y), (x + w, y + h / 2), (cuerpo, y + h),
                          (cuerpo, y + h * 0.75), (x, y + h * 0.75)], fill=D.rgb(c["relleno"]))
        elif t == "imagen":
            with Image.open(c["ruta"]) as src:
                src = src.convert("RGBA").resize((round(c["w"] * s), round(c["h"] * s)), Image.LANCZOS)
            capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
            capa.paste(src, (round(c["x"] * s), round(c["y"] * s)))
            im = Image.alpha_composite(im, capa)
            draw = ImageDraw.Draw(im)
        elif t == "texto":
            _dibujar_texto(draw, c, s)
    im = im.convert("RGB").resize((ancho, alto), Image.LANCZOS)
    im.save(ruta_png)
    return im


def hoja_de_contactos(imagenes, ruta, columnas=4, ancho_mini=480):
    alto_mini = round(ancho_mini * 9 / 16)
    gap = 18
    filas = -(-len(imagenes) // columnas)
    W = columnas * ancho_mini + (columnas + 1) * gap
    H = filas * (alto_mini + 24) + (filas + 1) * gap
    hoja = Image.new("RGB", (W, H), (233, 231, 226))
    d = ImageDraw.Draw(hoja)
    f = ImageFont.truetype(D.ruta_fuente("Calibri", False), 16)
    for i, im in enumerate(imagenes):
        r, c = divmod(i, columnas)
        x, y = gap + c * (ancho_mini + gap), gap + r * (alto_mini + 24 + gap)
        hoja.paste(im.resize((ancho_mini, alto_mini), Image.LANCZOS), (x, y))
        d.rectangle([x - 1, y - 1, x + ancho_mini, y + alto_mini], outline=(190, 190, 190))
        d.text((x, y + alto_mini + 3), f"{i + 1}", font=f, fill=(92, 99, 112))
    hoja.save(ruta)


# ------------------------------------------------------------------ verificacion de la demo
def _verificar_demo(d):
    try:
        sys.path.insert(0, str(D.RAIZ / "src"))
        from buscar import buscar
        r = buscar(d["consulta"], d.get("metodo", "w2v"), len(d["resultados"]))
        reales = [(int(x["rank"]), x["doc_id"], x["category"], x["titulo"]) for _, x in r.iterrows()]
        guion = [(x["rank"], x["doc_id"], x["category"], x["titulo"]) for x in d["resultados"]]
        if reales != guion:
            print("AVISO: el top-3 de slides.json difiere de buscar():", reales)
        else:
            print("demo verificada contra buscar():", d["consulta"])
    except Exception as e:  # noqa: BLE001
        print("AVISO: no se pudo verificar la demo:", e)


# ------------------------------------------------------------------ principal
def main() -> None:
    D.guardar_estilo()
    slides = json.loads(D.RUTA_SLIDES.read_text(encoding="utf-8"))
    proyecto = next((s["proyecto_corto"] for s in slides if "proyecto_corto" in s), "BBC News IR")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(round(D.ANCHO * 914400)), Emu(round(D.ALTO * 914400))
    _aplicar_tema(prs)
    prs.core_properties.title = slides[0]["titulo"]
    prs.core_properties.author = slides[0].get("equipo", "")
    prs.core_properties.subject = slides[0].get("materia", "")

    todas_cajas = []
    for n, d in enumerate(slides, 1):
        datos = dict(d, _numero=n, _proyecto=proyecto)
        # rutas de imagen relativas a la raiz del repo
        for k in ("imagen",):
            if k in datos:
                datos[k] = str(D.RAIZ / datos[k])
        if "bloques" in datos:
            datos["bloques"] = [dict(b, imagen=str(D.RAIZ / b["imagen"])) if "imagen" in b else b for b in datos["bloques"]]
        if d["layout"] == "demo":
            _verificar_demo(d)
        slide, cajas = L.LAYOUT_FUNCIONES[d["layout"]](prs, datos)
        slide.notes_slide.notes_text_frame.text = d["notas"]
        todas_cajas.append({"n": n, "layout": d["layout"], "cajas": cajas})

    D.DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    prs.save(D.RUTA_PPTX)
    D.RUTA_CAJAS.write_text(json.dumps(todas_cajas, ensure_ascii=False, indent=1), encoding="utf-8")

    D.DIR_PREVIEW.mkdir(parents=True, exist_ok=True)
    for viejo in D.DIR_PREVIEW.glob("*.png"):
        viejo.unlink()
    imgs = [dibujar_diapositiva(e["cajas"], D.DIR_PREVIEW / f"slide_{e['n']:02d}.png") for e in todas_cajas]
    hoja_de_contactos(imgs, D.DIR_PREVIEW / "contact_sheet.png")
    print(f"{len(slides)} diapositivas -> {D.RUTA_PPTX.relative_to(D.RAIZ)}; vistas previas en {D.DIR_PREVIEW.relative_to(D.RAIZ)}")


if __name__ == "__main__":
    main()
