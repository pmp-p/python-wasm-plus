#!/bin/bash

. ${CONFIG:-config}

FS=$PYTHONPYCACHEPREFIX/fs

echo "



    * packing minimal stdlib for
        PYTHON=$HPY
        FS=$FS


==================================================================================
" 1>&2



$HPY -v <<END 2>&1 | tee $FS.log  |grep py$ > $FS
from __future__ import annotations
import sys

M1='os, json, builtins, shutil, zipimport, time, trace, traceback, '
M2='asyncio, inspect, _thread, importlib, ctypes, tomllib'
for mod in (M1+M2).split(', '):
    try:
        __import__(mod)
    except:
        pass
try:
    sys.stdout.reconfigure(encoding='utf-16')
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# for dom event subscriptions and js interface
import webbrowser
import platform

# for wget to overload urlretrieve
import urllib.request

# nodezator
from logging.handlers import RotatingFileHandler
from colorsys  import rgb_to_hls, hls_to_rgb
import xml.dom.minidom
from xml.dom import expatbuilder
import pydoc

# rich
import zlib

# pygame_gui
import html.parser
import importlib.readers

#pymunk tests
import unittest, locale

#pymunk4
import imp, platform

#pymunk6
import numbers, random

#pgzero
import hashlib, queue, pkgutil

#numpy
import pathlib

# cffi
import copy

#curses
import curses

#pytmx
import gzip
import zlib
from xml.etree import ElementTree
import distutils.spawn

#pygame_gui
import importlib.resources

if 0:
    import cffi
    from cffi import FFI
    ffi = FFI()
END

grep -v ^# $FS.log | grep -v ^import 1>&2


echo "
==================================================================================


" 1>&2

$HPY -u -B <<END
import sys, os
stdlp=""
with open("$PYTHONPYCACHEPREFIX/stdl.list","w") as tarlist:
    sysconf = "_sysconfigdata__linux_x86_64-linux-gnu.py"
    with open("$FS") as fs:
        for l in fs.readlines():
            #print( l.strip() )
            if l.find('/')<0:
                continue
            _,trail = l.strip().split('/',1)
            stdlp, name = trail.rsplit('usr/lib/',1)

            #print (stdlp, name)
            #if name.find('asyncio/unix_events.py')>0:
            #    continue


            if name.endswith(sysconf):
                name = name.replace(sysconf,"_sysconfigdata__emscripten_wasm32-emscripten.py")

            name = name.replace('asyncio/selector_','asyncio/wasm_')
            print(name, file=tarlist )
        else:
            stdlp = stdlp.replace('$(arch)','emsdk')
            print(stdlp)
            tarcmd=f"tar --directory=/{stdlp}usr/lib --files-from=$PYTHONPYCACHEPREFIX/stdl.list -cf $PYTHONPYCACHEPREFIX/stdl.tar"
            print(tarcmd)
os.system(tarcmd)
END


mkdir -p $PYTHONPYCACHEPREFIX/stdlib-coldstart
#cp -vf devices/emsdk/usr/lib/python3.*/_sysconfigdata* $PYTHONPYCACHEPREFIX/stdlib-coldstart/python3.*/
pushd $PYTHONPYCACHEPREFIX/stdlib-coldstart
tar xvf $PYTHONPYCACHEPREFIX/stdl.tar | wc -l
rm $PYTHONPYCACHEPREFIX/stdl.tar
du -hs $PYTHONPYCACHEPREFIX/stdlib-coldstart/python3.${PYMINOR}
popd

