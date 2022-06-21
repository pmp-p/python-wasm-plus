def open(url, new=0, autoraise=True):
    __import__('__EMSCRIPTEN__').window.open(url, "_blank")

def open_new(url):
    return open(url, 1)

def open_new_tab(url):
    return open(url, 2)
