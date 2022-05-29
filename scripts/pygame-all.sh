. ${CONFIG:-config}

mkdir -p prebuilt

if [ -d src/pygame-wasm/.git ]
then
    echo "
    * pygame already fetched
"
else
    pushd src
    #git clone -b pygame-wasm-upstream https://github.com/pmp-p/pygame-wasm pygame-wasm
    git clone https://github.com/pygame/pygame pygame-wasm
    popd
fi


echo "


    *******************************************************************************
    *******************************************************************************

"


# remove old lib
[ -f ${ROOT}/prebuilt/libpygame.a ] && rm ${ROOT}/prebuilt/libpygame.a


pushd src/pygame-wasm 2>&1 >/dev/null

# regen cython files
if [ -f dev ]
then
    #TODO: $HPY setup.py cython config
    python3 setup.py config cython
fi


# for libSDL2_ttf.a
# LDFLAGS="$LDFLAGS -L$ROOT/emsdk/upstream/emscripten/cache/sysroot/lib/wasm32-emscripten/pic"

# emsdk is activated via python3-wasm

if $CI
then
    SDL_IMAGE="-s USE_SDL_IMAGE=2 -sUSE_LIBPNG -sUSE_LIBJPEG"
else
    SDL_IMAGE="-sUSE_LIBPNG -sUSE_LIBJPEG"
fi

if python3-wasm setup.py -config -auto -sdl2
then
    if CC=emcc CFLAGS="-DBUILD_STATIC -DSDL_NO_COMPAT -ferror-limit=1 -Wno-unused-command-line-argument -Wno-unreachable-code-fallthrough -fPIC"\
 EMCC_CFLAGS="-I$PREFIX/include/SDL2 -s USE_SDL=2 -sUSE_SDL_TTF=2 $SDL_IMAGE"\
 python3-wasm setup.py build
    then
        OBJS=$(find build/temp.wasm32-tot-emscripten-3.??/|grep o$)
        $ROOT/emsdk/upstream/emscripten/emar rcs ${ROOT}/prebuilt/libpygame.a $OBJS
        for obj in $OBJS
        do
            echo $obj
        done
    fi
fi
popd


