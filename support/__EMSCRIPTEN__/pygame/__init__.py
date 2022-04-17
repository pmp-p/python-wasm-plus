import sys
import os
import builtins

def clean_mod(modname):
    mod = sys.modules.pop(modname.replace(".", "_"))
    sys.modules[modname] = mod
    return mod


from pygame_base import *

base = clean_mod("pygame.base")

from pygame_constants import *

constants = clean_mod("pygame.constants")

from pygame.version import *

import pygame_rect
from pygame_rect import Rect
rect = clean_mod("pygame.rect")

from pygame_rwobject import encode_string, encode_file_path
rwobject = clean_mod("pygame.rwobject")


import pygame_surflock

surflock = clean_mod("pygame.surflock")

import pygame.colordict

import pygame_color

color = clean_mod("pygame.color")

Color = pygame.color.Color

import pygame_bufferproxy

bufferproxy = clean_mod("pygame.bufferproxy")
BufferProxy = pygame.bufferproxy.BufferProxy


import pygame_math

math = clean_mod("pygame.math")
Vector2 = pygame.math.Vector2
Vector3 = pygame.math.Vector3

__version__ = ver


# next, the "standard" modules
# we still allow them to be missing for stripped down pygame distributions
if get_sdl_version() < (2, 0, 0):
    # cdrom only available for SDL 1.2.X
    try:
        import pygame.cdrom
    except (ImportError, IOError):
        cdrom = MissingModule("cdrom", urgent=1)


import pygame_display
display = clean_mod("pygame.display")

import pygame_draw
draw = clean_mod("pygame.draw")

import pygame__freetype
_freetype = clean_mod("pygame._freetype")


import pygame_font
font = clean_mod("pygame.font")

import pygame.sysfont
pygame.font.SysFont = pygame.sysfont.SysFont
pygame.font.get_fonts = pygame.sysfont.get_fonts
pygame.font.match_font = pygame.sysfont.match_font


"""
import pygame.mask
from pygame.mask import Mask

from pygame.pixelarray import PixelArray

from pygame.overlay import Overlay

import pygame.transform

"""


import pygame_surface
Surface = pygame_surface.Surface
surface = clean_mod("pygame.surface")


import pygame_transform
transform = clean_mod("pygame.transform")


import pygame_key
key = clean_mod("pygame.key")

import pygame_mouse
mouse = clean_mod("pygame.mouse")

import pygame_event
event = clean_mod("pygame.event")

import pygame_imageext
imageext = clean_mod("pygame.imageext")

import pygame_mask
mask = clean_mod("pygame.mask")

import pygame_image
image = clean_mod("pygame.image")

import pygame_joystick
joystick = clean_mod("pygame.joystick")

import pygame_time
time = clean_mod("pygame.time")
time._internal_mod_init() # FIXME: won't work
# while ./emscripten/src/library_sdl.js:  SDL_CreateMutex: function() { return 0 },

import pygame.cursors as cursors

import pygame_mixer
mixer = clean_mod("pygame.mixer")

import pygame_mixer_music
music = clean_mod("pygame.mixer_music")

mixer.music = music
################################

import pygame._sdl2
sys.modules["pygame._sdl2.video"]=pygame._sdl2.video


import pygame_sprite
sprite = clean_mod("pygame.sprite")


import pygame.pkgdata as pkgdata


del clean_mod


# Thanks for supporting pygame. Without support now, there won't be pygame later.
if "PYGAME_HIDE_SUPPORT_PROMPT" not in os.environ:
    print("\n\n")
    print(open('/data/data/org.python/assets/pygame.six').read())


    print(
        "pygame {} (SDL {}.{}.{}, Python {}.{}.{})".format(  # pylint: disable=consider-using-f-string
            ver, *get_sdl_version() + sys.version_info[0:3]
        )
    )
    print("Hello from the pygame community. https://www.pygame.org/contribute.html")



#
