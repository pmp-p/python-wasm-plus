import sys
import os
import math
import time
import random as rm
from warnings import warn
import builtins
import pygame as pg

try:
    __EMSCRIPTEN__
except:
    __EMSCRIPTEN__ = False

__ANDROID__ = hasattr(sys,"getandroidapilevel")

if __ANDROID__:
    import android

PATH = os.path.abspath(".")

def status(self):
    if self.last_state != self.state:
        print(self.__class__.__name__, " state:", self.last_state, "->", self.state)
        self.last_state = self.state
        return self.state
    # no transition
    return ""


class App:
    def __init__(self):
        self.init()

    def init(self):
        self.swidth = 800
        self.sheight = 600
        self.audio = True

        if __ANDROID__ or __EMSCRIPTEN__:
            self.flags = pg.SCALED | pg.FULLSCREEN
        else:
            self.flags = 0

        self.screen = pg.display.set_mode((self.swidth, self.sheight), self.flags)

        self.last_state = "float"

        self.main_menu = Main_Menu(self.swidth, self.sheight, self.screen)

        self.game = Game(self.swidth, self.sheight, self.screen)

        # clear events
        pg.event.get()

        self.__class__.init = None
        self.state = "Main Menu"

        #self.state = "Test"


    def main(self):

        while self.state != "Quit":

            #on transition to menu
            if status(self) in ["Main Menu", "Test"]:
                print("WebAudio not supported by worker thread (yet)")
                if self.audio:
                    pg.mixer.init()
                    pg.music.set_volume(0.5)
                    pg.music.load("Eisenfunk - Pong.ogg")
                    pg.music.play()


                # no replay again
                self.audio = False


            if self.state == "Main Menu":
                self.state = self.main_menu.main()

            elif self.state == "Game":
                self.state = self.game.main()

            elif self.state == "Test":

                RED = (255, 0, 0)
                BLUE = (0, 0, 255)
                GREEN = (0, 255, 0)

                GRAY = (127, 127, 127)

                self.screen.fill(GRAY)

                pg.draw.rect(self.screen, color=RED, rect=(50, 20, 120, 100), width=5)
                pg.draw.ellipse(self.screen, GREEN, (100, 60, 160, 100))
                pg.draw.ellipse(self.screen, BLUE, (450, 100, 160, 100), 8)

            # wasm has auto update on end of frame
            # and NEED to exit to JS coroutine to process graphic proxy

            if __EMSCRIPTEN__:
                break

            pg.display.update()



