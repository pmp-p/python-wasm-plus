#!/bin/bash
reset

. ${CONFIG:-config}

# web application template
TMPL=${1:-$(realpath templates/worker-gui)}
shift

# source code + assets of app
APK=${1:-$(realpath tests/test-assets)}
shift


# final app name in build folder
CN=${1:-demo}
shift


SP=$(realpath support/__EMSCRIPTEN__)

echo "
TMPL=${TMPL}
APK=${APK}
site-packages=${SP}
"


if [[ ! -z ${EMSDK+z} ]]
then
    # emsdk_env already parsed
    echo -n
else
    pushd $ROOT
    . scripts/emsdk-fetch.sh
    popd
fi

# O0/g3 is much faster to build and easier to debug
if [ -f dev ]
then
    echo ' building DEBUG'
    COPTS="-O0 -g3 -gsource-map --source-map-base http://localhost:8000"
else
    echo ' building RELEASE'
    COPTS="-Os -g0"
fi

# to trigger emscripten worker
# whose init is in Programs/python.c have a "worker" folder in the template
# directory

if [ -d $TMPL/worker ]
then
    FINAL_OPTS="$COPTS --proxy-to-worker -s ENVIRONMENT=web,worker"
    MODE="worker"
else
    FINAL_OPTS="$COPTS"
    MODE="main"
fi


pushd build/cpython-wasm

[ -f python.html ] && rm python.*
[ -f Programs/python.o ] && rm Programs/python.o

emcc -D__PYDK__=1 -DNDEBUG\
 -c -g -fwrapv -Wall -fPIC $COPTS -std=gnu99 -Werror=implicit-function-declaration -fvisibility=hidden\
 -I$ROOT/src/cpython/Include/internal -IObjects -IInclude -IPython -I. -I$ROOT/src/cpython/Include -DPy_BUILD_CORE\
 -o Programs/python.o $ROOT/src/cpython/Programs/python.c


emcc $FINAL_OPTS -std=gnu99 -D__PYDK__=1 \
 -s USE_BZIP2=1 -s USE_ZLIB=1 -s USE_SDL=2 -s ASSERTIONS=1 -s ALLOW_MEMORY_GROWTH=1\
 --preload-file $ROOT/devices/emsdk/usr@/usr \
 --preload-file ${APK}@/assets \
 --preload-file ${SP}/@/assets/site-packages \
 -o python.html Programs/python.o ${ROOT}/prebuilt/libpython3.*.a Modules/_decimal/libmpdec/libmpdec.a Modules/expat/libexpat.a\
 ${ROOT}/prebuilt/libpygame.a -ldl -lz -lm -lSDL2 -lSDL2_mixer -lSDL2_ttf -lfreetype -lharfbuzz

popd

mkdir -p build/${CN}/${MODE}/

[ -f build/${CN}/${MODE}/python.js ] && rm build/${CN}/${MODE}/python.*

mv -vf build/cpython-wasm/python.* build/${CN}/${MODE}/

if [ -f build/${CN}/${MODE}/python.html ]
then

    # copy the test server
    cp -vf support/server.py build/${CN}/

    # hardlink the files
    # but symlinks the subfolders
    for df in ${TMPL}/*
    do
        if [ -d $df ]
        then
            ln -sf $df build/${CN}/ 2>/dev/null
        else
            [ -f $df ] && ln $df build/${CN}/ 2>/dev/null
        fi
    done

    echo "
_______________________________________________________________________________

Now running final app from [build/${CN}] :
 - beware files in worker/main subdirs overwritten each build, changes are lost
 - others are source files (hard/softlinks), changes impact the originals
_______________________________________________________________________________


"

    pushd build/${CN}
    $HOST/bin/python3 server.py $@
    popd

else
    echo "

    build failed

    "
fi

