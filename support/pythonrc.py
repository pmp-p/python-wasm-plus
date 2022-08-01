#!pythonrc.py

import os, sys, json, builtins

# to be able to access aio.cross.simulator
import aio
import aio.cross

import time

# the sim does not preload assets and cannot access currentline
# unless using https://github.com/pmp-p/aioprompt/blob/master/aioprompt/__init__.py

if not defined("undefined"):

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

    define("undefined", sentinel())
    del sentinel

    define("false", False)
    define("true", True)

    # fix const without writing const in that .py because of faulty micropython parser.
    exec("__import__('builtins').const = lambda x:x", globals(), globals())


def overloaded(i, *attrs):
    for attr in attrs:
        if attr in vars(i.__class__):
            if attr in vars(i):
                return True
    return False


builtins.overloaded = overloaded


try:
    # mpy already has execfile
    execfile
except:

    def execfile(filename):
        global pgzrun

        imports = []

        with __import__("tokenize").open(filename) as f:
            __prepro = []
            myglobs = ["setup", "loop", "main"]
            tmpl = []

            pgzrun = None

            for l in f.readlines():
                if pgzrun is None:
                    pgzrun = l.find("pgzrun") > 0

                testline = l.split("#")[0].strip(" \r\n,\t")

                if testline.startswith("global ") and (
                    testline.endswith(" setup")
                    or testline.endswith(" loop")
                    or testline.endswith(" main")
                ):
                    tmpl.append([len(__prepro), l.find("g")])
                    __prepro.append("#globals")
                    continue

                elif testline.startswith("import "):
                    testline = testline.replace("import ", "").strip()
                    imports.extend(map(str.strip, testline.split(",")))

                elif testline.startswith("from "):
                    testline = testline.replace("from ", "").strip()
                    imports.append(testline.split(" import ")[0].strip())

                __prepro.append(l)

                if l[0] in ("""\n\r\t'" """):
                    continue

                if not l.find("=") > 0:
                    continue

                l = l.strip()

                if l.startswith("def "):
                    continue
                if l.startswith("class "):
                    continue

                # maybe found a global assign
                varname = l.split("=", 1)[0].strip(" []()")

                for varname in map(str.strip, varname.split(",")):

                    if varname.find(" ") > 0:
                        continue

                    # it's a comment on an assign !
                    if varname.find("#") >= 0:
                        continue

                    # skip attr assign
                    if varname.find(".") > 0:
                        continue

                    # not a tuple assign
                    if varname.find("(") > 0:
                        continue

                    # not a list assign
                    if varname.find("[") > 0:
                        continue

                    # TODO handle (a,)=(0,) case types

                    if not varname in myglobs:
                        myglobs.append(varname)

            myglob = f"global {', '.join(myglobs)}\n"

            if aio.cross.simulator:
                print(myglob)


            for mark, indent in tmpl:
                __prepro[mark] = " " * indent + myglob

            def dump_code():
                nonlocal __prepro
                print()
                print("_" * 70)
                for i, l in enumerate(__prepro):
                    print(str(i).zfill(5), l, end="")
                print("_" * 70)
                print()

            # if aio.cross.simulator:
            #    dump_code()

            # use of globals() is only valid in __main__ scope
            # we really want the module __main__ dict here
            # whereever from we are called.
            __main__ = __import__("__main__")
            __main__dict = vars(__main__)
            __main__dict["__file__"] = filename
            try:
                code = compile("".join(__prepro), filename, "exec")
            except SyntaxError as e:
                # if not aio.cross.simulator:
                dump_code()
                sys.print_exception(e)
                code = None

            if code:
                if pgzrun or "pgzrun" in imports:
                    # Indicate that we're running with the pgzrun runner
                    # and disable the pgzrun module
                    sys._pgzrun = True

                    sys.modules["pgzrun"] = type(__main__)("pgzrun")
                    import pgzrun

                    pgzrun.go = lambda: None

                    import pgzero
                    import pgzero.runner

                    pgzero.runner.prepare_mod(__main__)
                print("*" * 40)
                print(imports)
                print("*" * 40)

                exec(code, __main__dict, __main__dict)
                if pgzrun:
                    pgzero.runner.run_mod(__main__)

        return __import__("__main__")

    define("execfile", execfile)

