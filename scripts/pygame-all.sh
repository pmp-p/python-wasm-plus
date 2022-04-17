. ${CONFIG:-config}

echo "








            *****************************************************************
                    BUILDING PYGAME
            *****************************************************************








________________________________________________________________________________
"


cat $(which python3-wasm)

echo "
________________________________________________________________________________
"

mkdir -p prebuilt

if [ -d src/pygame-wasm/.git ]
then
    echo "
    * pygame already fetched
"
else
    pushd src
    git clone -b pygame-wasm-upstream https://github.com/pmp-p/pygame-wasm pygame-wasm
    popd
fi


pushd src/pygame-wasm

# regen cython files

#TODO: $HPY setup.py cython config

popd


#chmod +x $(find $EMSDK|grep sdl2-config$)


pushd src/pygame-wasm

# remove old lib
[ -f ${ROOT}/prebuilt/libpygame.a ] && rm ${ROOT}/prebuilt/libpygame.a

#../../scripts/static-merger.sh

# NB: EMCC_CFLAGS="-s USE_SDL=2 is required to prevent '-iwithsysroot/include/SDL'
# from ./emscripten/tools/ports/__init__.py

# 2>&1 | grep --line-buffered -v DOC_

if python3-wasm setup.py -config -auto -sdl2
then
    if CC=emcc CFLAGS="-DBUILD_STATIC -DSDL_NO_COMPAT -ferror-limit=1"\
 EMCC_CFLAGS="-s USE_SDL=2 -s USE_LIBPNG=1 -s USE_LIBJPEG=1"\
 python3-wasm setup.py build
    then
        # activate emsdk

        OBJS=$(find build/temp.wasm32-tot-emscripten-3.??/|grep o$)
        $ROOT/emsdk/upstream/emscripten/emar rcs ${ROOT}/prebuilt/libpygame.a $OBJS
        for obj in $OBJS
        do
            echo $obj
        done
    fi
fi
popd


