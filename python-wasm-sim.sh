#!/bin/bash
reset
ROOT=$(dirname $(realpath $0))

export PLATFORM=$ROOT/support/sim.links

mkdir -p $PLATFORM
echo "

        Put platform (host) modules or symlink to platform independant ones there :
            $PLATFORM

"

export PYTHONSTARTUP=$ROOT/build/pycache/pythonrc.py
export PYTHONRC=$ROOT/support/pythonrc.py

export __FILE__="$1"
#export PATH=$ROOT/devices/$(arch)/usr/bin:$PATH
cat $ROOT/support/cross/aio/simulator.py | envsubst > $PYTHONSTARTUP

unset PYTHONHOME

PYTHONPATH=$(pwd):$ROOT/support/cross:$ROOT/support/sim.links:
export PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.11/lib-dynload:$PYTHONPATH

export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib

$ROOT/devices/$(arch)/usr/bin/python3.11 -i -u -B

