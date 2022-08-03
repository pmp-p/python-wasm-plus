#!/bin/bash
reset
export SDKROOT=${SDKROOT:-$(pwd)}
export PYBUILD=${PYBUILD:-3.11}

chmod +x scripts/*.sh ./support/*.sh

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1

# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

./scripts/cpython-fetch.sh
./support/__EMSCRIPTEN__.sh

./scripts/cpython-build-host-deps.sh >/dev/null
./scripts/cpython-build-host.sh >/dev/null
./scripts/cpython-build-host-prebuilt.sh >/dev/null

# use ./ or emsdk will pollute env
./scripts/emsdk-fetch.sh

echo " ------------------- building cpython wasm deps -------------------"
./scripts/cpython-build-emsdk-deps.sh > /dev/null


echo " ------------------- building cpython wasm -----------------------"
if ./scripts/cpython-build-emsdk.sh > /dev/null
then
    echo " ------------------- building cpython wasm packages ----------"
    ./scripts/cpython-build-emsdk-deps.sh

    echo " ------------------- building cpython pygame -------------------"
    ./scripts/pygame-all.sh > /dev/null

    # pygame won't build if python or sdl failed
    [ -f prebuilt/emsdk/libpygame${PYBUILD}.a ] || exit 34

else
    echo " cpython-build-emsdk failed"
    exit 38
fi

echo done
