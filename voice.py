#!/usr/bin/env python3
"""voice-kit CLI (Linux / macOS / Windows). Same interface for humans, hotkeys and agent harnesses.

  voice.py setup  [stt|tts|all]  venv, deps, models (default: all). Idempotent, re-run anytime
  voice.py doctor                validate every component, print the fix for each missing one
  voice.py serve  [stt|tts|all]  run servers in foreground (Ctrl-C stops). Or install-service for background
  voice.py check  [stt|tts|all]  end-to-end smoke test against running servers
  voice.py dictate [cancel]      toggle mic recording -> transcribe -> type into active window
  voice.py tts "text" | -o f.ogg | stop | speed [X|+|-]
  voice.py install-service | install-hotkey   register login start / global hotkeys (per OS)
All numeric knobs live in config.json.
"""
import os, sys, json, re, time, signal, subprocess, tempfile, urllib.request, urllib.error, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.environ.get("VOICEKIT_CONFIG", os.path.join(ROOT, "config.json"))))
W, T, TOKEN = CFG["whisper"], CFG["tts"], CFG.get("token", "")
STATE = os.path.join(tempfile.gettempdir(), "agent-voice-kit"); os.makedirs(STATE, exist_ok=True)
SPEED_FILE = os.path.join(ROOT, "speed")
WIN = sys.platform.startswith("win"); MAC = sys.platform == "darwin"
VENV_PY = os.path.join(ROOT, "venv", "Scripts" if WIN else "bin", "python.exe" if WIN else "python")
ACPP_BIN = os.path.join(ROOT, "bin", "audiocpp_server.exe" if WIN else "audiocpp_server")
HDR = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

def pidfile(name): return os.path.join(STATE, name + ".pid")
def read_pid(name):
    try: return int(open(pidfile(name)).read())
    except Exception: return None
def kill_pid(name):
    p = read_pid(name)
    if p:
        try: os.kill(p, signal.SIGTERM)
        except Exception: pass
    try: os.remove(pidfile(name))
    except Exception: pass
def write_pid(name, pid): open(pidfile(name), "w").write(str(pid))

# ---------- dictate ----------
def dictate(cancel=False):
    from platforms import record_start, type_text
    wav = os.path.join(STATE, "dictate.wav")
    if cancel:
        kill_pid("rec"); tts_stop(); return
    if read_pid("rec"):
        kill_pid("rec"); time.sleep(0.1)
        req = urllib.request.Request(f"http://127.0.0.1:{W['port']}/transcribe", data=open(wav, "rb").read(), headers=HDR)
        text = urllib.request.urlopen(req, timeout=60).read().decode().strip()
        if text: type_text(text)
    else:
        p = record_start(wav, W); write_pid("rec", p.pid)

# ---------- tts ----------
def speed_get(): 
    try: return float(open(SPEED_FILE).read())
    except Exception: return T["speed"]
def speed_cmd(arg):
    cur = speed_get()
    if arg in ("+", "up"): cur = min(T["speed_max"], cur + T["speed_step"])
    elif arg in ("-", "down"): cur = max(T["speed_min"], cur - T["speed_step"])
    elif arg:
        v = float(arg)
        if not T["speed_min"] <= v <= T["speed_max"]: sys.exit(f"speed must be {T['speed_min']}-{T['speed_max']}")
        cur = v
    open(SPEED_FILE, "w").write(str(cur))
    print(f"speed {cur}  (1.0 normal, {T['speed']} default, 2.0 fast)")

def fetch_tts(text, fmt, voice):
    req = urllib.request.Request(f"http://127.0.0.1:{T['port']}/tts?voice={voice}&fmt={fmt}", data=text.encode(), headers=HDR)
    return urllib.request.urlopen(req, timeout=T["timeout_s"] * 2).read()

def tts_stop():
    kill_pid("chunks"); kill_pid("play")