if defined("embed") and hasattr(embed, "readline"):

    class shell:
        if aio.cross.simulator:
            ROOT = os.getcwd()
            HOME = os.getcwd()
        else:
            ROOT = f"/data/data/{sys.argv[0]}"
            HOME = f"/data/data/{sys.argv[0]}/assets"

        @classmethod
        def cat(cls, *argv):
            for fn in map(str,argv):
                with open(fn, "r") as out:
                    print(out.read())

        @classmethod
        def ls(cls, *argv):
            if not len(argv):
                argv = ["."]
            for arg in map(str,argv):
                for out in sorted(os.listdir(arg)):
                    print(out)

        @classmethod
        def clear(cls, *argv,**kw):
            import pygame
            screen = pygame.display.set_mode()
            screen.fill( (0, 0, 0) )
            pygame.display.update()

        @classmethod
        def display(cls,*argv,**kw):
            import pygame
            if not len(argv):
                surf = _
            else:
                if argv[-1].lower().endswith('bmp'):
                    surf = pygame.image.load_basic( argv[-1] )
                else:
                    surf = pygame.image.load( argv[-1] )

            screen = pygame.display.set_mode()
            screen.blit( surf, (1,1) )
            pygame.display.update()


        @classmethod
        def pgzrun(cls, *argv):
            global pgzrun
            pgzrun = True
            cls.exec(*argv)

        @classmethod
        def mkdir(cls, *argv):
            exist_ok = "-p" in argv
            for arg in argv:
                if arg == "-p":
                    continue
                os.makedirs(arg, exist_ok=exist_ok)

        @classmethod
        def wget(cls, *argv, **env):
            import urllib.request
            filename = None
            for arg in map(str,argv):

                if arg.startswith("-O"):
                    filename = arg[2:].lstrip()
                    continue
                filename,_ = urllib.request.urlretrieve(arg, filename=filename)
                print(f"{arg} saved as : {filename}")
                filename = None
            return True

        @classmethod
        def pwd(cls, *argv):
            print(os.getcwd())

        @classmethod
        def cd(cls, *argv):
            if len(argv):
                os.chdir(argv[-1])
            else:
                os.chdir(cls.HOME)
            print("[ ", os.getcwd(), " ]")

        @classmethod
        def exec(cls, cmd, *argv, **env):
            global pgzrun
            # TODO extract env from __main__ snapshot
            if cmd.endswith(".py"):
                if pgzrun:
                    print("a program is already running, using 'stop' cmd before retrying")
                    cls.stop()
                    pgzrun = None
                    aio.defer(cls.exec,(cmd,*argv),env, delay=500)

                else:
                    execfile(cmd)
                return True
            return False

        @classmethod
        def dll(cls, *argv):
            cdll = __import__("ctypes").CDLL(None)
            print( getattr(cdll, argv[0])(*argv[1:]) )
            return True

        @classmethod
        def strace(cls, *argv, **env):
            import aio.trace

            sys.settrace(aio.trace.calls)
            return _process_args(argv, env)

