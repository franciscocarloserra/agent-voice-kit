#!/usr/bin/env bash
# UserPromptSubmit hook: "/tts", "/tts on", "/tts off" (slash optional) toggle this session's TTS gate
# without going through the model. Exit 2 blocks the prompt and shows stderr as feedback.
IN=$(cat)
P=$(printf '%s' "$IN" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("prompt","").strip())')
case "$P" in /tts|tts|/tts\ on|tts\ on|/tts\ off|tts\ off) ;; *) exit 0;; esac
G=$(python3 -c 'import json,os;print(os.path.expanduser(json.load(open("/home/usuario/.claude/tts-hook.json")).get("gateFile","~/.config/agent-voice-kit/tts-on")))')
mkdir -p "$(dirname "$G")"
case "$P" in *on) touch "$G";; *off) rm -f "$G";; *) [ -f "$G" ] && rm -f "$G" || touch "$G";; esac
[ -f "$G" ] && echo "tts on" >&2 || echo "tts off" >&2
exit 2
