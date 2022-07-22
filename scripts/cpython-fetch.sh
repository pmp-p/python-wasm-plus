##!/bin/bash

. ${CONFIG:-config}

echo "
    *   cpython-fetch $PYBUILD  *
"

mkdir -p src

pushd src 2>&1 >/dev/null

NOPATCH=false
[ -L cpython ] && rm cpython

[ -f $HPY ] || REBUILD=true


if echo $PYBUILD |grep -q 12$
then
    if [ -d cpython-git ]
    then
        pushd cpython-git 2>&1 >/dev/null
        # put the tree back to original state so we can pull
        # Programs/python.c Modules/readline.c
        git restore .

        if git pull|grep -q 'Already up to date'
        then
            export REBUILD=${REBUILD:-false}
        else
            export REBUILD=true
        fi
        #not here or pip won't install properly anymore its wheels
        #cat $ROOT/support/compilenone.py > ./Lib/compileall.py
        popd
    else
        git clone --no-tags --depth 1 --single-branch --branch main https://github.com/python/cpython.git cpython-git
        export REBUILD=true
    fi

    ln -s cpython-git cpython

fi

if echo $PYBUILD | grep -q 11$
then
    wget -q -c https://www.python.org/ftp/python/3.11.0/Python-3.11.0b4.tar.xz
    tar xf Python-3.11.0b4.tar.xz
    ln -s Python-3.11.0b4 cpython

    export REBUILD=true
fi

if echo $PYBUILD | grep -q 10$
then
    wget -q -c https://www.python.org/ftp/python/3.10.5/Python-3.10.5.tar.xz
    tar xf Python-3.10.5.tar.xz
    ln -s Python-3.10.5 cpython

    #tar xfj /data/git/python-wasm-sdk/src/Python-3.10.5-pydk.tar.bz2
    #ln -s Python-3.10.5-pydk cpython

    NOPATCH=true
    export REBUILD=true
fi


popd

# 3.10 is not wasm stable
if [ -f support/__EMSCRIPTEN__.patches/${PYBUILD}.diff ]
then
    pushd src/cpython 2>&1 >/dev/null
    patch -p1 < ../../support/__EMSCRIPTEN__.patches/${PYBUILD}.diff
    popd 2>&1 >/dev/null
fi

# the sys._emscripten_info is actually not compatible with shared build
# just move its stuff to main

if $NOPATCH
then
    echo "
    * assuming cpython tree already patched, press <enter>
"
else
    # do some patching
    pushd src/cpython 2>&1 >/dev/null
    patch -p1 < ../../support/__EMSCRIPTEN__.embed/cpython.diff
    popd 2>&1 >/dev/null
fi


echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"

[ -d build/cpython-host ] && rm -rf build/cpython-host
[ -d build/cpython-wasm ] && rm -rf build/cpython-wasm