def play_file(path):
    from platforms import play
    sp = speed_get()
    if abs(sp - 1.0) > 1e-6 and not MAC:  # afplay has native -r; others use ffmpeg atempo
        out = path + ".s.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-af", f"atempo={sp}", out], check=True); os.replace(out, path)
    if MAC and abs(sp - 1.0) > 1e-6:
        p = subprocess.Popen(["afplay", "-r", str(sp), path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        p = play(path)
    write_pid("play", p.pid); return p

def chunks(text, limit):
    parts = re.split(r"(?<=[\.\?\!])\s+|\n\n+", text); buf = ""
    for p in parts:
        p = p.strip()
        if not p: continue
        if len(buf) + len(p) + 1 > limit and buf: yield buf; buf = p
        else: buf = (buf + " " + p).strip() if buf else p
    if buf: yield buf

def tts(args):
    voice, out = T["voice"], None
    while args and args[0].startswith("-"):
        if args[0] == "-v": voice = args[1]; args = args[2:]
        elif args[0] == "-o": out = args[1]; args = args[2:]
        else: sys.exit(f"unknown {args[0]}")
    if args and args[0] == "stop": tts_stop(); return
    if args and args[0] == "speed": speed_cmd(args[1] if len(args) > 1 else None); return
    text = " ".join(args) if args else sys.stdin.read()
    if os.path.isfile(text): text = open(text, encoding="utf-8", errors="ignore").read()
    text = text.strip()
    if not text: sys.exit("no text")
    if out:
        open(out, "wb").write(fetch_tts(text, "ogg" if out.endswith(".ogg") else "wav", voice)); print(f"wrote {out}"); return
    tts_stop()
    if len(text) <= T["chunk_chars"]:
        f = os.path.join(STATE, f"tts-{os.getpid()}.wav"); open(f, "wb").write(fetch_tts(text, "wav", voice))
        _detach([sys.executable, __file__, "_play", f]); return
    _detach([sys.executable, __file__, "_chunks", voice, text])

def _detach(cmd):
    kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS} if WIN else {"start_new_session": True}
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)

def _play_worker(path):
    p = play_file(path); p.wait()
    for f in (path,):
        try: os.remove(f)
        except Exception: pass
    try: os.remove(pidfile("play"))
    except Exception: pass

def _chunks_worker(voice, text):
    write_pid("chunks", os.getpid()); cur = None
    try:
        for i, c in enumerate(chunks(text, T["chunk_chars"])):
            f = os.path.join(STATE, f"tts-{os.getpid()}-{i}.wav"); open(f, "wb").write(fetch_tts(c, "wav", voice))
            if cur: cur.wait()
            cur = play_file(f)
        if cur: cur.wait()
    finally:
        for f in os.listdir(STATE):
            if f.startswith(f"tts-{os.getpid()}-"): os.remove(os.path.join(STATE, f))
        for n in ("chunks", "play"):
            try: os.remove(pidfile(n))
            except Exception: pass

# ---------- serve / setup / check ----------
def acpp_cmd():
    backend = T["acpp_backend"] if T["acpp_backend"] != "auto" else ("metal" if MAC else "cuda" if shutil.which("nvidia-smi") else "cpu")
    conf = {"host": "127.0.0.1", "port": T["acpp_port"], "backend": backend, "device": 0, "threads": T["acpp_threads"], "lazy_load": False,
            "models": [{"id": "supertonic", "family": "supertonic", "path": os.path.join(ROOT, "models", "Supertonic-3-GGUF"), "task": "tts",
                        "mode": "offline", "default_voice_preset": {"voice_id": T["voice"]}}]}
    cp = os.path.join(STATE, "acpp.json"); json.dump(conf, open(cp, "w"))
    return [ACPP_BIN, "--config", cp, "--no-ui", "--model-spec-override", os.path.join(ROOT, "bin", "model_specs")]

def serve(what="all"):
    cmds = []
    if what in ("stt", "all"): cmds.append([VENV_PY, os.path.join(ROOT, "server", "whisper_server.py")])
    if what in ("tts", "all"):
        if os.path.exists(ACPP_BIN): cmds.append(acpp_cmd())
        else: print("[serve] audiocpp binary not found, tts uses the ONNX engine (slower, no build needed)", flush=True)
        cmds.append([VENV_PY, os.path.join(ROOT, "server", "tts_server.py")])
    procs = [subprocess.Popen(c) for c in cmds]
    try:
        while True:
            for i, p in enumerate(procs):
                if p.poll() is not None: print(f"[serve] process {i} exited rc={p.returncode}, restarting", flush=True); procs[i] = subprocess.Popen(p.args)
            time.sleep(2)
    except KeyboardInterrupt:
        for p in procs: p.terminate()

