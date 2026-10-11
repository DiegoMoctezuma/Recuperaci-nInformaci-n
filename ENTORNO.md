# Entorno de ejecución

Entorno con el que se construyó y validó la práctica. Con estas versiones el pipeline
(`src/*.py`) y el notebook `práctica.ipynb` corren de principio a fin.

| Dato | Valor |
|---|---|
| Entorno conda | `bbc-ir` |
| Python | 3.11.17 |
| conda | 25.7.0 |
| Sistema donde se validó | macOS 27.0 (arm64) |
| Fecha | 2026-10-11 |

## Librerías y versiones

| Librería | Versión | Para qué se usa |
|---|---|---|
| pandas | 3.0.6 | carga y manejo del corpus |
| numpy | 2.4.6 | cálculo numérico, ajustes de Zipf y Heaps |
| scikit-learn | 1.9.1 | CountVectorizer, TF-IDF, SVD, LDA, similitud coseno |
| scipy | 1.17.1 | matrices dispersas |
| rank-bm25 | 0.2.2 | índice BM25 |
| gensim | 4.4.0 | Word2Vec |
| spacy | 3.8.16 | stopwords y lematización |
| en_core_web_sm | 3.8.0 | modelo de spaCy en inglés (se instala aparte, ver abajo) |
| nltk | 3.10.3 | PorterStemmer |
| matplotlib | 3.11.2 | gráficas |
| wordcloud | 1.9.6 | nubes de palabras |
| pillow | 12.3.0 | vistas previas de la presentación (dependencia de wordcloud) |
| python-pptx | 1.0.2 | generación de la presentación |
| pyyaml | 6.0.3 | lectura de `checklist_calidad.yaml` |
| joblib | 1.6.0 | guardado de modelos |
| ipykernel | 7.4.0 | kernel del notebook |
| nbconvert | 7.17.1 | ejecución del notebook de principio a fin |

`requirements.txt` trae las dependencias directas con versiones mínimas;
`requirements-lock.txt` trae **todas** las versiones exactas (incluidas las transitivas).

## Cómo reproducirlo en otra computadora

```bash
# 1. Crear y activar el entorno
conda create -y -n bbc-ir python=3.11
conda activate bbc-ir

# 2. Instalar las librerías (versiones exactas)
pip install -r requirements-lock.txt
#    Alternativa si alguna versión exacta no existe para tu sistema:
#    pip install -r requirements.txt

# 3. Modelo de spaCy en inglés (el corpus está en inglés)
python -m spacy download en_core_web_sm

# 4. Comprobar
python -c "import sklearn, rank_bm25, gensim, spacy, wordcloud, pptx; spacy.load('en_core_web_sm'); print('ok')"
```

Sin conda funciona igual con `python3.11 -m venv .venv && source .venv/bin/activate`
(en Windows: `.venv\Scripts\activate`) y los pasos 2 a 4.

## Datos

`data/raw/` no se versiona. Si falta `data/raw/bbc-text.csv`, `python src/descarga.py` lo baja de
<https://github.com/mdsohaib/BBC-News-Classification> y verifica sus 2,225 filas.

## Ejecutar

Todo se ejecuta desde la raíz del repositorio, con el entorno activo:

```bash
python src/descarga.py                 # y el resto de scripts de src/, en el orden del README
jupyter nbconvert --to notebook --execute --inplace práctica.ipynb
```

Para abrir el notebook en VS Code o Jupyter, elige el kernel del entorno `bbc-ir`
(o regístralo con `python -m ipykernel install --user --name bbc-ir`).
