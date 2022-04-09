print("= ${__FILE__} in websim  for  ${PLATFORM} =")


#===============================================
import sys, os, builtins

# aioprompt ======== have asyncio loop runs interleaved with repl ============
# from https://github.com/pmp-p/aioprompt

scheduled = None
scheduler = None
wrapper_ref = None
loop = None

unsupported=('bionic','wasm','emscripten','wasi','android')

#TODO: all readline replacement with accurate timeframes
#TODO: droid integrate application lifecycle

if sys.platform not in unsupported:
    import sys
    import builtins
    import ctypes

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
    pdb("aiorepl no possible on", sys.platform, "expect main to block")
    schedule = None

#=====================================================

sys.path.append("${PLATFORM}")

import aio
import aio.prepro
import aio.cross
aio.cross.simulator = True



# cannot fake a cpu __WASM__ will be False

# but fake the platform AND the module
sys.platform = 'emscripten'

class __EMSCRIPTEN__:
    @classmethod
    def PyConfig_InitPythonConfig(*argv):pass
    @classmethod
    def init_platform(*argv):pass
    @classmethod
    def flush(cls):
        sys.stdout.flush()
        sys.stderr.flush()

sys.modules['__EMSCRIPTEN__'] = __EMSCRIPTEN__


exec( open("${PYTHONRC}").read() , globals(), globals())



#===============================================================================

import aio.clock


#===============================================================================
import inspect
import asyncio

DEBUG = 1

if __name__ == '__main__':
    aio.DEBUG = DEBUG

    print("main may block depending on your platform readline implementation")

    if schedule:
        aio.cross.scheduler = schedule

    #asyncio.create_task( aio.clock.loop() )
    aio.clock.start()

    __main__ = execfile("${__FILE__}")
    # on not arduino style, expect user to run main with asyncio.run( main() )
    # should be already called at this point.


    setup = __main__.__dict__.get('setup',None)
    loop = __main__.__dict__.get('loop',None)

    # arduino naming is just wrong anyway
    if loop is None:
        loop  = __main__.__dict__.get('step', None )

    if loop and setup:
        print("found setup, loop")
        if setup:
            setup()
    if loop:
        if not inspect.iscoroutinefunction(loop):
            if loop and setup:
                print("loop is not a coroutine, running arduino style")
                aio.steps.append( loop )
            # TODO : use a wrapper for non readline systems.

            async def coro():
                loop()
        else:
            coro = loop

        if not aio.started:
            aio.started = True
            if DEBUG:pdb("200: starting aio scheduler")
            aio.cross.scheduler( aio.step, 1)

    print(" -> asyncio.run passed")
    sys.stdout.flush()
    sys.stderr.flush()















#
