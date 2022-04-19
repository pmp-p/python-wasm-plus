#!/bin/bash

if [[ -z ${EMSDK+z} ]]
then

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
        tar xvf emsdk-fix.tar
    fi


    if [ -f emsdk/emsdk_env.sh ]
    then
        echo "
        * activating emsdk via emsdk_env.sh
"
        . emsdk/emsdk_env.sh 2>&1 > /dev/null


        for py in 10 9 8 7 6 5
        do
            if command -v python3.${py}
            then
                export EMSDK_PYTHON=$(command -v python3.${py})
                break
            fi
        done

    else
        echo "
        ERROR cannot find emsdk/emsdk_env.sh in $(pwd)
"
        exit 1
    fi


    if [ -f embuild.done ]
    then
        echo "
        * emsdk prereq ok
    "
    else
        ALL="libgl libal libhtml5 libstubs libnoexit libsockets"
        ALL="$ALL libc libdlmalloc libcompiler_rt libc++-noexcept libc++abi-noexcept"
        ALL="$ALL libpng libjpeg sdl2 sdl2_image sdl2_mixer sdl2_ttf sdl2_gfx"
        ALL="$ALL struct_info libfetch zlib bzip2 freetype harfbuzz"

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
        # emsdk env does not set it, but it's required for eg sdl2-config
        echo -n
    else
        export PATH=$EMSDK/upstream/emscripten/system/bin:$EMSDK/upstream/emscripten:$PATH
    fi

fi