class Main_Menu:
    def __init__(self, swidth, sheight, screen):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.init()

    def init(self):
        self.state = "float"
        self.clock = None
        self.fps = 60

        self.menu_render_gap = 100
        self.menu_render_pad = 300
        self.title = "Pong"

        self.menu_options = ("Play", "Quit")

        self.font_title = pg.font.Font(os.path.join(PATH, "font.ttf"), 150)
        self.font_menu = pg.font.Font(os.path.join(PATH, "font.ttf"), 80)
        self.font_menu_selected = pg.font.Font(os.path.join(PATH, "font.ttf"), 100)

        self.rendered_title = self.font_title.render(self.title, True, (0, 0, 0))
        self.title_rect = self.rendered_title.get_rect()
        self.title_rect.center = self.swidth / 2, 150
        self.rendered_menu_options = []
        for i in self.menu_options:
            text_normal = self.font_menu.render(i, True, (12, 12, 12))
            text_selected = self.font_menu_selected.render(i, True, (24, 24, 24))
            text_rect = text_normal.get_rect()
            text_rect_selected = text_selected.get_rect()
            self.rendered_menu_options.append(
                (text_rect, text_rect_selected, text_normal, text_selected)
            )


        self.menu_option_current = 0
        self.__class__.init = None
        self.state = "Main Menu"


    def main(self):
        if self.clock is None:
            self.clock = pg.time.Clock()
        # Some in loop variables
        dt = self.clock.tick(self.fps) / 1000
        pg.display.set_caption(str(int(self.clock.get_fps())))

        # Check for events
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                self.state = "Quit"
            elif ev.type == pg.KEYUP:
                print("PYGAME.KEYUP", ev.key)
                if ev.key in (pg.K_ESCAPE, pg.K_AC_BACK):
                    self.state = "Quit"
                elif ev.key == pg.K_f:
                    self.menu_option_current -= 1
                    if self.menu_option_current < 0:
                        self.menu_option_current = len(self.menu_options) - 1
                elif ev.key == pg.K_v:
                    self.menu_option_current += 1
                    if self.menu_option_current > len(self.menu_options) - 1:
                        self.menu_option_current = 0
                elif ev.key == pg.K_RETURN:
                    if self.menu_option_current == 0:
                        return "Game"
                    elif self.menu_option_current == 1:
                        return "Quit"
            elif ev.type == pg.MOUSEMOTION:
                # print("mouse-pos:", end=' ')
                mouse_pos = pg.mouse.get_pos()
                # print(mouse_pos)

                for i in range(len(self.rendered_menu_options)):
                    if self.rendered_menu_options[i][0].collidepoint(mouse_pos):
                        self.menu_option_current = i
            elif ev.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                # print(mouse_pos)
                for i in range(len(self.rendered_menu_options)):
                    if self.rendered_menu_options[i][0].collidepoint(mouse_pos):
                        if i == 0:
                            return "Game"

                        elif i == 1:
                            return "Quit"
                else:
                    print("mouse-b: Main_menu")
                    self.state = "Main Menu"
            else:
                print(ev)


        # Handle the events
        pass

        # Draw the objects on the screen
        self.screen.fill((5, 69, 153))

        pg.draw.rect(self.screen, (49, 60, 77), (0, 0, self.swidth, self.sheight))
        pg.draw.rect(
            self.screen, (5, 69, 153), (0, 0, self.swidth, self.sheight), width=10
        )

        self.screen.blit(self.rendered_title, self.title_rect)
        for i in range(len(self.rendered_menu_options)):
            if i == self.menu_option_current:
                self.rendered_menu_options[i][0].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                self.rendered_menu_options[i][1].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                # pg.draw.rect(self.screen,'Blue',self.rendered_menu_options[i][1])
                self.screen.blit(
                    self.rendered_menu_options[i][3],
                    self.rendered_menu_options[i][1],
                )
            else:
                self.rendered_menu_options[i][0].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                # pg.draw.rect(self.screen,'Blue',self.rendered_menu_options[i][0])
                self.screen.blit(
                    self.rendered_menu_options[i][2],
                    self.rendered_menu_options[i][0],
                )

        return self.state



# =============================== GAME ==================================


