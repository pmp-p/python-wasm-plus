# python startup for python3-wasm
import sys,os

# for emcc to build wasm shared lib
os.environ['EMCC_CFLAGS']='-s SIDE_MODULE=1'

ARCH=os.popen('arch').read().strip()

# the egg system may pollute the sys.path with non compatible .so
# clean it up
for i,path in enumerate(sys.path):
    if path.find('/emsdk/')>0:
        sys.path[i] = sys.path[i].replace('/emsdk/',f'/{ARCH}/')
        sys.path[i] = sys.path[i].replace('py3.11-wasm32-tot-emscripten',f'py3.11-linux-{ARCH}')

import _cffi_backend
import cffi
from cffi import FFI
