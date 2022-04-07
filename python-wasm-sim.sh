#!/bin/bash
pwd
ROOT=/data/git/python-wasm-plus
export PYTHONPATH=$(pwd):$ROOT/support/sim.links
#$ROOT/devices/$(arch)/usr/lib/python3.11/lib-dynload:$PYTHONPATH
export PYTHONSTARTUP=$ROOT/build/pycache/pythonrc.py

export PLATFORM=$ROOT/support/sim
export PYTHONRC=$ROOT/support/pythonrc.py

export __FILE__="$1"
#export PATH=$ROOT/devices/$(arch)/usr/bin:$PATH
cat $ROOT/support/sim/ulator.py | envsubst > $PYTHONSTARTUP

unset PYTHONHOME

export PYTHONPATH=$ROOT/support/sim.links:$ROOT/devices/$(arch)/usr/lib/python3.11/lib-dynload
export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib

$ROOT/devices/$(arch)/usr/bin/python3.11 -i -u -B