class Game:
    def __init__(self, swidth, sheight, screen):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.clock = pg.time.Clock()
        self.fps = 60
        self.last_state = "float"
        self.state = "Running"
        self.center_line_colour = (169, 172, 180)
        self.object = Object(self.swidth, self.sheight, self.screen)
        self.pause_menu = Pause_Menu(
            self.swidth, self.sheight, self.screen, "Paused", ("Resume", "Main Menu")
        )
        self.gameover_menu = GameOver_Menu(
            self.swidth,
            self.sheight,
            self.screen,
            "Game Over",
            ("Restart", "Main Menu"),
        )
        del Menu.init

        self.hud = HUD(self.swidth, self.sheight, self.screen)

    def main(self):
        status(self)
        if self.clock is None:
            self.clock = pg.time.Clock()

        # Some in loop variables
        dt = self.clock.tick(self.fps) / 1000
        # pg.display.set_caption(str(int(self.clock.get_fps())))
        # print(self.clock.get_fps())

        # Check for events
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                return "Quit"

            elif ev.type == pg.WINDOWFOCUSLOST:
                self.state == "Paused"

            elif ev.type == pg.KEYDOWN:
                if ev.key in (pg.K_ESCAPE, pg.K_AC_BACK):
                    #return "Main Menu"
                    return "Quit"
                elif ev.key == pg.K_p:
                    # print("Pause Request in ? state :", self.state)
                    if self.state == "Paused":
                        self.state = "Resume"
                    elif self.state == "Running":
                        self.state = "Paused"
                    else:
                        print("Pause Request in ? state :", self.state)

            if self.state == "Game Over":
                self.state = self.gameover_menu.events(ev)

            elif self.state == "Paused":
                self.state = self.pause_menu.events(ev)

            else:
                self.state = self.hud.events(ev, self.state)

        try:

            status(self)

            if self.state in ["Resume", "Restart"]:
                self.state = "Running"
                return "Game"

            status(self)

            if self.state == "Running":
                self.state = self.object.physics(dt)
                status(self)
                if self.state == "Game Over":
                    self.clock = None
                else:
                    self.hud.physics(
                        self.object.player_score, self.object.level, self.clock.get_fps()
                    )

                    # Draw the objects on the screen
                    self.screen.fill((5, 69, 153))
                    pg.draw.rect(
                        self.screen, (49, 60, 77), (0, 0, self.swidth, self.sheight)
                    )
                    pg.draw.line(
                        self.screen,
                        self.center_line_colour,
                        (self.swidth / 2, 0),
                        (self.swidth / 2, self.sheight),
                    )
                    self.object.draw()

                    pg.draw.rect(
                        self.screen,
                        (5, 69, 153),
                        (0, 0, self.swidth, self.sheight),
                        width=10,
                    )

            elif self.state == "Game Over":
                self.gameover_menu.draw()

            elif self.state == "Paused":
                self.pause_menu.draw()

            elif self.state == "Main Menu":
                return "Main Menu"

        finally:
            self.hud.draw()


        return "Game"

