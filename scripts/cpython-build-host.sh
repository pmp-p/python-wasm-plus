#!/bin/bash

. ${CONFIG:-config}

export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HPY}}

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


    export OPT="$COPTS -DNDEBUG -fwrapv"

    PYOPTS="--with-c-locale-coercion --disable-ipv6 \
     --without-pymalloc --without-pydebug \
     --with-ensurepip\
     --with-decimal-contextvar --enable-shared \
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
    CC=clang CXX=clang++ OPT="$OPT" \
    eval ${ROOT}/src/cpython/configure \
     --prefix=$HOST_PREFIX $PYOPTS $VERBOSE
    then
        eval make -j$(nproc) install $VERBOSE
        rm -rf $(find $ROOT/devices/ -type d|grep __pycache__$)

        #2>&1 \
         #|grep --line-buffered -v ^Compiling\
         #|grep --line-buffered -v ^Listing\
         #|grep --line-buffered -v ^install

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
