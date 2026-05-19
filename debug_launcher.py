"""Debug wrapper for Lexi GUI — injects click logging, call tracing, exception hooks.

Console window: stdout/stderr visible, survives GUI crash.
Usage: packaged into Lexi_debug.exe with console=True, upx=False.
"""

import sys
import time
import traceback
import threading
import functools
from datetime import datetime


def _ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

# ── 1. Global exception hooks ──────────────────────────────

_original_excepthook = sys.excepthook

def _debug_excepthook(exc_type, exc_value, exc_tb):
    print(f"\n[{_ts()}] ╔══ FATAL ERROR ═══════════════════════════════")
    print(f"[{_ts()}] ║ {exc_type.__name__}: {exc_value}")
    for line in traceback.format_exception(exc_type, exc_value, exc_tb):
        for l in line.rstrip().split("\n"):
            print(f"[{_ts()}] ║ {l}")
    print(f"[{_ts()}] ╚══════════════════════════════════════════════")
    print(f"[{_ts()}] Console alive — press Ctrl+C to exit")

sys.excepthook = _debug_excepthook


def _debug_thread_excepthook(args):
    print(f"\n[{_ts()}] ╔══ THREAD CRASH ═══════════════════════════════")
    print(f"[{_ts()}] ║ Thread: {args.thread.name}")
    print(f"[{_ts()}] ║ {args.exc_type.__name__}: {args.exc_value}")
    tb = getattr(args, 'exc_traceback', None) or getattr(args, 'exc_tb', None)
    if tb is not None:
        for line in traceback.format_exception(args.exc_type, args.exc_value, tb):
            for l in line.rstrip().split("\n"):
                print(f"[{_ts()}] ║ {l}")
    else:
        traceback.print_exception(args.exc_type, args.exc_value, None)
    print(f"[{_ts()}] ╚══════════════════════════════════════════════")

threading.excepthook = _debug_thread_excepthook

# ── 2. Call tracing ────────────────────────────────────────

_trace_depth = [0]

def trace(func):
    """Decorator: log function entry, exit, and duration."""
    @functools.wraps(func)
    def wrapper(*args, **kw):
        indent = "  " * _trace_depth[0]
        arg_str = ", ".join(
            [repr(a)[:60] for a in args[:3]] +
            [f"{k}={repr(v)[:40]}" for k, v in list(kw.items())[:3]]
        )
        print(f"[{_ts()}] {indent}→ {func.__name__}({arg_str})")
        _trace_depth[0] += 1
        t0 = time.time()
        try:
            result = func(*args, **kw)
            dt = (time.time() - t0) * 1000
            _trace_depth[0] -= 1
            indent = "  " * _trace_depth[0]
            r_str = repr(result)[:80] if result is not None else "ok"
            print(f"[{_ts()}] {indent}← {func.__name__} → {r_str}  ({dt:.0f}ms)")
            return result
        except Exception as e:
            dt = (time.time() - t0) * 1000
            _trace_depth[0] -= 1
            indent = "  " * _trace_depth[0]
            print(f"[{_ts()}] {indent}✗ {func.__name__} RAISED {type(e).__name__}: {e}  ({dt:.0f}ms)")
            raise
    return wrapper

# ── 3. Monkey-patch Flet button on_click ────────────────────

def _wrap_on_click(original, widget_type, widget_id):
    """Wrap an on_click handler with click logging."""
    if original is None:
        return None

    @functools.wraps(original)
    def wrapper(e=None):
        print(f"[{_ts()}] 🖱 CLICK: {widget_type}#{id(widget_id)}")
        return original(e)

    return wrapper


_original_filled_init = None
_original_outlined_init = None
_original_textbutton_init = None

def _install_click_hooks():
    """Patch Flet button constructors to wrap on_click with logging."""
    try:
        import flet as ft

        def _patch(cls, name):
            orig_init = cls.__init__

            @functools.wraps(orig_init)
            def new_init(self, *args, **kwargs):
                if "on_click" in kwargs and kwargs["on_click"] is not None:
                    kwargs["on_click"] = _wrap_on_click(
                        kwargs["on_click"], name, id(self)
                    )
                orig_init(self, *args, **kwargs)
                if hasattr(self, "on_click") and callable(self.on_click):
                    self.on_click = _wrap_on_click(
                        self.on_click, name, id(self)
                    )

            cls.__init__ = new_init
            print(f"[{_ts()}]   hooked {name}.on_click")

        _patch(ft.FilledButton, "FilledButton")
        _patch(ft.OutlinedButton, "OutlinedButton")
        _patch(ft.TextButton, "TextButton")
        _patch(ft.ElevatedButton, "ElevatedButton")
        _patch(ft.IconButton, "IconButton")

        # NavigationRail: patch on_change
        _orig_nav_init = ft.NavigationRail.__init__

        @functools.wraps(_orig_nav_init)
        def _nav_init(self, *args, **kwargs):
            original_on_change = kwargs.pop("on_change", None)
            if original_on_change:

                @functools.wraps(original_on_change)
                def _wrapped(e):
                    idx = e.control.selected_index if hasattr(e, 'control') else '?'
                    print(f"[{_ts()}] 🖱 NAV: NavigationRail → index {idx}")
                    return original_on_change(e)

                kwargs["on_change"] = _wrapped
            _orig_nav_init(self, *args, **kwargs)

        ft.NavigationRail.__init__ = _nav_init
        print(f"[{_ts()}]   hooked NavigationRail.on_change")

    except Exception as e:
        print(f"[{_ts()}] ⚠ click hook install failed: {e}")

# ── 4. Launch ──────────────────────────────────────────────

print(f"[{_ts()}] ╔══ Lexi Debug Launcher ════════════════════════════")
print(f"[{_ts()}] ║ Python:  {sys.version.split()[0]}")
print(f"[{_ts()}] ║ Time:    {_ts()}")
print(f"[{_ts()}] ║ Args:    {sys.argv[1:] if len(sys.argv) > 1 else '(none)'}")
print(f"[{_ts()}] ╠══════════════════════════════════════════════════")
print(f"[{_ts()}] ║ Installing click hooks...")

_install_click_hooks()

print(f"[{_ts()}] ║ Importing gui...")
import sys as _sys
_sys._lexi_debug = True  # 通知 gui.py 输出控制台日志
import gui

print(f"[{_ts()}] ║ Launching GUI...")
print(f"[{_ts()}] ╚══════════════════════════════════════════════════")
print()

try:
    import flet as ft
    ft.app(target=gui.main)
except Exception as e:
    print(f"\n[{_ts()}] ╔══ GUI MAIN CRASH ═══════════════════════════════")
    traceback.print_exc()
    print(f"[{_ts()}] ╚══════════════════════════════════════════════════")
    print(f"[{_ts()}] Console alive — press Ctrl+C to exit")
