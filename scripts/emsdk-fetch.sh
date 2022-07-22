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
        # emsdk could have been deleted for full rebuild
        rm embuild.done

        if git clone https://github.com/emscripten-core/emsdk.git
        then
            pushd emsdk
            ./emsdk install ${EMFLAVOUR}
            ./emsdk activate ${EMFLAVOUR}
            popd
            [ -f dev ] && tar -cpR emsdk > emsdk.tar
        fi
    fi

    if [ -f emsdk/emsdk_env.sh ]
    then
        echo "
        * activating emsdk via emsdk_env.sh
"
        . emsdk/emsdk_env.sh 2>&1 > /dev/null
        # EMSDK_PYTHON may be cleared, restore it
        export EMSDK_PYTHON=$SYS_PYTHON
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
        # sdl2_image is too old
        ALL="libembind libgl libal libhtml5 libstubs libnoexit libsockets"
        ALL="$ALL libc libdlmalloc libcompiler_rt libc++-noexcept libc++abi-noexcept"
        ALL="$ALL struct_info libfetch zlib bzip2"
        ALL="$ALL libpng libjpeg freetype harfbuzz"
        ALL="$ALL sdl2 sdl2_mixer sdl2_gfx sdl2_ttf"
        ALL="$ALL libsqlite3"

        echo "
        * building third parties libraries for emsdk ( can take time ... )
    "

        for one in $ALL
        do
            echo "
            + $done
    "
            embuilder --pic build $one
            #embuilder build $one
        done

        if $CI
        then
            echo "

        ==========================================================
                            stripping emsdk
        ==========================================================
"
            rm -rf ${SDKDIR}/emsdk/upstream/emscripten/cache/ports*
            # something triggers sdl2 *full* rebuild in pygame.
            # but only that one.
            embuilder --pic build sdl2
            embuilder build sdl2
            rm -rf ${SDKDIR}/emsdk/upstream/emscripten/cache/ports/sdl2/SDL-*
            rm -rf ${SDKDIR}/emsdk/upstream/emscripten/cache/ports
            rm -rf ${SDKDIR}/emsdk/upstream/emscripten/cache/ports-builds
            rm -rf ${SDKDIR}/emsdk/upstream/emscripten/tests
        fi

#

        cat > emsdk/upstream/emscripten/emcc <<END
#!/bin/bash

unset _PYTHON_SYSCONFIGDATA_NAME
unset PYTHONHOME
unset PYTHONPATH

COMMON="-Wno-limited-postlink-optimizations"
SHARED=""
IS_SHARED=false

for arg do
    shift

    # that is for some very bad setup.py behaviour regarding cross compiling. should not be needed ..
    [ "\$arg" = "-I/usr/include" ] && continue
    [ "\$arg" = "-I/usr/include/SDL2" ] && continue
    [ "\$arg" = "-L/usr/lib64" ]	&& continue
    [ "\$arg" = "-L/usr/lib" ]   && continue

    if [ "\$arg" = "-shared" ]
    then
        IS_SHARED=true
        SHARED="\$SHARED -sSIDE_MODULE"
    fi

    if \$IS_SHARED
    then
        true
    else
        if echo "\$arg"|grep -q wasm32-emscripten.so\$
        then
            IS_SHARED=true
            SHARED="\$SHARED -shared -sSIDE_MODULE"
        fi
    fi

    set -- "\$@" "\$arg"
done

if \$IS_SHARED
then
    $EMSDK_PYTHON -E \$0.py \$SHARED $LDFLAGS "\$@" \$COMMON
else
    $EMSDK_PYTHON -E \$0.py \$CPPFLAGS "\$@" \$COMMON
fi
END
        cat emsdk/upstream/emscripten/emcc > emsdk/upstream/emscripten/em++

        cat > emsdk/upstream/emscripten/emar <<END
#!/bin/bash

unset _PYTHON_SYSCONFIGDATA_NAME
unset PYTHONHOME
unset PYTHONPATH

$EMSDK_PYTHON -E \$0.py "\$@"
END

        cat emsdk/upstream/emscripten/emar > emsdk/upstream/emscripten/emcmake

        cat > emsdk/upstream/emscripten/emconfigure <<END
#!/bin/bash
$EMSDK_PYTHON -E \$0.py "\$@"
END

        chmod +x emsdk/upstream/emscripten/em*
        touch embuild.done
        sync
    fi

    export PKG_CONFIG_PATH="${PREFIX}/lib/pkgconfig"

    if echo $PATH|grep -q $EMSDK/upstream/emscripten/system/bin
    then
        # emsdk env does not set it, but it's required for eg sdl2-config
        echo -n
    else
        export PATH=$EMSDK/upstream/emscripten/system/bin:$EMSDK/upstream/emscripten:$PATH
    fi

fi
