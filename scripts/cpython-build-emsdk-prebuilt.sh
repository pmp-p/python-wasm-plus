#!/bin/bash

. ${CONFIG:-config}

PIP="$(realpath python3-wasm) -m pip"

echo "
    *   cpython-build-emsdk-prebuilt pip==$PIP   *
" 1>&2


