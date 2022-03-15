#!/bin/bash
reset

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1
# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

. ${CONFIG:-config}


. scripts/emsdk-fetch.sh
. scripts/cpython-fetch.sh
. scripts/cython-all.sh
. support/__EMSCRIPTEN__.sh
. scripts/cpython-build-host.sh
. scripts/cpython-build-emsdk.sh
. scripts/pygame-all.sh

echo done
