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



REQUIRED:

    clang, libffi-dev, git, patch, bash

    everything else will be downloaded. ( emsdk , cpython , pygame, various lib ... )

    
TESTING:
    
    need a browser with wasm + WebGL, see https://developer.mozilla.org/en-US/docs/WebAssembly#browser_compatibility

( on android kitkat please use Bromite release 81.0.4044.83 or chrome/firefox, the webview will NOT work )

