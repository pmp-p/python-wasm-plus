/*
// from python-main.c
static PyStatus pymain_init(const _PyArgv *args);
static void pymain_free(void);


TODO:
    virtual kbd
        https://github.com/emscripten-ports/SDL2/issues/80
        https://www.beuc.net/tmp/ti1.html

    display:
        osmesa / tinygl / tinygles / angle
        sixel and/or https://nick-black.com/dankwiki/index.php/Notcurses

    audio:
        https://developers.google.com/web/updates/2017/12/audio-worklet
        https://github.com/mackron/miniaudio

    net:
        https://hacks.mozilla.org/2017/06/introducing-humblenet-a-cross-platform-networking-library-that-works-in-the-browser/
        https://github.com/HumbleNet/HumbleNet
        https://github.com/dmotz/trystero
        https://github.com/aiortc/aiortc

    webusb:
        https://mpy-usb.zoic.org/

    advanced lexeme text compression stored via unicode PUA:
        https://www.wikidata.org/wiki/Q18514

    asyncify:
        https://web.dev/asyncify/
        IO in a webworker without asyncio?
            https://github.com/pyodide/pyodide/issues/1219

        https://github.com/pyodide/pyodide/issues/1503
    vs:
        https://github.com/joemarshall/unthrow

    fpcast:
        https://github.com/pyodide/pyodide/pull/2019

    webos:
        https://github.com/shmuelhizmi/web-desktop-environment
        https://qooxdoo.org/qxl.demobrowser/#widget~Desktop.html

    tools:
        https://greggman.github.io/html5-gamepad-test/

bookmarks:
    https://github.com/sunfishcode/wasm-reference-manual/blob/master/WebAssembly.md

*/

#if __EMSCRIPTEN__
    #include <emscripten/html5.h>
    #include <emscripten/key_codes.h>
    #include "emscripten.h"
    #include <SDL2/SDL.h>
    #include <SDL2/SDL_ttf.h>
//    #include <SDL_hints.h> // SDL_HINT_EMSCRIPTEN_KEYBOARD_ELEMENT
    #define SDL_HINT_EMSCRIPTEN_KEYBOARD_ELEMENT   "SDL_EMSCRIPTEN_KEYBOARD_ELEMENT"

    #define HOST_RETURN(value)  return value

#else
    #error "wasi unsupported yet"
#endif



PyMODINIT_FUNC PyInit_base(void);
PyMODINIT_FUNC PyInit_color(void);
PyMODINIT_FUNC PyInit_constants(void);
PyMODINIT_FUNC PyInit_version(void);
PyMODINIT_FUNC PyInit_rect(void);
PyMODINIT_FUNC PyInit_surflock(void);
PyMODINIT_FUNC PyInit_rwobject(void);
PyMODINIT_FUNC PyInit_bufferproxy(void);

PyMODINIT_FUNC PyInit_surface(void);
PyMODINIT_FUNC PyInit_display(void);
PyMODINIT_FUNC PyInit__freetype(void);
PyMODINIT_FUNC PyInit_font(void);

PyMODINIT_FUNC PyInit_draw(void);
PyMODINIT_FUNC PyInit_mouse(void);
PyMODINIT_FUNC PyInit_key(void);
PyMODINIT_FUNC PyInit_event(void);
PyMODINIT_FUNC PyInit_joystick(void);
PyMODINIT_FUNC PyInit_image(void);

PyMODINIT_FUNC PyInit_mixer_music(void);
PyMODINIT_FUNC PyInit_pg_mixer(void);

PyMODINIT_FUNC PyInit_pg_math(void);
PyMODINIT_FUNC PyInit_pg_time(void);


PyMODINIT_FUNC PyInit_sdl2(void);
PyMODINIT_FUNC PyInit_mixer(void);
PyMODINIT_FUNC PyInit_controller(void);

//PyMODINIT_FUNC PyInit_audio(void);
//PyMODINIT_FUNC PyInit_video(void);

#define __PyImport_AppendInittab__ {\
    PyImport_AppendInittab("embed", init_embed);\
    PyImport_AppendInittab("pygame_base", PyInit_base);\
    PyImport_AppendInittab("pygame_color", PyInit_color);\
    PyImport_AppendInittab("pygame_constants", PyInit_constants);\
    PyImport_AppendInittab("pygame_rect", PyInit_rect);\
    PyImport_AppendInittab("pygame_surflock", PyInit_surflock);\
    PyImport_AppendInittab("pygame_rwobject", PyInit_rwobject);\
    PyImport_AppendInittab("pygame_bufferproxy", PyInit_bufferproxy);\
    PyImport_AppendInittab("pygame_math", PyInit_pg_math);\
    PyImport_AppendInittab("pygame_surface", PyInit_surface);\
    PyImport_AppendInittab("pygame_display", PyInit_display);\
    PyImport_AppendInittab("pygame__freetype", PyInit__freetype);\
    PyImport_AppendInittab("pygame_font", PyInit_font);\
    PyImport_AppendInittab("pygame_draw", PyInit_draw);\
    PyImport_AppendInittab("pygame_image", PyInit_image);\
    PyImport_AppendInittab("pygame_mixer_music", PyInit_mixer_music);\
    PyImport_AppendInittab("pygame_mixer", PyInit_pg_mixer);\
    PyImport_AppendInittab("pygame_mouse", PyInit_mouse);\
    PyImport_AppendInittab("pygame_key", PyInit_key);\
    PyImport_AppendInittab("pygame_event", PyInit_event);\
    PyImport_AppendInittab("pygame_joystick", PyInit_joystick);\
    PyImport_AppendInittab("pygame_time", PyInit_pg_time);\
    PyImport_AppendInittab("pygame__sdl2_sdl2", PyInit_sdl2);\
    PyImport_AppendInittab("pygame__sdl2_sdl2_mixer", PyInit_mixer);\
    PyImport_AppendInittab("pygame__sdl2_controller", PyInit_controller);\
}