class Object:
    def __init__(self, swidth, sheight, screen):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.border_width = 10
        self.base_pad = 5
        self.base_properties = {
            "rect": pg.Rect(0, 0, 25, 150),
            "radius": 30,
            "main_colour": (128, 135, 145),
            "circle_colour": (55, 55, 55),
            "hit_colour": (70, 70, 70),
        }
        self.player = Base(
            self.swidth,
            self.sheight,
            self.screen,
            self.base_properties["rect"],
            self.base_properties["main_colour"],
            self.base_properties["hit_colour"],
            self.border_width,
        )
        self.opponent = Base(
            self.swidth,
            self.sheight,
            self.screen,
            self.base_properties["rect"],
            self.base_properties["main_colour"],
            self.base_properties["hit_colour"],
            self.border_width,
        )
        self.player_pos = [
            self.border_width + self.base_pad + self.base_properties["rect"].w / 2,
            self.sheight / 2,
        ]
        self.opponent_pos = [
            swidth
            - self.border_width
            - self.base_pad
            - self.base_properties["rect"].w / 2,
            self.sheight / 2,
        ]
        self.player_vel = 200
        self.max_vel = 100
        self.ball_rad = 25
        self.ball_colour = (156, 50, 56)
        self.ball_vel = pg.math.Vector2(self.max_vel, self.max_vel).rotate(
            rm.choice(
                (
                    rm.randint(80, 100),
                    rm.randint(170, 190),
                    rm.randint(260, 280),
                    rm.randint(350, 370),
                )
            )
        )
        self.ball_pos = pg.math.Vector2(swidth / 2, sheight / 2)
        self.player_score = 0
        self.level = 1
        self.increase_level_score = 5
        self.increase_ball_vel_after_level = 1.2
        self.increase_player_vel_after_level = 1.1
        if __ANDROID__:
            try:
                accelerometer.enable()
            except:
                warn(
                    "No accelerometer found! Play with keyboard.",
                )

        # self.opponent_score=0

    def events(self):
        pass

    def physics(self, dt):
        self.ball_pos += self.ball_vel * dt
        if self.ball_pos.y < self.border_width + self.ball_rad:
            self.ball_pos.y = self.border_width + self.ball_rad
            self.ball_vel.y = -self.ball_vel.y
        elif self.ball_pos.y > self.sheight - self.border_width - self.ball_rad:
            self.ball_pos.y = self.sheight - self.border_width - self.ball_rad
            self.ball_vel.y = -self.ball_vel.y
        self.opponent_pos[1] = self.ball_pos.y
        # Mouse controls
        # mouse_posy=pg.mouse.get_pos()[1]
        # self.player_pos[1]=mouse_posy
        # Keyboard controls

        pressed = pg.key.get_pressed()

        if pressed[pg.K_f]:
            self.player_pos[1] -= self.player_vel * dt

        if pressed[pg.K_v]:
            self.player_pos[1] += self.player_vel * dt

        if __ANDROID__:
            x, y, z = accelerometer.acceleration
            tilt_angle = math.degrees(math.atan(y / x))
            if tilt_angle > 15:
                self.player_pos[1] -= self.player_vel * dt
            elif tilt_angle < -13:
                self.player_pos[1] += self.player_vel * dt

        player_rect = self.player.rect

        if self.player_pos[1] < player_rect.h / 2 + self.border_width:
            self.player_pos[1] = player_rect.h / 2 + self.border_width
        elif self.player_pos[1] > self.sheight - player_rect.h / 2 - self.border_width:
            self.player_pos[1] = self.sheight - player_rect.h / 2 - self.border_width

        self.player.physics(self.player_pos, False)
        opponent_rect = self.opponent.rect

        if self.opponent_pos[1] < opponent_rect.h / 2 + self.border_width:
            self.opponent_pos[1] = opponent_rect.h / 2 + self.border_width
        elif (
            self.opponent_pos[1]
            > self.sheight - opponent_rect.h / 2 - self.border_width
        ):
            self.opponent_pos[1] = (
                self.sheight - opponent_rect.h / 2 - self.border_width
            )
        self.player.physics(self.player_pos, False)
        self.opponent.physics(self.opponent_pos, False)
        self.ball_pos, self.ball_vel = self.collision(
            self.player.small_rect, self.ball_pos, self.ball_vel, self.ball_rad
        )
        self.ball_pos, self.ball_vel = self.collision(
            self.opponent.small_rect, self.ball_pos, self.ball_vel, self.ball_rad
        )

        if self.player_score > self.level * self.increase_level_score:
            self.player_vel = self.player_vel * self.increase_player_vel_after_level
            self.ball_vel = self.ball_vel * self.increase_ball_vel_after_level
            self.level += 1

        if (
            self.ball_pos.x < self.border_width - self.ball_rad
            or self.ball_pos.x > self.swidth - self.border_width + self.ball_rad
        ):
            self.ball_vel = pg.math.Vector2(0, 0)
            self.ball_pos = pg.math.Vector2(self.swidth / 2, self.sheight / 2)
            print("Game Over!")
            return "Game Over"

        return "Running"

    def draw(self):
        self.player.draw()
        self.opponent.draw()
        pg.draw.circle(self.screen, self.ball_colour, self.ball_pos, self.ball_rad)

    def collision(self, rect, pos, vel, rad):
        new_rect = pg.Rect(0, 0, rect.w + 2 * rad, rect.h)
        new_rect.center = rect.center
        if new_rect.collidepoint(pos):
            self.player_score += 1
            if vel.x < 0:
                pos.x = new_rect.right
                vel.x = -vel.x
            elif vel.x > 0:
                pos.x = new_rect.left
                vel.x = -vel.x
        elif (
            self.distance(pos, rect.midtop) < rect.w / 2 + rad
            or self.distance(pos, rect.midbottom) < rect.w / 2 + rad
        ):
            self.player_score += 1
            if vel.x < 0:
                pos.x = new_rect.right
            elif vel.x > 0:
                pos.x = new_rect.left
            vel = -1 * vel
        return pos, vel

    def distance(self, pos1, pos2):
        s = ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5
        return s


