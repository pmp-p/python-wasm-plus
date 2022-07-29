# builtins.__EMSCRIPTEN__
# builtins.__WASI__
# builtins.__ANDROID__   also defines __ANDROID_API__
# builtins.__UPY__ too can point to this module

import sys, os, builtins

# are they not ?
builtins.builtins = builtins

from platform import *

try:
    import aio
except Exception as e:
    try:
        sys.print_exception(e)
    except:
        __import__("traceback").print_exc()

    # non asyncio stepper as a fallback
    class aio:
        paused = False
        steps = []
        oneshots = []
        ticks = 0
        protect = []
        enter = 0
        spent = 0

        @classmethod
        def breakpointhook(cls, *argv, **kw):
            cls.paused = True

        @classmethod
        def step(cls):
            cls.enter = time.time()
            try:
                if cls.paused:
                    return

                if aio.protect:
                    aio.protect.clear()

                try:
                    # NEED a scheduler + timesort
                    early = []
                    while len(cls.oneshots):
                        deferred = cls.oneshots.pop()
                        if deferred[0] > cls.ticks:
                            deferred[0] -= 1
                            early.append(deferred)
                        else:
                            _, fn, argv, kw = deferred
                            fn(*argv, **kw)
                    while len(early):
                        cls.oneshots.append(early.pop())

                    for step in cls.steps:
                        step()
                except Exception as e:
                    sys.print_exception(e)
                    cls.paused = True
                    pdb("- aio paused -")
            finally:
                cls.leave = time_time()
                cls.spent = cls.leave - cls.enter
        @classmethod
        def defer(cls, fn, argv, kw, deadline=0):
            # FIXME: set ticks + deadline for alarm
            cls.oneshots.append(
                [
                    cls.ticks + deadline,
                    fn,
                    argv,
                    kw,
                ]
            )


def breakpointhook(*argv, **kw):
    aio.paused = True


def shed_yield():
    #TODO: coroutine id as pid
    print("86", time_time() - aio.enter, aio.spent )
    return True



sys.breakpointhook = breakpointhook

define("aio", aio)


this = __import__(__name__)

# those  __dunder__ are usually the same used in C conventions.


try:
    __UPY__
except:
    if hasattr(sys.implementation, "mpy"):
        builtins.__UPY__ = this
    else:
        builtins.__UPY__ = None


try:
    __EMSCRIPTEN__
except:
    if sys.platform in ("emscripten", "asm.js", "wasm"):
        builtins.__EMSCRIPTEN__ = this
    else:
        builtins.__EMSCRIPTEN__ = None

    is_browser = not sys._emscripten_info.runtime.startswith('Node.js')

    from embed import *

    if not __UPY__:
        from platform import *
        from embed_browser import *
        from embed_emscripten import *
    else:
        pdb(__file__,":107 no browser/emscripten modules yet")


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
    try:
        from . import uasyncio_cpy as uasyncio
    except:
        pdb("INFO: no uasyncio implementation found")
        uasyncio = aio

sys.modules["uasyncio"] = uasyncio


def init_platform(embed):
    # simulator won't run javascript for now
    if not hasattr(embed, "run_script"):
        pdb("186: no js engine")
        return False

    import json

    def js(code, delay=0):
        # keep a ref till next loop
        aio.protect.append(code)
        if not delay:
            result = embed.run_script(f"JSON.stringify({code})")
            if result is not None:
                return json.loads(result)
        elif delay < 0:
            embed.run_script(code)
        else:
            embed.run_script(code, int(delay))

    embed.js = js


    if __WASM__:
        import _thread

        try:
            _thread.start_new_thread(lambda: None, ())
        except RuntimeError:
            pdb("WARNING: that wasm build does not support threads")


ROOTDIR = f"/data/data/{sys.argv[0]}/assets"


