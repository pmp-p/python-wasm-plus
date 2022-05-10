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
cat $ROOT/support/cross/aio/simulator.py | envsubst > $ROOT/build/pycache/.pythonrc.py

unset PYTHONHOME

export PYTHONSTARTUP=$ROOT/build/pycache/.pythonrc.py
export PYTHONPATH=$(pwd):$ROOT/support/cross:$ROOT/support/sim.links:$PYTHONPATH


if false
then
    PYTHONPATH=$ROOT/devices/emsdk/usr/lib/python3.11:$PYTHONPATH
    PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.11/site-packages:$PYTHONPATH
    export PYTHONPATH
    echo "======== SYSTEM PYTHON ============="
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib
    /usr/local/bin/python3.11
    python3.11 -i -u -B

else
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib
    export PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.11/lib-dynload:$PYTHONPATH
    $ROOT/devices/$(arch)/usr/bin/python3.11 -i -u -B
fi
stty sane
