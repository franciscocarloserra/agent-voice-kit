macOS hotkeys. Two routes: skhd (recommended) or Automator Quick Actions (no extra software).

## skhd (recommended)

Services shortcuts are unreliable: they are stored in the `pbs` preference domain, they only register
predictably when System Settings itself writes them, and an app's own shortcut wins over a Service that
shares the same combo. skhd binds at the event-tap level, so the key works in every app.

1. `brew install koekeishiya/formulae/skhd`
2. Put this in `~/.config/skhd/skhdrc`:

       cmd - 1       : {PY} {SCRIPT} dictate
       cmd + alt - 1 : {PY} {SCRIPT} dictate cancel

3. `skhd --start-service`
4. Grant Accessibility to skhd: System Settings -> Privacy & Security -> Accessibility -> `+` ->
   press Cmd+Shift+G, enter `/opt/homebrew/bin/skhd`, enable the toggle.
5. **Restart the service after granting**: `skhd --restart-service`. skhd checks the permission once at
   startup and aborts with `must be run with accessibility access` if it is missing; granting the
   permission does not relaunch it, so a first run before step 4 stays dead until you restart it.
6. First `cmd - 1` triggers the Microphone prompt, now owned by skhd. Accept it, or recording is silent.

Logs are at `/tmp/skhd_$USER.err.log` — the stderr of the commands skhd launches ends up there, which is
where a failing dictation surfaces.

Pick a combo no app claims. `cmd - 1` is "go to tab 1" in most browsers and skhd swallows it globally;
`ctrl + alt - 1` or a function key avoids the conflict.

## Automator Quick Actions (no extra software)

1. Automator -> New -> Quick Action. Workflow receives "no input" in "any application".
   Add "Run Shell Script" with:

       {PY} {SCRIPT} dictate

   Save as "Voice Dictate". Repeat with `dictate cancel` as "Voice Cancel".
2. System Settings -> Keyboard -> Keyboard Shortcuts -> Services -> General: assign the shortcuts.
   Assign them here in the UI — writing `NSServicesStatus` with `defaults` does not reliably take effect,
   because `pbs` will not pick up the override until a re-login.
3. Grant Microphone + Accessibility to the app that owns the shortcut
   (System Settings -> Privacy & Security).

## Both routes

The kit types with a clipboard paste followed by Return (`platforms/mac.py`), so the shortcut submits
whatever field has focus. Test it in a scratch window, not in a chat or a terminal you care about.
