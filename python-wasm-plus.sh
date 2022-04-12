#!/bin/bash
reset

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1

# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

. ${CONFIG:-config}

. scripts/cpython-fetch.sh
. support/__EMSCRIPTEN__.sh
. scripts/cpython-build-host.sh
. scripts/cpython-build-host-deps.sh

# optionnal, each sub module should call it
./scripts/emsdk-fetch.sh

# use ./ or emsdk will pollute env

./scripts/cpython-build-emsdk.sh
./scripts/pygame-all.sh

# prepare the minimal stdlib fs
./scripts/make_coldstartfs.sh

echo done
