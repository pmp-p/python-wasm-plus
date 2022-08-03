#!/bin/bash

. ${CONFIG:-config}

echo "
    *__EMSCRIPTEN__*
"


if grep -q PYDK src/cpython${PYBUILD}/Programs/python.c
then
    echo "
        * __EMSCRIPTEN__ support already added
    " 1>&2
else
    pushd src/cpython${PYBUILD}
    if echo $PYBUILD |grep -q 3.12$
    then
        echo 3.12 does not need patching for interactive FD
    else
        [ -f "Parser/pegen_errors.c" ] && patch -p1 <<END
diff --git a/Parser/pegen_errors.c b/Parser/pegen_errors.c
index 489699679633e..78266f712c05c 100644
--- a/Parser/pegen_errors.c
+++ b/Parser/pegen_errors.c
@@ -245,7 +245,7 @@ get_error_line_from_tokenizer_buffers(Parser *p, Py_ssize_t lineno)
      * (multi-line) statement are stored in p->tok->interactive_src_start.
      * If not, we're parsing from a string, which means that the whole source
      * is stored in p->tok->str. */
-    assert((p->tok->fp == NULL && p->tok->str != NULL) || p->tok->fp == stdin);
+    assert((p->tok->fp == NULL && p->tok->str != NULL) || p->tok->fp != NULL);

     char *cur_line = p->tok->fp_interactive ? p->tok->interactive_src_start : p->tok->str;
     if (cur_line == NULL) {
END
    fi

    # fix the main startup to it gets a minimal kernel for wasm
    cat > Programs/python.c <<END
/* Minimal main program -- everything is loaded from the library */

#include "Python.h"

#if __PYDK__
#include "pycore_call.h"          // _PyObject_CallNoArgs()
#include "pycore_initconfig.h"    // _PyArgv
#include "pycore_interp.h"        // _PyInterpreterState.sysdict
#include "pycore_pathconfig.h"    // _PyPathConfig_ComputeSysPath0()
#include "pycore_pylifecycle.h"   // _Py_PreInitializeFromPyArgv()
#include "pycore_pystate.h"       // _PyInterpreterState_GET()

static PyStatus
pymain_init(const _PyArgv *args)
{
    PyStatus status;

    status = _PyRuntime_Initialize();
    if (_PyStatus_EXCEPTION(status)) {
        return status;
    }

    PyPreConfig preconfig;
    PyPreConfig_InitPythonConfig(&preconfig);

    status = _Py_PreInitializeFromPyArgv(&preconfig, args);
    if (_PyStatus_EXCEPTION(status)) {
        return status;
    }

    PyConfig config;
    PyConfig_InitPythonConfig(&config);

    if (args->use_bytes_argv) {
        status = PyConfig_SetBytesArgv(&config, args->argc, args->bytes_argv);
    }
    else {
        status = PyConfig_SetArgv(&config, args->argc, args->wchar_argv);
    }
    if (_PyStatus_EXCEPTION(status)) {
        goto done;
    }

    status = Py_InitializeFromConfig(&config);
    if (_PyStatus_EXCEPTION(status)) {
        goto done;
    }
    status = _PyStatus_OK();

done:
    PyConfig_Clear(&config);
    return status;
}

static void
pymain_free(void)
{
    _PyImport_Fini2();
    _PyPathConfig_ClearGlobal();
    _Py_ClearStandardStreamEncoding();
    _Py_ClearArgcArgv();
    _PyRuntime_Finalize();
}

#include "${ROOT}/support/__EMSCRIPTEN__.c"
#else
int
main(int argc, char **argv)
{

    return Py_BytesMain(argc, argv);
}
#endif //#if __PYDK__
END

    popd
fi