def explore(root):
    global prelist, preloadedWasm, preloadedImages, preloadedAudios, counter

    counter = 0

    import shutil
    preloads = f"{preloadedImages} {preloadedAudios} {preloadedWasm}".split(" ")
    print(f"194: preloads {preloads}")

    for current, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.find('.')>1:
                ext = filename.rsplit(".", 1)[-1].lower()
                if ext in preloads:
                    counter += 1
                    src = f"{current}/{filename}"
                    dst = "/tmp/pre" + str(counter).zfill(4) + "." + ext
                    print(src,"->",dst)
                    shutil.copyfile(src, dst)
                    prelist[src] = dst
                    embed.preload(dst)



def fix_preload_table():
    global prelist, preloadedWasm, preloadedImages, preloadedAudios

    if embed.counter() < 0:
        pdb("233: asset manager not ready 0>", embed.counter())
        aio.defer(fix_preload_table, (), {}, delay=60)
    else:
        pdb("236: all assets were ready at", embed.counter())

    for (
        src,
        dst,
    ) in prelist.items():
        ext = dst.rsplit(".", 1)[-1]
        if ext in preloadedImages:
            ptype = "preloadedImages"
        elif ext in preloadedAudios:
            ptype = "preloadedAudios"
        elif ext == "so":
            ptype = "preloadedWasm"

        src = f"{ptype}[{repr(src)}]"
        dst = f"{ptype}[{repr(dst)}]"
        swap = f"({src}={dst}) && delete {dst}"
        embed.js(swap, -1)
        # print(swap)


def PyConfig_InitPythonConfig(PyConfig):
    global preloadedWasm, preloadedImages, preloadedAudios

    # simulator won't run javascript for now
    if not hasattr(embed, "run_script"):
        pdb("209: no js engine")
        return False

    # do not do stuff if not called properly from our js loader.
    if PyConfig.get("executable", None) is None:
        # running in sim
        return False

    sys.executable = PyConfig["executable"]

    preloadedWasm = "so"
    preloadedImages = "png jpeg jpg gif"
    preloadedAudios = "wav ogg mp4"


    def preload_apk(p=None):
        global counter, prelist, ROOTDIR
        global explore, preloadedWasm, preloadedImages, preloadedAudios
        ROOTDIR = p or ROOTDIR
        if os.path.isdir(ROOTDIR):
            os.chdir(ROOTDIR)
        else:
            pdb(f"cannot chdir to {ROOTDIR=}")
            return

        ROOTDIR = os.getcwd()
        LSRC = len(ROOTDIR) + 1
        counter = -1
        prelist = {}

        sys.path.insert(0, ROOTDIR)

        explore(ROOTDIR)

        if counter<0:
            pdb(f"{ROOTDIR=}")
            pdb(f"{os.getcwd()=}")

        print(f"assets found :", counter)
        if not counter:
            embed.run()

        return True

    import aio

    if PyConfig.get("interactive", False):
        import aio.clock
        aio.clock.start(x=80)
        # org.python REPL no preload !
        preload = (sys.argv[0] != 'org.python')
    else:
        # org.python script
        preload = True

    if preload and preload_apk():

        def fix_preload_table_apk():
            global fix_preload_table, ROOTDIR
            fix_preload_table()

            os.chdir(ROOTDIR)

            if os.path.isfile("main.py"):
                print(f"317: running {ROOTDIR}/main.py for {sys.argv[0]} (deferred)")
                aio.defer(execfile, [f"{ROOTDIR}/main.py"], {})
            else:
                pdb(f"no main found for {sys.argv[0]} in {ROOTDIR}")

            aio.defer(embed.prompt, (), {}, delay=2000)

        # C should unlock aio loop when preload count reach 0.

    else:
        def fix_preload_table_apk():
            global fix_preload_table_apk, ROOTDIR
            pdb("no assets preloaded")
            os.chdir(ROOTDIR)
            aio.defer(embed.prompt, (),{})

        # unlock embed looper because no preloading
        embed.run()

    aio.defer(fix_preload_table_apk, (), {}, delay=1000)

    # go pods !
    aio.started = True
































#
