var statusElement = document.getElementById('status');
var progressElement = document.getElementById('progress');
var spinnerElement = document.getElementById('spinner');

const sixel_prefix = String.fromCharCode(27)+"Pq"

var Module = {
    PyRun_SimpleString : function( code ) {
        console.log("N/I");        
    },
    
    locateFile : function(path, prefix) {
        
        if (path == "python.data")
            return "main/" + path;
        else
            console.log("locateFile: "+path+' '+prefix);
        // if it's a mem init file, use a custom dir
        //if (path.endsWith(".mem")) return "https://mycdn.com/memory-init-dir/" + path;
              // otherwise, use the default, the prefix (JS file's dir) + the path
        return prefix + path;
    },

    preRun: [],
    
    postRun: [],
    
    print: (function() {
      return function(text) {
        if (arguments.length > 1) text = Array.prototype.slice.call(arguments).join(' ');

        if (text.startsWith(sixel_prefix)) {
            console.log("[sixel image]");            
            if (window.terminal)
                window.terminal.print(text);       
        } else {
            // These replacements are necessary if you render to raw HTML
            //text = text.replace(/&/g, "&amp;");
            //text = text.replace(/</g, "&lt;");
            //text = text.replace(/>/g, "&gt;");
            //text = text.replace('\n', '<br>', 'g');            
            
            if (text.endsWith(String.fromCharCode(4)))
                terminal.print(text.slice(0, -1));
            else
                terminal.print(text+"\r\n");            
            console.log(text);
        }   
      };
    })(),
    
    canvas: (function() {
      var canvas = document.getElementById('canvas');

      // As a default initial behavior, pop up an alert when webgl context is lost. To make your
      // application robust, you may want to override this behavior before shipping!
      // See http://www.khronos.org/registry/webgl/specs/latest/1.0/#5.15.2
      canvas.addEventListener("webglcontextlost", function(e) { alert('WebGL context lost. You will need to reload the page.'); e.preventDefault(); }, false);

      return canvas;
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

Module.setStatus('Downloading...');
window.onerror = function(event) {
// TODO: do not warn on ok events like simulating an infinite loop or exitStatus
Module.setStatus('Exception thrown, see JavaScript console');
spinnerElement.style.display = 'none';
Module.setStatus = function(text) {
  if (text) console.error('[post-exception status] ' + text);
};
};

Module.printErr = Module.print


if  (window.custom_prerun)
    Module.preRun.push( custom_prerun )

if (window.custom_postrun)
    Module.postRun.push( custom_postrun )
