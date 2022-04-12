#!/bin/bash

. ${CONFIG:-config}

# TODO:
# fix /pip/_internal/operations/install/wheel.py
# for allowing to avoid pyc creation


export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST_PREFIX}/bin/python3}


. ./scripts/emsdk-fetch.sh


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

    if [ -f ${PREFIX}/lib/libffi.a ]
    then
        echo "
    * ffi already built"
    else
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
    fi


    mkdir -p build/cpython-wasm $PREFIX
    pushd build/cpython-wasm

#     --with-tzpath="/usr/share/zoneinfo" \


    export OPT="-DNDEBUG -g0 -fwrapv -Os"

    CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten OPT="$OPT" \
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

    cp -Rfv $ROOT/support/__EMSCRIPTEN__.patches/. $HOST_PREFIX/lib/python3.??/

    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py devices/x86_64/usr/lib/python3.??/
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/x86_64/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    cp -vf build/cpython-wasm/build/lib.emscripten-wasm32-*/_sysconfigdata_*.py $(echo -n devices/emsdk/usr/lib/python3.??/)_sysconfigdata__emscripten_.py
    mkdir -p prebuilt
    cp -vf build/cpython-wasm/libpython3.*.a prebuilt/
    rmdir  $PREFIX/lib/python3.??/lib-dynload
fi


# python setup.py install --single-version-externally-managed --root=/
# pip3 install .




cat > ${PYTHONPYCACHEPREFIX}/.nanorc <<END
set tabsize 4
set tabstospaces
END

cat > $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh <<END
#!/bin/bash
export PATH=${HOST_PREFIX}/bin:\$PATH
export PKG_CONFIG_PATH=${PKG_CONFIG_PATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
export HOME=${PYTHONPYCACHEPREFIX}
export PLATFORM_TRIPLET=${PYDK_PYTHON_HOST_PLATFORM}
export PREFIX=$PREFIX

export PYTHONDONTWRITEBYTECODE=1
export PYTHONSTARTUP="${ROOT}/support/__EMSCRIPTEN__.py"
> ${PYTHONPYCACHEPREFIX}/.pythonrc.py

export PS1="[PyDK:wasm] \w $ "

export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_

cat >${PYTHONPYCACHEPREFIX}/.numpy-site.cfg <<NUMPY
[DEFAULT]
library_dirs = $PREFIX//lib
include_dirs = $PREFIX/include
NUMPY


if [[ ! -z \${EMSDK+z} ]]
then
    # emsdk_env already parsed
    echo -n
else
    pushd $ROOT
    . scripts/emsdk-fetch.sh
    popd
fi
END

cat > $HOST_PREFIX/bin/python3-wasm <<END
#!/bin/bash
. $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh

# most important
export EMCC_CFLAGS="-s SIDE_MODULE=1"
export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_

# does not work with -mpip
export PYTHONSTARTUP="/data/git/python-wasm-plus/support/__EMSCRIPTEN__.py"


# so include dirs are good
export PYTHONHOME=$PREFIX

# but still can load dynload and setuptools
PYTHONPATH=$(echo -n ${HOST_PREFIX}/lib/python3.??/site-packages):\$PYTHONPATH
export PYTHONPATH=$(echo -n ${HOST_PREFIX}/lib/python3.??/lib-dynload):\$PYTHONPATH




#probably useless
export _PYTHON_HOST_PLATFORM=${PYDK_PYTHON_HOST_PLATFORM}
export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}

$HOST_PREFIX/bin/python3 -u -B \$@
END

chmod +x $HOST_PREFIX/bin/python3-wasm






















unset PYTHON_FOR_BUILD
unset EMCC_CFLAGS




















