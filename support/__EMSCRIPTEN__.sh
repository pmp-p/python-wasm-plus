
if grep -q PYDK src/cpython/Programs/python.c
then
    echo __EMSCRIPTEN__ support already added
else
    pushd src/cpython
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
fi
