#!/bin/bash
reset

mkdir -p build/pycache
export PYTHONDONTWRITEBYTECODE=1
# make install cpython will force bytecode generation
export PYTHONPYCACHEPREFIX="$(realpath build/pycache)"

. ${CONFIG:-config}


. src/emsdk-fetch.sh
. src/cpython-fetch.sh
. src/cpython-build-host.sh
. src/cpython-build-emsdk.sh