def setup(what="all"):
    if not os.path.exists(VENV_PY): subprocess.run([sys.executable, "-m", "venv", os.path.join(ROOT, "venv")], check=True)
    pip = [VENV_PY, "-m", "pip", "install", "-q", "--upgrade", "pip", "huggingface_hub"]
    if what in ("stt", "all"):
        pip += ["mlx-whisper"] if MAC else ["faster-whisper"]
        if not MAC and shutil.which("nvidia-smi"): pip += ["nvidia-cublas-cu12", "nvidia-cudnn-cu12"]  # CUDA libs for CTranslate2, no toolkit needed
    if what in ("tts", "all"): pip += ["supertonic", "numpy"] + ([] if MAC else ["onnxruntime-gpu"] if shutil.which("nvidia-smi") else [])
    if WIN and what in ("stt", "all"): pip += ["pyautogui", "pyperclip"]
    subprocess.run(pip, check=True)
    if not shutil.which("ffmpeg"): print("!! ffmpeg missing: brew install ffmpeg | winget install ffmpeg | apt install ffmpeg")
    if what in ("stt", "all") and not MAC:  # pre-download whisper weights
        subprocess.run([VENV_PY, "-c", f"from faster_whisper import WhisperModel; WhisperModel({W['model']!r}, device='cpu', compute_type='int8')"], check=True)
    if what == "stt": print("setup stt done"); doctor(); return
    code = f"""
from huggingface_hub import snapshot_download, hf_hub_download
import os
d = os.path.join({ROOT!r}, 'models')
snapshot_download({T['gguf_extra_repo']!r}, local_dir=os.path.join(d, 'Supertonic-3-GGUF'), allow_patterns=['config/*','voice_styles/*','model_specs/*'])
for f in {T['gguf_files']!r}: hf_hub_download({T['gguf_repo']!r}, f, local_dir=d)
"""
    subprocess.run([VENV_PY, "-c", code], check=True)
    src = os.path.join(ROOT, "models", T["gguf_files"][0]); dst = os.path.join(ROOT, "models", "Supertonic-3-GGUF", os.path.basename(src))
    if os.path.exists(src) and not os.path.exists(dst): shutil.move(src, dst)
    print(f"setup {what} done"); doctor()

def _up(port):
    try: urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1); return True
    except urllib.error.HTTPError: return True
    except Exception: return False

def doctor():
    """Validate components; print a fix line per problem. Exit 1 if anything missing."""
    ok = True
    def row(name, good, fix):
        nonlocal ok; ok &= bool(good); print(f"  [{'ok' if good else '--'}] {name}" + ("" if good else f"   -> {fix}"))
    print("system")
    row("python venv", os.path.exists(VENV_PY), "voice.py setup")
    row("ffmpeg", shutil.which("ffmpeg"), "brew install ffmpeg | winget install ffmpeg | apt install ffmpeg")
    if not WIN and not MAC: row("xdotool", shutil.which("xdotool"), "apt install xdotool")
    if WIN: row("AutoHotkey", shutil.which("AutoHotkey") or os.path.exists(r"C:\Program Files\AutoHotkey"), "winget install AutoHotkey.AutoHotkey")
    gpu = shutil.which("nvidia-smi") or MAC
    row("gpu (cuda or apple silicon)", gpu, "no GPU: whisper runs on CPU (slower), tts on CPU")
    if shutil.which("nvidia-smi"):
        try:
            drv = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
            row(f"nvidia driver {drv} (>= {CFG['min_nvidia_driver']})", float(drv.split(".")[0]) >= CFG["min_nvidia_driver"], "update the NVIDIA driver (GeForce/Studio driver is enough, no CUDA toolkit)")
        except Exception: row("nvidia driver readable", False, "nvidia-smi failed; reinstall the NVIDIA driver")
    print("stt (speak to the machine)")
    mod = "mlx_whisper" if MAC else "faster_whisper"
    row(f"{mod} installed", os.path.exists(VENV_PY) and subprocess.run([VENV_PY, "-c", f"import {mod}"], capture_output=True).returncode == 0, "voice.py setup stt")
    row(f"whisper server :{W['port']}", _up(W["port"]), "voice.py serve stt   (or install-service)")
    print("tts (the machine speaks)")
    row("supertonic (onnx) installed", os.path.exists(VENV_PY) and subprocess.run([VENV_PY, "-c", "import supertonic"], capture_output=True).returncode == 0, "voice.py setup tts")
    acpp = os.path.exists(ACPP_BIN) and os.path.isdir(os.path.join(ROOT, "bin", "model_specs")) and os.path.exists(os.path.join(ROOT, "models", "Supertonic-3-GGUF", "voice_styles"))
    print(f"  [{'ok' if acpp else '..'}] audio.cpp engine (optional, 5-8x faster)" + ("" if acpp else "   -> see AGENTS.md 'audio.cpp (optional)'"))
    if acpp: row(f"audiocpp :{T['acpp_port']}", _up(T["acpp_port"]), "voice.py serve tts")
    row(f"tts server :{T['port']}", _up(T["port"]), "voice.py serve tts")
    if MAC: print("  note: macOS needs Microphone + Accessibility permission for the app running the hotkey (manual, once)")
    print("all good" if ok else "missing components above")
    return ok

