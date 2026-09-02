[English](README.md) · **Español**

# agent-voice-kit

## Hablá con tu agente de IA en vez de escribir

# 🎤 ➜ 🤖 ➜ 🔊

```
vos hablás                     el agente responde               vos lo escuchás (opcional)
apretás F1, hablás, F1         el texto aparece en la ventana   la respuesta se lee en voz alta
```

Apretás una tecla, decís lo que querés, la apretás de nuevo. Tus palabras quedan escritas donde estabas escribiendo, en cualquier app.
Si querés, el agente te lee la respuesta.


https://github.com/user-attachments/assets/5b833182-b347-43ad-ab08-6782d41221e6


Todo corre en tu computadora. No se manda nada a ningún lado y no hay que esperar a un servidor: el texto está ahí en el momento en que dejás de hablar.

## Instalar

Pegale esto a tu agente (Claude Code, pi, Codex, Gemini CLI):

```
Instalá https://github.com/<you>/agent-voice-kit siguiendo su AGENTS.md
```

<ins>**Lo que vas a tener que hacer a mano.**</ins> El agente no puede clickear esto por vos:
- Mac: escribir tu contraseña para `brew`, asignar los dos atajos en Ajustes del Sistema, aceptar los diálogos de Micrófono y Accesibilidad.
- Windows: aprobar las instalaciones de ffmpeg y AutoHotkey cuando winget lo pida.
- Linux: escribir tu contraseña de `sudo` para los paquetes, asignar los dos atajos en la configuración de atajos de tu escritorio.

## Usar

| tecla | qué hace |
|---|---|
| F1 | empieza a grabar; apretar F1 de nuevo escribe tus palabras donde está el cursor, en cualquier app |
| Meta+F1 | cancela la grabación o calla al agente |
| `/tts` | prende o apaga la lectura en voz alta, en cualquier harness. Queda así hasta que lo vuelvas a tocar |

`python3 voice.py serve` corre los servidores en una terminal, `install-service` los deja corriendo al iniciar sesión, `doctor` dice qué falta, y `tts speed 1.5` ajusta la velocidad de lectura.

## Para tener en cuenta

**Conviene tener GPU.** NVIDIA en Linux o Windows, o cualquier Mac con Apple Silicon. Solo con CPU funciona, pero tarda unos segundos por oración.

**Los modelos se descargan, no vienen en el repo.** El setup baja Whisper large-v3-turbo y Supertonic 3 de Hugging Face, unos 2 GB.

**Se instalan algunas cosas en tu sistema.** Python 3.11+ y ffmpeg en todos, AutoHotkey en Windows, xdotool en Linux, drivers NVIDIA actualizados si tenés esa GPU.

**La voz funciona de entrada, y puede ir más rápido.** El motor por defecto no necesita compilar nada. Si querés que las respuestas arranquen al instante, pedile al agente que compile audio.cpp (unos 15 minutos, 5 a 8 veces más rápido).

**macOS te va a pedir permisos.** Micrófono y Accesibilidad, una sola vez. Sin ellos la grabación sale muda o no escribe.

**La lectura en voz alta está apagada hasta que la prendas.** `/tts` la prende para todos los harness y queda así. El dictado no necesita nada: escribe en la ventana que tenga el foco.

**Todo es personalizable.** Modelos, voz, velocidad de lectura, atajos, puertos. Pedile a tu agente que lo cambie; todo vive en `config.json`.

