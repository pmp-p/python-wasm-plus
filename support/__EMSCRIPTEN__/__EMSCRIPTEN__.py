# builtins.__EMSCRIPTEN__ point to this module

import sys, os, builtins

pdb = print

class aio:
    paused = False
    steps = []

    @classmethod
    def step(cls):
        if cls.paused:
            return

        for step in cls.steps:
            try:
                step()
            except Exception as e:
                cls.paused = True


builtins.aio = aio
builtins.builtins = builtins

try:
    import tokenize

    def execfile(filename):
        with tokenize.open(filename) as f:
            code = compile(f.read(), filename, "exec")
            exec(code, __import__("__main__").__dict__, __import__("__main__").__dict__)
    builtins.execfile = execfile
except:
    # mpy already has execfile
    pass




# those  __dunder__ are usually the same used in C conventions.

try:
    __UPY__
except:
    builtins.__UPY__ = hasattr(sys.implementation, "mpy")

try:
    __EMSCRIPTEN__
except:
    builtins.__EMSCRIPTEN__ = sys.platform in ("emscripten", "asm.js", "wasm")

try:
    __WASI__
except:
    builtins.__WASI__ = sys.platform in (
        "wasm",
        "wasi",
    )

try:
    __ANDROID__
except:
    # this *is* the cpython way
    builtins.__ANDROID__ = hasattr(sys, "getandroidapilevel")


# this should be done in site.py / main.c but that's not so easy for cpython.
# last chance to do it since required by aio.*
try:
    undefined
except:

    class sentinel:
        def __bool__(self):
            return False

        def __repr__(self):
            return "∅"

        def __nonzero__(self):
            return 0

        def __call__(self, *argv, **kw):
            if len(argv) and argv[0] is self:
                return True
            print("Null Pointer Exception")

    sentinel = sentinel()
    builtins.undefined = sentinel
    del sentinel


def overloaded(i, *attrs):
    for attr in attrs:
        if attr in i.__class__.__dict__:
            if attr in i.__dict__:
                return True
    return False


builtins.overloaded = overloaded


# force use a fixed, tested version of uasyncio to avoid non-determinism
if __UPY__:
    sys.modules["sys"] = sys
    sys.modules["builtins"] = builtins
    try:
        from . import uasyncio as uasyncio

        print("Warning : using WAPY uasyncio")
    except Exception as e:
        sys.print_exception(e)

else:
    # fix const without writing const in that .py because of micropython parser.
    exec("__import__('builtins').const = lambda x:x", globals(), globals())
    try:
        from . import uasyncio_cpy as uasyncio
    except:
        pdb("WARNING: no uasyncio implementation found")
        uasyncio = aio


sys.modules["uasyncio"] = uasyncio


# check for embedding support or use an emulation from host script __main__ .

try:
    import embed
except:
    print("WARNING: embed module not found, using __main__ for it", file=sys.stderr)
    embed = __import__("__main__")

try:
    embed.log
except:
    pdb("CRITICAL: embed functions not found in __main__")
    embed.enable_irq = print
    embed.disable_irq = print
    embed.log = print
