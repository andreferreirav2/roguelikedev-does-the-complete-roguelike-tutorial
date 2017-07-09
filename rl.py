import os

from libtcod import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

tilemap = None

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
        global tilemap
        if not tilemap.tiles[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self):
        # Draw the player
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # Draw tile where player was
        global tilemap
        tilemap.tiles[self.x][self.y].draw()


class Tile(Drawable):
    def __init__(self, x, y, blocked, block_sight=None):
        Drawable.__init__(self)
        self.x = x
        self.y = y
        self.blocked = blocked
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight

    def draw(self):
        if self.block_sight:
            # Draw wall
            libtcod.console_put_char_ex(con, self.x, self.y, libtcod.CHAR_BLOCK1, libtcod.white, libtcod.black)
        else:
            # Draw floor
            libtcod.console_put_char_ex(con, self.x, self.y, ' ', libtcod.white, libtcod.black)


class Map(Drawable):
    def __init__(self, width, height):
        Drawable.__init__(self)
        self.width = width
        self.height = height
        self.tiles = [[Tile(x, y, blocked=True) for y in range(0, self.height)] for x in range(0, self.width)]

    def draw(self):
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y].draw()

    def clear_tile(self, x, y):
        self.tiles[x][y].blocked = False
        self.tiles[x][y].block_sight = False

    def create_room(self, rect):
        for x in range(rect.x1 + 1, rect.x2):
            for y in range(rect.y1 + 1, rect.y2):
                self.clear_tile(x, y)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.clear_tile(x, y)

    def create_v_tunnel(self, x, y1, y2):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.clear_tile(x, y)


class Rect:
    def __init__(self, x, y, width, height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height


def render_all():
    for obj in objects:
        obj.draw()

    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
    libtcod.console_flush()

    for obj in objects:
        obj.clear()


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

    global tilemap
    tilemap = Map(MAP_WIDTH, MAP_HEIGHT)

    tilemap.create_room(Rect(20, 15, 10, 15))
    tilemap.create_room(Rect(50, 15, 10, 15))
    tilemap.create_h_tunnel(30, 50, 23)
    tilemap.create_v_tunnel(25, 15, 5)
    tilemap.create_h_tunnel(25, 40, 5)
    tilemap.create_v_tunnel(40, 5, 23)

    tilemap.draw()

    player = Object(25, 20, '@', libtcod.white)
    npc = Object(25, 25, '@', libtcod.yellow)
    objects = [player, npc]

    while not libtcod.console_is_window_closed():
        render_all()

        if handle_keys():
            break
