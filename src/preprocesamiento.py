"""Preprocesamiento unico y reutilizable (corpus, ingesta y consultas).

Importable sin efectos secundarios salvo la carga unica de spaCy a nivel de modulo.
"""
import re

import spacy
from nltk.stem import PorterStemmer
from spacy.lang.en.stop_words import STOP_WORDS

# Lista propia de stopwords, visible y documentada en reports/limpieza.md
STOPWORDS_EXTRA = ["said", "mr", "mrs", "ms", "also", "would", "could",
                   "year", "years", "new", "one", "two"]
STOPWORDS = set(STOP_WORDS) | set(STOPWORDS_EXTRA)
MIN_LONG_TOKEN = 3

# spaCy se carga una sola vez; solo se necesitan tagger/attribute_ruler/lemmatizer.
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
_stemmer = PorterStemmer()

_RE_MONEDA = re.compile(r"[£$]")
_RE_DIGITOS = re.compile(r"\d+")
_RE_NO_VALIDO = re.compile(r"[^a-z' ]")
_RE_POSESIVO = re.compile(r"'s\b")
_RE_ESPACIOS = re.compile(r"\s+")


def normalizar(texto: str) -> str:
    """Minusculas, sin £/$, sin digitos, solo a-z/espacio, sin apostrofos, espacios colapsados."""
    texto = texto.lower()
    texto = _RE_MONEDA.sub(" ", texto)
    texto = _RE_DIGITOS.sub("", texto)
    # espacios en blanco (tabs, saltos) se tratan como espacio antes de filtrar
    texto = _RE_ESPACIOS.sub(" ", texto)
    texto = _RE_NO_VALIDO.sub("", texto)
    texto = _RE_POSESIVO.sub("", texto)   # terminacion 's
    texto = texto.replace("'", "")          # apostrofos sueltos restantes
    return _RE_ESPACIOS.sub(" ", texto).strip()


def _valido(tok: str) -> bool:
    return len(tok) >= MIN_LONG_TOKEN and tok not in STOPWORDS


def tokenizar(texto: str) -> list[str]:
    """Split por espacios; descarta tokens < 3 letras y stopwords (spaCy + STOPWORDS_EXTRA)."""
    return [t for t in texto.split() if _valido(t)]


def _lematizar_lote(listas: list[list[str]]) -> list[list[str]]:
    textos = [" ".join(toks) for toks in listas]
    salida = []
    for doc in nlp.pipe(textos, batch_size=64):
        lemas = [t.lemma_.lower() for t in doc if not t.is_space]
        salida.append([l for l in lemas if l.isalpha() and _valido(l)])
    return salida


def lematizar(tokens: list[str]) -> list[str]:
    """Lematiza con spaCy y vuelve a filtrar stopwords y tokens < 3."""
    if not tokens:
        return []
    return _lematizar_lote([tokens])[0]


def stemizar(tokens: list[str]) -> list[str]:
    """Stemming de Porter."""
    return [_stemmer.stem(t) for t in tokens]


def preprocesar(texto: str, modo: str = "lemma") -> list[str]:
    """normalizar -> tokenizar -> lematizar | stemizar. modo: 'lemma' | 'stem'."""
    tokens = tokenizar(normalizar(texto))
    if modo == "lemma":
        return lematizar(tokens)
    if modo == "stem":
        return stemizar(tokens)
    raise ValueError("modo debe ser 'lemma' o 'stem'")


def preprocesar_lote(textos, modo: str = "lemma") -> list[list[str]]:
    """Version por lotes de preprocesar (usa nlp.pipe con batch_size=64); mismo resultado."""
    tokens = [tokenizar(normalizar(t)) for t in textos]
    if modo == "lemma":
        return _lematizar_lote(tokens)
    if modo == "stem":
        return [stemizar(t) for t in tokens]
    raise ValueError("modo debe ser 'lemma' o 'stem'")
