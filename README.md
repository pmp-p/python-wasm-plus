# python-wasm-plus

thanks to all that participated, the cpython ticket https://bugs.python.org/issue40280 is being solved

Here's a glimpse to the future :
a sandbox for making cpython app on webassembly with integrated pygame built with
emscripten portable sdk.

How does it work ?

see the excellent slides of Christian Heimes at PyCon DE

  https://www.youtube.com/watch?v=oa2LllRZUlU

  https://speakerdeck.com/tiran/python-3-dot-11-in-the-web-browser-a-journey-pycon-de-2022-keynote


or notes of PyCon US 2022
 https://speakerdeck.com/tiran/language-summit-2022-webassembly-python-in-the-browser-and-beyond


for just cpython on wasm see python-wasm https://github.com/ethanhs/python-wasm/

or stays with the classics :

for scientific python see pyodide https://pyodide.org

for cpython+panda3d see both https://rdb.name/panda3d-webgl.md.html or/and PyDK


Discussions very welcomed here French/English:
  https://gitter.im/Wasm-Python/community

English only:
WebAssembly/python on https://discord.gg/MCTM4xFDMK


NOTE: as time of cpython pre-3.11a7, released cython does not handle it - only git version - so pygame-wasm is not upstreamed yet
this is only temporary.

WIP:
https://github.com/pmp-p/pygame-wasm/tree/pygame-wasm-static

ready to use:

https://github.com/pmp-p/pygame-wasm/tree/pygame-wasm-upstream


devlog:
https://github.com/pygame/pygame/issues/718



***REQUIRED:***

    1 GNU/Linux system with clang, git, libffi-dev, libssl dev (1.1.1), zlib1g-dev, patch, bash and make
       for the simulator add sdl2-dev + sdl_* dev.

    everything else will be downloaded.
    includes emsdk , cpython , cython, pygame, various imaging lib ...


***TESTING:***

    # need a browser with wasm + WebGL, see https://developer.mozilla.org/en-US/docs/WebAssembly#browser_compatibility
    # ( on android kitkat please use Bromite release 81.0.4044.83 or chrome/firefox, the webview will NOT work )
    chromium engine based browsers are faster and also impose some limitations so they are the common denominator for Wasm.
    most of testing was made on current Brave browser on 64bits GNU/Linux.



    # (facultative you can use prebuilt) run :

    ./python-wasm-plus.sh

    # then run :

    ./buildapp.sh

    # navigate to http://localhost:8000 manually or :

    xdg-open http://localhost:8000

    #type in the terminal followed  by enter at the python prompt:

    execfile("touchpong.py")

    #enjoy a classic

    #mouse click first out of terminal, then onto canvas.
    # then move up/down with f,v keys.


***USING GITHUB ACTIONS TO PUBLISH SOFTWARE:***

add `support/__EMSCRIPTEN__.yml` to your `.github/workflows/` folder
create a folder name `static` at base of your repo

in that folder add `static/index.html`
containing eg :

`<html><a href=python311.html?org.python.myapp>My App</a></html>`

and the main.py but as as the fully qualified domain name eg `static/org.python.myapp.py`

everything in the "static" folder will be accessible as single files for the webserver, everything else will go
inside folder "assets" in the apk zip file named after fqdn eg here `org.python.myapp.apk` .

After CI completed  ( expect a bit more than 30 minutes ) go to  `https://<yourname>.github.io/<repo>/`

use ctrl+shift+i to see the wasm/js console while running your app.


***CREDITS:***

    touchpong.py could be shareware so if you like it, send an expensive thank you
    to @blubberquark on Pygame Community discord ;)


***MORE?:***

    multithreaded version with online file access and dynamic code is still brewing
    feel free to contact me if you have interest in more than single threaded demos.