# TODO: use run interactive c-api to run this one.
        @classmethod
        def run(cls, *argv, **env):

            __main__ = __import__("__main__")
            __main__dict = vars(__main__)

            builtins._ = undefined
            cmd =  " ".join(argv)

            try:
                time_start = time.time()
                code = compile("builtins._ =" + cmd, "<stdin>", "exec")
                exec(code, __main__dict, __main__dict)
                if builtins._ is undefined:
                    return True
                if aio.iscoroutine(_):
                    async def run(coro):
                        print(f"async[{cmd}] :",await coro)
                        print(f"time[{cmd}] : {time.time() - time_start:.6f}")
                    aio.create_task(run(_), name=cmd)
                else:
                    print(builtins._)
                    print(f"time[{cmd}] : {time.time() - time_start:.6f}")
                    return True
            except SyntaxError as e:
                # try run a file or cmd
                return cls._process_args(argv, env)
            return False

        time = run

        @classmethod
        def ps(cls, *argv, **env):
            for t in aio.all_tasks():
                print(t)
            return True

        @classmethod
        def stop(cls, *argv, **env):
            global pgzrun
            aio.exit = True
            # pgzrun will reset to None next exec
            if not pgzrun:
                # pgzrun does its own cleanup call
                aio.defer(aio.recycle.cleanup, (), {}, delay=500)
                aio.defer(embed.prompt, (), {}, delay=800)

        @classmethod
        def uptime(cls, *argv, **env):
            import asyncio
            if platform.is_browser:
                async def perf_index():
                    ft = [0.00001] * 60*10
                    while not aio.exit:
                        ft.pop(0)
                        ft.append(aio.spent / 0.016666666666666666 )
                        if not (aio.ticks % 60):
                            avg =  sum(ft) / len(ft)
                            try:
                                window.load_avg.innerText = '{:.4f}'.format(avg)
                                window.load_min.innerText = '{:.4f}'.format(min(ft))
                                window.load_max.innerText = '{:.4f}'.format(max(ft))
                            except:
                                pdb("366:uptime: window.load_* widgets not found")
                                break

                        await asyncio.sleep(0)
                aio.create_task( perf_index() )
            else:
                print(f"last frame : {aio.spent / 0.016666666666666666:.4f}")

    def _process_args(argv, env):
        catch = True
        for cmd in argv:
            cmd = cmd.strip()
            if cmd.find(" ") > 0:
                cmd, args = cmd.split(" ", 1)
                args = args.split(" ")
            else:
                args = ()

            if hasattr(shell, cmd):
                try:
                    getattr(shell, cmd)(*args)
                except Exception as cmderror:
                    print(cmderror, file=sys.stderr)
            else:
                catch = shell.exec(cmd, *args, **env)
        return catch

    def excepthook(etype, e, tb):
        global last_fail

        catch = False

        if isinstance(e, NameError):
            catch = True

        if isinstance(e, KeyboardInterrupt):
            print('\r\nKeyboardInterrupt')
            return embed.prompt()


        if catch or isinstance(e, SyntaxError) and (e.filename == "<stdin>"):
            catch = True
            cmdline = embed.readline().strip()

            # TODO: far from perfect !
            if cmdline.find('await ')>=0:
                import aio.toplevel
                aio.create_task( aio.toplevel.retry(cmdline, (etype, e, tb,) ) )
                # no prompt we're going async exec on aio now
                return

            # index = readline.get_current_history_length()

            # asyncio.get_event_loop().create_task(retry(index))
            # store trace
            # last_fail.append([etype, e, tb])


            catch = _process_args(cmdline.strip().split(";"), {})

        if not catch:
            sys.__excepthook__(etype, e, tb)
        else:
            embed.prompt()

    sys.excepthook = excepthook


try:
    PyConfig
    aio.cross.simulator = (
        __EMSCRIPTEN__ or __wasi__ or __WASM__
    ).PyConfig_InitPythonConfig(PyConfig)
# except NameError:
except Exception as e:
    sys.print_exception(e)
    #   TODO: get a pyconfig from C here
    #    <vstinner> pmp-p: JSON au C : connais les API secrète
    # _PyConfig_FromDict(), _PyInterpreterState_SetConfig() et _testinternalcapi.set_config()?
    #    <vstinner> pmp-p: j'utilise du JSON pour les tests unitaires sur PyConfig dans test_embed

    PyConfig = {}
    print(" - running in simulator - ")
    aio.cross.simulator = True

# make simulations same each time, easier to debug
import random
random.seed(1)

