#!pythonrc.py
import os, sys, json, builtins

PyConfig = json.loads(PyConfig)
sys.executable = PyConfig["sys"]["executable"]

try:
    pdb
except:
    pdb = print

import shutil

preloadedWasm = "so"
preloadedImages = "png jpeg jpg gif"
preloadedAudios = "wav ogg mp4"

def preload(p=None):
    global preload, prelist
    ROOTDIR = p or f"/data/data/{sys.argv[0]}"
    if  os.path.isdir(ROOTDIR):
        os.chdir(ROOTDIR)
    else:
        pdb(f"cannot chdir to {ROOTDIR=}")
        return

    ROOTDIR = os.getcwd()
    LSRC = len(ROOTDIR) + 1
    counter = 0
    prelist = {}

    def explore(pushpopd, newpath):
        nonlocal counter
        if newpath.endswith(".git"):
            return

        for dirname, dirnames, filenames in os.walk(newpath):
            try:
                os.chdir(dirname)
                print(f"\nNow in {os.getcwd()[LSRC:] or '.'}")

            except:
                print("Invalid Folder :", pushpopd, newpath)

            for f in filenames:
                if not os.path.isfile(f):
                    continue

                ext = f.rsplit(".", 1)[-1].lower()

                if ext not in f"{preloadedImages} {preloadedAudios} {preloadedWasm}":
                    continue

                src = os.path.join(os.getcwd(), f)
                dst = "/tmp/pre" + str(counter).zfill(4) + "." + ext
                shutil.copyfile(src, dst)
                prelist[src] = dst
                embed.preload(dst)
                counter += 1

            for subdir in dirnames:
                explore(os.getcwd(), subdir)

        os.chdir(pushpopd)

    explore(ROOTDIR, "assets")
    os.chdir(f"{ROOTDIR}/assets")
    sys.path.insert(0, os.getcwd())
    return True

if preload():

    def fix_preload_table():
        global prelist
        for (
            src,
            dst,
        ) in prelist.items():
            ext = dst.rsplit(".", 1)[-1]
            if ext in preloadedImages:
                ptype = "preloadedImages"
            elif ext in preloadedAudios:
                ptype = "preloadedAudios"
            elif ext == "so":
                ptype = "preloadedWasm"

            src = f"{ptype}[{repr(src)}]"
            dst = f"{ptype}[{repr(dst)}]"
            swap = f"({src}={dst}) && delete {dst}"
            embed.js(swap, -1)
            #print(swap)

        if os.path.isfile("main.py"):
            aio.defer( execfile, ["main.py"] )
            print(f"running {sys.argv[0]}.py as main")

    # TODO: call that from C after last callback reached instead.
    aio.defer(fix_preload_table, deadline=60)
else:
    def fix_preload_table():
        pdb("no assets preloaded")

    import pygame
    import pygame as pg

