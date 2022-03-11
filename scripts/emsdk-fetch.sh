#!/bin/bash

. ${CONFIG:-config}

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

if [ -f embuild.done ]
then
    echo "
    * emsdk prereq ok
"
else
    ALL="struct_info libfetch zlib bzip2 freetype harfbuzz"
    ALL="$ALL libpng libjpeg sdl2_image sdl2_mixer sdl2_ttf"
    echo "
    * building third parties libraries for emsdk ( can take time ... )
"
    for one in $ALL
    do
    echo "
        + $done
"
        embuilder --pic build $one
        embuilder build $one
    done
    touch embuild.done
fi

if echo $PATH|grep -q $EMSDK/upstream/emscripten/system/bin
then
    # emsdk env does not set it, it's needed for eg sdl2-config
    echo -n
else
    export PATH=$EMSDK/upstream/emscripten/system/bin:$PATH
fi
