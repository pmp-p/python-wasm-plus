#!/bin/bash

export ROOT=$(pwd)

. ${CONFIG:-config}

if $CI
then
    echo "
    * packing files for /python${PYMAJOR}${PYMINOR}/
"
else
    while true
    do
        echo "Waiting for pygame (prebuilt/emsdk/libpygame${PYBUILD}.a) build to complete ..."
        for i in 1 2 3 4
        do
            [ -f ${SDKROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a ] && break
            sleep 1
        done
        [ -f ${SDKROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a ] && break

    done
    reset
fi


EXE=python${PYMAJOR}${PYMINOR}



# check if initial repo
if echo $GITHUB_WORKSPACE|grep -q /python-wasm-plus
then
    echo " * packing testsuite * "
    # in this special case build testsuite frontend
    TMPL_DEFAULT="templates/no-worker"
    APK_DEFAULT="demos/org.python${PYBUILD}.0"
    mkdir -p $APK_DEFAULT
    pushd $APK_DEFAULT
    cp -Ru $SDKROOT/devices/x86_64/usr/lib/python${PYBUILD} ./
    rm -rf ./python${PYBUILD}/lib-dynload/* ./python${PYBUILD}/site-packages/* ./python${PYBUILD}/config-*
    cp -rf ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/* ./python${PYBUILD}/
    cp -vf $SDKROOT/devices/emsdk/usr/lib/python${PYBUILD}/_sysconfigdata* ./python${PYBUILD}/
    cp -vRf $SDKROOT/devices/emsdk/usr/lib/python${PYBUILD}/config-* ./python${PYBUILD}/
    popd
else
    APK_DEFAULT="demos/1-touchpong"
    TMPL_DEFAULT="templates/no-worker"
fi

cp -rf ${SDKROOT}/prebuilt/emsdk/common/* ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/

# web application template
TMPL=${1:-$TMPL_DEFAULT}
shift

# source code + assets of app
APK=${1:-$APK_DEFAULT}
shift

# final app name in build folder
CN=${1:-demo}
shift


TMPL=$(realpath $TMPL)
APK=$(realpath $APK)

# pre populated site-packages
REQUIREMENTS=$(realpath ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/site-packages)
DYNLOAD=$(realpath ${SDKROOT}/prebuilt/emsdk/${PYBUILD}/lib-dynload)

# should already be done, but usefull when testing new modules
if [ -d $SDKROOT/devices/emsdk/usr/lib/python${PYBUILD}/lib-dynload ]
then
    echo "
    * Adding new modules from $ROOT/devices/emsdk/usr/lib/python${PYBUILD}/lib-dynload
"
    mv $SDKROOT/devices/emsdk/usr/lib/python${PYBUILD}/lib-dynload/*.so $DYNLOAD/ 2>/dev/null
fi


# runtime patches on known modules for specific platform
# applies to prebuilt/emsdk/site-packages at preload stage.
PLATFORM=$(realpath support/__EMSCRIPTEN__)

[ -d ${REQUIREMENTS}/pygame ] || cp -R ${ROOT}/src/pygame-wasm/src_py ${REQUIREMENTS}/pygame
cp -Rf ${PLATFORM}.overlay/* ${REQUIREMENTS}/

# crosstools, aio and simulator
CROSS=$(realpath support/cross)



# clean up untested modules
#rm -fr $PREFIX/lib/python${PYBUILD}/site-packages/*
touch $(echo -n $PREFIX/lib/python${PYBUILD}/site-packages)/README.txt


. scripts/emsdk-fetch.sh


ALWAYS_ASSETS=$(realpath tests/assets)
ALWAYS_CODE=$(realpath tests/code)



LOPTS="-sMAIN_MODULE --bind -fno-rtti"

# O0/g3 is much faster to build and easier to debug

echo "  ************************************"
if [ -f dev ]
then
    export COPTS="-O0 -g3 -fPIC"

    echo "       building DEBUG $COPTS"
    LOPTS="$LOPTS -s ASSERTIONS=0"
    # -gsource-map --source-map-base /"
    ALWAYS_FS="--preload-file ${ALWAYS_CODE}@/data/data/org.python/assets"
else
    echo "       building RELEASE $COPTS"
    LOPTS="$LOPTS -s ASSERTIONS=0 -s LZ4=1"
    ALWAYS_FS=""
fi

echo "  ************************************"

ALWAYS_FS="$ALWAYS_FS --preload-file ${ALWAYS_ASSETS}@/data/data/org.python/assets"


# option -sSINGLE_FILE ?


echo "
TMPL=${TMPL}
APK=${APK}
site-packages=${PLATFORM}
crosstoosl=${CROSS}

COPTS=$COPTS
LOPTS=$LOPTS

ALWAYS_ASSETS=$ALWAYS_ASSETS
ALWAYS_CODE=$ALWAYS_CODE

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

    ln support/pythonrc.py build/${CN}/pythonrc.py
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

# apply stdlib patches
/bin/cp -Rfv $PLATFORM.patches/${PYBUILD}/. $ROOT/devices/$(arch)/usr/lib/python${PYBUILD}/
/bin/cp -Rf $PLATFORM.patches/${PYBUILD}/. $ROOT/devices/emsdk/usr/lib/python${PYBUILD}/

# and pack the minimal stdlib for current implicit requirements
# see inside ./scripts/make_coldstartfs.sh to view them
./scripts/make_coldstartfs.sh

pushd build/cpython-wasm 2>&1 >/dev/null

[ -f ${MODE}.js ] && rm ${MODE}.*
[ -f Programs/${MODE}.o ] && rm Programs/${MODE}.o


# SDL2_image turned off : -ltiff

if false
then
    CF_SDL="-s USE_SDL=2 -s USE_SDL_IMAGE=2 -s USE_SDL_TTF=2 -sUSE_LIBJPEG -sUSE_LIBPNG"
    LD_SDL="-lSDL2_gfx -lSDL2_mixer"
else
    CF_SDL="-s USE_SDL=2"
    LD_SDL="-lSDL2_gfx -lSDL2_mixer -lSDL2_image -ljpeg -lpng -lSDL2_ttf -lharfbuzz -lfreetype -lwebp"
fi


#  -sALLOW_MEMORY_GROWTH=1

# gnu99 not c99 for EM_ASM() js calls functions.



emcc -fPIC -D__PYDK__=1 -DNDEBUG $CF_SDL \
 $PY_HARFANG \
 -c -fwrapv -Wall $CPOPTS -std=gnu99 -Werror=implicit-function-declaration -fvisibility=hidden\
 -I$ROOT/src/cpython${PYBUILD}/Include/internal \
 -IObjects -IInclude -IPython -I. \
 -I$ROOT/src/cpython${PYBUILD}/Include -DPy_BUILD_CORE \
 -o Programs/${MODE}.o $ROOT/src/cpython${PYBUILD}/Programs/python.c

#if $CI
#then
#    STDLIBFS="--preload-file  $PYTHONPYCACHEPREFIX/stdlib-coldstart/python3.12@/usr/lib/python3.12"
#else
#    # --preload-file $ROOT/devices/emsdk/usr/lib/python${PYBUILD}@/usr/lib/python${PYBUILD}
#fi

STDLIBFS="--preload-file $PYTHONPYCACHEPREFIX/stdlib-coldstart/python${PYBUILD}@/usr/lib/python${PYBUILD}"

#  --preload-file /usr/share/terminfo/x/xterm@/usr/share/terminfo/x/xterm \


for lib in mpdec expat
do
    cpylib=${SDKROOT}/prebuilt/emsdk/lib${lib}${PYBUILD}.a
    if [ -f $cpylib ]
    then
        CPY_EXTRALIB="$CPY_EXTRALIB $cpylib"
    fi
done

echo CPY_EXTRALIB=$CPY_EXTRALIB

if false
then
    PY_HARFANG="-DPY_HARFANG=1"
    if echo "x$PY_HARFANG"|grep -q PY_HARFANG
    then
        PY_HARFANG="$PY_HARFANG -sUSE_WEBGL2 -sALLOW_MEMORY_GROWTH "
        for lib in \
        $(find ${ROOT}/build/harfgang-wasm/extern| grep lib.*.a$|grep -v stb_vorbis)
        do
            PY_HARFANG="$PY_HARFANG $lib"
        done

         for lib in\
     harfang/foundation/libfoundation.a\
     harfang/platform/libplatform.a\
     harfang/script/libscript.a\
     harfang/engine/libengine.a\
     languages/hg_python/harfang.a
        do
            PY_HARFANG="$PY_HARFANG ${ROOT}/build/harfgang-wasm/$lib"
        done
    fi
else
    PY_HARFANG=""
fi

if false
then
    PY_P3D="-DPY_P3D=1"
else
    PY_P3D=""
fi


time emcc $FINAL_OPTS $LOPTS -std=gnu99 -D__PYDK__=1 -DNDEBUG\
 -s TOTAL_MEMORY=512MB -s ALLOW_TABLE_GROWTH \
 -s USE_BZIP2=1 -s USE_ZLIB=1 $CF_SDL \
 --use-preload-plugins \
 $STDLIBFS \
 $ALWAYS_FS \
 --preload-file ${DYNLOAD}@/usr/lib/python${PYBUILD}/lib-dynload \
 --preload-file ${CROSS}@/data/data/org.python/assets/site-packages \
 --preload-file ${REQUIREMENTS}@/data/data/org.python/assets/site-packages \
 --preload-file $ROOT/support/xterm@/etc/termcap \
 -o ${MODE}.js Programs/${MODE}.o ${ROOT}/prebuilt/emsdk/libpython${PYBUILD}.a \
 $CPY_EXTRALIB \
 $PY_HARFANG \
 $PY_P3D \
 ${ROOT}/prebuilt/emsdk/libpygame${PYBUILD}.a $CFLDPFX $LD_SDL -lsqlite3 -lffi -ldl -lm

popd

[ -f build/${CN}/${EXE}/${MODE}.js ] && rm build/${CN}/${EXE}/${MODE}.*

mkdir -p build/${CN}/${EXE}
mv -vf build/cpython-wasm/${MODE}.* build/${CN}/${EXE}/
mv build/${CN}/${EXE}/*.map build/${CN}/

echo " * packing assets"
pushd $APK 2>&1 >/dev/null
../../scripts/re-pack-apk.sh demo
popd

if $CI
then
    echo " * CI not running server *"
else

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
fi
