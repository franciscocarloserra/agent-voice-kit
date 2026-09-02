"""OS-specific primitives. Each module exposes: record_start(path, cfg) -> Popen, type_text(text), play(path) -> Popen,
ffmpeg_ok() -> bool. Everything else in the kit is platform-independent."""
import sys
if sys.platform.startswith("linux"):
    from . import linux as impl
elif sys.platform == "darwin":
    from . import mac as impl
elif sys.platform.startswith("win"):
    from . import windows as impl
else:
    raise RuntimeError(f"unsupported platform {sys.platform}")
record_start, type_text, play = impl.record_start, impl.type_text, impl.play
