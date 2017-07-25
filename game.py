import os
import textwrap

from libtcod import libtcodpy as libtcod
from consts import *
import maps
import painters
import entities


class GameManager:

    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        libtcod.console_set_custom_font('{}/assets/arial10x10.png'.format(dir_path), libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'rl', False)
        libtcod.sys_set_fps(LIMIT_FPS)

        self.map = maps.Map(MAP_WIDTH, MAP_HEIGHT, auto_create=True)
        self.map.game_manager = self

        # Populate map
        self.populate_map()

        self.fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                libtcod.map_set_properties(self.fov_map, x, y, not self.map.tiles[x][y].block_sight, self.map.tiles[x][y].blocks)
        libtcod.map_compute_fov(self.fov_map, self.map.player.x, self.map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)

        self.messages = []
        self.add_message("Welcome stranger, will you dare to look around? Be careful, it's dangerous out there!", libtcod.red)

        self.painter = painters.GamePainter(owner=self)
        self.key = libtcod.Key()
        self.mouse = libtcod.Mouse()

        # Game State
        self.game_state = STATE_PLAYING

    def populate_map(self):
        # Place player and boss
        center_x1, center_y1 = self.map.rooms[0].center()
        center_x2, center_y2 = self.map.rooms[-1].center()
        self.map.add_object(entities.Object('player', center_x1, center_y1, speed=PLAYER_SPEED,
                                            fighter=entities.Fighter(hp=30, defense=1, power=4, death_function=entities.Fighter.player_death),
                                            painter=painters.ObjectPainter(obj_type='player')), is_player=True)
        self.map.add_object(entities.Object('boss', center_x2, center_y2,
                                            fighter=entities.Fighter(hp=20, defense=3, power=4, death_function=entities.Fighter.monster_death),
                                            ai=entities.BasicMonster(),
                                            painter=painters.ObjectPainter(obj_type='boss')))

        # Place monsters
        for room in self.map.rooms[1::]:
            num_monsters = libtcod.random_get_int(0, 0, MAX_MONSTERS_PER_ROOM)
            for i in range(num_monsters):
                x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
                y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

                if libtcod.random_get_int(0, 0, 100) < 80:  # 80% chance of getting an orc
                    self.map.add_object(entities.Object('orc', x, y,
                                                        ai=entities.BasicMonster(),
                                                        fighter=entities.Fighter(hp=5, defense=1, power=3, death_function=entities.Fighter.monster_death),
                                                        painter=painters.ObjectPainter('orc')))
                else:
                    self.map.add_object(entities.Object('troll', x, y,
                                                        ai=entities.BasicMonster(),
                                                        fighter=entities.Fighter(hp=10, defense=2, power=2, death_function=entities.Fighter.monster_death),
                                                        painter=painters.ObjectPainter('troll')))

    def recalculate_visibility(self):
        libtcod.map_compute_fov(self.fov_map, self.map.player.x, self.map.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALG)

    def calculate_visibility(self, obj):
        is_visible = libtcod.map_is_in_fov(self.fov_map, obj.x, obj.y)
        if not obj.seen and is_visible:
            obj.seen = True

        obj.visible = is_visible

        return is_visible

    def add_message(self, message, color = libtcod.white):
        message_lines = textwrap.wrap(message, MSG_WIDTH)

        for line in message_lines:
            if len(self.messages) >= MSG_HEIGHT:
                del self.messages[0]

            self.messages.append((line, color))

    def handle_keys(self):
        action = None

        if self.key.vk == libtcod.KEY_ENTER and self.key.lalt:
            # Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        elif self.key.vk == libtcod.KEY_SPACE:
            self.game_state = self.game_state ^ 1
            return None

        elif self.key.vk == libtcod.KEY_ESCAPE:
            return ACTION_EXIT

        # movement keys
        if self.game_state == STATE_PLAYING:
            if self.key.vk == libtcod.KEY_UP:
                self.map.player.move_or_attack(0, -1)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_DOWN:
                self.map.player.move_or_attack(0, 1)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_LEFT:
                self.map.player.move_or_attack(-1, 0)
                action = ACTION_MOVE

            elif self.key.vk == libtcod.KEY_RIGHT:
                self.map.player.move_or_attack(1, 0)
                action = ACTION_MOVE

        return action

    def get_element_under_mouse(self):
        (x, y) = self.mouse.cx, self.mouse.cy

        elements = [obj.name for obj in self.map.objects[::-1] if obj.visible and obj.x == x and obj.y == y]

        if x >= 0 and x < MAP_WIDTH and y >= 0 and y < MAP_HEIGHT and \
                self.map.tiles[x][y].visible and self.map.tiles[x][y].blocks:
            elements.append("wall")

        return ", ".join(elements).capitalize()

    def run(self):
        while not libtcod.console_is_window_closed():
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, self.key, self.mouse)
            self.painter.draw()
            action = self.handle_keys()

            # Do actions
            if self.game_state is STATE_PLAYING:
                for obj in self.map.objects:
                    obj.wait -= 1
                    if obj.ai:
                        obj.ai.take_turn()

            # Calculate visibility for tiles and objects
            for row in self.map.tiles:
                for tile in row:
                    self.calculate_visibility(tile)
            for obj in self.map.objects:
                self.calculate_visibility(obj)

            if action == ACTION_EXIT:
                break
            # if action == ACTION_MOVE:
            self.recalculate_visibility()

