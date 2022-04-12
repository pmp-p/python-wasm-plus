#!/bin/bash

. ${CONFIG:-config}

echo PYTHON=$HPY
echo LD_LIBRARY_PATH=./devices/x86_64/usr/lib =$LD_LIBRARY_PATH

ROOT=$(pwd)

FS=$PYTHONPYCACHEPREFIX/fs

$HPY -v <<END 2>&1 |grep py$ > $FS
import sys, os, json, builtins, shutil, zipimport, tomllib, time
import trace, traceback, asyncio, inspect, _thread
sys.stdout.reconfigure(encoding='utf-16')
END

echo "=============================="
$HPY -u -B <<END
import sys, os
stdlp=""
with open("$PYTHONPYCACHEPREFIX/stdl.list","w") as tarlist:
    with open("$FS") as fs:
        for l in fs.readlines():
            #print( l.strip() )
            _,trail = l.strip().split('/',1)
            stdlp, name = trail.rsplit('usr/lib/',1)
            #print (stdlp, name)
            #if name.find('asyncio/unix_events.py')>0:
            #    continue
            name = name.replace('asyncio/selector_','asyncio/wasm_')
            print(name, file=tarlist )
        else:
            stdlp = stdlp.replace('$(arch)','emsdk')
            print(stdlp)
            tarcmd=f"tar --directory=/{stdlp}usr/lib --files-from=$PYTHONPYCACHEPREFIX/stdl.list -cf $PYTHONPYCACHEPREFIX/stdl.tar"
            print(tarcmd)
os.system(tarcmd)
END


echo "=============================="
mkdir -p $PYTHONPYCACHEPREFIX/stdlib-coldstart
pushd $PYTHONPYCACHEPREFIX/stdlib-coldstart
tar xvf $PYTHONPYCACHEPREFIX/stdl.tar | wc -l
rm $PYTHONPYCACHEPREFIX/stdl.tar
du -hs $PYTHONPYCACHEPREFIX/stdlib-coldstart/python3.11
popd



