import builtins

# try to acquire syslog early
try:
    import embed
    builtins.pdb = embed.pdb
except:
    builtins.pdb = print
    builtins.embed = __import__('__main__')

try:
    # check it the embedding module was finished for that platform.
    # the least shoulbe syslog ( js console / adb logcat )
    embed.log
except:
    pdb("CRITICAL: embed softrt/syslog functions not found ( and also not in __main__ )")
    embed.enable_irq = print
    embed.disable_irq = print
    embed.log = print


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
