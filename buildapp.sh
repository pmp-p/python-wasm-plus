#!/bin/bash
reset

. ${CONFIG:-config}

EXE=python311

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

ALWAYS_ASSETS=$(realpath tests/assets)
ALWAYS_CODE=$(realpath tests/code)

# O0/g3 is much faster to build and easier to debug


if [ -f dev ]
then
    echo ' building DEBUG'
    COPTS="-O0 -g3 -s ASSERTIONS=1 -gsource-map --source-map-base /"
    ALWAYS_FS="--preload-file ${ALWAYS_ASSETS}@/assets --preload-file ${ALWAYS_CODE}@/assets"
else
    echo ' building RELEASE'
    COPTS="-Os -g0 -s ASSERTIONS=1"
    ALWAYS_FS="--preload-file ${ALWAYS_ASSETS}@/assets"
fi
# option -sSINGLE_FILE ?


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
else
# https://github.com/emscripten-core/emscripten/issues/10086
#       EXPORT_NAME does not affect generated html
#
    FINAL_OPTS="$COPTS"
    MODE="main"
    WORKER_STATUS="not using worker"
fi

if false
then
    FINAL_OPTS="$FINAL_OPTS -s MODULARIZE=1"
    FINAL_OPTS="$FINAL_OPTS -s EXPORT_NAME=\"${EXE}\""
    FINAL_OPTS="$FINAL_OPTS -s EXPORTED_RUNTIME_METHODS=[\"FS\"]"
fi


if [ -d build/$CN ]
then
    echo "
    * not regenerating projects files in build/$CN
"
else

    # create the folder that will receive wasm+emsdk files.
    mkdir -p build/${CN}/${EXE}/

    # copy libs found in "worker" or "main" text file
    # order matters as they can owerwrite themselves
    for lib in $(cat $TMPL/$MODE)
    do
        echo "      added lib $(basename $lib)"
        /bin/cp -Rfl $lib/. build/${CN}/
    done

    # copy the test server
    cp -lv support/server.py build/${CN}/

    ln support/__EMSCRIPTEN__.py build/${CN}/pythonrc.py
    # hardlink the projects files
    # but symlinks the subfolders
    # so editing build is same as editing the template
    # this is to avoid loosing changes

    for df in ${TMPL}/* ${APK}/static/*
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

[ -f ${MODE}.js ] && rm ${MODE}.*
[ -f Programs/${MODE}.o ] && rm Programs/${MODE}.o

emcc -D__PYDK__=1 -DNDEBUG\
 -c -fwrapv -Wall -fPIC $COPTS -std=gnu99 -Werror=implicit-function-declaration -fvisibility=hidden\
 -I$ROOT/src/cpython/Include/internal -IObjects -IInclude -IPython -I. -I$ROOT/src/cpython/Include -DPy_BUILD_CORE\
 -o Programs/${MODE}.o $ROOT/src/cpython/Programs/python.c

#  --preload-file ${APK}/@/assets

emcc $FINAL_OPTS -std=gnu99 -D__PYDK__=1 -DNDEBUG\
 -s TOTAL_MEMORY=512MB -s ALLOW_TABLE_GROWTH \
 -s USE_BZIP2=1 -s USE_ZLIB=1 -s USE_SDL=2\
 --use-preload-plugins \
 --preload-file $ROOT/devices/emsdk/usr/lib/python3.11@/usr/lib/python3.11 \
 --preload-file ${SP}/@/assets/site-packages \
 $ALWAYS_FS \
 -o ${MODE}.js Programs/${MODE}.o ${ROOT}/prebuilt/libpython3.*.a Modules/_decimal/libmpdec/libmpdec.a Modules/expat/libexpat.a \
 ${ROOT}/prebuilt/libpygame.a -lSDL2 -lSDL2_mixer -lSDL2_ttf -lSDL2_image -lfreetype -lharfbuzz \
 -ljpeg -lpng -ldl -lz -lm


popd

[ -f build/${CN}/${EXE}/${MODE}.js ] && rm build/${CN}/${EXE}/${MODE}.*

mv -vf build/cpython-wasm/${MODE}.* build/${CN}/${EXE}/
#mv build/${CN}/${EXE}/*.map build/${CN}/
#mv build/${CN}/${EXE}/*.data build/${CN}/
if [ -f build/${CN}/${EXE}/${MODE}.js ]
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

