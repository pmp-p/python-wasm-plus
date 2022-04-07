print("= ${__FILE__} in websim  for  ${PLATFORM} =")

import sys,builtins

sys.path.append("${PLATFORM}")

import xctools

sys.platform = 'emscripten'

class __EMSCRIPTEN__:
    @classmethod
    def PyConfig_InitPythonConfig(*argv):pass

define('__EMSCRIPTEN__', __EMSCRIPTEN__)

exec( open("${PYTHONRC}").read() , globals(), globals())


if __name__ == '__main__':
    execfile("${__FILE__}")
    setup()
    while True:
        loop()

