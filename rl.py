import os

from libtcod import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

FOV_ALG = libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Secondary console to draw on
con = None
# FOV MAP
fov_map = None

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
        self.game = None
        self.x = x
        self.y = y
        self.seen = False
        self.char = char
        self.color = color

    def move(self, dx, dy):
        if not self.game.map.tiles[self.x + dx][self.y + dy].blocked:
            self.x += dx
            self.y += dy

    def draw(self):
        # Draw the player
        global fov_map
        is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)

        if not self.seen and is_visible:
            self.seen = True

        if self.seen:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self):
        # Draw tile where player was
        self.game.map.tiles[self.x][self.y].draw()


class Tile(Drawable):
    def __init__(self, x, y, blocked, block_sight=None):
        Drawable.__init__(self)
        self.x = x
        self.y = y
        self.seen = False
        self.blocked = blocked
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight

    def draw(self):
        global fov_map
        is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)

        if is_visible:
            if not self.seen:
                self.seen = True

        if self.seen:
            if self.block_sight:
                # Draw wall
                if is_visible:
                    libtcod.console_put_char_ex(con, self.x, self.y, '#', libtcod.darkest_gray, libtcod.darkest_yellow)
                else:
                    libtcod.console_put_char_ex(con, self.x, self.y, '#', libtcod.darkest_gray, libtcod.black)
            else:
                # Draw floor
                if is_visible:
                    libtcod.console_put_char_ex(con, self.x, self.y, ' ', libtcod.white, libtcod.light_yellow)
                else:
                    libtcod.console_put_char_ex(con, self.x, self.y, ' ', libtcod.white, libtcod.darker_gray)


class Map(Drawable):
    def __init__(self, width, height):
        Drawable.__init__(self)
        self.width = width
        self.height = height
        self.tiles = [[Tile(x, y, blocked=True) for y in range(0, self.height)] for x in range(0, self.width)]

        self.rooms = []

    def draw(self):
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y].draw()

    def clear_tile(self, x, y):
        self.tiles[x][y].blocked = False
        self.tiles[x][y].block_sight = False

    def create_room(self, rect):
        self.rooms.append(rect)
        for x in range(rect.x1 + 1, rect.x2):
            for y in range(rect.y1 + 1, rect.y2):
                self.clear_tile(x, y)

    def connect_rooms(self):
        for i in range(0, len(self.rooms) - 1):
            room_x, room_y = self.rooms[i].center()
            next_x, next_y = self.rooms[i + 1].center()

            if libtcod.random_get_int(0, 0, 1) == 1:
                self.create_h_tunnel(room_x, next_x, room_y)
                self.create_v_tunnel(next_x, room_y, next_y)
            else:
                self.create_v_tunnel(room_x, next_y, room_y)
                self.create_h_tunnel(next_x, room_x, next_y)

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

    def center(self):
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2

    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Game:
    def __init__(self):
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)

        for i in range(MAX_ROOMS):
            # random width and height
            width = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            height = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            # random position without going out of the boundaries of the map
            x = libtcod.random_get_int(0, 0, MAP_WIDTH - width - 1)
            y = libtcod.random_get_int(0, 0, MAP_HEIGHT - height - 1)

            new_room = Rect(x, y, width, height)
            if len([True for room in self.map.rooms if new_room.intersects(room)]) == 0:
                self.map.create_room(new_room)

        self.map.connect_rooms()
        self.objects = []
        self.player = None

    def add_object(self, obj, player=False):
        obj.game = self
        self.objects.append(obj)
        if player:
            if self.player is None:
                self.player = obj
            else:
                raise Exception("There can only be one player, added more than one.")

    def render_all(self):
        self.map.draw()

        for obj in self.objects:
            obj.draw()

        libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

        for obj in self.objects:
            obj.clear()


def handle_keys(game):
    key = libtcod.console_check_for_keypress()
    abort, recalc_fov = False, False

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        abort = True

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        game.player.move(0, -1)
        recalc_fov = True

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        game.player.move(0, 1)
        recalc_fov = True

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        game.player.move(-1, 0)
        recalc_fov = True

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        game.player.move(1, 0)
        recalc_fov = True

    return abort, recalc_fov


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    libtcod.console_set_custom_font('{}/arial10x10.png'.format(dir_path), libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    global con
    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    game = Game()

    center_x1, center_y1 = game.map.rooms[0].center()
    center_x2, center_y2 = game.map.rooms[-1].center()
    game.add_object(Object(center_x1, center_y1, '@', libtcod.blue), player=True)
    game.add_object(Object(center_x2, center_y2, '@', libtcod.red))

    global fov_map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not game.map.tiles[x][y].block_sight, game.map.tiles[x][y].blocked)
    libtcod.map_compute_fov(fov_map, game.player.x, game.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)

    while not libtcod.console_is_window_closed():
        game.render_all()
        abort, recalc_fov = handle_keys(game)
        if abort:
            break
        if recalc_fov:
            libtcod.map_compute_fov(fov_map, game.player.x, game.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)


if __name__ == '__main__':
    main()
