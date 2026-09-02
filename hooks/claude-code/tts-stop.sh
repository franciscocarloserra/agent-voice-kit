#!/usr/bin/env bash
# Claude Code Stop hook: speak the last assistant message if this session's TTS gate is on.
# Config: ~/.claude/tts-hook.json. Gate: $gateDir/<session_id> (toggled by /tts skill).
CFG="$HOME/.claude/tts-hook.json"
python3 - "$CFG" 3<&0 <<'PY'
import sys, json, os, re, subprocess
cfg = json.load(open(sys.argv[1]))
ev = json.load(os.fdopen(3))
sid = ev.get("session_id", "")
if not cfg.get("enabled") or not os.path.exists(os.path.expanduser(cfg.get("gateFile", "~/.config/agent-voice-kit/tts-on"))):
    sys.exit(0)
text = ""
for line in open(ev["transcript_path"], encoding="utf-8", errors="ignore"):
    try: o = json.loads(line)
    except Exception: continue
    if o.get("type") != "assistant": continue
    parts = [b.get("text", "") for b in o.get("message", {}).get("content", []) if b.get("type") == "text"]
    if parts: text = "\n".join(parts)
t = text
if cfg.get("stripCodeBlocks"): t = re.sub(r"```[\s\S]*?```", " ", t)
if cfg.get("stripMarkdown"):
    t = re.sub(r"`[^`]*`", " ", t); t = re.sub(r"[*_#>|]+", " ", t); t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
t = re.sub(r"\s+", " ", t).strip()[: cfg.get("maxChars", 1500)]
if not t: sys.exit(0)
args = [cfg["ttsBin"]] + (["-v", cfg["voice"]] if cfg.get("voice") else []) + [t]
subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
PY
exit 0
