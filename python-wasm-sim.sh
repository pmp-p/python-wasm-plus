#!/bin/bash
reset
unset PYTHONSTARTUP
ROOT=$(dirname $(realpath $0))

export PLATFORM=$ROOT/support/sim.links

mkdir -p $PLATFORM
echo "

        Put platform (host) modules or symlink to platform independant ones there :
            $PLATFORM

"


export PYTHONRC=$ROOT/support/pythonrc.py

export __FILE__="$1"
#export PATH=$ROOT/devices/$(arch)/usr/bin:$PATH
cat $ROOT/support/cross/aio/simulator.py | envsubst > $ROOT/build/pycache/pythonrc.py

unset PYTHONHOME

export PYTHONSTARTUP=$ROOT/build/pycache/pythonrc.py
export PYTHONPATH=$(pwd):$ROOT/support/cross:$ROOT/support/sim.links:$PYTHONPATH


#LD_PRELOAD=/data/git/python-wasm-plus/src/libffi/x86_64-pc-linux-gnu/.libs/libffi.so.8

if false
then
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib:/data/git/python-wasm-plus/src/libffi/x86_64-pc-linux-gnu/.libs
    export PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.11/lib-dynload:$PYTHONPATH

    ldd $ROOT/devices/$(arch)/usr/bin/python3.11
    ldd /data/git/python-wasm-plus/devices/x86_64/usr/lib/python3.11/lib-dynload/_ctypes.cpython-311-x86_64-linux-gnu.so
    $ROOT/devices/$(arch)/usr/bin/python3.11 -i -u -B
else
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib
        ldd /usr/local/bin/python3.11
    python3.11 -i -u -B
fi
