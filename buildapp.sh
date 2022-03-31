#!/bin/bash
reset

. ${CONFIG:-config}

# web application template
TMPL=${1:- templates/no-worker-xterm}
TMPL=$(realpath $TMPL)
shift

# source code + assets of app
APK=${1:-demos/1-touchpong}
APK=$(realpath $APK)
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
    COPTS="-O0 -g3 -gsource-map --source-map-base /"
    ALWAYS_ASSETS=$(realpath tests/assets)
    ALWAYS_CODE=$(realpath tests/code)
    ALWAYS_FS="--preload-file ${ALWAYS_ASSETS}@/assets --preload-file ${ALWAYS_CODE}@/assets"

else
    echo ' building RELEASE'
    COPTS="-Os -g0"
    ALWAYS_CODE=$(realpath tests/code)
    ALWAYS_FS="--preload-file ${ALWAYS_CODE}@/assets"
fi

echo "

    ALWAYS_FS=$ALWAYS_FS

"

# to trigger emscripten worker
# whose init is in Programs/python.c have a "worker" folder in the template
# directory
if [ -f $TMPL/worker ]
then
    FINAL_OPTS="$COPTS --proxy-to-worker -s ENVIRONMENT=web,worker"
    MODE="worker"
    WORKER_STATUS="using worker"
    mkdir -p build/$CN/worker
else
    FINAL_OPTS="$COPTS"
    MODE="main"
    WORKER_STATUS="not using worker"
fi

if [ -d build/$CN ]
then
    echo "
    * not regenerating projects files in build/$CN
"
else

    # create the folder that will receive wasm+emsdk files.
    mkdir -p build/${CN}/${MODE}/

    # copy libs found in "worker" or "main" text file
    # order matters as they can owerwrite themselves
    for lib in $(cat $TMPL/$MODE)
    do
        echo "      added lib $(basename $lib)"
        /bin/cp -rf $lib/. build/${CN}/
    done

    # copy the test server
    cp -v support/server.py build/${CN}/

    # hardlink the projects files
    # but symlinks the subfolders
    # so editing build is same as editing the template
    # this is to avoid loosing changes

    for df in ${TMPL}/*
    do
        if [ -d $df ]
        then
            ln -sf $(realpath $df) build/${CN}/ 2>/dev/null
        else
            [ -f $df ] && ln $df build/${CN}/ 2>/dev/null
        fi
    done
fi

pushd build/cpython-wasm

[ -f python.html ] && rm python.*
[ -f Programs/python.o ] && rm Programs/python.o

emcc -D__PYDK__=1 -DNDEBUG\
 -c -fwrapv -Wall -fPIC $COPTS -std=gnu99 -Werror=implicit-function-declaration -fvisibility=hidden\
 -I$ROOT/src/cpython/Include/internal -IObjects -IInclude -IPython -I. -I$ROOT/src/cpython/Include -DPy_BUILD_CORE\
 -o Programs/python.o $ROOT/src/cpython/Programs/python.c

emcc $FINAL_OPTS -std=gnu99 -D__PYDK__=1 \
 -s USE_BZIP2=1 -s USE_ZLIB=1 -s USE_SDL=2 -s ASSERTIONS=1 -s ALLOW_MEMORY_GROWTH=1\
 --preload-file $ROOT/devices/emsdk/usr@/usr  --preload-file ${SP}/@/assets/site-packages \
 $ALWAYS_FS --preload-file ${APK}@/assets \
 -o python.html Programs/python.o ${ROOT}/prebuilt/libpython3.*.a Modules/_decimal/libmpdec/libmpdec.a Modules/expat/libexpat.a\
 ${ROOT}/prebuilt/libpygame.a -ldl -lz -lm -lSDL2 -lSDL2_mixer -lSDL2_ttf -lfreetype -lharfbuzz

popd

[ -f build/${CN}/${MODE}/python.js ] && rm build/${CN}/${MODE}/python.*

mv -vf build/cpython-wasm/python.* build/${CN}/${MODE}/

if [ -f build/${CN}/${MODE}/python.html ]
then
    echo "
_______________________________________________________________________________

Now running final app from [build/${CN}] :
 - beware files in worker/main subdirs overwritten each build, changes are lost
 - others are source files (hard/softlinks), changes impact the originals

Threading system: $WORKER_STATUS
_______________________________________________________________________________


"

    pushd build/${CN}
    ${HOST_PREFIX}/bin/python3 server.py $@
    popd

else
    echo "

    build failed

    "
fi

