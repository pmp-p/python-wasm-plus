
import builtins

# try to acquire syslog early
try:
    import embed
    builtins.pdb = embed.pdb
except:
    builtins.pdb = print
    builtins.embed = __import__('__main__')

try:
    # check it the embedding module was finished for that platform.
    # the least shoulbe syslog ( js console / adb logcat )
    embed.log
except:
    pdb("CRITICAL: embed softrt/syslog functions not found ( and also not in __main__ )")
    embed.enable_irq = print
    embed.disable_irq = print
    embed.log = print




from asyncio import *


# Within a coroutine, simply use `asyncio.get_running_loop()`, since the coroutine wouldn't be able
# to execute in the first place without a running event loop present.
try:
    loop = get_running_loop()
except RuntimeError:
    # depending on context, you might debug or warning log that a running event loop wasn't found
    loop = get_event_loop()


started = False
paused = False
steps = []
oneshots = []
ticks = 0
protect = []


def step():
    global paused, loop
    if not paused:
        loop.call_soon(loop.stop)
        loop.run_forever()

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

def run(coro, *, debug=None):

    global __wasm__, paused, loop, started

    task = loop.create_task(coro)
    _set_task_name(task, coro.__name__)

    # the stepper fonction when in simulator
    if debug:
        print("asyncio handler is",debug)
        paused = False
        started = True
        debug(1)
    elif __wasm__:
        if not _step in aio.steps:
            aio.steps.append(_step)
    else:
        loop.run_forever()
