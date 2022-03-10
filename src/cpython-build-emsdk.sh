#!/bin/bash

. ${CONFIG:-config}

if [ -d $EMSDK ]
then
    echo "
    * using emdk located at ${EMSDK}
"
else
    echo "
    ERROR cannot find EMSDK in env
"
    read
fi

if $REBUILD
then
    rm build/cpython-wasm/libpython3*.a
fi



if [ -f build/cpython-wasm/libpython3.??.a ]
then
    echo "
    * not rebuilding cpython-wasm
"
else
    echo "
    * rebuilding build/cpython-wasm
        PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}
"
    mkdir -p build/cpython-wasm $PREFIX

    pushd build/cpython-wasm

CONFIG_SITE=$ROOT/cpython/Tools/wasm/config.site-wasm32-emscripten \
  emconfigure $ROOT/cpython/configure -C \
    --host=wasm32-unknown-emscripten \
    --build=$($ROOT/cpython/config.guess) \
    --with-emscripten-target=browser \
    --prefix=$PREFIX \
    --with-build-python=${PYTHON_FOR_BUILD}

    emmake make -j$(nproc) install
    popd
fi

