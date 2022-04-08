print("= ${__FILE__} in websim  for  ${PLATFORM} =")

import sys, os, builtins

sys.path.append("${PLATFORM}")

import aio.prepro
import aio.cross

import inspect

# fake it
sys.platform = 'emscripten'
define('__WASM__', True)



class __EMSCRIPTEN__:
    @classmethod
    def PyConfig_InitPythonConfig(*argv):pass

define('__EMSCRIPTEN__', __EMSCRIPTEN__)

exec( open("${PYTHONRC}").read() , globals(), globals())


import aio

scheduled = None
scheduler = None
wrapper_ref = None
loop = None

# ======== have asyncio loop runs interleaved with repl

#TODO: all readline replacement with accurate timeframes
#TODO: droid integrate application lifecycle

if sys.platform not in ('bionic','wasm','emscripten','wasi','android') or aio.cross.sim:
    import sys
    import builtins

    if not sys.flags.inspect:
        print("Error: interpreter must be run with -i or PYTHONINSPECT must be set for using", __name__)
        raise SystemExit


    def init():
        global scheduled, scheduler, wrapper_ref
        #! KEEP IT WOULD BE GC OTHERWISE!
        # wrapper_ref

        scheduled = []
        import ctypes
        try:
            ctypes = ctypes.this
        except:
            pass

        c_char_p = ctypes.c_char_p
        c_void_p = ctypes.c_void_p

        HOOKFUNC = ctypes.CFUNCTYPE(c_char_p)
        PyOS_InputHookFunctionPointer = c_void_p.in_dll(ctypes.pythonapi, "PyOS_InputHook")

        def scheduler():
            global scheduled
            # prevent reenter
            lq = len(scheduled)
            while lq:
                fn, a = scheduled.pop(0)
                fn(a)
                lq -= 1

        wrapper_ref = HOOKFUNC(scheduler)
        scheduler_c = ctypes.cast(wrapper_ref, c_void_p)
        PyOS_InputHookFunctionPointer.value = scheduler_c.value

        # replace with faster function
        def schedule(fn, a):
            scheduled.append((fn, a))

        sys.modules[__name__].schedule = schedule

        # now the init code is useless
        del sys.modules[__name__].init



    def schedule(fn, a):
        global scheduled
        if scheduled is None:
            init()
        scheduled.append((fn, a))

else:
    schedule = None

# ========== asyncio stepping ================

def step(arg):
    global aio
    if aio.paused is None:
        aio.loop.close()
        return

    if aio.loop.is_closed():
        sys.__stdout__.write(f"\n:async: stopped\n{sys.ps1}")
        return

    aio.step()

    if arg:
        schedule(step, arg)


async def asleep_ms(ms=0):
    await aio.sleep(float(ms)/1000)




async def asleep_ms(ms=0):
    await aio.sleep(float(ms)/1000)


if __name__ == '__main__':
    __main__ = execfile("${__FILE__}")
    setup = __main__.__dict__.get('setup',None)
    loop  = __main__.__dict__.get('loop',None)

    if loop and setup:
        print("starting setup+loop")
    else:
        pdb("wrong setup/loop code configuration")
        raise SystemEXit

    setup()

    if schedule is None:
        print("aiorepl no possible on",sys.platform)
        while True:
            loop()
    else:
        coro = loop
        if not inspect.iscoroutinefunction(coro):
            del coro
            async def coro():
                loop()

        aio.run( coro(), debug = step )
        print("launched")
