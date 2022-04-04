# builtins.__EMSCRIPTEN__
# builtins.__WASI__
# builtins.__ANDROID__   also defines __ANDROID_API__
# builtins.__UPY__
# can point to this module

import sys, os, builtins
#are they not ?
builtins.builtins = builtins

# aio must be in __main__ or step/defer may lose access to globals
class aio:
    paused = False
    steps = []
    oneshots = []
    ticks = 0
    protect = []

    @classmethod
    def step(cls):
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
                    early.append( deferred )
                else:
                    _, fn,argv,kw = deferred
                    fn(*argv,**kw)
            while len(early):
                cls.oneshots.append(early.pop() )

            for step in cls.steps:
                step()
        except Exception as e:
            sys.print_exception(e)
            cls.paused = True
            pdb("- aio paused -")

    @classmethod
    def defer(cls, fn, argv=(), kw={}, deadline = 0):
        # FIXME: set ticks + deadline for alarm
        cls.oneshots.append( [cls.ticks+deadline, fn,argv,kw,] )

builtins.aio = aio



try:
    # mpy already has execfile
    execfile
except:
    import tokenize
    def execfile(filename):

        with tokenize.open(filename) as f:
            prepro = []
            myglobs = []
            tmpl = []

            for l in f.readlines():

                if l.strip().find('global loop')>=0:
                    tmpl.append( [len(prepro),l.find('g')] )
                    prepro.append("#globals")
                    continue

                prepro.append(l)

                if l[0] in ("""\n\r\t'" """):
                    continue

                if not l.find('=')>0:
                    continue

                l = l.strip()

                if l.startswith('def '):
                    continue
                if l.startswith('class '):
                    continue

                #maybe found a global assign
                varname =l.split('=',1)[0].strip()

                # not a tuple assign
                if varname.find('(')>0:
                    continue

                # not a list assign
                if varname.find('[')>0:
                    continue

                #TODO handle (a,)=(0,) case types

                if not varname in myglobs:
                    myglobs.append(varname)



            myglob = f"global {', '.join(myglobs)}\n"


            for mark, indent in tmpl:
                prepro[mark] = ' '*indent + myglob

#            os.system('reset')
#            print(myglob)
#            for i,line in enumerate(prepro):
#                print(str(i).zfill(4),line,end='')
#
#            print()
#            print()

            code = compile("".join(prepro), filename, "exec")
            main = __import__("__main__").__dict__
#            print(ROOTDIR)
#            os.chdir(ROOTDIR)
            exec(code, main, main)

    builtins.execfile = execfile


this = __import__(__name__)

# those  __dunder__ are usually the same used in C conventions.


try:
    __UPY__
except:
    if hasattr(sys.implementation, "mpy"):
        builtins.__UPY__ = this
    else:
        builtins.__UPY__ =  None

try:
    __EMSCRIPTEN__
except:
    if sys.platform in ("emscripten", "asm.js", "wasm"):
        builtins.__EMSCRIPTEN__ = this
    else:
        builtins.__EMSCRIPTEN__ = None

try:
    __WASI__
except:
    if sys.platform in (
        "wasm",
        "wasi",
    ):
        builtins.__WASI__ = this
    else:
        builtins.__WASI__ = None

try:
    __ANDROID__
except:
    # this *is* the cpython way
    if hasattr(sys, "getandroidapilevel"):
        builtins.__ANDROID__ = this
        builtins.__ANDROID_API__ = sys. getandroidapilevel()
    else:
        builtins.__ANDROID__ = False


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
    def pdb(*argv):
        print(*argv, file=sys.__stderr__)

    # setup exception display with same syntax as upy
    import traceback
    def print_exception(e, out=sys.stderr, **kw):
        kw["file"] = out
        traceback.print_exc(**kw)

    sys.print_exception = print_exception
    del print_exception

    # fix const without writing const in that .py because of micropython parser.
    exec("__import__('builtins').const = lambda x:x", globals(), globals())
    try:
        from . import uasyncio_cpy as uasyncio
    except:
        pdb("WARNING: no uasyncio implementation found")
        uasyncio = aio

sys.modules["uasyncio"] = uasyncio


builtins.pdb = pdb

# this should be done in site.py / main.c but that's not so easy.
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



# check for embedding support or use an emulation from host script __main__ .

try:
    import embed
except:
    print("WARNING: embed module not found, using __main__ for it", file=sys.stderr)
    embed = __import__("__main__")

if __EMSCRIPTEN__ and hasattr(embed,"run_script"):
    import json
    def js(code, delay=0):
        # keep a ref till next loop
        aio.protect.append( code )
        if not delay:
            result = embed.run_script(f"JSON.stringify({code})")
            if result is not None:
                return json.loads(result)
        elif delay<0:
            embed.run_script(code)
        else:
            embed.run_script(code, int(delay))

    embed.js = js

try:
    # check it the embedding module was finished for that platform.
    embed.log
except:
    pdb("CRITICAL: embed softrt/syslog functions not found ( and also not in __main__ )")
    embed.enable_irq = print
    embed.disable_irq = print
    embed.log = print



























