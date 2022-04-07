#!pythonrc.py

import os, sys, json, builtins

import crossplatforms

# the sim does not preload assets and cannot access currentline
# unless using https://github.com/pmp-p/aioprompt/blob/master/aioprompt/__init__.py



if not defined('undefined'):
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


def overloaded(i, *attrs):
    for attr in attrs:
        if attr in i.__class__.__dict__:
            if attr in i.__dict__:
                return True
    return False


builtins.overloaded = overloaded



try:
    # mpy already has execfile
    execfile
except:
    def execfile(filename):
        with __import__('tokenize').open(filename) as f:
            __prepro = []
            myglobs = []
            tmpl = []

            for l in f.readlines():
                testglob = l.split('#')[0].strip()
                if testglob in ['global loop','global setup']:
                    tmpl.append( [len(__prepro),l.find('g')] )
                    __prepro.append("#globals")
                    continue

                __prepro.append(l)

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
                __prepro[mark] = ' '*indent + myglob

            #for l in "".join(__prepro):
            #    print(l,end='')

            # use of globals() is only valid in __main__ scope
            # we really want the module __main__ dict here.

            __main__dict = __import__("__main__").__dict__
            __main__dict['__file__']= "${__FILE__}"

            del myglob, tmpl, l, mark, indent

            exec( compile("".join(__prepro), "${__FILE__}", "exec"), __main__dict, __main__dict )
            return __import__("__main__")


    define('execfile', execfile)

if hasattr(embed,'readline'):

    class shell:
        if crossplatforms.sim:
            ROOT = os.getcwd()
            HOME = os.getcwd()
        else:
            ROOT = f"/data/data/{sys.argv[0]}"
            HOME = f"{ROOT}/assets"


        @classmethod
        def cat(cls, *argv):
            for fn in argv:
                with open(fn,'r') as out:
                    print( out.read() )

        @classmethod
        def ls(cls, *argv):
            for out in os.listdir(*argv):
                print(out)

        @classmethod
        def pwd(cls, *argv):
            print( os.getcwd())

        @classmethod
        def cd(cls, *argv):
            if len(argv):
                os.chdir( argv[-1] )
            else:
                os.chdir( cls.HOME )
            print('[ ',os.getcwd(),' ]')


    def excepthook(etype, e, tb):
        global last_fail

        catch = False

        if isinstance(e, NameError):
            catch = True

        if catch or isinstance(e, SyntaxError) and e.filename == "<stdin>":
            catch = True
            #index = readline.get_current_history_length()

            #sys.__ps1__ = sys.ps1
            sys.ps1 = ""

            #asyncio.get_event_loop().create_task(retry(index))
            # store trace
            #last_fail.append([etype, e, tb])

            cmdline = embed.readline().strip()
            cmd = cmdline.strip()
            if cmd.find(' ')>0:
                cmd, args = cmdline.split(' ',1)
                args = args.split(' ')
            else:
                args = ()

            if hasattr(shell, cmd):
                try:
                    getattr(shell, cmd)(*args)
                except Exception as cmderror:
                    print(cmderror, file=sys.stderr)
            elif cmd.endswith('.py'):
                execfile(cmd)
            else:
                catch =False

        if not catch:
            sys.__excepthook__(etype, e, tb)
        else:
            embed.prompt()

    sys.excepthook = excepthook





try:
    PyConfig
    crossplatforms.sim = ( __EMSCRIPTEN__ or __WASI__ or __WASM__).PyConfig_InitPythonConfig( PyConfig )
except NameError:
#   TODO: get a pyconfig from C here
#    <vstinner> pmp-p: JSON au C : connais les API secrète _PyConfig_FromDict(), _PyInterpreterState_SetConfig() et _testinternalcapi.set_config()?
#    <vstinner> pmp-p: j'utilise du JSON pour les tests unitaires sur PyConfig dans test_embed


    PyConfig = {}
    print(" - running in simulator - ")
    crossplatforms.sim = True





























#
