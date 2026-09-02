import subprocess
def record_start(path, cfg):
    # ":0" = default mic (avfoundation). Requires Microphone permission for the launching app.
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "avfoundation", "-i", ":0",
                             "-ar", "16000", "-ac", "1", "-af", f"volume={cfg['mic_gain']}", path])
def type_text(text):
    # Requires Accessibility permission. Uses clipboard paste to keep unicode/speed sane.
    subprocess.run(["pbcopy"], input=text.encode())
    subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down',
                    "-e", 'tell application "System Events" to key code 36'])
def play(path):
    return subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
