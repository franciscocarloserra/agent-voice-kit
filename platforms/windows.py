import subprocess, sys
def record_start(path, cfg):
    # default dshow mic; list devices with: ffmpeg -list_devices true -f dshow -i dummy
    return subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "dshow", "-i", "audio=default",
                             "-ar", "16000", "-ac", "1", "-af", f"volume={cfg['mic_gain']}", path],
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
def type_text(text):
    import pyautogui, pyperclip
    pyperclip.copy(text); pyautogui.hotkey("ctrl", "v"); pyautogui.press("enter")
def play(path):
    return subprocess.Popen([sys.executable, "-c", f"import winsound;winsound.PlaySound(r'{path}',winsound.SND_FILENAME)"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
