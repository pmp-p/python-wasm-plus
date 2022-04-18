#!/bin/bash

. ${CONFIG:-config}

# TODO:
# fix /pip/_internal/operations/install/wheel.py
# for allowing to avoid pyc creation


export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST_PREFIX}/bin/python3}

# remove old compiler wrapper to avoid conflicts
rm $HOST_PREFIX/bin/cc


. ./scripts/emsdk-fetch.sh


if $REBUILD
then
    rm -rf build/cpython-wasm/ build/pycache/config.cache
fi




if [ -f $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/libffi.a ]
then
    echo "
    * ffi already built"
else
    echo "


    *************************************************************************
    *************************************************************************

"
    if [ -d src/libffi ]
    then
        echo -n
    else
        pushd src
        git clone https://github.com/pmp-p/libffi-emscripten.git libffi
        popd
    fi

    mkdir -p build/libffi $PREFIX
    pushd build/libffi

#TODO: check if export PATH=${HOST_PREFIX}/bin:$PATH is really set to avoid system python with different bytecode
#and no loder lib-dynload in the way.

    export EMCC_CFLAGS="$COPTS"

     CFLAGS="$COPTS"\
      emconfigure $ROOT/src/libffi/configure --host=wasm32-tot-linux\
      --prefix=$PREFIX --enable-static --disable-shared --disable-dependency-tracking\
      --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs\

    emmake make install

    popd

    cp -fv  ${PREFIX}/lib/libffi.a $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/
    cp -vf  ${PREFIX}/include/ffi*.h ${EMSDK}/upstream/emscripten/cache/sysroot/include/
echo "

    *************************************************************************
    *************************************************************************

"
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


    export OPT="$COPTS -DNDEBUG -fwrapv"

    CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten OPT="$OPT" \
  eval emconfigure $ROOT/src/cpython/configure  -C --without-pymalloc --disable-ipv6 \
    --cache-file=${PYTHONPYCACHEPREFIX}/config.cache \
    --enable-wasm-dynamic-linking \
    --host=$PYDK_PYTHON_HOST_PLATFORM \
    --build=$($ROOT/src/cpython/config.guess) \
    --with-emscripten-target=browser \
    --prefix=$PREFIX \
    --with-build-python=${PYTHON_FOR_BUILD} $VERBOSE


    EMCC_CFLAGS="-sUSE_ZLIB -sUSE_BZIP2" eval emmake make -j$(nproc) $VERBOSE
    EMCC_CFLAGS="-sUSE_ZLIB -sUSE_BZIP2" eval emmake make install $VERBOSE

    rm -rf $(find $ROOT/devices/ -type d|grep __pycache__$)
#    2>&1 \
#     |grep --line-buffered -v ^Compiling\
#     |grep --line-buffered -v ^Listing\
#     |grep --line-buffered -v ^install

    popd

    # move them to MEMFS
    mv $PREFIX/lib/python3.??/lib-dynload/* $ROOT/support/__EMSCRIPTEN__/

    # specific platform support
    cp -Rfv $ROOT/support/__EMSCRIPTEN__.patches/. $HOST_PREFIX/lib/python3.??/

    # TODO: use PYTHONPATH for python3-wasm to pick them in devices/emsdk/usr/lib/python3.11/
    #ln $PREFIX/lib/python3.??/_sysconfigdata__emscripten_wasm32-emscripten.py devices/x86_64/usr/lib/python3.??/

    mkdir -p prebuilt
    cp -vf build/cpython-wasm/libpython3.*.a prebuilt/
    rmdir  $PREFIX/lib/python3.??/lib-dynload
fi

mkdir -p $PYTHONPYCACHEPREFIX/sysconfig


# FIXME: seems CI cannot locate that one with python3-wasm
cp $PREFIX/lib/python3.??/_sysconfigdata__emscripten_wasm32-emscripten.py $PYTHONPYCACHEPREFIX/sysconfig/_sysconfigdata__emscripten_debug.py
sed -i 's|-Os|-O0|g' $PYTHONPYCACHEPREFIX/sysconfig/_sysconfigdata__emscripten_debug.py
sed -i 's|-g0|-g3|g' $PYTHONPYCACHEPREFIX/sysconfig/_sysconfigdata__emscripten_debug.py

#workaround
#cp $PYTHONPYCACHEPREFIX/sysconfig/_sysconfigdata__emscripten_debug.py  devices/x86_64/usr/lib/python3.11/_sysconfigdata__emscripten_debug.py



# python setup.py install --single-version-externally-managed --root=/
# pip3 install .

cat > $HOST_PREFIX/bin/cc <<END
#!/bin/bash

if echo \$@|grep -q shared
then
    # $COPTS
    emcc -O0 -g3 -fPIC -sSIDE_MODULE -gsource-map --source-map-base / \$@
else
    # $COPTS
    emcc -O0 -g3 -fPIC -DBUILD_STATIC \$@
fi
END

chmod +x $HOST_PREFIX/bin/cc


cat > ${PYTHONPYCACHEPREFIX}/.nanorc <<END
set tabsize 4
set tabstospaces
END

cat > $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh <<END
#!/bin/bash

if [[ ! -z \${EMSDK+z} ]]
then
    # emsdk_env already parsed
    echo -n
else
    pushd $ROOT
    . scripts/emsdk-fetch.sh
    popd
fi

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


END

cat > $HOST_PREFIX/bin/python3-wasm <<END
#!/bin/bash
. $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh

# most important
#export EMCC_CFLAGS="-sSIDE_MODULE -DBUILD_STATIC -fPIC"
export CC=cc
export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_debug

# does not work with -mpip
export PYTHONSTARTUP=$ROOT/support/__EMSCRIPTEN__.py

# so include dirs are good
export PYTHONHOME=$PREFIX

# find sysconfig ( tweaked )
# but still can load dynload and setuptools
PYTHONPATH=$(echo -n ${HOST_PREFIX}/lib/python3.??/site-packages):\$PYTHONPATH
export PYTHONPATH=$PYTHONPYCACHEPREFIX/sysconfig:$(echo -n ${HOST_PREFIX}/lib/python3.??/lib-dynload):\$PYTHONPATH


#probably useless
export _PYTHON_HOST_PLATFORM=${PYDK_PYTHON_HOST_PLATFORM}
export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}

$HOST_PREFIX/bin/python3.?? -u -B \$@
END

chmod +x $HOST_PREFIX/bin/python3-wasm






















unset PYTHON_FOR_BUILD
unset EMCC_CFLAGS




















