macOS hotkeys (no extra software):
1. Automator -> New -> Quick Action. Workflow receives: "no input" in "any application". Add "Run Shell Script":
     {PY} {SCRIPT} dictate
   Save as "Voice Dictate". Repeat with `dictate cancel` as "Voice Cancel".
2. System Settings -> Keyboard -> Keyboard Shortcuts -> Services -> General: assign F1 to Voice Dictate, Cmd+F1 to Voice Cancel.
3. First run: grant Microphone + Accessibility to the app that owns the shortcut (System Settings -> Privacy & Security).
Alternative: skhd (brew install skhd) with `f1 : {PY} {SCRIPT} dictate` in ~/.config/skhd/skhdrc.
