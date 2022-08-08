#!/bin/bash
reset
unset PYTHONSTARTUP
ROOT=$(dirname $(realpath $0))

export PYBUILD=${PYBUILD:-3.11}
export PYMAJOR=$(echo -n $PYBUILD|cut -d. -f1)
export PYMINOR=$(echo -n $PYBUILD|cut -d. -f2)

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
unset _PYTHON_SYSCONFIGDATA_NAME

export PYTHONPATH=$(pwd):$ROOT/support/cross:$ROOT/support/sim.links:$PYTHONPATH

export _PYTHON_SYSCONFIGDATA_NAME=$($ROOT/devices/$(arch)/usr/bin/python3 -c 'import sys;print(f"""_sysconfigdata_{sys.abiflags}_{sys.platform}_{getattr(sys.implementation, "_multiarch", "")}""")')
echo "_PYTHON_SYSCONFIGDATA_NAME=$_PYTHON_SYSCONFIGDATA_NAME"

export PYTHONSTARTUP=$ROOT/build/pycache/.pythonrc.py


if false
then
    PYTHONPATH=$ROOT/devices/emsdk/usr/lib/python3.${PYMINOR}:$PYTHONPATH
    PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.${PYMINOR}/site-packages:$PYTHONPATH
    export PYTHONPATH
    echo "======== SYSTEM PYTHON ============="
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib
    /usr/local/bin/python3.${PYMINOR}
    python3.${PYMINOR} -i -u -B

else
    export LD_LIBRARY_PATH=$ROOT/devices/$(arch)/usr/lib
    export PYTHONPATH=$ROOT/devices/$(arch)/usr/lib/python3.${PYMINOR}/lib-dynload:$PYTHONPATH
    $ROOT/devices/$(arch)/usr/bin/python3.${PYMINOR} -i -u -B
fi
stty sane
