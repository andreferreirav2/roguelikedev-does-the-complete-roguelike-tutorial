import os

from libtcod import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 15

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_MONSTERS_PER_ROOM = 3

FOV_ALG = libtcod.FOV_BASIC
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# Secondary console to draw on
con = None
# FOV MAP
fov_map = None

ACTION_EXIT, ACTION_RECALC_FOV = 0, 1

class Drawable:
    def __init__(self, x, y, blocks=False):
        self.x = x
        self.y = y
        self.blocks = blocks
        self.seen = False

    def calculate_visibility(self):
        is_visible = libtcod.map_is_in_fov(fov_map, self.x, self.y)
        if not self.seen and is_visible:
            self.seen = True

        return is_visible

    def draw(self):
        pass


class Object(Drawable):
    def __init__(self, x, y, char, color, blocks=False):
        Drawable.__init__(self, x, y, blocks)
        self.char = char
        self.color = color
        self.game_map = None

    def move(self, dx, dy):
        if self.game_map.is_empty(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        # Draw the player
        is_visible = self.calculate_visibility()

        if is_visible:
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)


class Tile(Drawable):
    def __init__(self, x, y, blocks, block_sight=None):
        Drawable.__init__(self, x, y, blocks)
        if block_sight is None:
            block_sight = blocks
        self.block_sight = block_sight

    def draw(self):
        is_visible = self.calculate_visibility()

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


class Map:
    def __init__(self, width, height, auto_create=False):
        self.width = width
        self.height = height
        self.tiles = [[Tile(x, y, blocks=True) for y in range(0, self.height)] for x in range(0, self.width)]

        self.rooms = []
        self.objects = []
        self.player = None

        if auto_create:
            self.create_rooms()

    def is_empty(self, x, y):
        if self.tiles[x][y].blocks:
            return False

        for obj in self.objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return False

        return True

    def draw(self):
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y].draw()

    def clear_tile(self, x, y):
        self.tiles[x][y].blocks = False
        self.tiles[x][y].block_sight = False

    def create_room(self, rect, place_monsters=False):
        for x in range(rect.x1 + 1, rect.x2):
            for y in range(rect.y1 + 1, rect.y2):
                self.clear_tile(x, y)

        self.rooms.append(rect)

        if place_monsters and len(self.rooms) != 1:  # Don't put monsters in the 1st room
            num_monsters = libtcod.random_get_int(0, 0, MAX_MONSTERS_PER_ROOM)
            for i in range(num_monsters):
                x = libtcod.random_get_int(0, rect.x1 + 1, rect.x2 - 1)
                y = libtcod.random_get_int(0, rect.y1 + 1, rect.y2 - 1)

                if libtcod.random_get_int(0, 0, 100) < 80:  # 80% chance of getting an orc
                    # create an orc
                    self.add_object(Object(x, y, 'o', libtcod.desaturated_green, blocks=True))
                else:
                    # create a troll
                    self.add_object(Object(x, y, 'T', libtcod.darker_green, blocks=True))

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

    def create_rooms(self):
        for i in range(MAX_ROOMS):
            # random width and height
            width = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            height = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)

            # random position without going out of the boundaries of the map
            x = libtcod.random_get_int(0, 0, MAP_WIDTH - width - 1)
            y = libtcod.random_get_int(0, 0, MAP_HEIGHT - height - 1)

            new_room = Rect(x, y, width, height)
            if len([True for room in self.rooms if new_room.intersects(room)]) == 0:
                self.create_room(new_room, place_monsters=True)

        self.connect_rooms()

    def add_object(self, obj, player=False):
        if not self.is_empty(obj.x, obj.y):
            return
        obj.game_map = self
        self.objects.append(obj)
        if player:
            if self.player is None:
                self.player = obj
            else:
                raise Exception("There can only be one player, added more than one.")

    def render_all(self):
        self.draw()

        for obj in self.objects:
            obj.draw()

        libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()


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


def handle_keys(game):
    key = libtcod.console_check_for_keypress()
    action = None

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

    elif key.vk == libtcod.KEY_ESCAPE:
        return ACTION_EXIT

    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_UP):
        game.player.move(0, -1)
        action = ACTION_RECALC_FOV

    elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
        game.player.move(0, 1)
        action = ACTION_RECALC_FOV

    elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
        game.player.move(-1, 0)
        action = ACTION_RECALC_FOV

    elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
        game.player.move(1, 0)
        action = ACTION_RECALC_FOV

    return action


def main():
    global con
    global fov_map

    dir_path = os.path.dirname(os.path.realpath(__file__))
    libtcod.console_set_custom_font('{}/arial10x10.png'.format(dir_path),
                                    libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
    libtcod.sys_set_fps(LIMIT_FPS)
    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    game_map = Map(MAP_WIDTH, MAP_HEIGHT, auto_create=True)

    center_x1, center_y1 = game_map.rooms[0].center()
    center_x2, center_y2 = game_map.rooms[-1].center()
    game_map.add_object(Object(center_x1, center_y1, '@', libtcod.blue), player=True)
    game_map.add_object(Object(center_x2, center_y2, '@', libtcod.red))

    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not game_map.tiles[x][y].block_sight, game_map.tiles[x][y].blocks)
    libtcod.map_compute_fov(fov_map, game_map.player.x, game_map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)

    while not libtcod.console_is_window_closed():
        game_map.render_all()
        action = handle_keys(game_map)
        if action == ACTION_EXIT:
            break
        if action == ACTION_RECALC_FOV:
            libtcod.map_compute_fov(fov_map, game_map.player.x, game_map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)


if __name__ == '__main__':
    main()