def check(what="all"):
    t = "Prueba del kit de voz."; d = None
    try:
        if what in ("tts", "all"):
            d = fetch_tts(t, "wav", T["voice"]); print(f"tts ok ({len(d)} bytes)")
        if what in ("stt", "all"):
            if d is None:
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-ar", "16000", "-ac", "1", os.path.join(STATE, "sine.wav")], check=True)
                d = open(os.path.join(STATE, "sine.wav"), "rb").read()
            req = urllib.request.Request(f"http://127.0.0.1:{W['port']}/transcribe", data=d, headers=HDR)
            print("stt ok:", urllib.request.urlopen(req, timeout=120).read().decode() or "(empty transcript, expected for a tone)")
    except Exception as e: sys.exit(f"check failed: {e!r}  -> run: voice.py doctor")

def install_service():
    py, script = VENV_PY, os.path.join(ROOT, "voice.py")
    if MAC:
        plist = os.path.expanduser("~/Library/LaunchAgents/com.voicekit.serve.plist")
        open(plist, "w").write(open(os.path.join(ROOT, "service", "mac.plist")).read().replace("{PY}", py).replace("{SCRIPT}", script).replace("{ROOT}", ROOT))
        subprocess.run(["launchctl", "load", "-w", plist]); print(f"installed {plist}")
    elif WIN:
        subprocess.run(["schtasks", "/Create", "/F", "/SC", "ONLOGON", "/TN", "VoiceKit", "/TR", f'"{py}" "{script}" serve']); print("installed task VoiceKit")
    else:
        unit = os.path.expanduser("~/.config/systemd/user/voicekit.service"); os.makedirs(os.path.dirname(unit), exist_ok=True)
        open(unit, "w").write(open(os.path.join(ROOT, "service", "linux.service")).read().replace("{PY}", py).replace("{SCRIPT}", script).replace("{ROOT}", ROOT))
        subprocess.run(["systemctl", "--user", "enable", "--now", "voicekit"]); print(f"installed {unit}")

def install_hotkey():
    script = os.path.join(ROOT, "voice.py")
    if WIN:
        ahk = os.path.join(os.path.expanduser("~"), "voicekit.ahk")
        open(ahk, "w").write(open(os.path.join(ROOT, "hotkeys", "windows.ahk")).read().replace("{PY}", VENV_PY).replace("{SCRIPT}", script))
        startup = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "voicekit.ahk"); shutil.copy(ahk, startup)
        print(f"installed {ahk} (+ Startup). Needs AutoHotkey v2: winget install AutoHotkey.AutoHotkey")
    elif MAC:
        print(open(os.path.join(ROOT, "hotkeys", "mac.md")).read().replace("{PY}", VENV_PY).replace("{SCRIPT}", script))
    else:
        print(open(os.path.join(ROOT, "hotkeys", "linux.md")).read().replace("{PY}", VENV_PY).replace("{SCRIPT}", script))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): print(__doc__); sys.exit(0)
    cmd, rest = a[0], a[1:]
    arg = rest[0] if rest else "all"
    {"setup": lambda: setup(arg), "serve": lambda: serve(arg), "check": lambda: check(arg), "doctor": doctor,
     "install-service": install_service, "install-hotkey": install_hotkey,
     "dictate": lambda: dictate(cancel=bool(rest and rest[0] == "cancel")), "tts": lambda: tts(rest),
     "_play": lambda: _play_worker(rest[0]), "_chunks": lambda: _chunks_worker(rest[0], rest[1])}.get(cmd, lambda: sys.exit(f"unknown {cmd}"))()
