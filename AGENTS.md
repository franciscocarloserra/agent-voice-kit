# agent-voice-kit: local dictation (Whisper) + TTS (Supertonic via audio.cpp), Linux / macOS / Windows

One CLI (`voice.py`) for humans, global hotkeys and agent harnesses. All numeric knobs in `config.json`.

## First thing to tell the user

Before doing anything, say this (in the user's language, in your own words, this short):

> With this you can talk to me with your voice instead of typing: press F1, speak, press F1 again, and your words appear wherever you are writing.
> Optionally, I will also be able to answer you out loud.
> To install it I will: (1) install two small programs (ffmpeg and a hotkey helper) which needs your password once,
> (2) download the speech models, about 2 GB, (3) set up the F1 key,
> which on Mac and Linux means you assign it in System Settings while I guide you.
> Do you want to speak only, listen only, or both?

Then follow the recipe below.

## Install (agent recipe)

How to talk to the user during install: before each step, say in one plain sentence what you are about to install and why,
in the user's language. No jargon, no file paths. Examples:
- "I'm installing Whisper so your voice from the microphone becomes text."
- "I'm installing Supertonic so your agent can read its answers out loud."
- "I'm setting up the F1 key so you can start and stop recording from any window."
When a step needs the user's hands (a password, a permission dialog, an install prompt), stop and tell them exactly what to do and why, then wait.

Steps. Each one is idempotent and skippable; `voice.py doctor` is the source of truth for what is still missing.

0. Ask: **speak only, listen only, or both?** Run only the matching parts (`stt`, `tts`, `all`).
1. System packages. USER ACTION likely (admin password or an install prompt). Tell them first.
   - mac: `brew install ffmpeg`
   - windows: `winget install ffmpeg` and, for the hotkey, `winget install AutoHotkey.AutoHotkey`
   - linux: `sudo apt install ffmpeg xdotool`
   Why: ffmpeg records the microphone and handles audio; AutoHotkey / xdotool provide the global key and typing.
2. `python3 voice.py setup [stt|tts|all]`: creates a private Python environment, downloads the models (about 2 GB, takes a few minutes). No user action.
3. (nothing to build; the ONNX engine from step 2 is the default)
4. Ask: run in a terminal (`voice.py serve [stt|tts]`, visible log) or in background at login (`voice.py install-service`)? Then `voice.py check`.
5. `voice.py install-hotkey`. Windows: writes the AutoHotkey script, no action. Mac and Linux: prints steps the USER must do in System Settings (assign F1 and Meta+F1 to the two commands). Walk them through it.
6. macOS only, USER ACTION: grant Microphone and Accessibility to the app that runs the hotkey when the dialog appears. Say why: without them recording is silent and typing does nothing.
7. If they want replies read aloud: install the harness hook (below). Off until toggled with `/tts`; the setting is global and persists.
8. Finish with `voice.py doctor` and a 3-line summary: what is installed, which key does what, how to start and stop it.
   Then offer the optional upgrades below, in one sentence, and stop. Do not start them unless asked.

## Optional upgrades (offer only once everything works)

**Faster text to speech: audio.cpp.** 5-8x faster than the default ONNX engine, replies start almost instantly.
Cost: 10-15 minutes of compiling and a C++ toolchain, which is a USER ACTION if missing
(mac: `xcode-select --install`; windows: Visual Studio Build Tools with the C++ workload; linux: `sudo apt install build-essential cmake`).
Then, no user action:
   ```
   git clone https://github.com/0xShug0/audio.cpp && cd audio.cpp
   scripts/build_linux.sh --backend cuda|cpu --model-set custom --models supertonic --target audiocpp_server   # linux
   scripts/build_metal.sh --model-set custom --models supertonic --target audiocpp_server                      # mac
   scripts/build_windows.ps1 ... (see repo README)                                                             # windows
   cp build/*/bin/audiocpp_server <kit>/bin/ && cp -r model_specs <kit>/bin/
   ```
   Download the GGUF: `voice.py setup tts` already fetches it into `models/Supertonic-3-GGUF`. Restart `serve`; `doctor` shows the engine in use.

**Background service.** If they chose the terminal at step 4 and later want it always on: `voice.py install-service`. No user action.

**A different voice or speed.** `config.json` -> `tts.voice` (F1..F5, M1..M5) and `tts.speed`. No restart needed for speed.

## Use
```
voice.py dictate            F1: start recording; F1 again: transcribe and type into the active window
voice.py dictate cancel     Meta/Win/Cmd+F1: drop recording and stop any TTS playback
voice.py tts "text"         speak (chunked if long). -v F1..F5/M1..M5   -o out.ogg saves instead
voice.py tts stop | speed [1.5|+|-]
```
Harness hooks call `voice.py tts "<text>"` and `voice.py tts stop`. Nothing else is needed.

## Ports
whisper 6969, tts 6971, audiocpp 6972 (127.0.0.1 only). Override with `VOICEKIT_CONFIG=/path/to/config.json`.

## Layout
`voice.py` CLI · `server/` two tiny HTTP servers · `platforms/` the only OS-specific code (record, type, play) ·
`hotkeys/`, `service/` templates · `bin/` audiocpp binary · `models/` weights (gitignored).

## Harness hooks (agent replies read aloud)

Principle: on "assistant turn finished", spawn `<tts bin> "<text>"` detached; on user interrupt, `<tts bin> stop`.
Gate: one global, persistent file `~/.config/agent-voice-kit/tts-on`, shared by every harness. `/tts` anywhere toggles it
for all (`/tts on|off` forces). Off until first toggled. Strip code blocks and markdown before speaking, cap at ~1500 chars.
Reference implementations live in `hooks/<harness>/`. Point `ttsBin` at `<venv python> <kit>/voice.py tts` (or any equivalent CLI).

What we learned per harness:

- **Claude Code** (`hooks/claude-code/`): two hooks in `~/.claude/settings.json`.
  `Stop` (async) runs `tts-stop.sh`, which reads the last assistant text from `transcript_path` (JSONL; lines with `type: assistant`,
  `message.content[].type == text`) and speaks it if the gate exists. `UserPromptSubmit` runs `tts-toggle.sh`, which matches
  `/tts`, `tts on`, `tts off`, flips the gate and exits 2 with the state on stderr: the prompt never reaches the model, instant.
  Do NOT implement `/tts` as a skill: it costs two model round trips. Hooks load at session start, so restart after editing settings.
  Pitfall: a bash script reading the hook JSON from stdin must not also feed a heredoc to python from stdin; pass the event on fd 3.
- **pi** (`hooks/pi/tts-hook.ts`): extension in `~/.pi/agent/extensions/`. `pi.registerCommand("tts")` toggles the gate file,
  `pi.on("message_end")` speaks assistant messages. Config in `~/.pi/agent/tts-hook.json`, reread per message. pi restart reloads the .ts.
- **OpenCode** (`hooks/opencode/`): plugin `~/.config/opencode/plugin/tts.ts` (needs `@opencode-ai/plugin` in `~/.config/opencode/package.json`).
  `command.execute.before` intercepts `/tts`, toggles the gate, shows a toast via `client.tui.showToast`, and empties `output.parts`
  so nothing goes to the model. `event` on `session.idle` fetches `client.session.messages({path:{id}})`, takes the last
  `info.role == "assistant"` message's text parts and speaks them. A `command/tts.md` file must exist for `/tts` to be a command.
- **Codex CLI** (`hooks/codex/README.md`): no hooks, but `notify = [...]` in `~/.codex/config.toml` runs a command after each turn
  with a JSON payload (`type: agent-turn-complete`, `last-assistant-message`). `/tts` can only be a custom prompt
  (`~/.codex/prompts/tts.md`) that asks the model to touch the gate file: one model round trip, unavoidable there. Untested.
- **Gemini CLI**: not done. Look for a turn-finished hook or notification setting; same pattern.

Dictation needs no hook: it is a global key that types text into whatever window is focused.
