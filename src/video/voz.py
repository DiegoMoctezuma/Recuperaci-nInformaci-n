"""Genera la narración del video (una pista por escena).

Uso, desde la raíz:
    python src/video/voz.py                    # voz gratuita Edge TTS (sin cuenta)
    python src/video/voz.py --listar-voces     # voces disponibles en tu cuenta de ElevenLabs
    python src/video/voz.py --motor elevenlabs --voz <voice_id>

Lee video/escenas.json, escribe video/audio/escena_XX.mp3, video/audio/duraciones.json
y video/audio/motor.json (qué motor y voz se usaron, para los créditos).

ElevenLabs necesita la clave en un archivo .env en la raíz (no se versiona):
    ELEVENLABS_API_KEY=...
Cada carácter gasta créditos del plan: la narración completa ronda 1,300.
"""
import argparse
import asyncio
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESCENAS = RAIZ / "video" / "escenas.json"
AUDIO = RAIZ / "video" / "audio"
VOZ_EDGE = "es-MX-JorgeNeural"
RITMO_EDGE = "+4%"
API = "https://api.elevenlabs.io/v1"
MODELO_ELEVEN = "eleven_v3"


def duracion(ruta: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def clave_eleven() -> str:
    clave = os.environ.get("ELEVENLABS_API_KEY", "")
    env = RAIZ / ".env"
    if not clave and env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("ELEVENLABS_API_KEY="):
                clave = linea.split("=", 1)[1].strip().strip("\"'")
    if not clave:
        raise SystemExit("Falta ELEVENLABS_API_KEY: crea el archivo .env en la raíz con esa línea.")
    return clave


def _eleven(ruta: str, cuerpo: dict | None = None) -> bytes:
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    pet = urllib.request.Request(f"{API}{ruta}", data=datos, headers={
        "xi-api-key": clave_eleven(), "Content-Type": "application/json", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(pet, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs respondió {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")


def listar_voces():
    voces = json.loads(_eleven("/voices"))["voices"]
    for v in voces:
        et = v.get("labels") or {}
        print(f"{v['voice_id']}  {v['name'][:28]:28}  {v.get('category', ''):12} "
              f"{et.get('gender', ''):7} {et.get('accent', ''):12} {et.get('language', ''):4} {et.get('description', '')}")
    try:
        sub = json.loads(_eleven("/user/subscription"))
        print(f"\nPlan: {sub.get('tier')} · créditos usados: {sub.get('character_count'):,} de {sub.get('character_limit'):,}")
    except SystemExit as e:
        print(f"\n(no se pudo leer el saldo: {e})")


def generar_eleven(escenas, voz: str, solo: list[int] | None):
    for e in escenas:
        if solo and e["n"] not in solo:
            continue
        audio = _eleven(f"/text-to-speech/{voz}?output_format=mp3_44100_128",
                        {"text": e.get("tts_eleven") or e["narracion"], "model_id": MODELO_ELEVEN,
                         "language_code": "es"})
        (AUDIO / f"escena_{e['n']:02d}.mp3").write_bytes(audio)
        print(f"  escena {e['n']:02d} lista", flush=True)


def generar_edge(escenas, solo: list[int] | None, voz: str = VOZ_EDGE):
    import edge_tts

    async def _todo():
        for e in escenas:
            if solo and e["n"] not in solo:
                continue
            await edge_tts.Communicate(e["tts"], voz, rate=RITMO_EDGE).save(str(AUDIO / f"escena_{e['n']:02d}.mp3"))

    asyncio.run(_todo())


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description="Narración del video BBC News IR")
    ap.add_argument("--motor", choices=["edge", "elevenlabs"], default="edge")
    ap.add_argument("--voz", help="voice_id de ElevenLabs, o nombre de voz de Edge TTS (p. ej. es-MX-DaliaNeural)")
    ap.add_argument("--escenas", type=int, nargs="*", help="solo estas escenas (para repetir una sin gastar de más)")
    ap.add_argument("--listar-voces", action="store_true")
    args = ap.parse_args(argv)
    if args.listar_voces:
        listar_voces()
        return {}
    AUDIO.mkdir(parents=True, exist_ok=True)
    escenas = json.loads(ESCENAS.read_text(encoding="utf-8"))
    if args.motor == "elevenlabs":
        if not args.voz:
            raise SystemExit("Indica --voz <voice_id> (usa --listar-voces para verlas).")
        generar_eleven(escenas, args.voz, args.escenas)
    else:
        generar_edge(escenas, args.escenas, args.voz or VOZ_EDGE)
    duraciones = {str(e["n"]): round(duracion(AUDIO / f"escena_{e['n']:02d}.mp3"), 2) for e in escenas}
    (AUDIO / "duraciones.json").write_text(json.dumps(duraciones, indent=2), encoding="utf-8")
    (AUDIO / "motor.json").write_text(json.dumps(
        {"motor": args.motor, "voz": args.voz or VOZ_EDGE}, indent=2), encoding="utf-8")
    for n, s in duraciones.items():
        print(f"escena {int(n):02d}: {s:5.2f} s")
    print(f"total: {sum(duraciones.values()):.2f} s")
    return duraciones


if __name__ == "__main__":
    main()
