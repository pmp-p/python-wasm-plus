print("========= $1  ============")
import builtins
try:
    __WASM__
except:
    builtins.__WASM__ = __import__('sys').platform in ['emscripten','wasi']

if __import__('sys').platform in ['emscripten']:
    import __EMSCRIPTEN__
    builtins.__EMSCRIPTEN__ = __EMSCRIPTEN__

if __import__('sys').platform in ['wasi']:
    import __WASI__
    builtins.__WASI__ = __WASI__

with __import__('tokenize').open("") as f:
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
    code = compile("".join(prepro), "", "exec")
    main = __import__("__main__").__dict__
    save = main.get('__file__',None)
    main['__file__']= ""
    exec(code, main, main )
    main['__file__']=save
    if save is None:
        main.pop('__file__')
END

