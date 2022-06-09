#!/bin/bash
reset
export ROOT=$(pwd)

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1

# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

. ${CONFIG:-config}

. scripts/cpython-fetch.sh
. support/__EMSCRIPTEN__.sh
. scripts/cpython-build-host.sh >/dev/null
. scripts/cpython-build-host-deps.sh >/dev/null

# use ./ or emsdk will pollute env
./scripts/emsdk-fetch.sh

echo " ------------------- building cpython wasm -----------------------"
if ./scripts/cpython-build-emsdk.sh > /dev/null
then
    echo " ------------------- building cpython wasm plus -------------------"
    ./scripts/cpython-build-emsdk-deps.sh > /dev/null

    echo " ------------------- building cpython pygame -------------------"
    ./scripts/pygame-all.sh > /dev/null

    # pygame won't build if python or sdl failed
    [ -f prebuilt/emsdk/libpygame.a ] || exit 1

else
    echo " cpython-build-emsdk failed"
    exit 2
fi

echo done
