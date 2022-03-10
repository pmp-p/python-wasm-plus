#!/bin/bash

if [ -d emsdk ]
then
    echo "
    * using emsdk from $(realpath emsdk)
"
else
    if git clone https://github.com/emscripten-core/emsdk.git
    then
        pushd emsdk
        ./emsdk install tot
        ./emsdk activate tot
        popd
    fi
fi

if [ -f emsdk/emsdk_env.sh ]
then
    echo "
    * activating emsdk via emsdk_env.sh
"
    . emsdk/emsdk_env.sh
else
    echo "
    ERROR cannot find emsdk/emsdk_env.sh in $(pwd)
"
    read
fi