class Base:
    def __init__(
        self,
        swidth,
        sheight,
        screen,
        small_rect,
        main_colour,
        hit_colour,
        border_width,
        circle_colour=None,
    ):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.border_width = border_width
        self.main_colour = main_colour
        self.colour = self.main_colour
        self.small_rect = pg.Rect(small_rect)
        self.radius = self.small_rect.w / 2
        self.rect = pg.Rect(0, 0, 2 * self.radius, self.small_rect.h + 2 * self.radius)
        self.circle_pos = self.small_rect.midtop, self.small_rect.midbottom
        if circle_colour is None:
            self.circle_colour = self.colour
        else:
            self.circle_colour = circle_colour
        self.hit_colour = hit_colour

    def physics(self, pos, collided):
        self.small_rect.center = pos
        self.circle_pos = self.small_rect.midtop, self.small_rect.midbottom
        self.rect.center = self.small_rect.center
        if collided:
            self.colour = self.hit_colour
        else:
            self.colour = self.main_colour

    def draw(self):
        pg.draw.circle(self.screen, self.circle_colour, self.circle_pos[0], self.radius)
        pg.draw.circle(self.screen, self.circle_colour, self.circle_pos[1], self.radius)
        pg.draw.rect(self.screen, self.colour, self.small_rect)


class Menu:
    def __init__(self, swidth, sheight, screen, title, options):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.title = title
        self.menu_options = options
        self.init()

    def init(self):
        self.font_title = pg.font.Font(os.path.join(PATH, "font.ttf"), 120)
        self.font_menu = pg.font.Font(os.path.join(PATH, "font.ttf"), 50)
        self.font_menu_selected = pg.font.Font(os.path.join(PATH, "font.ttf"), 70)
        self.last_state = "float"
        self.state = self.title
        self.rendered_title = self.font_title.render(self.title, True, (0, 0, 0))
        self.title_rect = self.rendered_title.get_rect()
        self.title_rect.center = self.swidth / 2, 250
        self.menu_render_gap = 60
        self.menu_render_pad = 400

        self.rendered_menu_options = []
        for i in self.menu_options:
            text_normal = self.font_menu.render(i, True, (12, 12, 12))
            text_selected = self.font_menu_selected.render(i, True, (24, 24, 24))
            text_rect = text_normal.get_rect()
            text_rect_selected = text_selected.get_rect()
            self.rendered_menu_options.append(
                (text_rect, text_rect_selected, text_normal, text_selected)
            )
        self.menu_option_current = 0

    def events(self, ev):
        self.state = self.title
        try:
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_f:
                    self.menu_option_current -= 1
                    if self.menu_option_current < 0:
                        self.menu_option_current = len(self.menu_options) - 1
                elif ev.key == pg.K_v:
                    self.menu_option_current += 1
                    if self.menu_option_current > len(self.menu_options) - 1:
                        self.menu_option_current = 0
                elif ev.key == pg.K_RETURN:
                    if self.menu_option_current == 0:
                        self.state = self.menu_options[0]
                    elif self.menu_option_current == 1:
                        self.state = "Main Menu"

            elif ev.type == pg.MOUSEMOTION:
                mouse_pos = pg.mouse.get_pos()
                for i in range(len(self.rendered_menu_options)):
                    if self.rendered_menu_options[i][0].collidepoint(mouse_pos):
                        self.menu_option_current = i

            elif ev.type == pg.MOUSEBUTTONDOWN:
                mouse_pos = pg.mouse.get_pos()
                for i in range(len(self.rendered_menu_options)):
                    if self.rendered_menu_options[i][0].collidepoint(mouse_pos):
                        if i == 0:
                            self.state = self.menu_options[0]
                        elif i == 1:
                            self.state = "Main Menu"

        finally:
            status(self)
        return self.state

    def draw(self):
        self.screen.fill((5, 69, 153))
        self.screen.blit(self.rendered_title, self.title_rect)
        for i in range(len(self.rendered_menu_options)):
            if i == self.menu_option_current:
                self.rendered_menu_options[i][0].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                self.rendered_menu_options[i][1].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                # pg.draw.rect(self.screen,'Blue',self.rendered_menu_options[i][1])
                self.screen.blit(
                    self.rendered_menu_options[i][3], self.rendered_menu_options[i][1]
                )
            else:
                self.rendered_menu_options[i][0].center = (
                    self.swidth / 2,
                    self.menu_render_pad + self.menu_render_gap * i,
                )
                # pg.draw.rect(self.screen,'Blue',self.rendered_menu_options[i][0])
                self.screen.blit(
                    self.rendered_menu_options[i][2], self.rendered_menu_options[i][0]
                )


