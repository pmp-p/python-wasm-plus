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

#TODO: check if export PATH=${HOST_PREFIX}/bin:$PATH is really set to avoid system python with different bytecode


CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten \
  emconfigure $ROOT/src/cpython/configure -C \
    --host=$PYDK_PYTHON_HOST_PLATFORM \
    --build=$($ROOT/src/cpython/config.guess) \
    --with-emscripten-target=browser \
    --prefix=$PREFIX \
    --with-build-python=${PYTHON_FOR_BUILD}

    EMCC_CFLAGS="-s USE_ZLIB=1 -s USE_BZIP2=1" emmake make -j$(nproc) install
    popd
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py devices/x86_64/usr/lib/python3.??/
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/x86_64/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/emsdk/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    mkdir -p prebuilt
    cp -vf build/cpython-wasm/libpython3.*.a prebuilt/
    rmdir  $PREFIX/lib/python3.??/lib-dynload
fi

