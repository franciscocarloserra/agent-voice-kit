#!/usr/bin/env python3
"""TTS front: POST /tts (text body, ?voice=&lang=&fmt=wav|ogg) -> audio. Supertonic via audiocpp_server if reachable
(fast, needs the native binary) else the pip `supertonic` ONNX package (no build, slower). Logs hit/result."""
import os, sys, json, time, re, io, subprocess, urllib.request, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.environ.get("VOICEKIT_CONFIG", os.path.join(ROOT, "config.json"))))
T, TOKEN = CFG["tts"], CFG.get("token", "")
ACPP = f"http://127.0.0.1:{T['acpp_port']}/v1/audio/speech"
Y, G, R = "\033[33m", "\033[32m", "\033[0m"

def clean(t):
    t = re.sub(r"```[\s\S]*?```", " ", t); t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t); t = re.sub(r"[*_#>|]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def lang_of(t):
    return "es" if re.search(r"[áéíóñ¿¡]|\b(que|el|la|los|las|para|con|una|es)\b", t.lower()) else "en"

def _acpp_up():
    try: urllib.request.urlopen(f"http://127.0.0.1:{T['acpp_port']}/health", timeout=0.5); return True
    except Exception: return False

ENGINE = "audiocpp" if _acpp_up() else "onnx"
_onnx, _styles, _lock = None, {}, threading.Lock()
if ENGINE == "onnx":
    providers = "CoreMLExecutionProvider,CPUExecutionProvider" if sys.platform == "darwin" else "CUDAExecutionProvider,CPUExecutionProvider"
    os.environ.setdefault("SUPERTONIC_ONNX_PROVIDERS", providers)
    from supertonic import TTS as _ST
    _onnx = _ST(model_dir=os.path.join(ROOT, "models", "Supertonic-3-onnx"), auto_download=True)
    for v in ("F1", "F2", "F3", "F4", "F5", "M1", "M2", "M3", "M4", "M5"):
        try: _styles[v] = _onnx.get_voice_style(voice_name=v)
        except Exception as e: print(f"[onnx] voice {v}: {e}", flush=True)

def synth(text, voice, lang):
    if ENGINE == "audiocpp":
        body = {"model": "supertonic", "input": text, "voice": voice, "language": lang, "response_format": "wav"}
        req = urllib.request.Request(ACPP, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req, timeout=T["timeout_s"]).read()
    import numpy as np, wave
    with _lock:
        wav, _ = _onnx.synthesize(text, voice_style=_styles[voice], total_steps=T["onnx_steps"], speed=1.0, lang=lang)
    pcm = (np.clip(np.asarray(wav, dtype=np.float32).squeeze(), -1, 1) * 32767).astype("<i2").tobytes()
    buf = io.BytesIO(); w = wave.open(buf, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(_onnx.sample_rate); w.writeframes(pcm); w.close()
    return buf.getvalue()

def wav_duration(b):
    import wave; w = wave.open(io.BytesIO(b)); return w.getnframes() / w.getframerate()

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path != "/tts": self.send_error(404); return
        if TOKEN and self.headers.get("Authorization", "") != f"Bearer {TOKEN}": self.send_error(401); return
        text = clean(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8", "ignore"))
        if not text: self.send_error(400, "empty"); return
        voice, lang, fmt = q.get("voice", T["voice"]), q.get("lang") or lang_of(text), q.get("fmt", "wav")
        words = len(text.split())
        print(f"{Y}[hit]{R} voice={voice} chars={len(text)} words={words}", flush=True)
        try:
            t0 = time.time(); data = synth(text, voice, lang); gen = time.time() - t0
            dur = wav_duration(data)
            if fmt == "ogg":
                data = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "ogg", "-c:a", "libvorbis", "-q:a", "3", "pipe:1"],
                                      input=data, capture_output=True, check=True).stdout
            print(f"{G}[result]{R} gen={gen:.2f}s duration={dur:.2f}s wpm={words/dur*60 if dur else 0:.0f}", flush=True)
            self.send_response(200); self.send_header("Content-Type", "audio/ogg" if fmt == "ogg" else "audio/wav")
            self.send_header("X-Audio-Duration", f"{dur:.3f}"); self.send_header("X-Gen-Time", f"{gen:.3f}")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)
        except Exception as e:
            print(f"[error] {e!r}", flush=True); self.send_error(500, str(e))
    def log_message(self, *a): pass

print(f"tts ({ENGINE}) listening on http://127.0.0.1:{T['port']}/tts", flush=True)
ThreadingHTTPServer(("127.0.0.1", T["port"]), H).serve_forever()
