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

        self.create_rooms()

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
        for x in range(rect.x1 + 1, rect.x2):
            for y in range(rect.y1 + 1, rect.y2):
                self.clear_tile(x, y)

        self.rooms.append(rect)

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
                self.create_room(new_room)

        self.connect_rooms()

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
        self.seen = False
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
