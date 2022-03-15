#!/bin/env python3.11

import pygame as pg

try:
    __EMSCRIPTEN__
except:
    __EMSCRIPTEN__ = False

# Define some colors.
BLACK = pg.Color('black')
WHITE = pg.Color('white')


# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class Texblit(object):
    def __init__(self):
        self.reset()
        self.font = pg.font.Font(None, 20)

    def blit(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


pg.init()

# Set the width and height of the screen (width, height).
screen = pg.display.set_mode((500, 700))

pg.display.set_caption("My Game")

# Loop until the user clicks the close button.
done = False

# Used to manage how fast the screen updates.
clock = pg.time.Clock()

# Initialize the joysticks.
pg.joystick.init()

# Get ready to print.
textPrint = Texblit()

# -------- Main Program Loop -----------
def loop():
    global screen, done, clock, textPrint, BLACK, WHITE

    while not done:
        #
        # EVENT PROCESSING STEP
        #
        # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
        # JOYBUTTONUP, JOYHATMOTION
        for event in pg.event.get(): # User did something.
            if event.type == pg.QUIT: # If user clicked close.
                done = True # Flag that we are done so we exit this loop.
            elif event.type == pg.JOYBUTTONDOWN:
                print("Joystick button pressed.")
            elif event.type == pg.JOYBUTTONUP:
                print("Joystick button released.")

        #
        # DRAWING STEP
        #
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill(WHITE)
        textPrint.reset()

        # Get count of joysticks.
        joystick_count = pg.joystick.get_count()

        textPrint.blit(screen, "Number of joysticks: {}".format(joystick_count))
        textPrint.indent()

        # For each joystick:
        for i in range(joystick_count):
            joystick = pg.joystick.Joystick(i)
            joystick.init()

            textPrint.blit(screen, "Joystick {}".format(i))
            textPrint.indent()

            # Get the name from the OS for the controller/joystick.
            name = joystick.get_name()
            textPrint.blit(screen, "Joystick name: {}".format(name))

            # Usually axis run in pairs, up/down for one, and left/right for
            # the other.
            axes = joystick.get_numaxes()
            textPrint.blit(screen, "Number of axes: {}".format(axes))
            textPrint.indent()

            for i in range(axes):
                axis = joystick.get_axis(i)
                textPrint.blit(screen, "Axis {} value: {:>6.3f}".format(i, axis))
            textPrint.unindent()

            buttons = joystick.get_numbuttons()
            textPrint.blit(screen, "Number of buttons: {}".format(buttons))
            textPrint.indent()

            for i in range(buttons):
                button = joystick.get_button(i)
                textPrint.blit(screen,
                                 "Button {:>2} value: {}".format(i, button))
            textPrint.unindent()

            hats = joystick.get_numhats()
            textPrint.blit(screen, "Number of hats: {}".format(hats))
            textPrint.indent()

            # Hat position. All or nothing for direction, not a float like
            # get_axis(). Position is a tuple of int values (x, y).
            for i in range(hats):
                hat = joystick.get_hat(i)
                textPrint.blit(screen, "Hat {} value: {}".format(i, str(hat)))
            textPrint.unindent()

            textPrint.unindent()

        #
        # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
        #

        # Go ahead and update the screen with what we've drawn.
        pg.display.flip()

        if __EMSCRIPTEN__:
            break
        # Limit to 20 frames per second.
        clock.tick(20)


# Close the window and quit.
# If you forget this line, the program will 'hang'
# on exit if running from IDLE.
if __EMSCRIPTEN__:
    aio.steps.append(loop)
    aio.steps.append(pg.display.update)
else:
    loop()
    pg.quit()

