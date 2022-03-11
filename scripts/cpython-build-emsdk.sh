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
    * not rebuilding cpython-wasm for [$PYDK_PYTHON_HOST_PLATFORM]
"
else
    echo "
    * rebuilding build/cpython-wasm for [$PYDK_PYTHON_HOST_PLATFORM]
        PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}
"
    mkdir -p build/cpython-wasm $PREFIX

    pushd build/cpython-wasm

#     --with-tzpath="/usr/share/zoneinfo" \    
    
CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten \
  emconfigure $ROOT/src/cpython/configure -C \
    --host=$PYDK_PYTHON_HOST_PLATFORM \
    --build=$($ROOT/src/cpython/config.guess) \
    --with-emscripten-target=browser \
    --prefix=$PREFIX \
    --with-build-python=${PYTHON_FOR_BUILD}

    emmake make -j$(nproc) install
    popd
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*_.py devices/x86_64/usr/lib/python3.??/
    cp -vf build/cpython-wasm/libpython3.*.a prebuilt/
    rmdir  $PREFIX/lib/python3.??/lib-dynload
fi

