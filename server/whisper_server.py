#!/usr/bin/env python3
"""STT server: POST /transcribe (audio bytes) -> text/plain. Backend: faster-whisper (linux/windows) or mlx-whisper (mac)."""
import os, sys, json, time, wave, tempfile, subprocess, glob, ctypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.environ.get("VOICEKIT_CONFIG", os.path.join(ROOT, "config.json"))))
W, TOKEN = CFG["whisper"], CFG.get("token", "")
BACKEND = W["backend"] if W["backend"] != "auto" else ("mlx" if sys.platform == "darwin" else "faster")
Y, G, R = "\033[33m", "\033[32m", "\033[0m"

if BACKEND == "faster":
    for lib in glob.glob(os.path.join(sys.prefix, "**", "nvidia", "*", "lib", "*.so*"), recursive=True):
        try: ctypes.CDLL(lib)
        except Exception: pass
    from faster_whisper import WhisperModel
    try: model = WhisperModel(W["model"], device="cuda", compute_type="float16"); dev = "cuda"
    except Exception: model = WhisperModel(W["model"], device="cpu", compute_type="int8"); dev = "cpu"
    def transcribe(path):
        segs, _ = model.transcribe(path, vad_filter=True, vad_parameters={"min_silence_duration_ms": W["vad_min_silence_ms"]},
                                   no_speech_threshold=W["no_speech_threshold"], log_prob_threshold=W["log_prob_threshold"])
        return " ".join(s.text.strip() for s in segs)
else:
    import mlx_whisper; dev = "metal"
    def transcribe(path):
        return mlx_whisper.transcribe(path, path_or_hf_repo=W["mlx_model"], no_speech_threshold=W["no_speech_threshold"],
                                      logprob_threshold=W["log_prob_threshold"])["text"].strip()

def transcribe_file(path):
    with wave.open(path) as wf: dur = wf.getnframes() / wf.getframerate()
    if dur > W["max_duration_s"]: raise ValueError(f"duration {dur:.1f}s > {W['max_duration_s']}s")
    print(f"{Y}[hit]{R} duration={dur:.2f}s", flush=True)
    t0 = time.time(); text = transcribe(path).replace("\n", " "); gen = time.time() - t0
    print(f"{G}[result]{R} gen={gen:.2f}s chars={len(text)} wpm={len(text.split())/dur*60 if dur else 0:.0f}", flush=True)
    return text

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/transcribe": self.send_error(404); return
        if TOKEN and self.headers.get("Authorization", "") != f"Bearer {TOKEN}": self.send_error(401); return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if not body: self.send_error(400, "empty"); return
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False); tmp.close()
        try:
            if body[:4] == b"RIFF": open(tmp.name, "wb").write(body)
            else:
                src = tmp.name + ".in"; open(src, "wb").write(body)
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", tmp.name], check=True)
                os.remove(src)
            text = transcribe_file(tmp.name)
            self.send_response(200); self.send_header("Content-Type", "text/plain; charset=utf-8"); self.end_headers()
            self.wfile.write(text.encode())
        except Exception as e:
            self.send_error(400, str(e))
        finally:
            try: os.remove(tmp.name)
            except Exception: pass
    def log_message(self, *a): pass

print(f"whisper ({BACKEND}/{dev}) listening on http://127.0.0.1:{W['port']}/transcribe", flush=True)
ThreadingHTTPServer(("127.0.0.1", W["port"]), H).serve_forever()
