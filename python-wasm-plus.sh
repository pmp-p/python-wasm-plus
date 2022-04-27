#!/bin/bash
reset

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1

# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

. ${CONFIG:-config}

. scripts/cpython-fetch.sh
. support/__EMSCRIPTEN__.sh
. scripts/cpython-build-host.sh >/dev/null
. scripts/cpython-build-host-deps.sh >/dev/null

# optionnal, each sub module should call it
./scripts/emsdk-fetch.sh

# use ./ or emsdk will pollute env
if ./scripts/cpython-build-emsdk.sh >/dev/null
then
    ./scripts/cpython-build-emsdk-deps.sh > /dev/null

    ./scripts/pygame-all.sh

    # pygame won't build if python or sdl failed
    [ -f prebuilt/libpygame.a ] || exit 1

else
    echo " cpython-build-emsdk failed"
    exit 2
fi

echo done
