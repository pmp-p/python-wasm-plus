import sys
import builtins

DEBUG=True

# try to acquire syslog early
try:
    import embed
    builtins.pdb = embed.log
except:
    def pdb(*argv):
        print(*argv, file=sys.__stderr__)
    builtins.pdb = pdb
    #builtins.embed = __import__('__main__')

# cascade debug by default
from . import cross
cross.DEBUG = DEBUG

#TODO: dbg stuff should be taken from the platform module in aio.cross
if DEBUG:
    import trace
    _tracer = trace.Trace(count=False, trace=True)
    def sys_trace(fn, *argv,**kw):
        global _tracer
        return _tracer.runfunc(fn, *argv, **kw)
else:
    def sys_trace(fn, *argv,**kw):
        pdb("debugging is OFF")

define("sys_trace", sys_trace)


try:
    import embed
    flush = embed.flush
except:
    def flush():
        sys.stdout.flush()
        sys.stderr.flush()
    if __WASM__:
        print("""



    WARNING: no flush method available, raw TTY may suffer



""")



from asyncio import *


# Within a coroutine, simply use `asyncio.get_running_loop()`,
# since the coroutine wouldn't be able
# to execute in the first place without a running event loop present.
try:
    loop = get_running_loop()
except RuntimeError:
    # depending on context, you might debug or warning log that a running event loop wasn't found
    loop = get_event_loop()


import asyncio.events
asyncio.events._set_running_loop(loop)


started = False
paused = False
steps = []
oneshots = []
ticks = 0
protect = []



sys.modules['asyncio'] = __import__(__name__)



def defer(fn, argv=(), kw={}, deadline = 0):
    global ticks, oneshots
    # FIXME: set ticks + deadline for alarm
    oneshots.append( [ticks+deadline, fn,argv,kw,] )

inloop = False

# this runs both asyncio loop and the arduino style stepper
def step(*argv):
    global inloop, paused, started, loop, oneshots, protect, ticks, steps, step, flush
    if inloop:
        pdb("70: aio not re-entrant !")
        return
    inloop = True

    ticks += 1

# TODO: fix global clock accordingly
    if not paused:

        if protect:
            protect.clear()

        try:
            # NEED a scheduler + timesort
            early = []
            while len(oneshots):
                deferred = oneshots.pop()
                if deferred[0] > ticks:
                    deferred[0] -= 1
                    early.append( deferred )
                else:
                    _, fn,argv,kw = deferred
                    fn(*argv,**kw)
            while len(early):
                oneshots.append(early.pop() )

            for onestep in steps:
                onestep()

            #loop.call_soon(loop.stop)
            #loop.run_forever()
            if started:
                loop._run_once()

        except Exception as e:
            sys.print_exception(e)
            paused = True
            pdb("- aio paused -")

    inloop = False

    if cross.scheduler:
        cross.scheduler(step, 1)

    flush()



async def sleep_ms(ms=0):
    await sleep(float(ms)/1000)


def _set_task_name(task, name):
    if name is not None:
        try:
            set_name = task.set_name
        except AttributeError:
            warnings.warn("Task.set_name() was added in Python 3.8, "
                      "the method support will be mandatory for third-party "
                      "task implementations since 3.13.",
                      DeprecationWarning, stacklevel=3)
        else:
            set_name(name)

def create_task(coro, *, name=None, context=None):
    """Schedule the execution of a coroutine object in a spawn task.

    Return a Task object.
    """
    global loop
    if context is None:
        # Use legacy API if context is not needed
        task = loop.create_task(coro)
    else:
        task = loop.create_task(coro, context=context)

    _set_task_name(task, name)
    return task


# save orignal asyncio.run in case platform does not support readline hooks.
# __run__ = run

#
def run(coro, *, debug=False):

    global paused, loop, started, step, DEBUG

    debug = debug or DEBUG

    if coro is not None:
        task = loop.create_task(coro)
        _set_task_name(task, coro.__name__)
        if debug:
            pdb("155: task [",coro.__name__,"] added")
    elif debug:
        pdb("157:None coro called, just starting loop")

    started = True

    # the stepper fonction when in simulator
    if cross.scheduler:
        if debug:
            pdb("164: asyncio handler is", cross.scheduler)
        paused = False
        cross.scheduler(step, 1)

    # the stepper when called from  window.requestAnimationFrame()
    # https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame
    elif __EMSCRIPTEN__ or __wasi__:
        print("AIO will auto-start at 0+, now is", embed.counter())
    # fallback to blocking asyncio
    else:
        loop.run_forever()

__exit__ = sys.exit

def aio_exit(maybecoro):
    print("aio will exit on return of", maybecoro)
    if inspect.iscoroutinefunction(maybecoro):
        #FIXME  __exit__( await coro )
        run(coro)
    else:
        __exit__(maybecoro)

sys.exit = aio_exit














#