class Pause_Menu(Menu):
    pass


class GameOver_Menu(Menu):
    pass


class HUD:
    def __init__(self, swidth, sheight, screen):
        self.swidth = swidth
        self.sheight = sheight
        self.screen = screen
        self.font = pg.font.Font(os.path.join(PATH, "font.ttf"), 30)
        self.hud_option_colour = "Black"
        self.pause_button_colour = "Black"
        self.hud_options = {
            "Keys: ": (15, 15),
            "Score: ": (15, 45),
            "Level: ": (15, 75),
            "Fps: ": (15, 105),
        }
        self.pause_button_rect = pg.Rect(self.swidth - 45, 15, 30, 30)
        self.paused = False
        self.rendered_options = []

    def events(self, ev, current_state):
        if ev.type == pg.MOUSEBUTTONDOWN and self.pause_button_rect.collidepoint(
            pg.mouse.get_pos()
        ):
            if current_state == "Paused":
                return "Running"
            else:
                return "Paused"
        return current_state

    def physics(self, score, level, fps):
        self.rendered_options.clear()
        for option in self.hud_options :
            if option == "Score: ":
                text = option + str(score)
            elif option == "Level: ":
                text = option + str(level)
            elif option == "Fps: ":
                text = option + str(round(fps))
            elif option == "Keys: ":
                text = option + " f,v for up,down. p to pause."

            self.rendered_options.append(
                (
                    self.font.render(text, True, self.hud_option_colour),
                    self.hud_options[option],
                )
            )

    def draw(self):
        for i in self.rendered_options:
            self.screen.blit(i[0], i[1])
        self.draw_pause_button()

    def draw_pause_button(self):
        if self.paused:
            pg.draw.polygon(
                self.screen,
                self.pause_button_colour,
                (
                    self.pause_button_rect.topleft,
                    self.pause_button_rect.bottomleft,
                    self.pause_button_rect.midright,
                ),
            )
        else:
            pg.draw.rect(
                self.screen,
                self.pause_button_colour,
                pg.Rect(
                    self.pause_button_rect.topleft,
                    (self.pause_button_rect.w / 3, self.pause_button_rect.h),
                ),
            )
            pg.draw.rect(
                self.screen,
                self.pause_button_colour,
                pg.Rect(
                    self.pause_button_rect.x + 2 * self.pause_button_rect.w / 3,
                    self.pause_button_rect.y,
                    self.pause_button_rect.w / 3,
                    self.pause_button_rect.h,
                ),
            )


# ========================================================================


def start():

    pg.init()

    global app
    builtins.self = None

    try:
        app = App()
        builtins.self = app
        if __EMSCRIPTEN__:
            aio.steps.append(self.main)
            aio.steps.append(pg.display.update)
        else:
            self.main()

    except Exception as error:
        error = str(error)
        if __ANDROID__:
            notification.notify(message=error, toast=True)
            notification.notify(title="Error", message=error)
            time.sleep(10)
        else:
            print(error)

    if not __EMSCRIPTEN__:
        pg.quit()


# builtins.start = start
start()
