# python-wasm-plus

thanks to all that participated, the cpython ticket https://bugs.python.org/issue40280 is being solved

Here's a glimpse to the future :
a sandbox for making cpython app on webassembly with integrated pygame


for just cpython on wasm see python-wasm https://github.com/ethanhs/python-wasm/

or stays with the classics :

for scientific python see pyodide https://pyodide.org

for cpython+panda3d see both https://rdb.name/panda3d-webgl.md.html or/and PyDK


discussions very welcomed here:
  https://gitter.im/Wasm-Python/community


NOTE: as time of cpython pre-3.11a6, cython is a bit broken so pygame-wasm is not upstream
one but my fork with some hand edited cythonized files.

https://github.com/pmp-p/pygame-wasm/tree/pygame-wasm


REQUIRED:
    
    1 GNU/Linux system with clang, libffi-dev, git, patch, bash

    everything else will be downloaded. ( emsdk , cpython , cython, pygame, various lib ... )

    
TESTING:
    
    need a browser with wasm + WebGL, see https://developer.mozilla.org/en-US/docs/WebAssembly#browser_compatibility

( on android kitkat please use Bromite release 81.0.4044.83 or chrome/firefox, the webview will NOT work )

    (facultative you can use prebuilt) run :
        ./python-wasm-plus.sh

    then run :

        ./buildapp.sh

    navigate to:

        http://localhost:8000

    type in the terminal followed  by enter at the python prompt:
    
        execfile("touchpong.py") 

    enjoy a classic 

    manual:
        mouse click first out of terminal, then onto canvas.
        then move up/down with f,v keys.


    touchpong.py is shareware so if you like it, send an expensive thank you
    to @blubberquark on Pygame Community discord ;)



PS: multithreaded version with online file access and dynamic code is still brewing
feel free to contact me if you have interest in more than simple demo.
