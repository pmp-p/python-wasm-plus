import sys, xctools



if not defined('__WASM__'):
    if __import__('os').uname().machine.startswith("wasm"):
        import __WASM__
    else:
        __WASM__ = False

    define('__WASM__', __WASM__)



if __import__('sys').platform in ['emscripten']:
    redef = False
    try:
        if not defined('__EMSCRIPTEN__'):
            import __EMSCRIPTEN__ as platform
            redef = True
        import embed

    except Exception as e:
        pdb("__EMSCRIPTEN__ module not found, assuming simulator instead of error :")
        pdb(e)
        # fake it
        class platform:
            sim = True
        # FIXME truth

    try:
        embed
    except:
        # use the simulator defined value as a platform module.
        sys.modules.setdefault('embed', platform)
        define('embed', platform)

    if not redef:
        define('__EMSCRIPTEN__', platform)
    del redef



if not defined('__WASI__'):
    if __import__('sys').platform in ['wasi']:
        import __WASI__
    else:
        __WASI__ = False

    define('__WASI__', __WASI__)



sim = '?'

