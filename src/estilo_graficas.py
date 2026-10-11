"""Estilo compartido de graficas del proyecto (paleta fija por categoria)."""

PALETA_CATEGORIAS = {
    "business": "#1f77b4",
    "entertainment": "#ff7f0e",
    "politics": "#2ca02c",
    "sport": "#d62728",
    "tech": "#9467bd",
}

ORDEN_CATEGORIAS = list(PALETA_CATEGORIAS)

DPI = 150


def color(categoria):
    """Color fijo de una categoria."""
    return PALETA_CATEGORIAS[categoria]
