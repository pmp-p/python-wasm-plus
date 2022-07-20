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


def path_pygame_display_set_mode(size, flags, depth=0):
    import platform

    # apparently no need to remove scaled.
    if (sys.platform == "emscripten") and platform.is_browser:
        platform.window.window_resize()

    return __pygame_display_set_mode__(size, flags, depth)


pygame.display.set_mode = path_pygame_display_set_mode

# ====================================================================
print("\n\n")
print(open("/data/data/org.python/assets/pygame.six").read())
