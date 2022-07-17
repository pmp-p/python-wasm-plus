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
print("\n\n")
print(open("/data/data/org.python/assets/pygame.six").read())
