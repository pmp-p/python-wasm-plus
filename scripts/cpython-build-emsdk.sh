#!/bin/bash

. ${CONFIG:-config}

# TODO:
# fix /pip/_internal/operations/install/wheel.py
# for allowing to avoid pyc creation

    echo "
    * building cpython-wasm EMSDK_PYTHON=$SYS_PYTHON
"


export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST_PREFIX}/bin/python3}

# remove old compiler wrapper to avoid conflicts
rm $HOST_PREFIX/bin/cc


. ./scripts/emsdk-fetch.sh


REBUILD_WASM=${REBUILD_WASMPY:-false}

if $REBUILD || $REBUILD_WASMPY
then
    rm -rf build/cpython-wasm/ build/pycache/config.cache
    rm build/cpython-wasm/libpython3.??.a 2>/dev/null
    REBUILD=true
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
        pushd src 2>&1 >/dev/null
        git clone https://github.com/pmp-p/libffi-emscripten.git libffi
        popd
    fi

    mkdir -p build/libffi $PREFIX
    pushd build/libffi

#TODO: check if export PATH=${HOST_PREFIX}/bin:$PATH is really set to avoid system python with different bytecode
#and no loder lib-dynload in the way.

    export EMCC_CFLAGS="-O0 -g0 -fPIC"

     CFLAGS="-O0 -g0 -fPIC" \
      emconfigure $ROOT/src/libffi/configure --host=wasm32-tot-linux\
      --prefix=$PREFIX --enable-static --disable-shared --disable-dependency-tracking\
      --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs >/dev/null

    emmake make install >/dev/null

    unset EMCC_CFLAGS
    popd

    cp -fv  ${PREFIX}/lib/libffi.a $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/
    cp -vf  ${PREFIX}/include/ffi*.h ${EMSDK}/upstream/emscripten/cache/sysroot/include/
echo "

    *************************************************************************
    *************************************************************************

"
fi

# in this special case build testsuite
if echo $GITHUB_WORKSPACE|grep -q /python-wasm-plus
then
    TESTSUITE="--enable-test-modules"
else
    TESTSUITE=""
fi

echo "

TESTSUITE=$TESTSUITE

"



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

    export EMCC_CFLAGS="$CPOPTS"

    CPPFLAGS="$CPPFLAGS -I$PREFIX/include/ncursesw"
    CFLAGS="$CPPFLAGS -I$PREFIX/include/ncursesw"

# CFLAGS="-DHAVE_FFI_PREP_CIF_VAR=1 -DHAVE_FFI_PREP_CLOSURE_LOC=1 -DHAVE_FFI_CLOSURE_ALLOC=1"

    CONFIG_SITE=$ROOT/src/cpython/Tools/wasm/config.site-wasm32-emscripten\
    OPT="$CPOPTS -DNDEBUG -fwrapv" \
    eval emconfigure $ROOT/src/cpython/configure -C --without-pymalloc --disable-ipv6 \
     --cache-file=${PYTHONPYCACHEPREFIX}/config.cache \
     --with-c-locale-coercion --without-pydebug \
     --enable-wasm-dynamic-linking $TESTSUITE\
     --host=$PYDK_PYTHON_HOST_PLATFORM \
     --build=$($ROOT/src/cpython/config.guess) \
     --with-emscripten-target=browser \
     --prefix=$PREFIX \
     --with-build-python=${PYTHON_FOR_BUILD} $QUIET

    #echo "#define HAVE_NCURSES_H" >> pyconfig.h

    if EMCC_CFLAGS="-sUSE_ZLIB -sUSE_BZIP2" eval emmake make -j$(nproc) $QUIET
    then
        EMCC_CFLAGS="-sUSE_ZLIB -sUSE_BZIP2" eval emmake make install $QUIET
    else
        echo " **** cpython wasm build failed *** "
        exit 1
    fi

    rm -rf $(find $ROOT/devices/ -type d|grep __pycache__$)

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
unset _PYTHON_SYSCONFIGDATA_NAME
unset PYTHONHOME
unset PYTHONPATH
for py in 10 9 8 7
do
    if command -v python3.${py}
    then
        export EMSDK_PYTHON=$(command -v python3.${py})
        break
    fi
done

for arg do
    shift
    [ "\$arg" = "-I/usr/include" ] && continue
    [ "\$arg" = "-I/usr/include/SDL2" ] && continue
    [ "\$arg" = "-L/usr/lib64" ]	&& continue
    [ "\$arg" = "-L/usr/lib" ]   && continue
    set -- "\$@" "\$arg"
done

SHARED=""
IS_SHARED=false

if echo \$@|grep -q shared
then
    IS_SHARED=true
    SHARED="-sSIDE_MODULE"
else
    if echo \$@|grep -q wasm32-emscripten.so
    then
        IS_SHARED=true
        SHARED="-shared -sSIDE_MODULE"
    fi
fi

if \$IS_SHARED
then
    # $COPTS
    emcc \$SHARED $COPTS $LDFLAGS -sSIDE_MODULE -gsource-map --source-map-base / \$@
else
    # $COPTS
    emcc $COPTS $CPPFLAGS -DBUILD_STATIC \$@
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
    . ${ROOT}/config
    . ${ROOT}/emsdk/emsdk_env.sh
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
library_dirs = $PREFIX/lib
include_dirs = $PREFIX/include
NUMPY

END

cat > $HOST_PREFIX/bin/python3-wasm <<END
#!/bin/bash
. $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh

# most important
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

$HPY -u -B \$@
END

chmod +x $HOST_PREFIX/bin/python3-wasm
cp -f $HOST_PREFIX/bin/python3-wasm ${ROOT}/


unset PYTHON_FOR_BUILD
unset EMCC_CFLAGS




