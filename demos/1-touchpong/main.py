try:
    import android

    __ANDROID__ = True
except:
    __ANDROID__ = False
    android = None

try:
    __EMSCRIPTEN__
except:
    __EMSCRIPTEN__ = False

import pygame as pg

pg.init()
if __ANDROID__ :
    screen = pg.display.set_mode((640, 360), pg.SCALED | pg.FULLSCREEN)
elif __EMSCRIPTEN__:
    screen = pg.display.set_mode((640, 360), pg.SCALED)
else:
    screen = pg.display.set_mode((640, 360), 0 )

clock = pg.time.Clock()
score_font = pg.font.SysFont("monospace", 64)

left_paddle = pg.Rect(45, 5, 15, 60)
right_paddle = pg.Rect(580, 5, 15, 60)
ball = pg.Rect(320, 240, 20, 20)
ball_speed = [-2, 1]

fingers = {}

p1fingers = []
p2fingers = []

p1score = 0
p2score = 0
last_scorer = 0

big_ball_time = 0
big_left_time = 0
big_right_time = 0
score_time = 0

audio = False
running = True


def step():
    global running, score_time, ball, ball_speed, big_left_time, big_right_time
    global big_ball_time, p1score, p2score, last_scorer, clock, screen
    global audio

    if not running:
        return

    if audio:
        pg.mixer.init()
        pg.mixer_music.set_volume(0.5)
        pg.mixer_music.load("Eisenfunk - Pong.ogg")
        pg.mixer_music.play()
        audio = False

    pg.event.pump()

    for event in pg.event.get(pg.FINGERDOWN, pump=False):
        fingers[event.finger_id] = (event.x, event.y)
        if event.x < 0.5:
            p1fingers.append(event.finger_id)
        else:
            p2fingers.append(event.finger_id)

    for event in pg.event.get(pg.FINGERMOTION, pump=False):
        fingers[event.finger_id] = (event.x, event.y)

    for event in pg.event.get(pg.FINGERUP, pump=False):
        del fingers[event.finger_id]

        if event.finger_id in p1fingers:
            p1fingers.remove(event.finger_id)
        if event.finger_id in p2fingers:
            p2fingers.remove(event.finger_id)

    for event in pg.event.get(pg.QUIT, pump=False):
        running = False

    for event in pg.event.get():
        #print(event.type)
        pass

    keys = pg.key.get_pressed()

    if score_time > 0:
        score_time -= 1
        if score_time == 0:
            ball = pg.Rect(320, 240, 20, 20)
            if last_scorer == 1:
                ball_speed = [-2, 1]
            else:
                ball_speed = [2, -1]
    else:
        if p1fingers:
            fx, fy = fingers[p1fingers[0]]
            y = int(fy * 360)
            if y - left_paddle.centery > 10:
                left_paddle.centery += 10
            elif y - left_paddle.centery < -10:
                left_paddle.centery -= 10
            else:
                left_paddle.centery = y

        if p2fingers:
            fx, fy = fingers[p2fingers[0]]
            y = int(fy * 360)
            if y - right_paddle.centery > 10:
                right_paddle.centery += 10
            elif y - right_paddle.centery < -10:
                right_paddle.centery -= 10
            else:
                right_paddle.centery = y

        if keys[pg.K_f]:
            left_paddle.centery -= 3
        if keys[pg.K_v]:
            left_paddle.centery += 3

        if left_paddle.bottom > 360:
            left_paddle.bottom = 360
        if left_paddle.top < 0:
            left_paddle.top = 0

        if right_paddle.bottom > 360:
            right_paddle.bottom = 360
        if right_paddle.top < 0:
            right_paddle.top = 0

        ball.centerx += ball_speed[0]
        if ball_speed[0] < 0 and ball.colliderect(left_paddle):
            ball_speed[0] = -ball_speed[0]
            big_ball_time += 5
            big_left_time += 15

        if ball_speed[0] > 0 and ball.colliderect(right_paddle):
            ball_speed[0] = -ball_speed[0]
            big_ball_time += 5
            big_right_time += 15

        if ball_speed[0] < 0 and ball.left < 0:
            score_time = 50
            p2score += 1
            last_scorer = 2
        if ball_speed[0] > 0 and ball.right > 640:
            score_time = 50
            p1score += 1
            last_scorer = 1

        ball.centery += ball_speed[1]
        if ball_speed[1] > 0 and ball.bottom >= 360:
            ball_speed[1] = -ball_speed[1]
            big_ball_time += 5
        if ball_speed[1] < 0 and ball.top <= 0:
            ball_speed[1] = -ball_speed[1]
            big_ball_time += 5

    if score_time > 0:
        fg = (255, 255, 255)
        bg = (50, 20, 20)
    else:
        fg = (255, 255, 255)
        bg = (0, 0, 0)

    screen.fill(bg)
    if big_left_time > 0:
        pg.draw.rect(screen, fg, left_paddle, 5)
        big_left_time -= 1
    else:
        pg.draw.rect(screen, fg, left_paddle)

    if big_right_time > 0:
        pg.draw.rect(screen, fg, right_paddle, 5)
        big_right_time -= 1
    else:
        pg.draw.rect(screen, fg, right_paddle)

    if big_ball_time > 0:
        pg.draw.rect(screen, fg, ball, 5)
        big_ball_time -= 1
    else:
        pg.draw.rect(screen, fg, ball)

    pg.draw.line(screen, fg, (320 - 1, 0), (320 - 1, 360), 2)
    score_surf = score_font.render(f"{p1score:02}:{p2score:02}", 1, fg)
    screen.blit(score_surf, (320 - score_surf.get_width() // 2, 5))

    clock.tick(30)

    pg.display.flip()


if __EMSCRIPTEN__:
    aio.steps.append(step)
else:
    while running:
        step()
