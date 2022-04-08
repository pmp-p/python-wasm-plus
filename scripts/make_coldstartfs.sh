#!/bin/bash

. ${CONFIG:-config}

echo PYTHON=$PYTHON
echo LD_LIBRARY_PATH=./devices/x86_64/usr/lib =$LD_LIBRARY_PATH

ROOT=$(pwd)

FS=$PYTHONPYCACHEPREFIX/fs

$PYTHON -v <<END 2>&1 |grep py$ > $FS
import sys, os, json, builtins, shutil, zipimport, tomllib, time
END

echo "=============================="
$PYTHON <<END
import sys, os
stdlp=""
with open("$PYTHONPYCACHEPREFIX/stdl.list","w") as tarlist:
    with open("$FS") as fs:
        for l in fs.readlines():
            #print( l.strip() )
            _,trail = l.strip().split('/',1)
            stdlp, name = trail.rsplit('usr/lib/',1)
            print (stdlp, name)
            print(name, file=tarlist )
        else:
            print(stdlp)
            print(f"tar --directory=/{stdlp}usr/lib --files-from=$PYTHONPYCACHEPREFIX/stdl.list -cvf $PYTHONPYCACHEPREFIX/stdl.tar")
END

echo "=============================="
mkdir -p $PYTHONPYCACHEPREFIX/stdlib-coldstart
pushd $PYTHONPYCACHEPREFIX/stdlib-coldstart
tar xvf $PYTHONPYCACHEPREFIX/stdl.tar && rm $PYTHONPYCACHEPREFIX/stdl.tar
popd



