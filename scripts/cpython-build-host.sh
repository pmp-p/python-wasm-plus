#!/bin/bash

. ${CONFIG:-config}

export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST_PREFIX}/bin/python3}

mkdir -p build/cpython-host

if $REBUILD
then
    echo "
    * building cpython
"
else
    if [ -f ${PYTHON_FOR_BUILD} ]
    then
        REBUILD=false
        echo "  * will *RE-USE* PYTHON_FOR_BUILD found at ${PYTHON_FOR_BUILD}"
    else
        REBUILD=true
    fi
fi

if $REBUILD
then
    pushd build/cpython-host

#--with-c-locale-coercion
#--without-pymalloc --without-pydebug
    PYOPTS="--disable-ipv6  \
     --with-ensurepip\
     --with-decimal-contextvar --with-system-ffi --enable-shared\
     --with-computed-gotos"

    # Prevent freezing bytecode with a different magic
    rm -f $HOST_PREFIX/bin/python3*

    if which python3.11|grep -q python
    then
        echo "



    ===================================================================================

            it's not safe to have a python3.11 in the path while in pre-release cycle
            _sre.MAGIC / bytecode weird errors etc ...

    ===================================================================================

"
        sleep 3
    fi

    # CFLAGS="-DHAVE_FFI_PREP_CIF_VAR=1 -DHAVE_FFI_PREP_CLOSURE_LOC=1 -DHAVE_FFI_CLOSURE_ALLOC=1"

    if \
    CC=clang CXX=clang++ \
    ${ROOT}/src/cpython/configure \
     --prefix=$HOST_PREFIX $PYOPTS
    then
        make -j$(nproc) install
        cp -Rfv $ROOT/support/__EMSCRIPTEN__.patches/. $HOST_PREFIX/lib/python3.??/
    else
        echo "
==========================================================================
    ERROR: could not configure cpython

    reminder: you need clang libffi-dev and usual cpython requirements.
==========================================================================
    "
        read
    fi



    popd
else
    echo "

    *   cpython host already built :
            PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}
"
fi


unset PYTHON_FOR_BUILD
