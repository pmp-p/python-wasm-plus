##!/bin/bash

. ${CONFIG:-config}

# same goal as  "python-wasm/fetch-python.sh"
# get python from git ( actually the only one supporting emsdk without patches)

pushd src

if [ -d cpython ]
then
    pushd cpython
    # put the tree back to original state so we can pull
    # Programs/python.c Modules/readline.c
    git restore .

    if git pull|grep -q 'Already up to date'
    then
        export REBUILD=${REBUILD:-false}
    else
        export REBUILD=true
    fi
    popd
else
    git clone https://github.com/python/cpython.git
    cd cpython
    #git checkout b36d222110d0d6d84dc8e973ca87d976c2423f5d # OK
    # FAIL git checkout a00518d9ad9a8f408a9699191019d75dd8406c32 # bpo-47120: Replace the JUMP_ABSOLUTE opcode by the relative JUMP_BACKWARD
    cd ..
fi

popd

echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"

