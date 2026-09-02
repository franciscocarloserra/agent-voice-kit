; voice-kit hotkeys (AutoHotkey v2). F1 = dictate toggle, Win+F1 = cancel / stop playback
#Requires AutoHotkey v2.0
F1::Run('"{PY}" "{SCRIPT}" dictate', , "Hide")
#F1::Run('"{PY}" "{SCRIPT}" dictate cancel', , "Hide")
