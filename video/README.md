# Video del proyecto

`video/salida/bbc_news_ir.mp4`: 1920×1080, 30 fps, unos 100 segundos, con narración.
Cuenta los resultados como un viaje del héroe; el guion aprobado está en `guion.md`
y se escribió con `skills/video-storytelling/SKILL.md`.

## Cómo se regenera

Desde la raíz del repositorio, con el entorno `bbc-ir`:

```bash
brew install ffmpeg            # una sola vez
pip install edge-tts           # una sola vez (voz sintética gratuita; necesita internet)
python src/video/voz.py                  # narración -> video/audio/
python src/video/render.py --fotogramas  # un fotograma por escena -> video/salida/fotogramas/
python src/video/render.py               # video completo -> video/salida/bbc_news_ir.mp4
```

Antes hay que tener los índices construidos (`python src/indices.py`) y los dos clips de archivo
descargados en `video/archivo/` (ver abajo); los clips no se versionan.

## De dónde sale cada cosa

- **Cifras y rankings**: `src/video/render.py` los lee de `reports/` y `data/processed/` al renderizar,
  y ejecuta `src/buscar.py` para los resultados de la escena 7. No hay números escritos a mano.
- **Diseño**: paleta de `presentacion/estilo.json`; títulos en Georgia y cuerpo en Arial.
- **Narración**: `video/escenas.json`. La versión actual usa la voz mexicana `es-MX-DaliaNeural` de Edge TTS
  (gratuita, sin cuenta): `python src/video/voz.py --voz es-MX-DaliaNeural`, que lee el campo `tts`.
  Para una voz más expresiva, `video/textos_para_elevenlabs.md` trae los textos con dirección emocional
  (campo `tts_eleven`) listos para pegar en la web de ElevenLabs con una voz mexicana de su biblioteca;
  en el plan gratuito esas voces no funcionan por API. Los MP3 se guardan en `video/audio/escena_XX.mp3`
  y después se ejecuta `python src/video/render.py --audio-externo`.
  Versiones anteriores de la voz: `video/audio_edge/` (Jorge, Edge TTS) y `video/audio_george/` (ElevenLabs).

## Imágenes de archivo y licencias

| Escenas | Clip | Autor | Licencia | Guardar como |
|---|---|---|---|---|
| 1 | [The 910 ton printing presses at the Las Vegas Review-Journal…](https://commons.wikimedia.org/wiki/File:The_910_ton_printing_presses_at_the_Las_Vegas_Review-Journal_were_the_largest_in_the_world_when_installed_in_2000.webm) | Harrison Keely | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0) | `video/archivo/lvrj_press/clip.webm` |
| 6 y 10 | [Tidningstryck 1937](https://commons.wikimedia.org/wiki/File:Tidningstryck_1937.ogv) (extracto de "Varje dag en världsrevy") | AB Svensk Filmindustri | Dominio público | `video/archivo/tidningstryck_1937/clip.ogv` |

Ambos se usan recortados y oscurecidos con el color de fondo del proyecto. La atribución aparece
en la tarjeta final del video.
