#!/bin/bash

if [[ -z ${EMSDK+z} ]]
then

    . ${CONFIG:-config}

    if [ -d emsdk ]
    then
        echo "
        * using emsdk from $(realpath emsdk)
            with sys python $SYS_PYTHON
" 1>&2
    else
        # emsdk could have been deleted for full rebuild
        rm embuild.done

        if git clone --no-tags --depth 1 --single-branch --branch main https://github.com/emscripten-core/emsdk.git
        then
            pushd emsdk
            ./emsdk install ${EMFLAVOUR:-latest}
            ./emsdk activate ${EMFLAVOUR:-latest}
            popd
        fi
    fi

    export EMSDK_PYTHON=$SYS_PYTHON

    if [ -f ${SDKROOT}/emsdk/emsdk_env.sh ]
    then
        echo "
        * activating emsdk via emsdk_env.sh with EMSDK_PYTHON=$EMSDK_PYTHON
" 1>&2
        . ${SDKROOT}/emsdk/emsdk_env.sh
        # EMSDK_PYTHON may be cleared, restore it

    else
        echo "
        ERROR cannot find emsdk/emsdk_env.sh in $(pwd)
" 1>&2
        exit 41
    fi

    export EMSDK_PYTHON=$SYS_PYTHON

    if [ -f embuild.done ]
    then
        echo "
        * emsdk prereq ok
    "  1>&2
    else
        # sdl2_image is too old
        ALL="libembind libgl libal libhtml5 libstubs libnoexit libsockets"
        ALL="$ALL libc libdlmalloc libcompiler_rt libc++-noexcept libc++abi-noexcept"
        ALL="$ALL struct_info libfetch zlib bzip2"
        ALL="$ALL libpng libjpeg freetype harfbuzz"
        ALL="$ALL sdl2 sdl2_mixer sdl2_gfx sdl2_ttf"
        ALL="$ALL sqlite3"

        echo "
        * building third parties libraries for emsdk ( can take time ... )
    "  1>&2

        for one in $ALL
        do
            echo "
            + $done
    "  1>&2
            embuilder --pic build $one
            embuilder build $one
        done

        cat > emsdk/upstream/emscripten/emcc <<END
#!/bin/bash

if [ -z "\$_EMCC_CCACHE" ]
then

unset _PYTHON_SYSCONFIGDATA_NAME
unset PYTHONHOME
unset PYTHONPATH

# -Wwarn-absolute-paths
# --valid-abspath ${SDKROOT}

COMMON="-Wno-limited-postlink-optimizations"
SHARED=""
IS_SHARED=false

for arg do
    shift

    if [ "\$arg" = "-v" ]
    then
        \$EMSDK_PYTHON -E \$0.py -v
        exit 0
    fi

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
else
  unset _EMCC_CCACHE
  exec ccache "\$0" "\$@"
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

    TRUE=$(which true)
    for fix in readelf ldconfig
    do
        FIXED=$EMSDK/upstream/emscripten/system/bin/$fix
        [ -f $FIXED ] || cp $TRUE $FIXED
    done


    if [ -f /lowend ]
    then
        # yes, i only have a amd200GE with 32G
        NPROC=1
        export EMSDK_NUM_CORES=1
    else
        NPROC=$(nproc)
    fi

    mkdir -p src
    export PKG_CONFIG_PATH="${SDKROOT}/emsdk/upstream/emscripten/system/lib/pkgconfig:${HOST_PREFIX}/lib/pkgconfig"

    export CPPFLAGS="-I$PREFIX/include"
    export LDFLAGS="-msoft-float -L$PREFIX/lib"

    # module build opts
    export CFLDPFX="$CPPFLAGS $LDFLAGS -Wno-unused-command-line-argument"
    export PYDK=minimal

    if command -v ccache 2>&1 >/dev/null; then
        export EM_COMPILER_WRAPPER=ccache
        export _EMCC_CCACHE=1
    fi

    export EMCC_SKIP_SANITY_CHECK=1
    export EM_IGNORE_SANITY=1

else

    echo "emsdk: config already set !" 1>&2
fi


