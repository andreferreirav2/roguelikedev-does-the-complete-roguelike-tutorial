import os

from libtcod import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45


class Drawable:
    def __init__(self):
        pass

    def draw(self):
        pass

    def clear(self):
        pass


class Object(Drawable):
    def __init__(self, x, y, char, color):
        Drawable.__init__(self)
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx, dy):
        if not map.map[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self):
        # Draw the player
        libtcod.console_set_default_foreground(0, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)


class Map(Drawable):
    def __init__(self, width, height):
        Drawable.__init__(self)
        self.width = width
        self.height = height
        self.map = [[Tile(False) for y in range(0, self.height)] for x in range(0, self.width)]

        self.color_dark_wall = libtcod.Color(0, 0, 100)
        self.color_dark_ground = libtcod.Color(50, 50, 150)

        self.map[20][30].blocked = True
        self.map[20][30].block_sight = True
        self.map[25][33].blocked = True
        self.map[25][33].block_sight = True

    def draw(self):
        for x in range(self.width):
            for y in range(self.height):
                if self.map[x][y].block_sight:
                    libtcod.console_put_char_ex(con, x, y, '#', libtcod.white, libtcod.black)
                else:
                    libtcod.console_put_char_ex(con, x, y, '.', libtcod.white, libtcod.black)


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight


def render_all():
    for object in objects:
        object.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_flush()

    for object in objects:
        object.clear()

def handle_keys():
    key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return True

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        player.move(0, -1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        player.move(0, 1)

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        player.move(-1, 0)

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        player.move(1, 0)


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    libtcod.console_set_custom_font('{}/arial10x10.png'.format(dir_path),
                                    libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    player = Object(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, '@', libtcod.white)
    npc = Object(SCREEN_WIDTH / 2 + 5, SCREEN_HEIGHT / 2, '@', libtcod.yellow)
    map = Map(MAP_WIDTH, MAP_HEIGHT)
    objects = [map, player, npc]

    while not libtcod.console_is_window_closed():
        render_all()

        if handle_keys():
            break