if not aio.cross.simulator:
    import __EMSCRIPTEN__ as platform

    def apply_patches():
        builtins.true = True
        builtins.false = False

        import webbrowser

        def browser_open(url, new=0, autoraise=True):

            platform.window.open(url, "_blank")

        def browser_open_new(url):
            return browser_open(url, 1)

        def browser_open_new_tab(url):
            return browser_open(url, 2)

        webbrowser.open = browser_open
        webbrowser.open_new = browser_open_new
        webbrowser.open_new_tab = browser_open_new_tab

        # extensions

        def browser_open_file(target=None,accept="*"):
            if target:
                platform.EventTarget.addEventListener("upload", target)
            platform.window.dlg_multifile.click()

        webbrowser.open_file = browser_open_file

        # merge emscripten browser module here ?
        # https://rdb.name/panda3d-webgl.md.html#supplementalmodules/asynchronousloading
        #


        # dom events
        class EventTarget:
            clients = {}
            events = []
            def addEventListener(self, host, type, listener, options=None, useCapture=None ):
                cli = self.clients.setdefault(type,[])
                cli.append( listener )

            def build(self, evt_name, jsondata ):
                #print( evt_name, jsondata )
                self.events.append( [evt_name, json.loads(jsondata) ] )

            #def dispatchEvent

            async def process(self):
                import inspect
                from types import SimpleNamespace
                while not aio.exit:
                    if len(self.events):
                        evtype , evdata = self.events.pop(0)
                        discarded = True
                        for client in self.clients.get(evtype,[]):
                            is_coro = inspect.iscoroutinefunction(client)
                            print("    -> ", is_coro, client)
                            discarded = False
                            if is_coro:
                                await client(SimpleNamespace(**evdata))
                            else:
                                client(SimpleNamespace(**evdata))
                        if discarded:
                            print("DISCARD :",evtype , evdata)

                    await aio.sleep(0)

        platform.EventTarget = EventTarget()
        aio.create_task(platform.EventTarget.process())

        # bad and deprecated use of sync XHR

        import urllib
        import urllib.request

        def urlretrieve(url, filename=None, reporthook=None, data=None):

            filename = filename or f"/tmp/uru-{aio.ticks}"
            rc=platform.window.python.DEPRECATED_wget_sync(str(url), str(filename))
            if rc==200:
                return filename, []
            raise Exception(f"urlib.error {rc}")


        urllib.request.urlretrieve = urlretrieve

    if (__WASM__ and __EMSCRIPTEN__) or platform.is_browser:
        from platform import window, document


        class fopen:
            ticks = 0
            def __init__(self, url, mode ="r"):
                self.url = str(url)
                self.mode = mode
                self.tmpfile = None

            async def __aenter__(self):
                import platform
                print(f'572: Download start: "{self.url}"')
                if "b" in self.mode:
                    self.__class__.ticks += 1
                    self.tmpfile = f"/tmp/cf-{self.ticks}"
                    cf = platform.window.cross_file(self.url, self.tmpfile)
                    content = await platform.jsiter(cf)
                    self.filelike = open(content, "rb")
                else:
                    import io
                    jsp = platform.window.fetch(self.url)
                    response = await platform.jsprom(jsp)
                    content = await platform.jsprom(response.text())
                    if len(content) == 4:
                        print("585 fopen", f"Binary {self.url=} ?")
                    self.filelike = io.StringIO(content)
                return self.filelike

            async def __aexit__(self, *exc):
                self.filelike.close()
                if self.tmpfile:
                    os.unlink(self.tmpfile)
                del self.filelike, self.url, self.mode, self.tmpfile
                return False

        platform.fopen = fopen

        async def jsiter(iterator):
            mark =None
            value = undefined
            while mark!=undefined:
                value = mark
                await asyncio.sleep(0)
                mark = next( iterator, undefined )
            return value
        platform.jsiter = jsiter

        async def jsprom(prom):
            mark = None
            value = undefined
            wit = window.iterator( prom )
            while mark!=undefined:
                value = mark
                await aio.sleep(0)
                mark = next( wit , undefined )
            return value
        platform.jsprom = jsprom

        apply_patches()

    del apply_patches
else:
    pdb("TODO: js simulator")

# ======================================================

def ESC(*argv):
    for arg in argv:
        sys.__stdout__.write(chr(27),arg, sep="", endl="")

def CSR(*argv):
    for arg in argv:
        sys.__stdout__.write(chr(27), "[", arg, sep="", endl="")

pgzrun = None
if sys.argv[0]!="org.python":
    try:
        import pygame
    except Exception as e:
        sys.print_exception(e)
        print("pygame not loaded")
else:
    shell.uptime()

if os.path.isfile('/data/data/custom.py'):
    execfile('/data/data/custom.py')

import aio.recycle
# ============================================================
# DO NOT ADD ANYTHING FROM HERE OR APP RECYCLING WILL TRASH IT





#
