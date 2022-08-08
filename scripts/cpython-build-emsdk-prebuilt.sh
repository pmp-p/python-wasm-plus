#!/bin/bash

. ${CONFIG:-config}

PIP="$(realpath python3-wasm) -m pip"

echo "
    *   cpython-build-emsdk-prebuilt pip==$PIP   *
" 1>&2


for pkg in installer
do
    if [ -d prebuilt/emsdk/${PYBUILD}/site-packages/$pkg ]
    then
        echo "
            $pkg already set to prebuilt
            "
    else
        $PIP install $pkg
        mv $PREFIX/lib/python${PYBUILD}/site-packages/${pkg} prebuilt/emsdk/${PYBUILD}/site-packages/
        mv $PREFIX/lib/python${PYBUILD}/site-packages/${pkg}-* prebuilt/emsdk/${PYBUILD}/site-packages/
    fi
done