/*    PyImport_AppendInittab("pygame__sdl2_audio", PyInit_audio);*/\
/*    PyImport_AppendInittab("pygame__sdl2_video", PyInit_video);*/\





static PyObject *
embed_test(PyObject *self, PyObject *args, PyObject *kwds) //, PyObject *buff)
{
    SDL_version v;

    SDL_GetVersion(&v);
    TTF_Init();
    return Py_BuildValue("iii", v.major, v.minor, v.patch);

}


static PyMethodDef mod_embed_methods[] = {
    //{"get_sdl_version", embed_get_sdl_version, METH_VARARGS, "get_sdl_version"},
    {"test", (PyCFunction)embed_test, METH_VARARGS | METH_KEYWORDS, "test"},
    // {"get_sdl_version", embed_get_sdl_version, METH_NOARGS, "get_sdl_version"}, + (PyObject *self, PyObject *args, PyObject *kwds) == FAIL
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef mod_embed = {
    PyModuleDef_HEAD_INIT,
    "embed",
    NULL,
    -1,
    mod_embed_methods
};

static PyObject *embed_dict;

PyMODINIT_FUNC init_embed(void) {

    PyObject *embed_mod = PyModule_Create(&mod_embed);
    embed_dict = PyModule_GetDict(embed_mod);
    PyDict_SetItemString(embed_dict, "js2py", PyUnicode_FromString("{}"));
    return embed_mod;
}




struct timeval time_last, time_current, time_lapse;

// "files"

#define FD_MAX 64
#define FD_BUFFER_MAX 2048


FILE *io_fd[FD_MAX];
char *io_shm[FD_MAX];
int io_stdin_filenum;
int wa_panic = 0;

#define LOG_V puts
#define wa_break { wa_panic=1;goto panic; }



em_callback_func
main_iteration(void) {
    static int i = 0;

    if (!wa_panic) {

        // first pass coming back from js, if anything js was planned from main() it should be done now.
        if (!i++) {
            // repl banner
            PyRun_SimpleString(
                "print('CPython',sys.version, '\\n>>>', chr(4), file=sys.stderr);"
                "sys.stdout.flush();sys.stderr.flush();"
            );
        } else {
            // run a frame.
            PyRun_SimpleString("aio.step()");
        }

// REPL + PyRun_SimpleString asked from wasm vm host .

        gettimeofday(&time_current, NULL);
        timersub(&time_current, &time_last, &time_lapse);

//TODO put a user-def value to get slow func
        if (time_lapse.tv_usec>1) {

            gettimeofday(&time_last, NULL);

#define stdin_cstr io_shm[io_stdin_filenum]

            if ( stdin_cstr[0] ) {

#define file io_fd[0]

                if ( stdin_cstr[0] == '#' ) {
                    // special message display it on console
                    puts(stdin_cstr);
                }
                fprintf( file ,"%s", stdin_cstr );

                if ( !fseek(file, 0L, SEEK_END) ) {
                    if ( ftell(file) ) {
                        rewind(file);
                    }
                }

                int line = 0;
                char buf[FD_BUFFER_MAX];

                while( fgets(&buf[0], FD_BUFFER_MAX, file) ) {
                    line++;
                    //fprintf( stderr, "%d: %s", line, buf );
                }

                rewind(file);


                if (line>1) {
                    line=0;
                    while( fgets(&buf[0], FD_BUFFER_MAX, file) ) {
                        line++;
                        fprintf( stderr, "%d: %s", line, buf );
                    }
                    rewind(file);
                    PyRun_SimpleFile( file, "<stdin>");
                } else {
                    line = 0;
                    while( !PyRun_InteractiveOne( file, "<stdin>") ) line++;
                }

                if (line) {
                    fprintf( stderr, ">>> ");
                    PyRun_SimpleString(
                        "print(chr(4),file=sys.__stdout__);"
                        "print(chr(4),file=sys.__stderr__);"
                        "sys.__stdout__.flush();"
                        "sys.__stderr__.flush()\n"
                    );
                }

                // reset stdin
                stdin_cstr[0] = 0;
                rewind(file);
                // ? no op ?
                ftruncate(io_stdin_filenum, 0);
#undef file
#undef stdin_cstr
            }

//            if (i>20)
  //              wa_break;
        }
    } else {

//panic:
        pymain_free();
        emscripten_cancel_main_loop();
        puts(" ---------- done ----------");
    }
    HOST_RETURN(0);
}

PyStatus status;



EM_BOOL
on_keyboard_event(int type, const EmscriptenKeyboardEvent *event, void *user_data) {
    puts("canvas keyboard event");
    return false;
}

   SDL_Window *window;
    SDL_Renderer *renderer;

int
main(int argc, char **argv)
{
    gettimeofday(&time_last, NULL);
    //LOG_V("---------- SDL2 on #canvas + pygame ---------");

    _PyArgv args = {
        .argc = argc,
        .use_bytes_argv = 1,
        .bytes_argv = argv,
        .wchar_argv = NULL
    };

    __PyImport_AppendInittab__;

    puts("pymain_init");

    setenv("PYTHONHOME","/usr", 1);

    status = pymain_init(&args);

    if (_PyStatus_IS_EXIT(status)) {
        pymain_free();
        return status.exitcode;
    }

    if (_PyStatus_EXCEPTION(status)) {
        puts(" ---------- pymain_exit_error ----------");
        Py_ExitStatusException(status);
        pymain_free();
        return 1;
    }

    if (!mkdir("dev", 0700)) {
       LOG_V("no 'dev' directory, creating one ...");
    }

    if (!mkdir("dev/fd", 0700)) {
       LOG_V("no 'dev/fd' directory, creating one ...");
    }

    if (!mkdir("tmp", 0700)) {
       LOG_V("no 'tmp' directory, creating one ...");
    }


    io_fd[0] = fopen("dev/fd/0", "w+" );
    io_stdin_filenum = fileno(io_fd[0]);
// FD LEAK!
    io_shm[io_stdin_filenum] =  (char *) malloc(FD_BUFFER_MAX);

    for (int i=0;i<FD_BUFFER_MAX;i++)
        io_shm[io_stdin_filenum][i]=0;


//TODO: check if shm is cleared ?
// https://stackoverflow.com/questions/7507638/any-standard-mechanism-for-detecting-if-a-javascript-is-executing-as-a-webworker
// https://stackoverflow.com/questions/7931182/reliably-detect-if-the-script-is-executing-in-a-web-worker

EM_ASM({
    var shm_stdin = $0;
    Module.printErr = Module.print;
    if (typeof WorkerGlobalScope !== 'undefined' && self instanceof WorkerGlobalScope) {
        console.log("PyMain: running in a worker, setting onCustomMessage");
        function onCustomMessage(event) {
            const utf8 = unescape(encodeURIComponent(event.data.userData));
            stringToUTF8( utf8, shm_stdin, $1);
        };

        Module['onCustomMessage'] = onCustomMessage;

    } else {
        console.log("PyMain: running in main thread");
        Module.postMessage = function custom_postMessage(data) {
            const utf8 = unescape(encodeURIComponent(data));
            stringToUTF8( utf8, shm_stdin, $1);
        };
    }
}, io_shm[io_stdin_filenum], FD_BUFFER_MAX);


    PyRun_SimpleString("import sys, embed, builtins, os, time;");

if (1)
    {
        // display a nice six logo python-powered in xterm.js
        #define MAX 132
        char buf[MAX];
        FILE *six = fopen("/assets/cpython.six","r");
        while (six) {
            fgets(buf, MAX, six);
            if (!buf[0]) {
                fclose(six);
                puts("");
                break;
            }
            fputs(buf, stdout);
            buf[0]=0;
        }


    }
    else {
        // same but with python
        PyRun_SimpleString("print(open('/assets/cpython.six').read());");
    }


    // SDL2 basic init
    {
        SDL_Init(SDL_INIT_VIDEO);

        if (TTF_Init())
            puts("TTF_Init error");
        const char *target = "1";
        SDL_SetHint(SDL_HINT_EMSCRIPTEN_KEYBOARD_ELEMENT, target);



/* note for self : typical sdl2 init ( emscripten samples are sdl1 )
            SDL_CreateWindow("default", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 800, 600, 0);
    window = SDL_CreateWindow("CheckKeys Test",
                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                              800, 600, 0);
    renderer = SDL_CreateRenderer(window, -1, 0);
    SDL_RenderPresent(renderer);

    emscripten_set_keypress_callback_on_thread(target, NULL, false, &on_keyboard_event, NULL);
    emscripten_set_keypress_callback(target, NULL, false, &on_keyboard_event);
*/

    }

    chdir("/assets");
    PyRun_SimpleString(
        "sys.path.append('/assets/site-packages');"
        "import __EMSCRIPTEN__;builtins.__EMSCRIPTEN__ = __EMSCRIPTEN__;"
    );




    emscripten_set_main_loop( (em_callback_func)main_iteration, 0, 1);
    return 0;
}
