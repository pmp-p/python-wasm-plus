window.__defineGetter__('__FILE__', function() {
  return (new Error).stack.split('/').slice(-1).join().split(':')[0] +": ";
});


window.readline = { last_cx : -1 , index : 0 }

readline.history = ["os.listdir('/data/data')","preload()","test()"]

readline.complete = function (line) {
    if ( readline.history[ readline.history.length -1 ] != line )
        readline.history.push(line);
    readline.index = 0;

    PyRun_SimpleString(line + "\n")
}


function PyRun_SimpleString(code) {
    if (window.worker) {
        window.worker.postMessage({ target: 'custom', userData: code });
    } else {
        Module.postMessage(code);
    }
}

function emscripten(canvasid, wasmterm) {
    const canvas = document.getElementById(canvasid || "canvas");

    console.log(__FILE__, "canvas found at "+ canvasid)

    // As a default initial behavior, pop up an alert when webgl context is lost. To make your
    // application robust, you may want to override this behavior before shipping!
    // See http://www.khronos.org/registry/webgl/specs/latest/1.0/#5.15.2
    canvas.addEventListener("webglcontextlost", function(e) { alert('WebGL context lost. You will need to reload the page.'); e.preventDefault(); }, false);


    console.log(__FILE__, "terminal found at "+ wasmterm)

    var statusElement = document.getElementById('status');
    var progressElement = document.getElementById('progress');
    var spinnerElement = document.getElementById('spinner');

    const sixel_prefix = String.fromCharCode(27)+"Pq"

    var Module = {

        vt : wasmterm,

        //arguments : ["-i","-"],
        arguments : [],

        PyRun_SimpleString : PyRun_SimpleString,

        locateFile : function(path, prefix) {

            if (path == "python.data") {
                console.log("locateData: "+path+' '+prefix);
                return "main/" + path;
            } else {
                console.log("locateFile: "+path+' '+prefix);
            }
            return prefix + path;
        },

        preRun: [],

        postRun: [],

        print: (function() {
          return function(text) {
            if (arguments.length > 1) text = Array.prototype.slice.call(arguments).join(' ');

            if (text.startsWith(sixel_prefix)) {
                console.log("[sixel image]");
                if (wasmterm)
                    wasmterm.print(text);
            } else {
                // These replacements are necessary if you render to raw HTML
                //text = text.replace(/&/g, "&amp;");
                //text = text.replace(/</g, "&lt;");
                //text = text.replace(/>/g, "&gt;");
                //text = text.replace('\n', '<br>', 'g');
                if (text.endsWith(String.fromCharCode(4)))
                    wasmterm.print(text.slice(0, -1));
                else {
                    if (text.startsWith("Looks like you are rendering"))
                        return;
                    wasmterm.print(text+"\r\n");
                }
                console.log(text);
            }
          };
        })(),


        setStatus: function(text) {
          if (!Module.setStatus.last) Module.setStatus.last = { time: Date.now(), text: '' };
          if (text === Module.setStatus.last.text) return;
          var m = text.match(/([^(]+)\((\d+(\.\d+)?)\/(\d+)\)/);
          var now = Date.now();
          if (m && now - Module.setStatus. last.time < 30) return; // if this is a progress update, skip it if too soon
          Module.setStatus.last.time = now;
          Module.setStatus.last.text = text;
          if (m) {
            text = m[1];
            progressElement.value = parseInt(m[2])*100;
            progressElement.max = parseInt(m[4])*100;
            progressElement.hidden = false;
            spinnerElement.hidden = false;
          } else {
            progressElement.value = null;
            progressElement.max = null;
            progressElement.hidden = true;
            if (!text) spinnerElement.style.display = 'none';
          }
          statusElement.innerHTML = text;
        },

        totalDependencies: 0,

        monitorRunDependencies: function(left) {
          this.totalDependencies = Math.max(this.totalDependencies, left);
          Module.setStatus(left ? 'Preparing... (' + (this.totalDependencies-left) + '/' + this.totalDependencies + ')' : 'All downloads complete.');
        }
    };

    Module.canvas = canvas

    Module.printErr = Module.print

    if  (window.custom_prerun)
        Module.preRun.push( custom_prerun )

    if (window.custom_postrun)
        Module.postRun.push( custom_postrun )


    Module.setStatus('Downloading...');

    window.onerror = function(event) {
        // TODO: do not warn on ok events like simulating an infinite loop or exitStatus
        Module.setStatus('Exception thrown, see JavaScript console');
        spinnerElement.style.display = 'none';
        Module.setStatus = function(text) {
          if (text)
            console.error('[post-exception status] ' + text);
        };
    };


    const jswasmloader=document.createElement('script')
    jswasmloader.setAttribute("type","text/javascript")
    jswasmloader.setAttribute("src", "main/python.js")
    jswasmloader.setAttribute('async', true);
    document.getElementsByTagName("head")[0].appendChild(jswasmloader)

    // so python.js can always find it
    window.Module = Module

    Module.readline_history = []

    // there's no point stacking python code requests until it's really started.
    window.PyRun_SimpleString = PyRun_SimpleString
}





