**English** · [Español](README.es.md)

# agent-voice-kit

## Talk with your AI agent instead of typing

# 🎤 ➜ 🤖 ➜ 🔊

```
you speak                  the agent answers              you hear it (optional)
press F1, talk, press F1   the text lands in the window   the reply is read aloud
```

Press a key, say what you want, press it again. Your words are typed wherever you were writing, in any app.
If you want, the agent reads its answer back to you.


https://github.com/user-attachments/assets/5b833182-b347-43ad-ab08-6782d41221e6


It all runs on your own computer. Nothing is sent anywhere, and there is no waiting for a server: the text is there the moment you stop talking.

## Install

Paste this into your agent (Claude Code, pi, Codex, Gemini CLI):

```
Install https://github.com/franciscocarloserra/agent-voice-kit/ following its AGENTS.md
```

<ins>**What you will have to do by hand.**</ins> The agent cannot click these for you:
- Mac: type your password for `brew`, assign the two hotkeys in System Settings, accept the Microphone and Accessibility dialogs.
- Windows: approve the ffmpeg and AutoHotkey installs when winget asks.
- Linux: type your `sudo` password for the packages, assign the two hotkeys in your desktop's shortcut settings.

## Use

| key | what it does |
|---|---|
| F1 | starts recording; pressing F1 again types your words at the cursor, in any app |
| Meta+F1 | cancels the recording or silences the agent |
| `/tts` | turns read-aloud on or off, in any harness. Persists until you toggle it again |

`python3 voice.py serve` runs the servers in a terminal, `install-service` runs them at login, `doctor` reports what is missing, and `tts speed 1.5` sets the reading speed.

## Good to know

**You want a GPU.** NVIDIA on Linux or Windows, or any Apple Silicon Mac. On CPU only it works but takes a few seconds per sentence.

**Models are downloaded, not bundled.** Setup pulls Whisper large-v3-turbo and Supertonic 3 from Hugging Face, about 2 GB.

**A few things get installed on your system.** Python 3.11+ and ffmpeg everywhere, AutoHotkey on Windows, xdotool on Linux, current NVIDIA drivers if you have that GPU.

**Text to speech works out of the box, and can get faster.** The default engine needs no build. If you want replies to start instantly, ask the agent to build audio.cpp (about 15 minutes, 5 to 8 times faster).

**macOS will ask for permissions.** Microphone and Accessibility, once. Without them dictation records silence or does not type.

**Read-aloud is off until you turn it on.** `/tts` toggles it for every harness and it stays that way. Dictation needs nothing: it types into whatever window has focus.

**Everything is customizable.** Models, voice, reading speed, hotkeys, ports. Just ask your agent to change it; it all lives in `config.json`.

