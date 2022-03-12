window.__defineGetter__('__FILE__', function() {
  return (new Error).stack.split('/').slice(-1).join().split(':')[0] +": ";
});


export class WasmTerminal {

  constructor() {
    this.input = ''
    this.resolveInput = null
    this.activeInput = true
    this.inputStartCursor = null

    this.xterm = new Terminal(
      { scrollback: 10000, fontSize: 14, theme: { background: '#1a1c1f' }, cols: 100}
    );

    const imageAddon = new ImageAddon.ImageAddon("./xtermjsixel/xterm-addon-image-worker.js", {sixelSupport: true});

    this.xterm.loadAddon(imageAddon);
    this.xterm.open(document.getElementById('terminal'))

    // hack to hide scrollbar inside box
    document.getElementsByClassName('xterm-viewport')[0].style.left="-15px"

    this.xterm.onKey((keyEvent) => {
      // Fix for iOS Keyboard Jumping on space
      if (keyEvent.key === " ") {
        keyEvent.domEvent.preventDefault();
      }
    });

    this.xterm.onData(this.handleTermData)
  }

  open(container) {
    this.xterm.open(container);
  }

  handleTermData = (data) => {

    const ord = data.charCodeAt(0);
    let ofs;

    // TODO: Handle ANSI escape sequences
    if (ord === 0x1b) {

    // Handle special characters
    } else if (ord < 32 || ord === 0x7f) {
      switch (data) {
        case "\r": // ENTER
        case "\x0a": // CTRL+J
        case "\x0d": // CTRL+M
            this.xterm.write('\r\n');
            PyRun_SimpleString(this.input + "\n")
            readline_history.push = this.input ;
            this.input = '';
            break;
        case "\x7F": // BACKSPACE
        case "\x08": // CTRL+H
        case "\x04": // CTRL+D
          this.handleCursorErase(true);
          break;

      }
    } else {
        this.input += data;
        this.xterm.write(data)
    }
  }

  handleCursorErase() {
    // Don't delete past the start of input
    if (this.xterm.buffer.active.cursorX <= this.inputStartCursor) {
      return
    }
    this.input = this.input.slice(0, -1)
    this.xterm.write('\x1B[D')
    this.xterm.write('\x1B[P')
  }


  clear() {
    this.xterm.clear();
  }

  print(message) {
    const normInput = message.replace(/[\r\n]+/g, "\n").replace(/\n/g, "\r\n");
    this.xterm.write(normInput);
  }

}


window.onload = async () => {

    await custom_onload(WasmTerminal)

}

