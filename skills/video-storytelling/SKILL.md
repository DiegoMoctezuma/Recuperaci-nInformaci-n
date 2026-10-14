---
name: video-storytelling
description: Escribe el guion de un video corto que cuenta los resultados de un proyecto de recuperación de información como una historia (viaje del héroe, triángulo retórico, adaptación a la audiencia) usando solo cifras que existen en reports/. Úsala cuando pidan un video, comercial, pitch o guion narrativo del proyecto, antes de producir cualquier imagen o audio.
---

# Guion de video con storytelling

Esta skill produce **el guion**, no el video. La producción (metraje, voz, montaje) se hace después con una herramienta de video y solo cuando el guion esté aprobado.

## Regla que no se negocia: nada inventado

- Toda cifra, consulta, título de noticia o afirmación de resultado que aparezca en la narración o en pantalla debe salir de `reports/`, `data/processed/` o de ejecutar `src/buscar.py`. Cada escena lleva una columna **Fuente** con el archivo y el campo.
- El metraje de apoyo (imágenes de archivo, ilustración, clips generados) puede ser ajeno al proyecto. Los **datos** no.
- No redondees para que suene mejor: miles con coma (`12,345`), porcentajes con 2 decimales (`88.17%`). "9 de cada 10" solo si la cifra exacta (`90.96%`) aparece en pantalla en la misma escena.
- Si los reportes declaran un límite (supuesto de relevancia, intervalo que incluye 0), el guion lo dice. Un resultado no concluyente no se presenta como victoria.
- Si falta un dato para una escena, no lo supongas: cambia la escena o detente y repórtalo.

## Paso 1 — Audiencia (antes de escribir nada)

Responde por escrito, al inicio de `video/guion.md`:

1. **¿Qué sabe ya la audiencia?** Eso se deja fuera. No le expliques a un experto lo que ya domina.
2. **¿Qué queremos que sepa al final?** Máximo tres ideas, cada una con su cifra.
3. **Pitch**: nivel de términos y jerga que se puede usar sin perder interés.
4. **Tone**: conversacional o formal.

El objetivo de toda la pieza es **educar, entretener e inspirar**: decir algo nuevo, que importe y que mueva.

## Paso 2 — Quién es quién

- **El héroe es la audiencia**, nunca el equipo, el producto ni el método ganador. Se le habla de "tú".
- **Nosotros somos el guía**: mostramos empatía (conocemos su problema), autoridad (hicimos el recorrido y lo medimos) y visión (cómo queda todo al final).

## Paso 3 — Estructura: el viaje del héroe en cinco bloques

Los doce pasos del monomito (Campbell) se agrupan así. Cada bloque debe existir; dentro de un bloque se pueden fundir pasos si el video es corto.

| Bloque | Pasos | Qué debe lograr |
|---|---|---|
| **Paisaje** | Mundo ordinario | La situación de partida de la audiencia, reconocible en segundos. |
| **Desafíos** | Llamada a la aventura; rechazo de la llamada | El problema concreto y la salida fácil que tienta y no alcanza. |
| **Soluciones** | Encuentro con el guía; cruzar el umbral; aliados; acercamiento a la cueva más profunda | Aparecemos como guía, mostramos el método y preparamos la prueba difícil. |
| **Puntos de prueba** | La prueba; la recompensa; el camino de regreso | La evidencia: con el guía se llega al final. El regreso infunde confianza diciendo también los límites. |
| **Resumen** | Resurrección; regreso con el elixir | La transformación de la audiencia y cómo se ve el futuro con la solución en marcha. |

Introducción, cuerpo principal y final lógico: Paisaje y Desafíos son la introducción; Soluciones y Puntos de prueba, el cuerpo; Resumen, el final.

## Paso 4 — Triángulo retórico

Marca en cada escena qué pilar domina y comprueba el equilibrio del conjunto:

- **Pathos (emoción)**: abre la pieza y vuelve en el cierre. Hasta cierto punto: nada de dramatizar ni manipular.
- **Logos (lógica)**: los hechos y cifras que la audiencia necesita. Es el centro del cuerpo.
- **Ethos (credibilidad)**: cómo se midió, con cuántas consultas, qué supuesto se usó y qué no se puede afirmar. Con una audiencia experta, el ethos pesa tanto como el logos.

Ninguna pieza se sostiene con un solo pilar. Si un bloque entero no tiene logos o ethos, reescríbelo.

## Paso 5 — Escribir `video/guion.md`

1. Las respuestas del Paso 1.
2. Las tres ideas finales con su cifra y su fuente.
3. Tabla de escenas con estas columnas: `#`, `Bloque / paso`, `Tiempo`, `Narración`, `En pantalla`, `Visual`, `Fuente`, `Pilar`.
   - **Narración**: una o dos frases por escena, escritas para ser dichas. Ritmo de 2.0 a 2.5 palabras por segundo; cuenta las palabras, no las estimes.
   - **En pantalla**: máximo 12 palabras; una cifra protagonista por escena.
   - **Visual**: `archivo` (metraje libre), `gráfica animada` (desde `reports/`) o `captura real` (salida de `src/buscar.py`). Describe qué se ve, no cómo se anima.
4. Lista de **recursos por conseguir** (metraje de archivo con licencia libre, voz, música) y de **cifras citadas** con su fuente, para que un revisor las contraste una a una.
5. Duración total: 60 a 100 segundos.

## Paso 6 — Autorrevisión antes de entregar

- Cada cifra del guion aparece en la lista de cifras citadas y coincide con su fuente (ábrela y compárala).
- El héroe es la audiencia en todas las escenas; el equipo solo aparece como guía.
- Están los cinco bloques y los tres pilares.
- Nada de lo que la audiencia ya sabe (Paso 1) quedó explicado.
- El supuesto de relevancia y los resultados no concluyentes están dichos en voz o en pantalla.

## No hagas

- No produzcas video, audio ni imágenes en esta skill, ni instales herramientas: el guion se aprueba primero.
- No uses la identidad visual de otra pieza: el video hereda la paleta y la tipografía de `presentacion/estilo.json`.
- No conviertas el guion en una lista de resultados: si una escena no hace avanzar la historia, sobra.
