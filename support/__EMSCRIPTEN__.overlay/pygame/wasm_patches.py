import sys
import asyncio

# do no change import order

# patching threading.Thread
import aio.gthread

# patched module

from threading import Thread

pygame = sys.modules[__package__]

# ====================================================================
# replace non working native function.

print(
    """\
https://github.com/pygame-web/pygbag/issues/16
    applying: use aio green thread for pygame.time.set_timer
"""
)

# build the event and send it directly in the queue
# caveats :
#   - could be possibly very late
#   - delay cannot be less than frametime at device refresh rate.


def patch_set_timer(cust_event_no, millis, loops=0):
    dlay = float(millis) / 1000
    cevent = pygame.event.Event(cust_event_no)

    async def fire_event():
        while true:
            await asyncio.sleep(dlay)
            if aio.exit:
                break
            pygame.event.post(cevent)

    Thread(target=fire_event).start()


pygame.time.set_timer = patch_set_timer

# ====================================================================
# pygame.quit is too hard on gc, and re-importing pygame is problematic
# if interpreter is not fully renewed.
# so just clear screen cut music and hope for the best.


def pygame_quit():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.display.update()


pygame.quit = pygame_quit


# =====================================================================
# we want fullscreen-windowed template for games as a default
# so call javascript to resize canvas viewport to fill the current
# window each time mode is changed, also remove the "scaled" option

__pygame_display_set_mode__ = pygame.display.set_mode


def patch_pygame_display_set_mode(size=(0,0), flags=0, depth=0):
    import platform

    # apparently no need to remove scaled.
    if size != (0,0):
        if (sys.platform == "emscripten") and platform.is_browser:
            try:
                platform.window.window_resize()
            except:
                print("ERROR: browser host does not provide window_resize() function",file=sys.__stderr__)

    return __pygame_display_set_mode__(size, flags, depth)


pygame.display.set_mode = patch_pygame_display_set_mode


#=======================================================================
# replace sdl thread music playing by browser native player
#

tracks = { "current": 0 }



def patch_pygame_mixer_music_stop_pause_unload():
    last = tracks["current"]
    if last:
        window.tracks.stop(last)
        tracks["current"] = 0

pygame.mixer.music.unload = patch_pygame_mixer_music_stop_pause_unload

def patch_pygame_mixer_music_load(fileobj, namehint=""):
    from platform import window
    global tracks

    patch_pygame_mixer_music_stop_pause_unload()

    tid = tracks.get( fileobj, 0 )
    # track was never loaded
    if not tid:
        tid = window.tracks.add(fileobj)
    tracks["current"] = tid
pygame.mixer.music.load = patch_pygame_mixer_music_load

def patch_pygame_mixer_music_play(loops=0, start=0.0, fade_ms=0):
    patch_pygame_mixer_music_stop_pause_unload()

    window.tracks.play( tracks["current"], loops )

pygame.mixer.music.play = patch_pygame_mixer_music_play





























# ====================================================================
print("\n\n")
print(open("/data/data/org.python/assets/pygame.six").read())
