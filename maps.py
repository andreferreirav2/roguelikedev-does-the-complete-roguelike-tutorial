from libtcod import libtcodpy as libtcod

from consts import *
import painters
import entities


class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [[Tile(x, y, blocks=True) for y in range(0, self.height)] for x in range(0, self.width)]

        self.rooms = []
        self.objects = []
        self.player = None
        self.game_manager = None

        # self.create_rooms()
        self.create_rooms_bsp()

    def is_occupied(self, x, y):
        return self.tiles[x][y].blocks or self.get_occupier(x, y)

    def get_occupier(self, x, y):
        for obj in self.objects:
            if obj.blocks and obj.x == x and obj.y == y:
                return obj

        return None

    def clear_tile(self, x, y):
        self.tiles[x][y].blocks = False
        self.tiles[x][y].block_sight = False

    def create_room(self, rect):
        for x in range(rect.x1, rect.x2):
            for y in range(rect.y1, rect.y2):
                self.clear_tile(x, y)

        self.rooms.append(rect)

    def vline(self, x, y1, y2):
        if y1 > y2:
            y1, y2 = y2, y1

        for y in range(y1, y2 + 1):
            self.clear_tile(x, y)

    def vline_up(self, x, y):
        while y >= 0 and self.tiles[x][y].blocks:
            self.clear_tile(x, y)
            y -= 1

    def vline_down(self, x, y):
        while y < MAP_HEIGHT and self.tiles[x][y].blocks:
            self.clear_tile(x, y)
            y += 1

    def hline(self, x1, y, x2):
        if x1 > x2:
            x1, x2 = x2, x1
        for x in range(x1, x2 + 1):
            self.clear_tile(x, y)

    def hline_left(self, x, y):
        while x >= 0 and self.tiles[x][y].blocks:
            self.clear_tile(x, y)
            x -= 1

    def hline_right(self, x, y):
        while x < MAP_WIDTH and self.tiles[x][y].blocks:
            self.clear_tile(x, y)
            x += 1

    def create_rooms_bsp(self):
        # New root node
        bsp = libtcod.bsp_new_with_size(0, 0, MAP_WIDTH, MAP_HEIGHT)

        # Split into nodes
        libtcod.bsp_split_recursive(bsp, 0, BSP_MAP_DEPTH, ROOM_MIN_SIZE + 1, ROOM_MIN_SIZE + 1, 1.5, 1.5)

        # Traverse the nodes and create rooms
        libtcod.bsp_traverse_inverted_level_order(bsp, self.traverse_node())

    def traverse_node(self):
        map = self

        def traverse_node(node, _):
            # Create rooms
            if libtcod.bsp_is_leaf(node):
                minx = node.x + 1
                maxx = node.x + node.w - 1
                miny = node.y + 1
                maxy = node.y + node.h - 1

                if maxx == MAP_WIDTH:
                    maxx -= 1
                if maxy == MAP_HEIGHT:
                    maxy -= 1

                # If it's False the rooms sizes are random, else the rooms are filled to the node's size
                if not BSP_FULL_ROOMS:
                    minx = libtcod.random_get_int(None, minx, maxx - ROOM_MIN_SIZE + 1)
                    miny = libtcod.random_get_int(None, miny, maxy - ROOM_MIN_SIZE + 1)
                    maxx = libtcod.random_get_int(None, minx + ROOM_MIN_SIZE - 2, maxx)
                    maxy = libtcod.random_get_int(None, miny + ROOM_MIN_SIZE - 2, maxy)

                node.x = minx
                node.y = miny
                node.w = maxx - minx
                node.h = maxy - miny

                # Dig room
                self.create_room(Rect(node.x, node.y, node.w, node.h))

            # Create corridors
            elif DIG_CORRIDORS:
                left = libtcod.bsp_left(node)
                right = libtcod.bsp_right(node)
                node.x = min(left.x, right.x)
                node.y = min(left.y, right.y)
                node.w = max(left.x + left.w, right.x + right.w) - node.x
                node.h = max(left.y + left.h, right.y + right.h) - node.y
                if node.horizontal:
                    if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:  # No overlap
                        x1 = libtcod.random_get_int(None, left.x, left.x + left.w - 1)
                        x2 = libtcod.random_get_int(None, right.x, right.x + right.w - 1)
                        y = libtcod.random_get_int(None, left.y + left.h, right.y)
                        map.vline_up(x1, y - 1)
                        map.hline(x1, y, x2)
                        map.vline_down(x2, y + 1)

                    else:  # Overlap
                        minx = max(left.x, right.x)
                        maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                        x = libtcod.random_get_int(None, minx, maxx)
                        map.vline_down(x, right.y)
                        map.vline_up(x, right.y - 1)

                else:
                    if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:  # No overlap
                        y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                        y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                        x = libtcod.random_get_int(None, left.x + left.w, right.x)
                        map.hline_left(x - 1, y1)
                        map.vline(x, y1, y2)
                        map.hline_right(x + 1, y2)
                    else:  # Overlap
                        miny = max(left.y, right.y)
                        maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                        y = libtcod.random_get_int(None, miny, maxy)
                        map.hline_left(right.x - 1, y)
                        map.hline_right(right.x, y)

            return True
        return traverse_node

    def populate(self):
        # Place player and boss
        center_x1, center_y1 = self.rooms[0].center()
        center_x2, center_y2 = self.rooms[-1].center()
        self.add_object(entities.Object('player', center_x1, center_y1, speed=PLAYER_SPEED,
                                            fighter=entities.Fighter(hp=30, defense=1, power=4,
                                                                     death_function=entities.Fighter.player_death),
                                            painter=painters.ObjectPainter(obj_type='player')), is_player=True)
        self.add_object(entities.Object('boss', center_x2, center_y2,
                                            fighter=entities.Fighter(hp=20, defense=3, power=4,
                                                                     death_function=entities.Fighter.monster_death),
                                            ai=entities.BasicMonster(),
                                            painter=painters.ObjectPainter(obj_type='boss')))

        # Place monsters
        for room in self.rooms[1::]:
            num_monsters = libtcod.random_get_int(0, 0, MAX_MONSTERS_PER_ROOM)
            for i in range(num_monsters):
                x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
                y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

                if libtcod.random_get_int(0, 0, 100) < 80:  # 80% chance of getting an orc
                    self.add_object(entities.Object('orc', x, y,
                                                        ai=entities.BasicMonster(),
                                                        fighter=entities.Fighter(hp=5, defense=1, power=3,
                                                                                 death_function=entities.Fighter.monster_death),
                                                        painter=painters.ObjectPainter('orc')))
                else:
                    self.add_object(entities.Object('troll', x, y,
                                                        ai=entities.BasicMonster(),
                                                        fighter=entities.Fighter(hp=10, defense=2, power=2,
                                                                                 death_function=entities.Fighter.monster_death),
                                                        painter=painters.ObjectPainter('troll')))

    def add_object(self, obj, is_player=False):
        if self.is_occupied(obj.x, obj.y):
            return
        obj.is_player = is_player
        self.objects.append(obj)
        obj.map = self

        if is_player:
            if self.player is None:
                self.player = obj
            else:
                raise Exception("There can only be one player, added more than one.")

    def send_to_back(self, obj):
        self.objects.remove(obj)
        self.objects.insert(0, obj)


class Tile:
    def __init__(self, x, y, blocks, block_sight=None):
        self.x = x
        self.y = y
        self.blocks = blocks
        self.seen = not FOG_OF_WAR
        self.visible = False
        if block_sight is None:
            block_sight = blocks
        self.block_sight = block_sight
        self.painter = painters.TilePainter(owner=self)

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
