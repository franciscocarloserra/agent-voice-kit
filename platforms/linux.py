import subprocess, shutil
def record_start(path, cfg):
    if shutil.which("pw-record"):
        return subprocess.Popen(["pw-record", "--format=s16", "--rate=16000", "--channels=1", f"--volume={cfg['mic_gain']}", path])
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "pulse", "-i", "default", "-ar", "16000", "-ac", "1", path])
def type_text(text):
    subprocess.run(["xdotool", "type", "--clearmodifiers", "--delay", "1", "--", text])
    subprocess.run(["xdotool", "key", "--clearmodifiers", "Return"])
def play(path):
    if shutil.which("pw-play"):
        return subprocess.Popen(["pw-play", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
