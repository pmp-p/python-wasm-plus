import asyncio
import pygame


import aio.gthread

from threading import Thread

#====================================================================

print("""\
https://github.com/pygame-web/pygbag/issues/16
    applying: use aio green thread for pygame.time.set_timer
""")

# build the event and send it directly in the queue
# caveats :
#   - could be possibly very late
#   - delay cannot be less than frametime at device refresh rate.


def patch_set_timer(cust_event_no, millis, loops=0):
    dlay = float(millis) / 1000
    cevent = pygame.event.Event(cust_event_no)
    async def fire_event():
        while not aio.exit:
            await asyncio.sleep( dlay )
            pygame.event.post(cevent)
    Thread(target=fire_event).start()

pygame.time.set_timer = patch_set_timer



#====================================================================

