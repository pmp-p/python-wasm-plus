
. ${CONFIG:-config}

if [[ ! -z ${EMSDK+z} ]]
then
    echo -n
else
    . scripts/emsdk-fetch.sh
fi

echo "
    * emsdk ready in $EMSDK
"

cat > $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh <<END
#!/bin/bash
export PATH=$HOST/bin:$PATH
export PKG_CONFIG_PATH=${PKG_CONFIG_PATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}
export HOME=${PYTHONPYCACHEPREFIX}
export PLATFORM_TRIPLET=${PYDK_PYTHON_HOST_PLATFORM}
export PREFIX=$PREFIX

export PYTHONSTARTUP="${ROOT}/support/__EMSCRIPTEN__.py"
> ${PYTHONPYCACHEPREFIX}/.pythonrc.py

export PS1="[PyDK:wasm] \w $ "

export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata__emscripten_

if [[ ! -z \${EMSDK+z} ]]
then
    # emsdk_env already parsed
    echo -n
else
    pushd $ROOT
    . scripts/emsdk-fetch.sh
    popd
fi
END

cat > $HOST/bin/python3-wasm <<END
#!/bin/bash
. $ROOT/${PYDK_PYTHON_HOST_PLATFORM}-shell.sh

# to fix non interactive startup
#touch $HOST/__main__.py

cat >${PYTHONPYCACHEPREFIX}/.numpy-site.cfg <<NUMPY
[DEFAULT]
library_dirs = $PREFIX//lib
include_dirs = $PREFIX/include
NUMPY

# so include dirs are good
export PYTHONHOME=$PREFIX

# but still can load dynload and setuptools
export PYTHONPATH=$(echo -n $HOST/lib/python3.??/lib-dynload):$(echo -n $HOST/lib/python3.??/site-packages)

#probably useless
export _PYTHON_HOST_PLATFORM=${PYDK_PYTHON_HOST_PLATFORM}
export PYTHON_FOR_BUILD=${PYTHON_FOR_BUILD}

$HOST/bin/python3 -u -B \$@
END

chmod +x $HOST/bin/python3-wasm


if [ -d src/pygame-wasm ]
then
    echo "
    * pygame already fetched
"
else
    pushd src
    git clone -b pygame-wasm https://github.com/pmp-p/pygame-wasm pygame-wasm
    popd
fi

pushd src/pygame-wasm

# -s USE_FREETYPE=1 -s USE_SDL=2

if CC=emcc python3-wasm setup.py -config -auto -sdl2
then
    if CFLAGS="-DBUILD_STATIC=1 -DSDL_NO_COMPAT=1 -ferror-limit=1" CC=emcc EMCC_CFLAGS="" python3-wasm setup.py build
    then
        OBJS=$(find build/temp.wasm32-tot-emscripten-3.??/|grep o$)
        llvm-ar rcs ${ROOT}/prebuilt/libpygame.a $OBJS
        for obj in $OBJS
        do
            echo $obj
        done
    fi
fi
popd



