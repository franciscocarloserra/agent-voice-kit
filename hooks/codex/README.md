# Codex CLI: read replies aloud, toggled with /tts

Goal: when a Codex turn finishes, speak the last assistant message with `voice.py tts "<text>"` if a gate file exists.
`/tts` toggles the gate. Off by default.

Codex CLI has no Stop hook, but it has `notify` in `~/.codex/config.toml`: an external command run after each turn
with a JSON payload on argv[1]. Fields include `type` ("agent-turn-complete") and `last-assistant-message`.
Verify the exact field names against the installed Codex version (`codex --help`, docs/config.md in the openai/codex repo) before relying on them.

Steps for the agent:

1. Create `~/.codex/tts-notify.py`:
   ```python
   #!/usr/bin/env python3
   import sys, json, os, re, subprocess
   GATE = os.path.expanduser("~/.codex/tts-on")          # global gate (Codex gives no session id to notify)
   TTS = [<venv python>, "<kit>/voice.py", "tts"]
   ev = json.loads(sys.argv[1])
   if ev.get("type") != "agent-turn-complete" or not os.path.exists(GATE): sys.exit(0)
   t = ev.get("last-assistant-message") or ""
   t = re.sub(r"```[\s\S]*?```", " ", t); t = re.sub(r"`[^`]*`", " ", t); t = re.sub(r"[*_#>|]+", " ", t)
   t = re.sub(r"\s+", " ", t).strip()[:1500]
   if t: subprocess.Popen(TTS + [t], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
   ```
2. In `~/.codex/config.toml` add: `notify = ["python3", "/home/<user>/.codex/tts-notify.py"]`
3. Create the custom prompt `~/.codex/prompts/tts.md` so `/tts` exists:
   ```
   Toggle read-aloud for this Codex session. Run exactly:
   sh -c 'f=~/.codex/tts-on; if [ -f "$f" ]; then rm "$f"; echo "tts off"; else touch "$f"; echo "tts on"; fi'
   Reply with only the printed state.
   ```
4. Test: `/tts`, then ask anything; the reply should be spoken. `/tts` again silences future replies. `voice.py tts stop` cuts playback.

Notes: the gate is global, not per session, because notify receives no session id. The `/tts` prompt goes through the model
(one round trip); that is the only toggle mechanism Codex offers today.
