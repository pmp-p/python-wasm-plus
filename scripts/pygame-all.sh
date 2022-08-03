#!/bin/bash

if $CI
then
    echo "
        * not building host pygame
    " 1>&2
else
    if $HPY -c "import pygame"
    then
        echo "
    * not re-building host pygame
        " 1>&2
    else
        echo "
    * building host pygame for desktop simulator
        " 1>&2
        rm -rf src/pygame-wasm/Setup src/pygame-wasm/build
        pushd src/pygame-wasm
        $HPY setup.py -config -auto -sdl2
        $HPY setup.py install
        popd
    fi
fi

. ${CONFIG:-config}

mkdir -p prebuilt

if [ -d src/pygame-wasm/.git ]
then
    echo "
        * pygame already fetched
    " 1>&2
else
    pushd src
    # if running from main repo use the upstreaming pygame-wasm
    if echo $GITHUB_WORKSPACE|grep -q /python-wasm-plus/
    then
        # pygame-wasm testing
        git clone --no-tags --depth 1 --single-branch -b pygame-wasm https://github.com/pmp-p/pygame-wasm pygame-wasm
    else
        # git pygame for pygame-web
        git clone --no-tags --depth 1 --single-branch -b main https://github.com/pygame/pygame pygame-wasm
    fi
    popd
fi


echo "


    *******************************************************************************
    *******************************************************************************

"


# remove old lib
[ -f ${ROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a ] && rm ${ROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a



# remove anything that could be native
if [ -d src/pygame-wasm/build ]
then
    echo "
        * cleaning up pygame build
    " 1>&2
    rm -rf src/pygame-wasm/Setup src/pygame-wasm/build
fi

pushd src/pygame-wasm

# regen cython files
if [ -f dev ]
then
    #TODO: $HPY setup.py cython config
    python3 setup.py cython_only
fi


# for libSDL2_ttf.a
# LDFLAGS="$LDFLAGS -L$ROOT/emsdk/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic"

# emsdk is activated via python3-wasm

if false
then
    SDL_IMAGE="-s USE_SDL_IMAGE=2 -sUSE_LIBPNG -sUSE_LIBJPEG"
else
    SDL_IMAGE="-I$PREFIX/include/SDL2 -s USE_SDL=2 -sUSE_SDL_TTF=2 -sUSE_LIBPNG -sUSE_LIBJPEG -lwebp"
fi

rm -rf build/temp.wasm32-* 2>/dev/null

if python3-wasm setup.py -config -auto -sdl2
then
    if CC=emcc CFLAGS="-DHAVE_STDARG_PROTOTYPES -DBUILD_STATIC -DSDL_NO_COMPAT -ferror-limit=1 -Wno-unused-command-line-argument -Wno-unreachable-code-fallthrough -fPIC"\
 EMCC_CFLAGS="$SDL_IMAGE"\
 python3-wasm setup.py build -j3
    then
        OBJS=$(find build/temp.wasm32-*/|grep o$)
        $ROOT/emsdk/upstream/emscripten/emar rcs ${ROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a $OBJS
        for obj in $OBJS
        do
            echo $obj
        done
    else
        exit 82
    fi
else
    exit 85
fi
popd


