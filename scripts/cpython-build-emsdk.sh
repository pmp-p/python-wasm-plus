#!/bin/bash

. ${CONFIG:-config}

# TODO:
# fix /pip/_internal/operations/install/wheel.py
# for allowing to avoid pyc creation

    echo "
    * building cpython-wasm EMSDK_PYTHON=$SYS_PYTHON
" 1>&2


export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HPY}}

# remove old compiler wrapper to avoid conflicts
[ -f $HOST_PREFIX/bin/cc ] && rm $HOST_PREFIX/bin/cc

. ./scripts/emsdk-fetch.sh

REBUILD_WASM=${REBUILD_WASMPY:-false}

if $REBUILD || $REBUILD_WASMPY
then
    rm -rf build/cpython-wasm/ build/pycache/config.cache
    rm build/cpython-wasm/libpython${PYBUILD}.a 2>/dev/null
    rm prebuilt/emsdk/libpython${PYBUILD}.a prebuilt/emsdk/${PYBUILD}/*.so
    REBUILD=true
fi

# 3.10 is not wasm stable
if [ -f support/__EMSCRIPTEN__.patches/${PYBUILD}.diff ]
then
    pushd src/cpython${PYBUILD} 2>&1 >/dev/null
    patch -p1 < ../../support/__EMSCRIPTEN__.patches/${PYBUILD}.diff
    popd 2>&1 >/dev/null
fi


if [ -f $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/libffi.a ]
then
    echo "
        * ffi already built
    " 1>&2
else
    echo "
        * building libffi javascript port
    " 1>&2

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
      --disable-builddir --disable-multi-os-directory --disable-raw-api --disable-docs

    emmake make install

    unset EMCC_CFLAGS
    popd

    cp -fv  ${PREFIX}/lib/libffi.a $EMSDK/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/
    cp -vf  ${PREFIX}/include/ffi*.h ${EMSDK}/upstream/emscripten/cache/sysroot/include/

    ffipc=${SDKROOT}/emsdk/upstream/emscripten/system/lib/pkgconfig/libffi.pc
    cat > $ffipc <<END
prefix=${SDKROOT}/emsdk/upstream/emscripten/cache/sysroot
exec_prefix=\${prefix}
libdir=\${exec_prefix}/lib/wasm32-emscripten/pic
toolexeclibdir=\${libdir}
includedir=\${prefix}/include

Name: libffi
Description: Library supporting Foreign Function Interfaces
Version: 3.4.2
Libs: -L\${toolexeclibdir} -lffi
Cflags: -I\${includedir}
END
    chmod +x $ffipc

echo "

    *************************************************************************
    *************************************************************************

"
fi

# in this special case build testsuite
# main repo https://github.com/pmp-p/python-wasm-plus

# pygame-web won't build test modules

if echo $GITHUB_WORKSPACE|grep -q /python-wasm-plus/
then
    TESTSUITE="--enable-test-modules"
    #TESTSUITE=""
else
    TESTSUITE=""
fi

echo "




    ********** TESTSUITE test-modules == $TESTSUITE *******************




" 1>&2



if [ -f build/cpython-wasm/libpython${PYBUILD}.a ]
then
    echo "
        * not rebuilding cpython-wasm for [$PYDK_PYTHON_HOST_PLATFORM]
    " 1>&2
else
    echo "
        * rebuilding build/cpython-wasm for [$PYDK_PYTHON_HOST_PLATFORM]
            PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}
    " 1>&2


    mkdir -p build/cpython-wasm $PREFIX
    pushd build/cpython-wasm

#     --with-tzpath="/usr/share/zoneinfo" \

    export EMCC_CFLAGS="$CPOPTS -D_XOPEN_SOURCE_EXTENDED=1 -I$PREFIX/include/ncursesw -sUSE_ZLIB -sUSE_BZIP2"

    CPPFLAGS="$CPPFLAGS -I$PREFIX/include/ncursesw"
    CFLAGS="$CPPFLAGS -I$PREFIX/include/ncursesw"

# CFLAGS="-DHAVE_FFI_PREP_CIF_VAR=1 -DHAVE_FFI_PREP_CLOSURE_LOC=1 -DHAVE_FFI_CLOSURE_ALLOC=1"

    cat $ROOT/src/cpython${PYBUILD}/Tools/wasm/config.site-wasm32-emscripten \
         > $ROOT/src/cpython${PYBUILD}/Tools/wasm/config.site-wasm32-pydk

    cat >> $ROOT/src/cpython${PYBUILD}/Tools/wasm/config.site-wasm32-pydk << END


have_libffi=yes
ac_cv_func_dlopen=yes
ac_cv_lib_ffi_ffi_call=yes
py_cv_module__ctypes=yes
py_cv_module__ctypes_test=yes
END



# OPT="$CPOPTS -DNDEBUG -fwrapv" \
#      --with-c-locale-coercion --without-pydebug --without-pymalloc --disable-ipv6  \

#     --with-libs='-lz -lffi' \


    CONFIG_SITE=$ROOT/src/cpython${PYBUILD}/Tools/wasm/config.site-wasm32-pydk \
    emconfigure $ROOT/src/cpython${PYBUILD}/configure -C --with-emscripten-target=browser \
     --cache-file=${PYTHONPYCACHEPREFIX}/config.cache \
     --enable-wasm-dynamic-linking $TESTSUITE\
     --host=$PYDK_PYTHON_HOST_PLATFORM \
     --build=$($ROOT/src/cpython${PYBUILD}/config.guess) \
     --prefix=$PREFIX \
     --with-build-python=${PYTHON_FOR_BUILD}

    mkdir -p ${PYTHONPYCACHEPREFIX}/empty
    touch ${PYTHONPYCACHEPREFIX}/empty/$($HPY -V|cut -f2 -d' ')

    #echo "#define HAVE_NCURSES_H" >> pyconfig.h
    if echo $PYBUILD|grep -q 3.10
    then
        cat > Modules/Setup.local <<END
*disabled*
_decimal
xxsubtype
_crypt
curses

*static*
zlib zlibmodule.c
END
# _ctypes _ctypes/_ctypes.c _ctypes/callbacks.c _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c
    else
        cat > Modules/Setup.local <<END
*disabled*
_decimal
xxsubtype
_crypt

*static*
_ctypes _ctypes/_ctypes.c _ctypes/callbacks.c _ctypes/callproc.c _ctypes/stgdict.c _ctypes/cfield.c ${SDKROOT}/emsdk/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic/libffi.a

END


fi

    if emmake make -j$NPROC WASM_ASSETS_DIR=$(realpath ${PYTHONPYCACHEPREFIX}/empty)@/
    then
        emmake make WASM_ASSETS_DIR=$(realpath ${PYTHONPYCACHEPREFIX}/empty)@/ install
    else
        echo " **** cpython wasm build failed ***

        emmake make WASM_ASSETS_DIR=$(realpath ${PYTHONPYCACHEPREFIX}/empty)@/ install

        " 1>&2

        exit 1
    fi

    rm -rf $(find $ROOT/devices/ -type d|grep /__pycache__$)

    popd

    mkdir -p ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/site-packages
    mkdir -p ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/lib-dynload

    if [ -d $PREFIX/lib/python${PYBUILD}/lib-dynload ]
    then
        # move them to MEMFS
        mv $PREFIX/lib/python${PYBUILD}/lib-dynload/* ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/lib-dynload/

        # specific platform support
        cp -Rfv $ROOT/support/__EMSCRIPTEN__.patches/${PYBUILD}/. $PREFIX/lib/python${PYBUILD}/

        cp -vf build/cpython-wasm/libpython${PYBUILD}.a prebuilt/emsdk/
        for lib in $(find build/cpython-wasm/|grep lib.*.a$)
        do
            name=$(basename $lib .a)
            cp $lib prebuilt/emsdk/${name}${PYBUILD}.a
        done
        rmdir  $PREFIX/lib/python${PYBUILD}/lib-dynload
    fi
fi

mkdir -p $PYTHONPYCACHEPREFIX/sysconfig


# FIXME: seems CI cannot locate that one with python3-wasm
cp $PREFIX/lib/python${PYBUILD}/_sysconfigdata__emscripten_wasm32-emscripten.py \
 ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/_sysconfigdata__emscripten_debug.py

sed -i 's|-Os|-O0|g' ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/_sysconfigdata__emscripten_debug.py
sed -i 's|-g0|-g3|g' ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/_sysconfigdata__emscripten_debug.py


# python setup.py install --single-version-externally-managed --root=/
# pip3 install .

cat > $HOST_PREFIX/bin/cc <<END
#!/bin/bash
if [ -z "\$_EMCC_CCACHE" ]
then
unset _PYTHON_SYSCONFIGDATA_NAME
unset PYTHONHOME
unset PYTHONPATH

COMMON="-Wno-unused-command-line-argument -Wno-unreachable-code-fallthrough"
SHARED=""
IS_SHARED=false

for arg do
    shift

    # that is for some very bad setup.py behaviour regarding cross compiling. should not be needed ..
    [ "\$arg" = "-I/usr/include" ] && continue
    [ "\$arg" = "-I/usr/include/SDL2" ] && continue
    [ "\$arg" = "-L/usr/lib64" ]	&& continue
    [ "\$arg" = "-L/usr/lib" ]   && continue

    if [ "\$arg" = "-shared" ]
    then
        IS_SHARED=true
        SHARED="$SHARED -sSIDE_MODULE"
    fi

    if echo "\$arg"|grep -q wasm32-emscripten.so\$
    then
        IS_SHARED=true
        SHARED="$SHARED -shared -sSIDE_MODULE"
    fi
    set -- "\$@" "\$arg"
done

if \$IS_SHARED
then
    $SYS_PYTHON -E $EMSDK/upstream/emscripten/emcc.py \
     \$SHARED $COPTS $LDFLAGS -sSIDE_MODULE -gsource-map --source-map-base / "\$@" \$COMMON
else
    $SYS_PYTHON -E $EMSDK/upstream/emscripten/emcc.py \
     $COPTS $CPPFLAGS -DBUILD_STATIC "\$@" \$COMMON
fi
else
    unset _EMCC_CCACHE
    exec ccache "\$0" "\$@"
fi
END

chmod +x $HOST_PREFIX/bin/cc

cat > ${PYTHONPYCACHEPREFIX}/.nanorc <<END
set tabsize 4
set tabstospaces
END

cat >${PYTHONPYCACHEPREFIX}/.numpy-site.cfg <<NUMPY
[DEFAULT]
library_dirs = $PREFIX/lib
include_dirs = $PREFIX/include
NUMPY

cat > $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh <<END
#!/bin/bash
export ROOT=${SDKROOT}
export SDKROOT=${SDKROOT}

export PYBUILD=\${PYBUILD:-$PYBUILD}
export PYMAJOR=\$(echo -n \$PYBUILD|cut -d. -f1)
export PYMINOR=\$(echo -n \$PYBUILD|cut -d. -f2)

export CARGO_HOME=\${CARGO_HOME:-/opt/python-rust-sdk}
export RUSTUP_HOME=\${RUSTUP_HOME:-/opt/python-rust-sdk}
export PATH=\${CARGO_HOME}/bin:$PATH


if [[ ! -z \${EMSDK+z} ]]
then
    # emsdk_env already parsed
    echo -n
else
    . ${SDKROOT}/config
    . ${SDKROOT}/emsdk/emsdk_env.sh
    export PATH=$SDKROOT/emsdk/upstream/emscripten/system/bin:\$PATH
    export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig"
fi

export SYS_PYTHON=${SYS_PYTHON}
export EMSDK_PYTHON=${SYS_PYTHON}

export PATH=${HOST_PREFIX}/bin:\$PATH:${SDKROOT}/devices/emsdk/usr/bin
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
export HOME=${SDKROOT}
export PLATFORM_TRIPLET=${PYDK_PYTHON_HOST_PLATFORM}
export PREFIX=$PREFIX
export PYTHONPYCACHEPREFIX=${PYTHONPYCACHEPREFIX:-$PYTHONPYCACHEPREFIX}
mkdir -p \$PYTHONPYCACHEPREFIX

# so pip does not think everything in ~/.local is useable
export HOME=${SDKROOT}

export PYTHONDONTWRITEBYTECODE=1
export PYTHONSTARTUP="${SDKROOT}/support/__EMSCRIPTEN__.py"
> \${HOME}/.pythonrc.py

export PS1="[PyDK:wasm] \w $ "

export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_

END

cat > $HOST_PREFIX/bin/python3-wasm <<END
#!/bin/bash

. ${SDKROOT}/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh

# most important
export CC=emcc
export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_debug

# it's just for interactive python testing of modules.
export PYTHONSTARTUP=$ROOT/support/__EMSCRIPTEN__.py

# so include dirs are good
export PYTHONHOME=$PREFIX

# find sysconfig ( tweaked )
# but still can load dynload and setuptools

PYTHONPATH=${HOST_PREFIX}/lib/python\${PYBUILD}/site-packages:\$PYTHONPATH
export PYTHONPATH=${SDKROOT}/prebuilt/emsdk/${PYBUILD}:${HOST_PREFIX}/lib/python\${PYBUILD}/lib-dynload:\$PYTHONPATH

# just in case
export _PYTHON_HOST_PLATFORM=${PYDK_PYTHON_HOST_PLATFORM}
export PYTHON_FOR_BUILD=${HOST_PREFIX}/bin/python\${PYBUILD}

${HOST_PREFIX}/bin/python\${PYBUILD} -u -B "\$@"
END

chmod +x $HOST_PREFIX/bin/python3-wasm

# TODO: FIXME:
echo "368 cannot use python3-wasm as python3 for setup.py in pygame build" 1>&2
ln -sf $HOST_PREFIX/bin/python${PYBUILD} $HOST_PREFIX/bin/python3

cp -f $HOST_PREFIX/bin/python3-wasm ${ROOT}/


HPFX=./devices/$(arch)/usr/lib/python${PYBUILD}
TPFX=./devices/emsdk/usr/lib/python${PYBUILD}

rm $TPFX/ensurepip/_bundled/setuptools-*.whl

for moveit in setuptools distutils _distutils _distutils_hack pkg_resources
do
    echo "
    * migrating ${moveit}
" 1>&2
    cp -rf $HPFX/${moveit}   $TPFX/
    cp -rf $HPFX/${moveit}-* $TPFX/
done


unset PYTHON_FOR_BUILD
unset EMCC_CFLAGS
