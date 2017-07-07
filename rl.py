import os

from libtcod import libtcodpy as libtcod
from libtcod.libtcodpy import Color

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

PLAYER = dict(x=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT / 2)


def handle_keys():
    global PLAYER

    key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return True  # exit game

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        PLAYER['y'] -= 1

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        PLAYER['y'] += 1

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        PLAYER['x'] -= 1

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        PLAYER['x'] += 1


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    libtcod.console_set_custom_font('{}/arial10x10.png'.format(dir_path), libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
    libtcod.sys_set_fps(LIMIT_FPS)

    while not libtcod.console_is_window_closed():
        # Draw the player
        libtcod.console_set_default_foreground(0, libtcod.red)
        libtcod.console_put_char(0, PLAYER['x'], PLAYER['y'], '@', libtcod.BKGND_NONE)

        #libtcod.console_set_default_foreground(0, libtcod.blue)
        #libtcod.console_put_char(0, 10, 10, '@', libtcod.BKGND_NONE)

        libtcod.console_flush()
        # Clear char behind the player
        libtcod.console_set_default_foreground(0, Color(255, 127, 127))
        libtcod.console_put_char(0, PLAYER['x'], PLAYER['y'], '@', libtcod.BKGND_NONE)


        # key = libtcod.console_wait_for_keypress(True)
        if handle_keys():
            break

