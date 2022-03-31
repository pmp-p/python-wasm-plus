#!/bin/bash

. ${CONFIG:-config}

mkdir -p build/cpython-host

export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD:-${HOST}/bin/python3}


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
    PYOPTS="--without-pymalloc --without-pydebug\
     --disable-ipv6 --with-c-locale-coercion --with-ensurepip\
     --with-decimal-contextvar --with-system-ffi --enable-shared\
     --with-computed-gotos"

    if CC=clang CXX=clang++ ${ROOT}/src/cpython/configure \
     --prefix=$HOST_PREFIX $PYOPTS
    then
        make -j$(nproc) install
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


