##!/bin/bash

. ${CONFIG:-config}

# same goal as  "python-wasm/fetch-python.sh"
# get python from git ( actually the only one supporting emsdk without patches)

pushd src

if [ -d src/cpython ]
then
    pushd cpython
    # put the tree back to original state so we can pull
    git restore Programs/python.c Modules/readline.c

    git pull|grep -q 'Already up to date' && export REBUILD=${REBUILD:-false}
    popd
else
    git clone https://github.com/python/cpython.git
fi

popd

echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"

