##!/bin/bash

# same goal as  "python-wasm/fetch-python.sh"
export REBUILD=true

# get python from git ( actually the only one supporting emsdk without patches)
if [ -d cpython ]
then
    pushd cpython
    # put the tree back to original state so we can pull
    git restore Programs/python.c Modules/readline.c

    git pull|grep -q 'Already up to date' && export REBUILD=false
    popd

else
    git clone https://github.com/python/cpython.git
fi


pushd cpython
# fix the main startup to it gets a minimal kernel for wasm
cat > Programs/python.c <<END
/* Minimal main program -- everything is loaded from the library */

#include "Python.h"

#if __TEST__
#include "../../../../python-main.c"
#include "../../../../python-wasm.c"
#else
int
main(int argc, char **argv)
{

    return Py_BytesMain(argc, argv);
}
#endif
END


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
+            struct timeval timeout = {0, 10000}; /* 0.01 seconds */

             /* [Bug #1552726] Only limit the pause if an input hook has been
                defined.  */
END

popd

echo "
    * fetched cpython source, status is :
        REBUILD=${REBUILD}
"


