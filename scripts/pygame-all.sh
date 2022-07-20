. ${CONFIG:-config}

mkdir -p prebuilt

if [ -d src/pygame-wasm/.git ]
then
    echo "
    * pygame already fetched
"
else
    pushd src
    if echo $GITHUB_WORKSPACE|grep -q /python-wasm-plus/
    then
        # pygame-wasm testing
        git clone --no-tags --depth 1 --single-branch -b pygame-wasm https://github.com/pmp-p/pygame-wasm pygame-wasm
    else
        # git pygame
        git clone --no-tags --depth 1 --single-branch -b main https://github.com/pygame/pygame pygame-wasm
    fi
    popd
fi


echo "


    *******************************************************************************
    *******************************************************************************

"


# remove old lib
[ -f ${ROOT}/prebuilt/emsdk/libpygame.a ] && rm ${ROOT}/prebuilt/emsdk/libpygame.a

# remove anything that could be native
rm -rf src/pygame-wasm/Setup src/pygame-wasm/build


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
    SDL_IMAGE="-sUSE_LIBPNG -sUSE_LIBJPEG -lwebp"
fi

rm -rf build/temp.wasm32-* 2>/dev/null

if python3-wasm setup.py -config -auto -sdl2
then
    if CC=emcc CFLAGS="-DBUILD_STATIC -DSDL_NO_COMPAT -ferror-limit=1 -Wno-unused-command-line-argument -Wno-unreachable-code-fallthrough -fPIC"\
 EMCC_CFLAGS="-I$PREFIX/include/SDL2 -s USE_SDL=2 -sUSE_SDL_TTF=2 $SDL_IMAGE"\
 python3-wasm setup.py build -j3
    then
        OBJS=$(find build/temp.wasm32-*/|grep o$)
        $ROOT/emsdk/upstream/emscripten/emar rcs ${ROOT}/prebuilt/emsdk/libpygame.a $OBJS
        for obj in $OBJS
        do
            echo $obj
        done
    fi
fi
popd


