##!/bin/bash

. ${CONFIG:-config}

echo "
    *cpython-fetch*
"


pushd src 2>&1 >/dev/null

if false
then

    # same goal as  "python-wasm/fetch-python.sh"
    # get python from git ( actually the only one supporting emsdk without patches)

    if [ -d cpython ]
    then
        pushd cpython 2>&1 >/dev/null
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
        git clone https://github.com/python/cpython.git
        export REBUILD=true
    fi

else
    rm cpython 2>/dev/null
    #wget -q -c https://www.python.org/ftp/python/3.11.0/Python-3.11.0b1.tar.xz
    #tar xf Python-3.11.0b1.tar.xz
    #ln -s Python-3.11.0b1 cpython

    wget -q -c https://www.python.org/ftp/python/3.11.0/Python-3.11.0b3.tgz
    tar xf Python-3.11.0b3.tgz
    ln -s Python-3.11.0b3 cpython
fi

popd


# do some patching

pushd src/cpython 2>&1 >/dev/null

patch -p1 < ../../support/__EMSCRIPTEN__.embed/cpython.diff

popd

echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"

