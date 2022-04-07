import builtins

def defined(plat):
    try:
        eval(plat)
        return True
    except:
        return False

def define(tag, value):
    if defined(tag):
        pdb(f"WARNING: redefinition of {tag}")
    setattr( builtins , tag, value)

builtins.define = define
builtins.defined = defined
