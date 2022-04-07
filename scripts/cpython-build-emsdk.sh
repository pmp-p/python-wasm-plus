#!/bin/bash

. ${CONFIG:-config}

 PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST_PREFIX}/bin/python3}

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
    mkdir -p build/libffi $PREFIX
    pushd build/libffi

#TODO: check if export PATH=${HOST_PREFIX}/bin:$PATH is really set to avoid system python with different bytecode
#and no loder lib-dynload in the way.

    export EMCC_CFLAGS="-Os -g0 -fPIC"

     CFLAGS="-Os -g0 -fPIC"\
      emconfigure $ROOT/src/libffi/configure --host=wasm32-tot-linux\
      --prefix=$PREFIX --enable-static --disable-shared --disable-dependency-tracking\
      --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs\

    emmake make install

    popd

    cp -fv  ${PREFIX}/lib/libffi.a $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/
    cp -vf  ${PREFIX}/include/ffi*.h ${EMSDK}/upstream/emscripten/cache/sysroot/include/



    mkdir -p build/cpython-wasm $PREFIX
    pushd build/cpython-wasm

#     --with-tzpath="/usr/share/zoneinfo" \

CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten \
  emconfigure $ROOT/src/cpython/configure  -C --without-pymalloc --disable-ipv6 \
    --cache-file=${PYTHONPYCACHEPREFIX}/config.cache \
    --enable-wasm-dynamic-linking \
    --host=$PYDK_PYTHON_HOST_PLATFORM \
    --build=$($ROOT/src/cpython/config.guess) \
    --with-emscripten-target=browser \
    --prefix=$PREFIX \
    --with-build-python=${PYTHON_FOR_BUILD}


    EMCC_CFLAGS="$EMCC_CFLAGS -s USE_ZLIB=1 -s USE_BZIP2=1" emmake make -j$(nproc) install
    popd
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py devices/x86_64/usr/lib/python3.??/
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/x86_64/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/emsdk/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    mkdir -p prebuilt
    cp -vf build/cpython-wasm/libpython3.*.a prebuilt/
    rmdir  $PREFIX/lib/python3.??/lib-dynload
fi

unset PYTHON_FOR_BUILD
unset EMCC_CFLAGS
