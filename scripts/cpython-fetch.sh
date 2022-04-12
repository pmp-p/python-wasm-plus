##!/bin/bash

. ${CONFIG:-config}

# same goal as  "python-wasm/fetch-python.sh"
# get python from git ( actually the only one supporting emsdk without patches)

pushd src

if [ -d cpython ]
then
    pushd cpython
    # put the tree back to original state so we can pull
    # Programs/python.c Modules/readline.c
    git restore .

    if git pull|grep -q 'Already up to date'
    then
        export REBUILD=${REBUILD:-false}
    else
        export REBUILD=true
    fi
    #not here or pip won't install properly anymore its wheels
    #cat $ROOT/support/compilenone.py > ./Lib/compileall.py
    popd
else
    git clone https://github.com/python/cpython.git
fi

popd

# last bc modif 98ff4a68773c49619d486c7e758ebbe1662f8387

# do some patching


pushd src/cpython

# fix the readline loop so host simulator can run 60FPS
patch -p1 <<END
--- cpython/Modules/readline.c	2022-03-10 09:17:57.598757042 +0100
+++ cpython.wasm/Modules/readline.c	2022-01-21 04:44:22.000000000 +0100
@@ -1326,7 +1326,9 @@
         int has_input = 0, err = 0;

         while (!has_input)
-        {               struct timeval timeout = {0, 100000}; /* 0.1 seconds */
+        {
+
+            struct timeval timeout = {0, 5000}; /* 0.005 seconds */

             /* [Bug #1552726] Only limit the pause if an input hook has been
                defined.  */
END


popd

echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"

