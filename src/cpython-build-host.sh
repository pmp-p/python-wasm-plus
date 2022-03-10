#!/bin/bash

REBUILD=${REBUILD:-false}
ROOT="$(pwd)"
HOST="$ROOT/host"

mkdir -p host build/host


export PYTHON_FOR_BUILD="${HOST}/bin/python3"


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
    pushd build/host
    PYOPTS="--without-pymalloc --without-pydebug\
     --disable-ipv6 --with-c-locale-coercion --with-ensurepip\
     --with-decimal-contextvar --with-system-ffi --enable-shared\
     --with-computed-gotos"

    if CC=clang CXX=clang++ ${ROOT}/cpython/configure \
     --prefix="$(realpath ${HOST})" $PYOPTS
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



